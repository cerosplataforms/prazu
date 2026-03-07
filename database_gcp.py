"""
database_gcp.py — Prazu Fase 2
Acesso ao Cloud SQL (Postgres) via asyncpg.

Substitui database_fase2.py (SQLite) e coexiste com database.py (legado Telegram).
Todas as funções são async — compatível com FastAPI.

Conexão via Cloud SQL Connector (produção) ou host direto (dev local).
"""

import os
import asyncio
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg
from google.cloud.sql.connector import AsyncConnector

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuração de conexão
# ---------------------------------------------------------------------------

# Em produção (Cloud Run): usa Cloud SQL Connector via socket Unix
# Em desenvolvimento local: usa host IP direto
ENVIRONMENT   = os.getenv("ENVIRONMENT", "development")
DB_HOST       = os.getenv("DB_HOST", "34.39.197.67")
DB_NAME       = os.getenv("DB_NAME", "prazu")
DB_USER       = os.getenv("DB_USER", "prazu_user")
DB_PASSWORD   = os.getenv("DB_PASSWORD", "")
GCP_PROJECT   = os.getenv("GCP_PROJECT", "prazu-prod")
CLOUD_SQL_CONN = f"{GCP_PROJECT}:southamerica-east1:prazu-db"

_pool: Optional[asyncpg.Pool] = None
_connector: Optional[AsyncConnector] = None


async def _get_conn_prod(connector: AsyncConnector) -> asyncpg.Connection:
    """Conexão via Cloud SQL Connector (produção)."""
    return await connector.connect(
        CLOUD_SQL_CONN,
        "asyncpg",
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
    )


async def init_db():
    """Inicializa o pool de conexões. Chamar no startup do FastAPI."""
    global _pool, _connector

    if ENVIRONMENT == "production":
        _connector = AsyncConnector()
        _pool = await asyncpg.create_pool(
            min_size=2,
            max_size=10,
            connect=lambda: _get_conn_prod(_connector),
        )
        log.info("DB: pool conectado via Cloud SQL Connector")
    else:
        # Dev local: conexão direta pelo IP
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            min_size=1,
            max_size=5,
        )
        log.info(f"DB: pool conectado em {DB_HOST}/{DB_NAME}")


async def close_db():
    """Fecha o pool. Chamar no shutdown do FastAPI."""
    global _pool, _connector
    if _pool:
        await _pool.close()
    if _connector:
        await _connector.close()
    log.info("DB: pool encerrado")


@asynccontextmanager
async def db():
    """Context manager para pegar uma conexão do pool."""
    async with _pool.acquire() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Senhas
# ---------------------------------------------------------------------------

def hash_senha(senha: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{senha}".encode()).hexdigest()
    return f"{salt}:{h}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        salt, h = senha_hash.split(":", 1)
        return hashlib.sha256(f"{salt}{senha}".encode()).hexdigest() == h
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Advogados
# ---------------------------------------------------------------------------

async def criar_advogado(
    nome: str,
    email: str,
    senha: str,
    oab_numero: str,
    oab_seccional: str,
    whatsapp: Optional[str] = None,
) -> Optional[int]:
    """
    Cria advogado com trial de 7 dias.
    Retorna ID ou None se email/OAB/whatsapp já existe.
    """
    agora = datetime.now(timezone.utc)
    trial_fim = agora + timedelta(days=7)

    try:
        async with db() as conn:
            async with conn.transaction():
                advogado_id = await conn.fetchval(
                    """
                    INSERT INTO advogados
                        (nome, email, senha_hash, oab_numero, oab_seccional,
                         whatsapp, status, trial_inicio, trial_fim)
                    VALUES ($1, $2, $3, $4, $5, $6, 'trial', $7, $8)
                    RETURNING id
                    """,
                    nome.strip(),
                    email.lower().strip(),
                    hash_senha(senha),
                    oab_numero.strip().upper(),
                    oab_seccional.strip().upper(),
                    whatsapp,
                    agora,
                    trial_fim,
                )

                # Registra trial em assinaturas
                await conn.execute(
                    """
                    INSERT INTO assinaturas
                        (advogado_id, plano, status, periodo_inicio, periodo_fim)
                    VALUES ($1, 'individual', 'trial', $2, $3)
                    """,
                    advogado_id,
                    agora.date(),
                    trial_fim.date(),
                )

        return advogado_id

    except asyncpg.UniqueViolationError:
        return None


async def buscar_por_email(email: str) -> Optional[dict]:
    async with db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM advogados WHERE email = $1",
            email.lower().strip(),
        )
    return dict(row) if row else None


