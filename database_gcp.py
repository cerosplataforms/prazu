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
    global _pool
    db_name = os.getenv("DB_NAME", "prazu")
    db_user = os.getenv("DB_USER", "prazu_user")
    db_pass = os.getenv("DB_PASSWORD", "")

    if os.getenv("ENVIRONMENT") == "production":
        socket_path = "/cloudsql/prazu-prod:southamerica-east1:prazu-db"
        _pool = await asyncpg.create_pool(
            host=socket_path, database=db_name, user=db_user, password=db_pass,
            min_size=2, max_size=10, command_timeout=30,
        )
    else:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=db_name, user=db_user, password=db_pass,
            min_size=2, max_size=10, command_timeout=30,
        )
    log.info("Pool PostgreSQL inicializado")


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("Pool PostgreSQL fechado")


async def diagnostico() -> dict:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) AS total FROM advogados")
        return {"advogados": row["total"], "status": "ok"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash_guardado: str) -> bool:
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
    """Insere novo advogado com trial de 7 dias. Retorna id ou None se duplicado."""
    senha_hash = _hash_senha(senha)
    trial_fim  = datetime.now(timezone.utc) + timedelta(days=7)
    try:
        async with _pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO advogados
                        (nome, email, senha_hash, oab_numero, oab_seccional,
                         whatsapp, status, trial_fim, ativo, zapi_confirmado, created_at)
                    VALUES ($1,$2,$3,$4,$5,$6,'trial',$7,true,false,NOW())
                    RETURNING id
                    """,
                    nome, email.lower(), senha_hash,
                    oab_numero, oab_seccional.upper(), whatsapp, trial_fim,
                )
                adv_id = row["id"]
                await conn.execute(
                    "INSERT INTO assinaturas (advogado_id, plano, status, inicio, fim) VALUES ($1,'trial','ativo',NOW(),$2)",
                    adv_id, trial_fim,
                )
                log.info(f"Novo advogado id={adv_id} {email} OAB {oab_numero}/{oab_seccional}")
                return adv_id
    except asyncpg.UniqueViolationError:
        log.warning(f"Cadastro duplicado: {email} / {oab_numero}/{oab_seccional}")
        return None


async def criar_advogado_minimo(
    nome: str,
    email: str,
    senha: str,
    telefone: Optional[str] = None,
) -> Optional[int]:
    """
    Cadastro rápido: só nome, email, senha e telefone.
    OAB e WhatsApp de notificação são preenchidos no onboarding.
    Retorna id criado, ou None se email já existir.
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
                         whatsapp, status, trial_fim, ativo, zapi_confirmado, created_at)
                    VALUES ($1,$2,$3,'','', $4,'trial',$5,true,false,NOW())
                    RETURNING id
                    """,
                    nome, email.lower(), senha_hash, telefone, trial_fim,
                )
                adv_id = row["id"]
                await conn.execute(
                    "INSERT INTO assinaturas (advogado_id, plano, status, inicio, fim) VALUES ($1,'trial','ativo',NOW(),$2)",
                    adv_id, trial_fim,
                )
                log.info(f"Cadastro mínimo id={adv_id} {email}")
                return adv_id
    except asyncpg.UniqueViolationError:
        log.warning(f"Cadastro duplicado (mínimo): {email}")
        return None


async def salvar_onboarding(
    advogado_id: int,
    oab_numero: str,
    oab_seccional: str,
    tratamento: str,
    whatsapp_notificacao: str,
    horario_briefing: str,
    lembrete_fds: bool,
) -> bool:
    """
    Salva os dados do onboarding obrigatório.
    Retorna False se a OAB já estiver em outra conta.
    """
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE advogados SET
                    oab_numero                      = $1,
                    oab_seccional                   = $2,
                    tratamento                      = $3,
                    whatsapp_notificacao            = $4,
                    whatsapp_notificacao_confirmado = true,
                    zapi_confirmado                 = true,
                    horario_briefing                = $5,
                    lembrete_fds                    = $6
                WHERE id = $7
                """,
                oab_numero, oab_seccional.upper(), tratamento,
                whatsapp_notificacao, horario_briefing, lembrete_fds, advogado_id,
            )
            log.info(f"Onboarding salvo adv={advogado_id} OAB {oab_numero}/{oab_seccional}")
            return True
    except asyncpg.UniqueViolationError:
        log.warning(f"OAB duplicada no onboarding: {oab_numero}/{oab_seccional}")
        return False


