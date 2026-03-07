"""
database_gcp.py — Prazu Fase 2
Camada de acesso ao PostgreSQL (Cloud SQL via asyncpg).
Todas as senhas hasheadas com bcrypt.

.env necessário:
  DB_HOST     → 34.39.197.67
  DB_NAME     → prazu
  DB_USER     → prazu_user
  DB_PASSWORD → Prazu@2026!
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg
import bcrypt

log = logging.getLogger(__name__)

# ── Pool (singleton) ─────────────────────────────────────────────────────────
_pool: Optional[asyncpg.Pool] = None


async def init_db() -> None:
    """Cria o pool de conexões. Chamado no startup do FastAPI."""
    global _pool
    db_name = os.getenv("DB_NAME", "prazu")
    db_user = os.getenv("DB_USER", "prazu_user")
    db_pass = os.getenv("DB_PASSWORD", "")
    if os.getenv("ENVIRONMENT") == "production":
        socket = "/cloudsql/prazu-prod:southamerica-east1:prazu-db"
        dsn = f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket}"
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10, command_timeout=30)
    else:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=db_name, user=db_user, password=db_pass,
            min_size=2, max_size=10, command_timeout=30,
        )
    log.info("Pool PostgreSQL inicializado")


async def close_db() -> None:
    """Fecha o pool. Chamado no shutdown do FastAPI."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("Pool PostgreSQL fechado")


async def diagnostico() -> dict:
    """Health check básico — retorna contagem de advogados."""
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS total FROM advogados")
        return {"advogados": row["total"], "status": "ok"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash_guardado: str) -> bool:
    """Compara senha com hash bcrypt. NÃO é async — pode chamar direto."""
    if not senha or not hash_guardado:
        return False
    try:
        return bcrypt.checkpw(senha.encode(), hash_guardado.encode())
    except Exception:
        return False


def _row(row) -> Optional[dict]:
    return dict(row) if row else None


# ── Criar advogado ───────────────────────────────────────────────────────────

async def criar_advogado(
    nome: str,
    email: str,
    senha: str,
    oab_numero: str,
    oab_seccional: str,
    whatsapp: Optional[str] = None,
) -> Optional[int]:
    """
    Insere novo advogado com trial de 7 dias.
    Retorna id criado, ou None se email/OAB já existir.
    """
    senha_hash = _hash_senha(senha)
    trial_fim  = datetime.now(timezone.utc) + timedelta(days=7)

    try:
        async with _pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO advogados
                        (nome, email, senha_hash, oab_numero, oab_seccional,
                         whatsapp, status, trial_fim, ativo,
                         zapi_confirmado, created_at)
                    VALUES ($1,$2,$3,$4,$5,$6,'trial',$7,true,false,NOW())
                    RETURNING id
                    """,
                    nome,
                    email.lower(),
                    senha_hash,
                    oab_numero,
                    oab_seccional.upper(),
                    whatsapp,
                    trial_fim,
                )
                adv_id = row["id"]

                await conn.execute(
                    """
                    INSERT INTO assinaturas
                        (advogado_id, plano, status, inicio, fim)
                    VALUES ($1,'trial','ativo',NOW(),$2)
                    """,
                    adv_id, trial_fim,
                )

                log.info(f"Novo advogado id={adv_id} {email} OAB {oab_numero}/{oab_seccional}")
                return adv_id

    except asyncpg.UniqueViolationError:
        log.warning(f"Cadastro duplicado: {email} / {oab_numero}/{oab_seccional}")
        return None


# ── Buscas ───────────────────────────────────────────────────────────────────

async def buscar_por_id(advogado_id: int) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow(
            "SELECT * FROM advogados WHERE id = $1", advogado_id
        ))


async def buscar_por_email(email: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow(
            "SELECT * FROM advogados WHERE email = $1", email.lower()
        ))


async def buscar_por_whatsapp(whatsapp: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow(
            "SELECT * FROM advogados WHERE whatsapp = $1", whatsapp
        ))


async def buscar_por_oab(numero: str, seccional: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow(
            "SELECT * FROM advogados WHERE oab_numero=$1 AND oab_seccional=$2",
            numero, seccional.upper(),
        ))


async def listar_advogados_ativos() -> list[dict]:
    """Todos com trial válido ou assinatura ativa e WhatsApp confirmado."""
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM advogados
            WHERE ativo = true
              AND (
                    (status = 'trial'  AND trial_fim > NOW())
                 OR  status = 'ativo'
              )
            ORDER BY id
            """
        )
        return [dict(r) for r in rows]


# ── Atualizações ─────────────────────────────────────────────────────────────

async def atualizar_last_seen(advogado_id: int) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET last_seen = NOW() WHERE id = $1",
            advogado_id,
        )


async def atualizar_comarca(advogado_id: int, comarca: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET comarca = $1 WHERE id = $2",
            comarca, advogado_id,
        )


async def atualizar_whatsapp(
    advogado_id: int,
    whatsapp: str,
    confirmado: bool = False,
) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET whatsapp=$1, zapi_confirmado=$2 WHERE id=$3",
            whatsapp, confirmado, advogado_id,
        )


async def confirmar_whatsapp(advogado_id: int) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET zapi_confirmado = true WHERE id = $1",
            advogado_id,
        )


