# Technology Stack

**Analysis Date:** 2026-03-06

## Languages

**Primary:**
- Python 3 — Runtime principal. Código em `bot.py`, `database.py`, `prazos_calc.py`, `djen.py`, `datajud.py`, `ia.py`, `scheduler.py`, `atualizar.py`, `feriados_br.py`, `feriados_mg.py`, `test_prazobot.py` e pacote `cal_forense/`.

**Secondary:**
- SQL — Schemas e queries em `database.py` (SQLite). Definições em `cal_forense/calendar_store.py`.

## Runtime

**Environment:**
- Python 3.14 (venv detectado)

**Package Manager:**
- pip
- Lockfile: ausente (apenas `requirements.txt`)

## Frameworks

**Core:**
- python-telegram-bot 21.3 — Bot Telegram (comandos, callbacks, handlers)
- APScheduler 3.10.4 — Agendamento (não usado ativamente; scheduler usa cron manual)

**AI/LLM:**
- openai (compatível Groq) — Chat completions via `base_url="https://api.groq.com/openai/v1"`
- groq >= 0.4.0 — Cliente Groq (Llama 3.3 70B)

**Build/Dev:**
- python-dotenv 1.0.1 — Carga de variáveis `.env`

## Key Dependencies

**Critical:**
- python-telegram-bot 21.3 — Interface com usuários
- requests >= 2.31.0 — HTTP para DJEN, DataJud
- httpx >= 0.25.0 — HTTP alternativo (possivelmente para Groq)

**Infrastructure:**
- sqlite3 (stdlib) — Bancos `prazobot.db`, `calendar_v2.db`, `calendar.db`

## Configuration

**Environment:**
- Arquivo `.env` (não versionado). Template em `.env.example`
- Variáveis: `TELEGRAM_TOKEN`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `LOG_LEVEL`

**Build:**
- Nenhum build step. Execução direta: `python bot.py`, `python scheduler.py`, `python atualizar.py`

## Platform Requirements

**Development:**
- Python 3.10+
- Acesso à internet (APIs DJEN, DataJud, Groq, Telegram)

**Production:**
- Servidor Linux/Mac com cron para `scheduler.py` e `atualizar.py`
- SQLite (arquivos locais)

---

*Stack analysis: 2026-03-06*
