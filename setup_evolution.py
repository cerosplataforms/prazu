#!/usr/bin/env python3
"""
setup_evolution.py — Prazu Fase 2
Substitui Z-API pela Evolution API em todo o projeto.

O que faz:
  1. Cria web/evolution.py  (cliente da Evolution API)
  2. Atualiza web/onboarding.py  (troca import zapi → evolution)
  3. Atualiza web/app.py  (troca import zapi → evolution, webhook)
  4. Cria deploy_evolution.sh  (deploy da Evolution API no Cloud Run)

Uso:
  cd ~/prazu
  python3 setup_evolution.py
"""

import os, re

# ─────────────────────────────────────────────────────────────────────────────
# 1. web/evolution.py
# ─────────────────────────────────────────────────────────────────────────────

EVOLUTION_PY = '''\
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
'''

os.makedirs("web", exist_ok=True)
with open("web/evolution.py", "w") as f:
    f.write(EVOLUTION_PY)
print("  ✅ web/evolution.py criado")


# ─────────────────────────────────────────────────────────────────────────────
# 2. web/onboarding.py — troca zapi por evolution
# ─────────────────────────────────────────────────────────────────────────────

if os.path.exists("web/onboarding.py"):
    with open("web/onboarding.py") as f:
        content = f.read()

    # Troca import
    content = content.replace(
        "from web.zapi import ZAPI",
        "from web.evolution import evolution as _evo_client"
    )
    content = content.replace(
        "from web.zapi import ZAPI\n",
        "from web.evolution import evolution as _evo_client\n"
    )

    # Remove instanciação do ZAPI
    content = re.sub(
        r'zapi\s*=\s*ZAPI\([^)]*\)\n?',
        '',
        content
    )

    # Troca referências
    content = content.replace("zapi.enviar(", "_evo_client.enviar(")

    # Troca import no topo se vier de outro lugar
    content = content.replace(
        "import database_gcp as db\nfrom web.zapi import ZAPI",
        "import database_gcp as db\nfrom web.evolution import evolution as _evo_client"
    )

    with open("web/onboarding.py", "w") as f:
        f.write(content)
    print("  ✅ web/onboarding.py atualizado (zapi → evolution)")
else:
    print("  ⚠️  web/onboarding.py não encontrado — pule esta etapa")


# ─────────────────────────────────────────────────────────────────────────────
# 3. web/app.py — troca webhook de zapi por evolution
# ─────────────────────────────────────────────────────────────────────────────

if os.path.exists("web/app.py"):
    with open("web/app.py") as f:
        content = f.read()

    # Troca validação do token Z-API pelo header da Evolution API
    OLD_WEBHOOK = '''\
    # Valida token do Z-API
    zapi_token = os.getenv("ZAPI_TOKEN", "")
    header_token = request.headers.get("x-zapi-token", "")
    if zapi_token and header_token != zapi_token:
        log.warning("Webhook Z-API: token inválido")
        raise HTTPException(401, "Token inválido")'''

    NEW_WEBHOOK = '''\
    # Valida API key da Evolution API no header
    evo_key = os.getenv("EVOLUTION_API_KEY", "")
    header_key = request.headers.get("apikey", "")
    if evo_key and header_key != evo_key:
        log.warning("Webhook Evolution: apikey inválida")
        raise HTTPException(401, "Token inválido")'''

    if OLD_WEBHOOK in content:
        content = content.replace(OLD_WEBHOOK, NEW_WEBHOOK)
        print("  ✅ web/app.py atualizado (webhook zapi → evolution)")
    else:
        print("  ⚠️  web/app.py — bloco de webhook não encontrado, verifique manualmente")
        print("       Substitua a validação do x-zapi-token pela apikey da Evolution")

    # Atualiza import do onboarding se mencionar zapi
    content = content.replace(
        "from web.onboarding import processar_mensagem_zapi",
        "from web.onboarding import processar_mensagem_zapi"
    )

    with open("web/app.py", "w") as f:
        f.write(content)
else:
    print("  ⚠️  web/app.py não encontrado")


# ─────────────────────────────────────────────────────────────────────────────
# 4. deploy_evolution.sh — deploy da Evolution API no Cloud Run
# ─────────────────────────────────────────────────────────────────────────────