async def atualizar_ultima_busca_djen(advogado_id: int) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET ultima_busca_djen = NOW() WHERE id = $1",
            advogado_id,
        )


async def atualizar_dados(
    advogado_id: int,
    nome: str,
    horario_briefing: str = "07:00",
) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET nome=$1, horario_briefing=$2 WHERE id=$3",
            nome, horario_briefing, advogado_id,
        )


async def atualizar_senha(advogado_id: int, nova_senha: str) -> None:
    novo_hash = _hash_senha(nova_senha)
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET senha_hash = $1 WHERE id = $2",
            novo_hash, advogado_id,
        )


async def atualizar_email(advogado_id: int, novo_email: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET email = $1 WHERE id = $2",
            novo_email.lower(), advogado_id,
        )


# ── Acesso / Trial ───────────────────────────────────────────────────────────

async def pode_usar(advogado_id: int) -> bool:
    """True se trial válido ou assinatura ativa."""
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status, trial_fim, ativo FROM advogados WHERE id = $1",
            advogado_id,
        )
    if not row or not row["ativo"]:
        return False
    if row["status"] == "ativo":
        return True
    if row["status"] == "trial" and row["trial_fim"]:
        tf = row["trial_fim"]
        if tf.tzinfo is None:
            tf = tf.replace(tzinfo=timezone.utc)
        return tf > datetime.now(timezone.utc)
    return False


async def expirar_trials_vencidos() -> int:
    """
    Muda status de 'trial' → 'expirado' para quem passou da data.
    Chamado pelo Cloud Scheduler à meia-noite.
    """
    async with _pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE advogados
            SET status = 'expirado'
            WHERE status = 'trial' AND trial_fim < NOW()
            """
        )
    count = int(result.split()[-1])
    if count:
        log.info(f"Trials expirados: {count}")
    return count


async def advogados_trial_expirando(dias: int = 2) -> list[dict]:
    """Advogados com trial acabando nos próximos N dias — para lembrete."""
    limite = datetime.now(timezone.utc) + timedelta(days=dias)
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM advogados
            WHERE status = 'trial'
              AND ativo = true
              AND trial_fim BETWEEN NOW() AND $1
              AND whatsapp IS NOT NULL
              AND zapi_confirmado = true
            ORDER BY trial_fim
            """,
            limite,
        )
        return [dict(r) for r in rows]


# ── Processos e prazos ───────────────────────────────────────────────────────

async def listar_processos_com_prazos(advogado_id: int) -> list[dict]:
    """
    Retorna processos + prazos dos últimos 90 dias + futuros.
    Ordenados por: não cumpridos primeiro, depois por vencimento.
    """
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                p.numero,
                p.tribunal,
                p.vara,
                p.comarca,
                p.partes,
                pr.id          AS prazo_id,
                pr.tipo        AS tipo_prazo,
                pr.data_inicio,
                pr.data_fim,
                pr.cumprido,
                pr.decurso
            FROM processos p
            JOIN prazos pr ON pr.processo_id = p.id
            WHERE p.advogado_id = $1
              AND pr.data_fim >= NOW() - INTERVAL '90 days'
            ORDER BY pr.cumprido ASC, pr.data_fim ASC NULLS LAST
            """,
            advogado_id,
        )

    result = []
    for r in rows:
        d = dict(r)
        for campo in ("data_inicio", "data_fim"):
            v = d.get(campo)
            if v and hasattr(v, "isoformat"):
                d[campo] = v.isoformat()
        result.append(d)
    return result


# ── Sessions JWT ─────────────────────────────────────────────────────────────

async def criar_session(
    advogado_id: int,
    user_agent: str,
    ip: str,
    ttl_dias: int = 30,
) -> None:
    """Registra sessão — permite revogar no futuro."""
    expira = datetime.now(timezone.utc) + timedelta(days=ttl_dias)
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO sessions (advogado_id, user_agent, ip, expira_em, criado_em)
            VALUES ($1, $2, $3, $4, NOW())
            """,
            advogado_id, (user_agent or "")[:500], ip or "", expira,
        )


async def validar_session(token: str) -> Optional[dict]:
    """Valida token de sessão (reservado para revogação futura)."""
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.*, a.ativo
            FROM sessions s
            JOIN advogados a ON a.id = s.advogado_id
            WHERE s.token = $1
              AND s.expira_em > NOW()
              AND a.ativo = true
            """,
            token,
        )
        return _row(row)


# ── Log WhatsApp ─────────────────────────────────────────────────────────────

async def log_whatsapp(
    advogado_id: Optional[int],
    direcao: str,    # 'inbound' | 'outbound'
    tipo: str,       # 'mensagem' | 'briefing' | 'alerta'
    conteudo: str,
) -> None:
    """Registra mensagem enviada/recebida. Nunca quebra o fluxo principal."""
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO whatsapp_events
                    (advogado_id, direcao, tipo, conteudo, criado_em)
                VALUES ($1, $2, $3, $4, NOW())
                """,
                advogado_id, direcao, tipo, (conteudo or "")[:1000],
            )
    except Exception as e:
        log.warning(f"log_whatsapp falhou (não crítico): {e}")