# ── Buscas ───────────────────────────────────────────────────────────────────

async def buscar_por_id(advogado_id: int) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow("SELECT * FROM advogados WHERE id = $1", advogado_id))


async def buscar_por_email(email: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow("SELECT * FROM advogados WHERE email = $1", email.lower()))


async def buscar_por_whatsapp(whatsapp: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow("SELECT * FROM advogados WHERE whatsapp = $1", whatsapp))


async def buscar_por_oab(numero: str, seccional: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        return _row(await conn.fetchrow(
            "SELECT * FROM advogados WHERE oab_numero=$1 AND oab_seccional=$2",
            numero, seccional.upper(),
        ))


async def listar_advogados_ativos() -> list[dict]:
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
        await conn.execute("UPDATE advogados SET last_seen = NOW() WHERE id = $1", advogado_id)


async def atualizar_comarca(advogado_id: int, comarca: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE advogados SET comarca = $1 WHERE id = $2", comarca, advogado_id)


async def atualizar_whatsapp(advogado_id: int, whatsapp: str, confirmado: bool = False) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET whatsapp=$1, zapi_confirmado=$2 WHERE id=$3",
            whatsapp, confirmado, advogado_id,
        )


async def confirmar_whatsapp(advogado_id: int) -> None:
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE advogados SET zapi_confirmado = true WHERE id = $1", advogado_id)


async def atualizar_ultima_busca_djen(advogado_id: int) -> None:
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE advogados SET ultima_busca_djen = NOW() WHERE id = $1", advogado_id)


async def atualizar_dados(advogado_id: int, nome: str, horario_briefing: str = "07:00", tratamento: str = "") -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE advogados SET nome=$1, horario_briefing=$2, tratamento=$3 WHERE id=$4",
            nome, horario_briefing, tratamento or "Dr(a).", advogado_id,
        )


async def atualizar_senha(advogado_id: int, nova_senha: str) -> None:
    novo_hash = _hash_senha(nova_senha)
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE advogados SET senha_hash = $1 WHERE id = $2", novo_hash, advogado_id)


async def atualizar_email(advogado_id: int, novo_email: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE advogados SET email = $1 WHERE id = $2", novo_email.lower(), advogado_id)


# ── Acesso / Trial ───────────────────────────────────────────────────────────

async def pode_usar(advogado_id: int) -> bool:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status, trial_fim, ativo FROM advogados WHERE id = $1", advogado_id,
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
    async with _pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE advogados SET status = 'expirado' WHERE status = 'trial' AND trial_fim < NOW()"
        )
    count = int(result.split()[-1])
    if count:
        log.info(f"Trials expirados: {count}")
    return count


async def advogados_trial_expirando(dias: int = 2) -> list[dict]:
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
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                p.id, p.numero, p.tribunal, p.vara, p.comarca, p.partes,
                MIN(CASE WHEN pr.cumprido = false AND pr.decurso = false
                    THEN pr.data_fim END) AS proximo_vencimento,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'prazo_id',    pr.id,
                            'tipo_prazo',  pr.tipo,
                            'data_inicio', pr.data_inicio::text,
                            'data_fim',    pr.data_fim::text,
                            'cumprido',    pr.cumprido,
                            'decurso',     pr.decurso
                        ) ORDER BY pr.data_fim ASC
                    ) FILTER (WHERE pr.id IS NOT NULL),
                    '[]'
                ) AS prazos
            FROM processos p
            LEFT JOIN prazos pr ON pr.processo_id = p.id
                AND pr.data_fim >= NOW() - INTERVAL '90 days'
            WHERE p.advogado_id = $1
            GROUP BY p.id, p.numero, p.tribunal, p.vara, p.comarca, p.partes
            ORDER BY proximo_vencimento ASC NULLS LAST
            """,
            advogado_id,
        )

    import json
    result = []
    for r in rows:
        d = dict(r)
        d.pop("proximo_vencimento", None)
        prazos = d.get("prazos")
        if isinstance(prazos, str):
            d["prazos"] = json.loads(prazos)
        elif prazos is None:
            d["prazos"] = []
        result.append(d)
    return result


# ── Sessions JWT ─────────────────────────────────────────────────────────────

async def criar_session(advogado_id: int, user_agent: str, ip: str, ttl_dias: int = 30) -> None:
    import secrets
    token = secrets.token_urlsafe(32)
    expira = datetime.now(timezone.utc) + timedelta(days=ttl_dias)
    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (advogado_id, token, user_agent, ip, expira_em, criado_em) VALUES ($1,$2,$3,$4,$5,NOW())",
            advogado_id, token, (user_agent or "")[:500], ip or "", expira,
        )


async def validar_session(token: str) -> Optional[dict]:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.*, a.ativo FROM sessions s
            JOIN advogados a ON a.id = s.advogado_id
            WHERE s.token = $1 AND s.expira_em > NOW() AND a.ativo = true
            """,
            token,
        )
        return _row(row)