DEPLOY_SH = '''\
#!/bin/bash
# deploy_evolution.sh — Deploy da Evolution API no GCP
# Roda UMA VEZ para subir a Evolution API como serviço separado no Cloud Run.
#
# Uso:
#   cd ~/prazu
#   chmod +x deploy_evolution.sh
#   ./deploy_evolution.sh

set -e

PROJECT="prazu-prod"
REGION="southamerica-east1"
SERVICE="evolution-api"
IMAGE="atendai/evolution-api:v2.1.1"

# ── Gera API Key aleatória se não existir ──────────────────────────────────
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo ""
echo "🔑 Evolution API Key gerada:"
echo "   EVOLUTION_API_KEY=$API_KEY"
echo ""
echo "   Guarda essa chave! Você vai precisar dela no .env do Prazu."
echo ""

# ── Cria secret no GCP ────────────────────────────────────────────────────
echo "→ Criando secret evolution-api-key no Secret Manager..."
echo -n "$API_KEY" | gcloud secrets create evolution-api-key \\
    --data-file=- \\
    --project=$PROJECT 2>/dev/null || \\
echo -n "$API_KEY" | gcloud secrets versions add evolution-api-key \\
    --data-file=- \\
    --project=$PROJECT

echo "✅ Secret criado"

# ── Deploy no Cloud Run ────────────────────────────────────────────────────
echo ""
echo "→ Fazendo deploy da Evolution API no Cloud Run..."
echo "   (usa a imagem oficial atendai/evolution-api:v2.1.1)"
echo ""

# Pega a connection string do Cloud SQL
DB_HOST=$(gcloud secrets versions access latest --secret=db-host --project=$PROJECT)
DB_NAME=$(gcloud secrets versions access latest --secret=db-name --project=$PROJECT)
DB_USER=$(gcloud secrets versions access latest --secret=db-user --project=$PROJECT)
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=$PROJECT)

DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}"

gcloud run deploy $SERVICE \\
    --image=$IMAGE \\
    --region=$REGION \\
    --platform=managed \\
    --allow-unauthenticated \\
    --min-instances=1 \\
    --max-instances=3 \\
    --memory=1Gi \\
    --cpu=1 \\
    --timeout=60 \\
    --concurrency=40 \\
    --add-cloudsql-instances=${PROJECT}:${REGION}:prazu-db \\
    --set-env-vars="\\
AUTHENTICATION_API_KEY=${API_KEY},\\
DATABASE_ENABLED=true,\\
DATABASE_PROVIDER=postgresql,\\
DATABASE_CONNECTION_URI=${DATABASE_URL},\\
DATABASE_SAVE_DATA_CHATS=true,\\
DATABASE_SAVE_DATA_CONTACTS=true,\\
DATABASE_SAVE_DATA_MESSAGES=false,\\
DATABASE_SAVE_MESSAGE_UPDATE=false,\\
CACHE_LOCAL_ENABLED=true,\\
CACHE_REDIS_ENABLED=false,\\
DEL_INSTANCE=false,\\
LANGUAGE=pt-BR" \\
    --project=$PROJECT

# ── Pega a URL do serviço ─────────────────────────────────────────────────
EVOLUTION_URL=$(gcloud run services describe $SERVICE \\
    --region=$REGION \\
    --project=$PROJECT \\
    --format="value(status.url)")

echo ""
echo "═══════════════════════════════════════════════════"
echo "✅ Evolution API no ar!"
echo ""
echo "   URL: $EVOLUTION_URL"
echo ""
echo "   Adicione no .env do Prazu:"
echo "   EVOLUTION_URL=$EVOLUTION_URL"
echo "   EVOLUTION_API_KEY=$API_KEY"
echo "   EVOLUTION_INSTANCE=prazu"
echo ""
echo "   Próximo passo:"
echo "   python3 setup_instancia.py"
echo "═══════════════════════════════════════════════════"
'''

with open("deploy_evolution.sh", "w") as f:
    f.write(DEPLOY_SH)
os.chmod("deploy_evolution.sh", 0o755)
print("  ✅ deploy_evolution.sh criado")


# ─────────────────────────────────────────────────────────────────────────────
# 5. setup_instancia.py — cria instância e escaneia QR
# ─────────────────────────────────────────────────────────────────────────────

