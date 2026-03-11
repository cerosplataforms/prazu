# Prazu — Project Knowledge

**Atualizado:** março 2026

## 1. O QUE É

Prazu é um SaaS para advogados brasileiros que monitora prazos processuais e envia alertas via WhatsApp. Produto principal: web app com dashboard, busca automática no DJEN e briefings diários.

**Site:** prazu.com.br  
**Suporte:** wa.me/5511916990578  
**Stack:** Python 3.11, FastAPI, PostgreSQL (Cloud SQL), Z-API WhatsApp, Resend, Gemini 2.0 Flash  
**Deploy:** Google Cloud Run (southamerica-east1)

---

## 2. ARQUITETURA ATUAL

```
prazu/
├── web/
│   ├── app.py              # FastAPI: rotas, auth, API, jobs
│   ├── auth.py             # JWT, tokens (prazu_token cookie)
│   ├── onboarding.py       # DJEN, WhatsApp, briefing, monitoramento
│   ├── email_sender.py     # Resend (códigos, recuperação senha)
│   ├── zapi.py             # Cliente Z-API WhatsApp
│   └── templates/          # Jinja2 HTML
├── database_gcp.py         # PostgreSQL async (asyncpg)
├── prazos_calc.py          # Motor CPC (arts. 216, 219, 220, 224)
├── djen.py                 # API REST DJEN (comunicaapi.pje.jus.br)
├── datajud.py              # API DataJud CNJ
├── ia.py                   # Gemini 2.0 Flash (briefings)
├── cal_forense/            # Calendário forense (calendar_v2.db)
├── deploy.sh               # Deploy dev/prod
├── migrate_fase2.sql       # Schema PostgreSQL
└── requirements.txt
```

### Fluxos principais

- **Cadastro:** `/cadastro` → POST `/api/auth/cadastro` → `/onboarding` (OAB, WhatsApp, preferências) → `/dashboard`
- **Login:** `/login` → JWT em cookie → redirect
- **Recuperação de senha:** `/esqueci-senha` → código por email (Resend) → nova senha
- **WhatsApp:** Webhook Z-API → `processar_mensagem_zapi` → onboarding ou conversa (prazos, buscar)
- **Briefing diário:** Cloud Scheduler → `/jobs/briefing` → `enviar_briefing_todos`

---

## 3. REGRAS DE PRAZO (CPC)

- **Art. 216:** Feriados da comarca **do processo** (não do advogado)
- **Art. 219:** Contagem em dias úteis
- **Art. 220:** Recesso forense 20/dez–20/jan
- **Art. 224:** Exclui dia do começo, inclui dia do vencimento
- Publicação DJEN → 1º dia útil após disponibilização
- Início prazo = 1º dia útil após publicação

---

## 4. APIs

| API | Uso |
|-----|-----|
| DJEN (comunicaapi.pje.jus.br) | Publicações por OAB, últimos 30 dias |
| DataJud (CNJ) | Detalhes do processo (classe, partes, movimentações) |
| Z-API | Envio e recebimento de mensagens WhatsApp |
| Resend | Emails transacionais (noreply@prazu.com.br) |
| Gemini 2.0 Flash | Briefings e resumos em linguagem natural |

---

## 5. COMANDOS BOT WHATSAPP

| Mensagem | Ação |
|----------|------|
| `prazos`, `resumo`, `briefing`, `oi`, `olá`, `bom dia`, etc. | Envia resumo de prazos |
| `buscar`, `atualizar`, `djen` | Busca novas publicações DJEN |
| Outras | Resposta padrão com comandos + prazu.com.br + suporte |

---

## 6. VARIÁVEIS DE AMBIENTE

| Variável | Produção | Descrição |
|----------|----------|-----------|
| ENVIRONMENT | production | Modo deploy |
| DB_HOST, DB_NAME, DB_USER, DB_PASSWORD | Secrets | PostgreSQL |
| CLOUD_SQL_INSTANCE | prazu-prod:southamerica-east1:prazu-db | Socket Cloud SQL |
| JWT_SECRET | Secret | Assinatura JWT |
| ZAPI_INSTANCE_ID, ZAPI_TOKEN, ZAPI_CLIENT_TOKEN | Env | Z-API |
| ZAPI_WEBHOOK_SECRET | (opcional) | Validação webhook |
| RESEND_API_KEY | Env | Emails |
| GEMINI_API_KEY | Secret | Briefings IA |
| SCHEDULER_SECRET | Secret | Jobs Cloud Scheduler |

---

## 7. CALENDÁRIO FORENSE (cal_forense)

- **calendar_v2.db** — SQLite local, copiado na imagem Docker
- 63 tribunais, 2.000+ localidades, ~6.000 eventos 2026
- Ver `.planning/COBERTURA_CALENDARIO.md`

---

## 8. ROADMAP (visão)

1. **Fase 1** — MVP Telegram (comarcas) — em andamento
2. **Fase 2** — Supabase + deploy — **concluído** (Cloud SQL + Cloud Run)
3. **Fase 3** — Interface Web — **concluído**
4. **Fase 4** — WhatsApp — **concluído**
5. **Fase 5** — Vendas (pagamentos, planos)

---

## 9. CONVENÇÕES

- Resposta em português
- Commits atômicos ao executar planos
- Chaves sensíveis nunca no código
- Logs via `logging` padrão
