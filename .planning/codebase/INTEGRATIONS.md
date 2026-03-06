# External Integrations

**Analysis Date:** 2026-03-06

## APIs & External Services

**DJEN (Diário de Justiça Eletrônico Nacional):**
- URL: `https://comunicaapi.pje.jus.br/api/v1/comunicacao`
- Uso: Consulta publicações por OAB/UF (últimos 90–365 dias)
- Cliente: `requests`
- Auth: nenhuma

**DataJud CNJ:**
- URL: `https://api-publica.datajud.cnj.jus.br`
- Uso: Busca de processos por número CNJ, andamentos, movimentações
- Cliente: `requests`
- Auth: API key pública do CNJ (hardcoded em `datajud.py` linha 25)

**Groq (LLM):**
- URL: `https://api.groq.com/openai/v1`
- Uso: Briefing matinal e respostas a perguntas em linguagem natural
- Cliente: `openai.OpenAI(api_key=..., base_url=...)`
- Auth: `GROQ_API_KEY` (env)

**Telegram Bot API:**
- Uso: Envio de mensagens, comandos, callbacks
- Cliente: python-telegram-bot
- Auth: `TELEGRAM_TOKEN` (env)

## Data Storage

**Databases:**
- SQLite — `prazobot.db` (advogados, processos, prazos, andamentos, comunicacoes_djen, feriados)
- SQLite — `cal_forense/calendar_v2.db` (eventos forenses, tribunais, localidades)
- SQLite — `calendar.db` (raiz, possível legado)

**File Storage:**
- Sistema de arquivos local

**Caching:**
- Cache em memória em `CalendarResolver._cache` para sets de feriados por (ano, uf, comarca)

## Authentication & Identity

**Auth Provider:**
- Telegram — identificação por `chat_id`
- Sem OAuth; OAB/UF coletados no onboarding

## Monitoring & Observability

**Error Tracking:**
- Nenhum serviço externo

**Logs:**
- `logging` padrão Python, nível configurável via `LOG_LEVEL`

## CI/CD & Deployment

**Hosting:**
- Não definido (execução local/cron)

**CI Pipeline:**
- Nenhum (sem GitHub Actions, etc.)

## Environment Configuration

**Required env vars:**
- `TELEGRAM_TOKEN`
- `GROQ_API_KEY`

**Optional:**
- `LOG_LEVEL` (default: INFO)
- `GEMINI_API_KEY` (mencionado em `.env.example`, uso não confirmado)

**Secrets location:**
- `.env` (não versionado)

## Webhooks & Callbacks

**Incoming:**
- Long polling do Telegram (padrão python-telegram-bot)

**Outgoing:**
- Mensagens Telegram; chamadas HTTP para DJEN, DataJud, Groq

---

*Integration audit: 2026-03-06*
