#!/bin/bash
# deploy.sh — Prazu
# Uso:
#   ./deploy.sh dev    → testa no ambiente de desenvolvimento
#   ./deploy.sh prod   → joga em produção (pede confirmação)

set -e

AMBIENTE=$1
PROJECT="prazu-prod"
REGION="southamerica-east1"

# ── Cores ────────────────────────────────────────────────────────────────────
VERDE='\033[0;32m'
AZUL='\033[0;34m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
RESET='\033[0m'

if [ -z "$AMBIENTE" ]; then
  echo -e "${VERMELHO}Uso: ./deploy.sh dev   ou   ./deploy.sh prod${RESET}"
  exit 1
fi

# ── Verificar sintaxe Python antes de qualquer coisa ────────────────────────
echo -e "${AZUL}🔍 Verificando sintaxe...${RESET}"
python3 -m py_compile web/app.py
python3 -m py_compile database_gcp.py
echo -e "${VERDE}✅ Sintaxe OK${RESET}"

# ════════════════════════════════════════════════════════════════════════════
# DEPLOY DEV
# ════════════════════════════════════════════════════════════════════════════
if [ "$AMBIENTE" = "dev" ]; then
  echo ""
  echo -e "${AZUL}🚀 Deployando no ambiente DEV...${RESET}"
  echo -e "Branch: ${AMARELO}$(git branch --show-current)${RESET}"
  echo ""

  # Commit automático se tiver mudanças
  if [ -n "$(git status --porcelain)" ]; then
    echo -e "${AMARELO}📝 Você tem mudanças não commitadas.${RESET}"
    read -p "Mensagem do commit: " MSG
    if [ -z "$MSG" ]; then
      echo -e "${VERMELHO}Mensagem não pode ser vazia.${RESET}"
      exit 1
    fi
    git add .
    git commit -m "$MSG"
    git push origin dev
    echo -e "${VERDE}✅ Commit feito: $MSG${RESET}"
  else
    echo -e "${VERDE}✅ Nada para commitar${RESET}"
  fi

  echo ""
  echo -e "${AZUL}🔨 Fazendo build...${RESET}"
  gcloud builds submit \
    --tag gcr.io/$PROJECT/prazu-dev:latest \
    --project=$PROJECT --quiet

  echo ""
  echo -e "${AZUL}☁️  Subindo no Cloud Run DEV...${RESET}"
  gcloud run deploy prazu-dev \
    --image gcr.io/$PROJECT/prazu-dev:latest \
    --region $REGION \
    --project $PROJECT \
    --quiet

  echo ""
  echo -e "${VERDE}✅ Deploy DEV concluído!${RESET}"
  echo -e "🔗 URL: ${AZUL}https://prazu-dev-710127610365.southamerica-east1.run.app${RESET}"
  echo ""

  # Health check
  sleep 5
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    https://prazu-dev-710127610365.southamerica-east1.run.app/health)
  if [ "$STATUS" = "200" ]; then
    echo -e "${VERDE}✅ Health check OK${RESET}"
  else
    echo -e "${VERMELHO}⚠️  Health check retornou HTTP $STATUS — verifique os logs${RESET}"
  fi

# ════════════════════════════════════════════════════════════════════════════
# DEPLOY PROD
# ════════════════════════════════════════════════════════════════════════════
elif [ "$AMBIENTE" = "prod" ]; then

  # Garantir que está na branch master
  BRANCH=$(git branch --show-current)
  if [ "$BRANCH" != "master" ]; then
    echo -e "${AMARELO}⚠️  Você está na branch '$BRANCH', não no master.${RESET}"
    echo -e "O deploy de prod vai fazer merge de dev → master."
    read -p "Continuar? (s/n): " CONTINUAR
    if [ "$CONTINUAR" != "s" ]; then
      echo "Cancelado."
      exit 0
    fi
    git checkout master
    git merge dev
    git push origin master
    echo -e "${VERDE}✅ Merge dev → master feito${RESET}"
  fi

  # Confirmação obrigatória
  echo ""
  echo -e "${VERMELHO}⚠️  ATENÇÃO: Você está prestes a deployar em PRODUÇÃO (prazu.com.br)${RESET}"
  echo -e "${AMARELO}Isso vai afetar usuários reais.${RESET}"
  echo ""
  read -p "Digite PRODUÇÃO para confirmar: " CONFIRMA

  if [ "$CONFIRMA" != "PRODUÇÃO" ]; then
    echo -e "${VERMELHO}Cancelado. Você digitou '$CONFIRMA', não 'PRODUÇÃO'.${RESET}"
    exit 1
  fi

  echo ""
  echo -e "${AZUL}🔨 Fazendo build...${RESET}"
  gcloud builds submit \
    --tag gcr.io/$PROJECT/prazu:latest \
    --project=$PROJECT --quiet

  echo ""
  echo -e "${AZUL}☁️  Subindo no Cloud Run PROD...${RESET}"
  gcloud run deploy prazu \
    --image gcr.io/$PROJECT/prazu:latest \
    --region $REGION \
    --project $PROJECT \
    --quiet

  echo ""
  echo -e "${VERDE}✅ Deploy PROD concluído!${RESET}"
  echo -e "🔗 URL: ${AZUL}https://prazu.com.br${RESET}"
  echo ""

  # Health check
  sleep 5
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    https://prazu-710127610365.southamerica-east1.run.app/health)
  if [ "$STATUS" = "200" ]; then
    echo -e "${VERDE}✅ Health check OK — produção no ar${RESET}"
  else
    echo -e "${VERMELHO}⚠️  Health check retornou HTTP $STATUS — verifique os logs${RESET}"
  fi

  # Voltar para dev
  git checkout dev
  echo -e "${AZUL}↩️  Voltando para branch dev${RESET}"

else
  echo -e "${VERMELHO}Ambiente inválido: '$AMBIENTE'. Use 'dev' ou 'prod'.${RESET}"
  exit 1
fi