async def buscar_por_id(advogado_id: int) -> Optional[dict]:
    async with db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM advogados WHERE id = $1", advogado_id
        )
    return dict(row) if row else None


async def buscar_por_whatsapp(whatsapp: str) -> Optional[dict]:
    """Lookup pelo número WhatsApp — usado no webhook Z-API."""
    async with db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM advogados WHERE whatsapp = $1", whatsapp
        )
    return dict(row) if row else None


async def buscar_por_oab(oab_numero: str, oab_seccional: str) -> Optional[dict]:
    async with db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM advogados WHERE oab_numero = $1 AND oab_seccional = $2",
            oab_numero.strip().upper(),
            oab_seccional.strip().upper(),
        )
    return dict(row) if row else None


async def listar_advogados_ativos() -> list[dict]:
    """Retorna todos os advogados ativos — usado pelo scheduler de briefing."""
    async with db() as conn:
        rows = await conn.fetch(
            "SELECT * FROM advogados WHERE ativo = TRUE AND status IN ('trial','ativo')"
        )
    return [dict(r) for r in rows]


async def atualizar_whatsapp(advogado_id: int, whatsapp: str, confirmado: bool = False):
    async with db() as conn:
        await conn.execute(
            "UPDATE advogados SET whatsapp = $1, zapi_confirmado = $2 WHERE id = $3",
            whatsapp, confirmado, advogado_id,
        )


async def confirmar_whatsapp(advogado_id: int):
    async with db() as conn:
        await conn.execute(
            "UPDATE advogados SET zapi_confirmado = TRUE WHERE id = $1",
            advogado_id,
        )


async def atualizar_comarca(advogado_id: int, comarca: str):
    async with db() as conn:
        await conn.execute(
            "UPDATE advogados SET comarca = $1 WHERE id = $2",
            comarca, advogado_id,
        )


async def atualizar_last_seen(advogado_id: int):
    async with db() as conn:
        await conn.execute(
            "UPDATE advogados SET last_seen = NOW() WHERE id = $1",
            advogado_id,
        )


async def atualizar_ultima_busca_djen(advogado_id: int):
    async with db() as conn:
        await conn.execute(
            "UPDATE advogados SET ultima_busca_djen = NOW() WHERE id = $1",
            advogado_id,
        )


async def atualizar_status(advogado_id: int, status: str):
    async with db() as conn:
        await conn.execute(
            "UPDATE advogados SET status = $1 WHERE id = $2",
            status, advogado_id,
        )


# ---------------------------------------------------------------------------
# Controle de acesso
# ---------------------------------------------------------------------------

async def pode_usar(advogado_id: int) -> bool:
    adv = await buscar_por_id(advogado_id)
    if not adv:
        return False
    if adv["status"] == "ativo":
        return True
    if adv["status"] == "trial":
        trial_fim = adv.get("trial_fim")
        if trial_fim:
            if trial_fim.tzinfo is None:
                trial_fim = trial_fim.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) <= trial_fim
    return False


