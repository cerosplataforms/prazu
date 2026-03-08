"""
web/zapi.py — Prazu Fase 2
Cliente Z-API para envio de mensagens WhatsApp.
"""

import os
import logging
import httpx

log = logging.getLogger(__name__)


class ZAPI:
    def __init__(self, instance_id: str, token: str, client_token: str = ""):
        self.instance_id = instance_id
        self.token = token
        self.client_token = client_token
        self.base_url = f"https://api.z-api.io/instances/{instance_id}/token/{token}"

    async def enviar(self, phone: str, texto: str) -> bool:
        if not self.instance_id or not self.token:
            log.warning(f"Z-API não configurado. Msg para {phone}: {texto[:50]}")
            return False
        url = f"{self.base_url}/send-text"
        headers = {"Client-Token": self.client_token} if self.client_token else {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={"phone": phone, "message": texto}, headers=headers)
                resp.raise_for_status()
                log.info(f"Z-API enviado para {phone} ✅")
                return True
        except httpx.HTTPStatusError as e:
            log.error(f"Z-API HTTP {e.response.status_code} para {phone}: {e.response.text[:100]}")
            return False
        except Exception as e:
            log.error(f"Z-API erro para {phone}: {e}")
            return False

    async def enviar_lista(self, phones: list, texto: str) -> int:
        import asyncio
        resultados = await asyncio.gather(
            *[self.enviar(p, texto) for p in phones], return_exceptions=True
        )
        return sum(1 for r in resultados if r is True)
