#!/bin/bash
# deploy_evolution.sh — Deploy da Evolution API no GCP (v3 - banco separado)
set -e

PROJECT="prazu-prod"
REGION="southamerica-east1"
SERVICE="evolution-api"
IMAGE="atendai/evolution-api:v2.1.1"
SQL_INSTANCE="${PROJECT}:${REGION}:prazu-db"
DB_NAME="evolution"   # banco separado do Prazu

# Pega a API Key já criada
echo "→ Buscando API Key..."
API_KEY=$(gcloud secrets versions access latest --secret=evolution-api-key --project=$PROJECT)
echo "✅ API Key: ${API_KEY:0:10}..."

# Pega credenciais
echo "→ Buscando credenciais..."
DB_USER=$(gcloud secrets versions access latest --secret=db-user --project=$PROJECT)
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=$PROJECT)

# Socket Unix para Cloud SQL
DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@localhost/${DB_NAME}?host=/cloudsql/${SQL_INSTANCE}"

echo "→ Deploy no Cloud Run (banco: ${DB_NAME})..."

gcloud run deploy $SERVICE \
    --image=$IMAGE \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=1 \
    --max-instances=3 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=120 \
    --concurrency=40 \
    --add-cloudsql-instances=${SQL_INSTANCE} \
    --set-env-vars="AUTHENTICATION_API_KEY=${API_KEY},DATABASE_ENABLED=true,DATABASE_PROVIDER=postgresql,DATABASE_CONNECTION_URI=${DATABASE_URL},DATABASE_CONNECTION_CLIENT_NAME=evolution,DATABASE_SAVE_DATA_CHATS=true,DATABASE_SAVE_DATA_CONTACTS=true,DATABASE_SAVE_DATA_MESSAGES=false,DATABASE_SAVE_MESSAGE_UPDATE=false,CACHE_LOCAL_ENABLED=true,CACHE_REDIS_ENABLED=false,DEL_INSTANCE=false,LANGUAGE=pt-BR" \
    --project=$PROJECT

# URL do serviço
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