async def advogados_trial_expirando(dias: int = 2) -> list[dict]:
    """Para enviar lembrete de trial acabando."""
    alvo = (datetime.now(timezone.utc) + timedelta(days=dias)).date()
    async with db() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM advogados
            WHERE status = 'trial'
              AND trial_fim::date = $1
              AND whatsapp IS NOT NULL
              AND zapi_confirmado = TRUE
            """,
            alvo,
        )
    return [dict(r) for r in rows]


async def expirar_trials_vencidos() -> int:
    """Atualiza trials vencidos para 'expirado'. Chamado pelo Cloud Scheduler."""
    async with db() as conn:
        result = await conn.execute(
            """
            UPDATE advogados
            SET status = 'expirado'
            WHERE status = 'trial' AND trial_fim < NOW()
            """
        )
    count = int(result.split()[-1])
    if count:
        log.info(f"expirar_trials_vencidos: {count} advogado(s) expirados")
    return count


# ---------------------------------------------------------------------------
# Sessions (autenticação do site)
# ---------------------------------------------------------------------------

async def criar_session(
    advogado_id: int,
    user_agent: str = "",
    ip: str = "",
    ttl_dias: int = 30,
) -> str:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_dias)
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO sessions (advogado_id, token, user_agent, ip, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            advogado_id, token, user_agent, ip, expires_at,
        )
    return token


async def validar_session(token: str) -> Optional[dict]:
    async with db() as conn:
        session = await conn.fetchrow(
            "SELECT * FROM sessions WHERE token = $1 AND expires_at > NOW()",
            token,
        )
        if not session:
            return None
        row = await conn.fetchrow(
            "SELECT * FROM advogados WHERE id = $1", session["advogado_id"]
        )
    return dict(row) if row else None


async def revogar_session(token: str):
    async with db() as conn:
        await conn.execute("DELETE FROM sessions WHERE token = $1", token)


async def limpar_sessions_expiradas() -> int:
    async with db() as conn:
        result = await conn.execute(
            "DELETE FROM sessions WHERE expires_at < NOW()"
        )
    return int(result.split()[-1])


# ---------------------------------------------------------------------------
# WhatsApp events log
# ---------------------------------------------------------------------------

async def log_whatsapp(
    advogado_id: Optional[int],
    direcao: str,
    tipo: str,
    conteudo: str = "",
    zapi_message_id: str = "",
    status: str = "enviado",
):
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO whatsapp_events
                (advogado_id, direcao, tipo, conteudo, zapi_message_id, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            advogado_id, direcao, tipo, conteudo, zapi_message_id, status,
        )


# ---------------------------------------------------------------------------
# Processos
# ---------------------------------------------------------------------------

async def listar_processos_com_prazos(advogado_id: int) -> list[dict]:
    """Retorna processos ativos com prazos abertos — usado pelo briefing."""
    async with db() as conn:
        processos = await conn.fetch(
            "SELECT * FROM processos WHERE advogado_id = $1 AND status = 'ativo'",
            advogado_id,
        )
        resultado = []
        for p in processos:
            p_dict = dict(p)
            prazos = await conn.fetch(
                """
                SELECT * FROM prazos
                WHERE processo_id = $1 AND cumprido = FALSE
                ORDER BY data_fim ASC
                """,
                p["id"],
            )
            p_dict["prazos"] = [dict(pr) for pr in prazos]
            resultado.append(p_dict)
    return resultado


async def processo_existe(advogado_id: int, numero: str) -> bool:
    async with db() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM processos WHERE advogado_id = $1 AND numero = $2 AND status = 'ativo'",
            advogado_id, numero,
        )
    return row is not None


async def comunicacao_existe(advogado_id: int, numero_processo: str, data_disponibilizacao) -> bool:
    async with db() as conn:
        row = await conn.fetchrow(
            """
            SELECT id FROM comunicacoes_djen
            WHERE advogado_id = $1 AND numero_processo = $2 AND data_disponibilizacao = $3
            """,
            advogado_id, numero_processo, data_disponibilizacao,
        )
    return row is not None


# ---------------------------------------------------------------------------
# Assinaturas (Stripe)
# ---------------------------------------------------------------------------

async def ativar_assinatura(
    advogado_id: int,
    stripe_subscription_id: str,
    stripe_price_id: str,
    valor_centavos: int,
    periodo_inicio,
    periodo_fim,
):
    async with db() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO assinaturas
                    (advogado_id, plano, status, stripe_subscription_id,
                     stripe_price_id, valor_centavos, periodo_inicio, periodo_fim)
                VALUES ($1, 'individual', 'ativo', $2, $3, $4, $5, $6)
                """,
                advogado_id, stripe_subscription_id, stripe_price_id,
                valor_centavos, periodo_inicio, periodo_fim,
            )
            await conn.execute(
                """
                UPDATE advogados
                SET status = 'ativo', stripe_subscription_id = $1
                WHERE id = $2
                """,
                stripe_subscription_id, advogado_id,
            )


# ---------------------------------------------------------------------------
# Diagnóstico
# ---------------------------------------------------------------------------

async def diagnostico() -> dict:
    async with db() as conn:
        total     = await conn.fetchval("SELECT COUNT(*) FROM advogados")
        trials    = await conn.fetchval("SELECT COUNT(*) FROM advogados WHERE status='trial'")
        ativos    = await conn.fetchval("SELECT COUNT(*) FROM advogados WHERE status='ativo'")
        expirados = await conn.fetchval("SELECT COUNT(*) FROM advogados WHERE status='expirado'")
        wpp_ok    = await conn.fetchval(
            "SELECT COUNT(*) FROM advogados WHERE whatsapp IS NOT NULL AND zapi_confirmado=TRUE"
        )
        processos = await conn.fetchval("SELECT COUNT(*) FROM processos WHERE status='ativo'")
        prazos    = await conn.fetchval("SELECT COUNT(*) FROM prazos WHERE cumprido=FALSE")
    return {
        "total_advogados": total,
        "trials_ativos": trials,
        "assinantes": ativos,
        "expirados": expirados,
        "whatsapp_confirmados": wpp_ok,
        "processos_ativos": processos,
        "prazos_abertos": prazos,
    }
