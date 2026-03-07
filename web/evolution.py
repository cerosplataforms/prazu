"""
web/evolution.py — Prazu Fase 2
Cliente da Evolution API v2 (substitui zapi.py).

Variáveis de ambiente:
  EVOLUTION_URL      → URL do Cloud Run da Evolution API
  EVOLUTION_API_KEY  → API key global definida no deploy
  EVOLUTION_INSTANCE → Nome da instância (padrão: prazu)
"""

import os
import logging
import httpx

log = logging.getLogger(__name__)

EVOLUTION_URL      = os.getenv("EVOLUTION_URL", "").rstrip("/")
EVOLUTION_API_KEY  = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "prazu")


def _headers():
    return {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
    }


def _normalizar_phone(phone: str) -> str:
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) <= 11:
        digits = "55" + digits
    return digits


def parsear_webhook(payload: dict) -> tuple:
    """
    Extrai (phone, texto) do payload do webhook da Evolution API.
    Retorna (None, None) se não for mensagem de texto de entrada.
    """
    event = payload.get("event", "")
    if event != "messages.upsert":
        return None, None

    data = payload.get("data", {})
    key = data.get("key", {})

    if key.get("fromMe"):
        return None, None

    remote = key.get("remoteJid", "")
    if "@g.us" in remote:
        return None, None  # ignora grupos

    phone = remote.replace("@s.whatsapp.net", "").replace("@g.us", "")

    msg = data.get("message", {})
    texto = (
        msg.get("conversation")
        or msg.get("extendedTextMessage", {}).get("text")
        or msg.get("imageMessage", {}).get("caption")
        or ""
    ).strip()

    if not phone or not texto:
        return None, None

    return phone, texto


class EvolutionAPI:
    """Cliente assíncrono para a Evolution API v2."""

    def __init__(self):
        self.base     = EVOLUTION_URL
        self.instance = EVOLUTION_INSTANCE

    async def enviar(self, phone: str, texto: str) -> bool:
        url = f"{self.base}/message/sendText/{self.instance}"
        payload = {
            "number": _normalizar_phone(phone),
            "text": texto,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json=payload, headers=_headers())
                if r.status_code not in (200, 201):
                    log.error(f"Evolution enviar {r.status_code}: {r.text[:200]}")
                    return False
                return True
        except Exception as e:
            log.error(f"Evolution enviar: {e}")
            return False

    async def status(self) -> str:
        url = f"{self.base}/instance/fetchInstances"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers=_headers())
                for inst in r.json():
                    if inst.get("instance", {}).get("instanceName") == self.instance:
                        return inst.get("instance", {}).get("state", "close")
                return "close"
        except Exception as e:
            log.error(f"Evolution status: {e}")
            return "close"

    async def qrcode(self) -> str | None:
        url = f"{self.base}/instance/connect/{self.instance}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url, headers=_headers())
                data = r.json()
                return data.get("base64") or data.get("qrcode", {}).get("base64")
        except Exception as e:
            log.error(f"Evolution qrcode: {e}")
            return None

    async def criar_instancia(self, webhook_url: str) -> dict:
        url = f"{self.base}/instance/create"
        payload = {
            "instanceName": self.instance,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
            "webhook": {
                "url": webhook_url,
                "byEvents": False,
                "base64": False,
                "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
            },
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload, headers=_headers())
            return r.json()

    async def configurar_webhook(self, webhook_url: str) -> bool:
        url = f"{self.base}/webhook/set/{self.instance}"
        payload = {
            "url": webhook_url,
            "byEvents": False,
            "base64": False,
            "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json=payload, headers=_headers())
                return r.status_code in (200, 201)
        except Exception as e:
            log.error(f"Evolution webhook: {e}")
            return False


evolution = EvolutionAPI()
