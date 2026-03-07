"""
web/evolution.py — Prazu Fase 2
Cliente da Evolution API v2 (substitui zapi.py).

Variáveis de ambiente:
  EVOLUTION_URL      → URL do Cloud Run da Evolution API
                       ex: https://evolution-api-xxx-rj.a.run.app
  EVOLUTION_API_KEY  → API key global (definida no deploy da Evolution)
  EVOLUTION_INSTANCE → Nome da instância (ex: prazu)
"""

import os
import logging
import httpx

log = logging.getLogger(__name__)

EVOLUTION_URL      = os.getenv("EVOLUTION_URL", "").rstrip("/")
EVOLUTION_API_KEY  = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "prazu")

_HEADERS = {
    "Content-Type": "application/json",
    "apikey": EVOLUTION_API_KEY,
}


class EvolutionAPI:
    """Cliente assíncrono para a Evolution API v2."""

    def __init__(self):
        self.base = EVOLUTION_URL
        self.instance = EVOLUTION_INSTANCE
        self.headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY,
        }

    # ── Envio de mensagens ───────────────────────────────────────────────────

    async def enviar(self, phone: str, texto: str) -> bool:
        """
        Envia mensagem de texto para um número.
        phone: somente dígitos, com DDI — ex: 5531999999999
        """
        url = f"{self.base}/message/sendText/{self.instance}"
        payload = {
            "number": _normalizar_phone(phone),
            "text": texto,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json=payload, headers=self.headers)
                if r.status_code not in (200, 201):
                    log.error(f"Evolution enviar erro {r.status_code}: {r.text[:200]}")
                    return False
                return True
        except Exception as e:
            log.error(f"Evolution enviar exceção: {e}")
            return False

    # ── Gestão da instância ──────────────────────────────────────────────────

    async def criar_instancia(self, webhook_url: str) -> dict:
        """
        Cria a instância 'prazu' na Evolution API.
        Chamado uma vez no setup, não no dia a dia.
        """
        url = f"{self.base}/instance/create"
        payload = {
            "instanceName": self.instance,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
            "webhook": {
                "url": webhook_url,
                "byEvents": False,
                "base64": False,
                "events": [
                    "MESSAGES_UPSERT",
                    "CONNECTION_UPDATE",
                ],
            },
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload, headers=self.headers)
            return r.json()

    async def qrcode(self) -> str | None:
        """
        Retorna o QR Code em base64 para escanear com o WhatsApp.
        Chamar após criar_instancia().
        """
        url = f"{self.base}/instance/connect/{self.instance}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url, headers=self.headers)
                data = r.json()
                # Retorna string base64 da imagem ou None
                return data.get("base64") or data.get("qrcode", {}).get("base64")
        except Exception as e:
            log.error(f"Evolution qrcode exceção: {e}")
            return None

    async def status(self) -> str:
        """
        Retorna status da instância: 'open' | 'close' | 'connecting'
        """
        url = f"{self.base}/instance/fetchInstances"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers=self.headers)
                instancias = r.json()
                for inst in instancias:
                    if inst.get("instance", {}).get("instanceName") == self.instance:
                        return inst.get("instance", {}).get("state", "close")
                return "close"
        except Exception as e:
            log.error(f"Evolution status exceção: {e}")
            return "close"

    async def configurar_webhook(self, webhook_url: str) -> bool:
        """
        Atualiza a URL do webhook na instância existente.
        Chamar após o deploy do Prazu estar no ar.
        """
        url = f"{self.base}/webhook/set/{self.instance}"
        payload = {
            "url": webhook_url,
            "byEvents": False,
            "base64": False,
            "events": [
                "MESSAGES_UPSERT",
                "CONNECTION_UPDATE",
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(url, json=payload, headers=self.headers)
                ok = r.status_code in (200, 201)
                if not ok:
                    log.error(f"Evolution webhook erro {r.status_code}: {r.text[:200]}")
                return ok
        except Exception as e:
            log.error(f"Evolution webhook exceção: {e}")
            return False


# ── Helpers ──────────────────────────────────────────────────────────────────

def _normalizar_phone(phone: str) -> str:
    """Remove tudo que não é dígito e garante DDI 55."""
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) <= 11:
        digits = "55" + digits
    return digits


def parsear_webhook(payload: dict) -> tuple[str | None, str | None]:
    """
    Extrai (phone, texto) do payload do webhook da Evolution API.
    Retorna (None, None) se não for mensagem de texto de entrada.
    """
    event = payload.get("event", "")

    # Só processa mensagens recebidas
    if event != "messages.upsert":
        return None, None

    data = payload.get("data", {})

    # Ignora mensagens enviadas pelo próprio bot
    key = data.get("key", {})
    if key.get("fromMe"):
        return None, None

    # Extrai número
    remote = key.get("remoteJid", "")
    phone = remote.replace("@s.whatsapp.net", "").replace("@g.us", "")
    if "@g.us" in remote:
        return None, None  # ignora grupos

    # Extrai texto
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


# Instância global — importar onde precisar
evolution = EvolutionAPI()
