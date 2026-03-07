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
echo -n "$API_KEY" | gcloud secrets create evolution-api-key \
    --data-file=- \
    --project=$PROJECT 2>/dev/null || \
echo -n "$API_KEY" | gcloud secrets versions add evolution-api-key \
    --data-file=- \
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

gcloud run deploy $SERVICE \
    --image=$IMAGE \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=1 \
    --max-instances=3 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=60 \
    --concurrency=40 \
    --add-cloudsql-instances=${PROJECT}:${REGION}:prazu-db \
    --set-env-vars="\
AUTHENTICATION_API_KEY=${API_KEY},\
DATABASE_ENABLED=true,\
DATABASE_PROVIDER=postgresql,\
DATABASE_CONNECTION_URI=${DATABASE_URL},\
DATABASE_SAVE_DATA_CHATS=true,\
DATABASE_SAVE_DATA_CONTACTS=true,\
DATABASE_SAVE_DATA_MESSAGES=false,\
DATABASE_SAVE_MESSAGE_UPDATE=false,\
CACHE_LOCAL_ENABLED=true,\
CACHE_REDIS_ENABLED=false,\
DEL_INSTANCE=false,\
LANGUAGE=pt-BR" \
    --project=$PROJECT

# ── Pega a URL do serviço ─────────────────────────────────────────────────
EVOLUTION_URL=$(gcloud run services describe $SERVICE \
    --region=$REGION \
    --project=$PROJECT \
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