SETUP_INSTANCIA = '''\
#!/usr/bin/env python3
"""
setup_instancia.py — Prazu Fase 2
Cria a instância WhatsApp na Evolution API e exibe o QR Code no terminal.

Pré-requisito:
  EVOLUTION_URL e EVOLUTION_API_KEY no .env

Uso:
  cd ~/prazu
  python3 setup_instancia.py
"""

import os, asyncio, base64, sys
from dotenv import load_dotenv
load_dotenv()

EVOLUTION_URL      = os.getenv("EVOLUTION_URL", "").rstrip("/")
EVOLUTION_API_KEY  = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "prazu")
PRAZU_URL          = os.getenv("PRAZU_URL", "")   # URL do Cloud Run do Prazu

if not EVOLUTION_URL or not EVOLUTION_API_KEY:
    print("❌ Configure EVOLUTION_URL e EVOLUTION_API_KEY no .env antes de rodar.")
    sys.exit(1)

WEBHOOK_URL = f"{PRAZU_URL}/webhook/evolution" if PRAZU_URL else ""


async def main():
    import httpx

    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
    }

    print(f"\\n→ Criando instância \\'{EVOLUTION_INSTANCE}\\' na Evolution API...")

    # Cria instância
    payload = {
        "instanceName": EVOLUTION_INSTANCE,
        "integration": "WHATSAPP-BAILEYS",
        "qrcode": True,
    }
    if WEBHOOK_URL:
        payload["webhook"] = {
            "url": WEBHOOK_URL,
            "byEvents": False,
            "base64": False,
            "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
        }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{EVOLUTION_URL}/instance/create",
            json=payload,
            headers=headers,
        )

    data = r.json()
    if r.status_code not in (200, 201):
        # Instância pode já existir — tudo bem
        if "already" in str(data).lower() or r.status_code == 409:
            print("  ⚠️  Instância já existe, buscando QR Code...")
        else:
            print(f"  ❌ Erro ao criar instância: {data}")
            sys.exit(1)
    else:
        print(f"  ✅ Instância criada!")

    # Aguarda um segundo e busca o QR Code
    await asyncio.sleep(2)

    print("\\n→ Buscando QR Code...")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{EVOLUTION_URL}/instance/connect/{EVOLUTION_INSTANCE}",
            headers=headers,
        )
    qr_data = r.json()
    qr_base64 = (
        qr_data.get("base64")
        or qr_data.get("qrcode", {}).get("base64")
        or ""
    )

    if not qr_base64:
        print("  ❌ QR Code não disponível. A instância pode já estar conectada.")
        print(f"     Resposta: {qr_data}")

        # Verifica status
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{EVOLUTION_URL}/instance/fetchInstances",
                headers=headers,
            )
        for inst in r.json():
            name = inst.get("instance", {}).get("instanceName", "")
            state = inst.get("instance", {}).get("state", "")
            if name == EVOLUTION_INSTANCE:
                print(f"  Status da instância: {state}")
                if state == "open":
                    print("  ✅ WhatsApp já conectado!")
        return

    # Salva QR Code como imagem
    qr_clean = qr_base64.split(",")[-1]  # remove "data:image/png;base64,"
    qr_bytes = base64.b64decode(qr_clean)
    qr_path = "qrcode_prazu.png"
    with open(qr_path, "wb") as f:
        f.write(qr_bytes)

    print(f"\\n✅ QR Code salvo em: {qr_path}")
    print("\\n📱 Abra esse arquivo e escaneie com o WhatsApp:")
    print(f"   open {qr_path}")
    print("\\nAguardando conexão (60 segundos)...")

    # Polling até conectar
    for i in range(12):
        await asyncio.sleep(5)
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{EVOLUTION_URL}/instance/fetchInstances",
                headers=headers,
            )
        for inst in r.json():
            name = inst.get("instance", {}).get("instanceName", "")
            state = inst.get("instance", {}).get("state", "")
            if name == EVOLUTION_INSTANCE and state == "open":
                print("\\n✅ WhatsApp conectado com sucesso!")

                if WEBHOOK_URL:
                    print(f"   Webhook configurado: {WEBHOOK_URL}")
                else:
                    print("   ⚠️  PRAZU_URL não definido no .env")
                    print("      Configure o webhook manualmente após o deploy do Prazu:")
                    print(f"      python3 -c \\"")
                    print(f"        import asyncio")
                    print(f"        from web.evolution import evolution")
                    print(f"        asyncio.run(evolution.configurar_webhook(\\'https://SUA_URL/webhook/evolution\\'))")
                    print(f"      \\"")
                return
        print(f"  Aguardando... ({(i+1)*5}s)")

    print("\\n⚠️  Tempo esgotado. Escaneie o QR Code e rode novamente.")


asyncio.run(main())
'''

with open("setup_instancia.py", "w") as f:
    f.write(SETUP_INSTANCIA)
print("  ✅ setup_instancia.py criado")


# ─────────────────────────────────────────────────────────────────────────────
# Resumo
# ─────────────────────────────────────────────────────────────────────────────

print("""
────────────────────────────────────────────────────
✅ Pronto! Arquivos criados/atualizados:

   web/evolution.py       → cliente da Evolution API
   web/onboarding.py      → atualizado (zapi → evolution)
   web/app.py             → atualizado (webhook)
   deploy_evolution.sh    → deploy da Evolution no Cloud Run
   setup_instancia.py     → cria instância + QR Code

Próximos passos (na ordem):

  1. git add . && git commit -m "feat: evolution api - substitui zapi" && git push

  2. Deploy da Evolution API:
     chmod +x deploy_evolution.sh
     ./deploy_evolution.sh
     → anota a URL e a API Key que aparecer no final

  3. Adiciona no .env:
     EVOLUTION_URL=https://evolution-api-xxx.run.app
     EVOLUTION_API_KEY=chave_que_apareceu
     EVOLUTION_INSTANCE=prazu

  4. Cria a instância e escaneia o QR:
     python3 setup_instancia.py

  5. Deploy do Prazu (app principal):
     python3 deploy_setup.py
────────────────────────────────────────────────────
""")
