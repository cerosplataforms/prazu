# Prazu — Monitoramento de Prazos Processuais

SaaS para advogados brasileiros. Monitora publicações no DJEN, calcula prazos processuais com feriados forenses e envia alertas diários no WhatsApp.

**Site:** [prazu.com.br](https://prazu.com.br)  
**Suporte:** [wa.me/5511916990578](https://wa.me/5511916990578)

---

## O que faz

- **Cadastro e onboarding** — Nome, OAB, verificação WhatsApp
- **Busca automática no DJEN** — Publicações dos últimos 30 dias
- **Prazos processuais** — Cálculo CPC-compliant com feriados por comarca
- **Dashboard web** — Processos, prazos urgentes, vencidos, links PJe
- **Notificações WhatsApp** — Boas-vindas, resumo inicial e briefing diário
- **Recuperação de senha** — Código por e-mail (Resend)
- **Termos e Política de Privacidade**

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | FastAPI, Python 3.11 |
| Banco | PostgreSQL (Cloud SQL) |
| Auth | JWT em cookie httpOnly |
| Webhook | Z-API (WhatsApp) |
| Email | Resend (noreply@prazu.com.br) |
| IA | Google Gemini 2.0 Flash |
| Deploy | Google Cloud Run |
| Build | Cloud Build, Docker |

---

## Estrutura do projeto

```
prazu/
├── web/
│   ├── app.py              # FastAPI — rotas, auth, API
│   ├── auth.py             # JWT, tokens
│   ├── onboarding.py       # DJEN, WhatsApp, briefing, jobs
│   ├── email_sender.py     # Resend (transacional)
│   ├── zapi.py             # Cliente Z-API WhatsApp
│   └── templates/          # HTML (Jinja2)
├── database_gcp.py         # PostgreSQL async (asyncpg)
├── prazos_calc.py          # Motor de prazos CPC
├── djen.py                 # API DJEN (comunicaapi.pje.jus.br)
├── datajud.py              # API DataJud CNJ
├── ia.py                   # Gemini — briefings, perguntas
├── cal_forense/            # Calendário forense (comarcas, feriados)
├── deploy.sh               # Deploy dev/prod
├── requirements.txt
└── .planning/              # Roadmap, docs internos
```

---

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `ENVIRONMENT` | `production` ou `development` |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL |
| `CLOUD_SQL_INSTANCE` | Cloud SQL (prod): `projeto:regiao:instancia` |
| `JWT_SECRET` | Assinatura JWT |
| `ZAPI_INSTANCE_ID`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` | Z-API WhatsApp |
| `ZAPI_WEBHOOK_SECRET` | Validação webhook (opcional) |
| `RESEND_API_KEY` | Emails transacionais |
| `GEMINI_API_KEY` | Briefings via IA |
| `SCHEDULER_SECRET` | Jobs Cloud Scheduler |

---

## Deploy

```bash
# Dev (branch dev)
./deploy.sh dev

# Prod (merge dev → master, pede confirmação)
./deploy.sh prod
```

---

## Comandos do bot WhatsApp

| Mensagem | Ação |
|----------|------|
| `prazos`, `resumo`, `briefing`, `oi`, `olá` | Envia resumo dos prazos |
| `buscar`, `atualizar`, `djen` | Busca novas publicações no DJEN |
| Outras | Resposta padrão: comandos + link prazu.com.br + suporte |

---

## Cobertura de feriados

- **63 tribunais** cadastrados  
- **2.000+ localidades** com feriados forenses  
- **~6.000 eventos** 2026  
- Ver `.planning/COBERTURA_CALENDARIO.md` para detalhes  

---

## Testes

```bash
python test_prazobot.py
```

Testes focados em `prazos_calc.py` e banco.

---

## Licença

Uso privado. Prazu © 2026.