# ── Log WhatsApp ─────────────────────────────────────────────────────────────

async def log_whatsapp(advogado_id: Optional[int], direcao: str, tipo: str, conteudo: str) -> None:
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO whatsapp_events (advogado_id, direcao, tipo, conteudo, criado_em) VALUES ($1,$2,$3,$4,NOW())",
                advogado_id, direcao, tipo, (conteudo or "")[:1000],
            )
    except Exception as e:
        log.warning(f"log_whatsapp falhou (não crítico): {e}")


# ── Processos ────────────────────────────────────────────────────────────────

async def criar_ou_atualizar_processo(advogado_id, numero, partes="", vara="", tribunal="", comarca="", fonte="djen"):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM processos WHERE advogado_id=$1 AND numero=$2", advogado_id, numero)
        if row:
            return row["id"]
        row = await conn.fetchrow(
            "INSERT INTO processos (advogado_id, numero, partes, vara, tribunal, comarca, fonte) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id",
            advogado_id, numero, partes, vara, tribunal, comarca, fonte,
        )
        return row["id"]


async def criar_prazo_processo(processo_id, tipo, data_inicio, data_fim, fatal=False, contagem="uteis", dias_totais=15):
    from datetime import date as _date
    if isinstance(data_fim, str): data_fim = _date.fromisoformat(data_fim)
    if isinstance(data_inicio, str): data_inicio = _date.fromisoformat(data_inicio)
    async with _pool.acquire() as conn:
        existe = await conn.fetchrow("SELECT id FROM prazos WHERE processo_id=$1 AND tipo=$2 AND data_fim=$3", processo_id, tipo, data_fim)
        if existe: return
        await conn.execute(
            "INSERT INTO prazos (processo_id, tipo, data_inicio, data_fim, fatal, contagem, dias_totais) VALUES ($1,$2,$3,$4,$5,$6,$7)",
            processo_id, tipo, data_inicio, data_fim, fatal, contagem, dias_totais,
        )


async def comunicacao_djen_existe(advogado_id, numero_processo, data_disponibilizacao):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM comunicacoes_djen WHERE advogado_id=$1 AND numero_processo=$2 AND data_disponibilizacao=$3",
            advogado_id, numero_processo, data_disponibilizacao,
        )
        return row is not None


async def salvar_comunicacao_djen(advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao="", tipo_comunicacao=""):
    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO comunicacoes_djen (advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao, tipo_comunicacao) VALUES ($1,$2,$3,$4,$5,$6,$7)",
            advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao, tipo_comunicacao,
        )


async def marcar_prazo_cumprido(processo_id: int, tipo: str, data_fim) -> None:
    from datetime import date as _date
    if isinstance(data_fim, str): data_fim = _date.fromisoformat(data_fim)
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE prazos SET cumprido=TRUE WHERE processo_id=$1 AND tipo=$2 AND data_fim=$3", processo_id, tipo, data_fim)


async def marcar_prazo_decurso(processo_id: int, tipo: str, data_fim) -> None:
    from datetime import date as _date
    if isinstance(data_fim, str): data_fim = _date.fromisoformat(data_fim)
    async with _pool.acquire() as conn:
        await conn.execute("UPDATE prazos SET decurso=TRUE WHERE processo_id=$1 AND tipo=$2 AND data_fim=$3", processo_id, tipo, data_fim)
