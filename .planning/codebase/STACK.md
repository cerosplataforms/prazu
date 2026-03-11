# Technology Stack — Prazu

**Atualizado:** março 2026

## Linguagens

- **Python 3.11** — Runtime principal
- **SQL** — PostgreSQL (asyncpg), schemas em `migrate_fase2.sql`
- **HTML/CSS/JS** — Templates Jinja2 em `web/templates/`

## Frameworks e bibliotecas

| Categoria | Tecnologia |
|-----------|------------|
| Web | FastAPI 0.111+, Uvicorn |
| Templates | Jinja2 3.1+ |
| Banco | asyncpg 0.29+ |
| Auth | python-jose (JWT), bcrypt |
| HTTP | httpx, requests |
| IA | google-generativeai (Gemini 2.0 Flash) |
| Env | python-dotenv |

## Infraestrutura

| Camada | Tecnologia |
|--------|------------|
| Compute | Google Cloud Run |
| Banco | Cloud SQL (PostgreSQL 15) |
| Build | Cloud Build, Docker |
| Secrets | Google Secret Manager |
| Scheduler | Cloud Scheduler |
| Storage | Google Container Registry |

## Integrações externas

| Serviço | Uso |
|---------|-----|
| Z-API | WhatsApp (envio e webhook) |
| Resend | Emails transacionais |
| DJEN | comunicaapi.pje.jus.br |
| DataJud | api-publica.datajud.cnj.jus.br |
| Gemini | google-generativeai |

## Configuração

- **.env** — Variáveis locais (não versionado)
- **Cloud Run** — Env vars e Secret Manager em produção
- **deploy.sh** — Script de deploy dev/prod

## Plano de execução

- `python web/app.py` via Uvicorn
- Workers: 1 (Cloud Run)
- Porta: 8080 (PORT env)
