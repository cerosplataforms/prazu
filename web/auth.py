"""
web/auth.py — Prazu Fase 2
JWT para autenticação do site.
Token armazenado em cookie httpOnly.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Request

import database_gcp as db

log = logging.getLogger(__name__)

JWT_SECRET   = os.getenv("JWT_SECRET", "dev-secret-troca-em-producao")
JWT_ALGO     = "HS256"
JWT_TTL_DIAS = 30
TOKEN_COOKIE = "prazu_token"


async def criar_token_acesso(advogado: dict, request: Request) -> str:
    """Cria JWT + registra sessão no banco."""
    expira = datetime.now(timezone.utc) + timedelta(days=JWT_TTL_DIAS)
    payload = {
        "sub": str(advogado["id"]),
        "email": advogado.get("email", ""),
        "exp": expira,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    await db.criar_session(
        advogado_id=advogado["id"],
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else "",
        ttl_dias=JWT_TTL_DIAS,
    )
    return token


async def verificar_token(token: str) -> Optional[dict]:
    """Valida JWT e retorna o advogado, ou None se inválido."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        advogado_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None
    adv = await db.buscar_por_id(advogado_id)
    if not adv or not adv["ativo"]:
        return None
    return adv
