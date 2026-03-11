# Prazu — Guia de Setup

## Desenvolvimento local

### 1. Pré-requisitos

- Python 3.11+
- PostgreSQL (local ou Cloud SQL Proxy)
- Conta Z-API (WhatsApp)
- Conta Resend (email)
- API Key Gemini (Google AI)

### 2. Clonar e instalar

```bash
git clone https://github.com/cerosplataforms/prazu.git
cd prazu
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Variáveis de ambiente (.env)

Crie um arquivo `.env` na raiz:

```env
# Banco (local)
ENVIRONMENT=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prazu
DB_USER=prazu_user
DB_PASSWORD=sua_senha

# Auth
JWT_SECRET=uma-chave-secreta-forte

# WhatsApp (Z-API)
ZAPI_INSTANCE_ID=seu_instance_id
ZAPI_TOKEN=seu_token
ZAPI_CLIENT_TOKEN=seu_client_token

# Email (Resend)
RESEND_API_KEY=re_xxxxx
EMAIL_FROM=noreply@prazu.com.br
EMAIL_FROM_NAME=Prazu

# IA
GEMINI_API_KEY=sua_chave_gemini

# Jobs (para testar localmente)
SCHEDULER_SECRET=um_secret_qualquer
```

### 4. Banco de dados

Execute as migrações:

```bash
psql -U prazu_user -d prazu -f migrate_fase2.sql
```

Ou use Cloud SQL Proxy se for conectar ao banco remoto:

```bash
cloud_sql_proxy -instances=prazu-prod:southamerica-east1:prazu-db=tcp:5433
# DB_HOST=127.0.0.1 DB_PORT=5433
```

### 5. Rodar o servidor

```bash
uvicorn web.app:app --reload --port 8080
```

Acesse: http://localhost:8080

---

## Deploy (Cloud Run)

### Dev

```bash
./deploy.sh dev
```

- Branch `dev`
- Commit automático se houver mudanças
- Build → Cloud Run `prazu-dev`
- URL: https://prazu-dev-710127610365.southamerica-east1.run.app

### Prod

```bash
./deploy.sh prod
```

- Merge `dev` → `master`
- Confirmação digitando `PRODUÇÃO`
- Build → Cloud Run `prazu`
- URL: https://prazu-710127610365.southamerica-east1.run.app

### Variáveis no Cloud Run

As variáveis são configuradas no console ou via `gcloud run services update`:

```bash
gcloud run services update prazu --region southamerica-east1 --project prazu-prod \
  --update-env-vars="RESEND_API_KEY=re_xxx,EMAIL_FROM=noreply@prazu.com.br"
```

Secrets (DB_PASSWORD, JWT_SECRET, GEMINI_API_KEY) vêm do Secret Manager.

---

## Webhook Z-API

Para o bot responder no WhatsApp, configure o webhook da Z-API:

- **URL:** `https://prazu-710127610365.southamerica-east1.run.app/webhook/zapi`
- **Eventos:** mensagens recebidas (ReceivedCallback)
- **Secret:** opcional, use `ZAPI_WEBHOOK_SECRET` se quiser validar

---

## Cloud Scheduler (jobs)

Jobs configurados no GCP:

| Job | Cron | Função |
|-----|------|--------|
| briefing-diario | 0 6-22 * * * (horário cheio) | Envia briefing por horário do usuário |
| expirar-trials | diário | Marca trials vencidos |
| djen | periódico | Monitora DJEN para todos |
| lembrete-trial | diário | Lembrete antes de expirar |

Header: `X-Scheduler-Secret` com valor de `SCHEDULER_SECRET`.

---

## Testes

```bash
python test_prazobot.py
```

Testes focados em `prazos_calc.py` e funcionalidades de banco.
