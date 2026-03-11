# Architecture — Prazu

**Atualizado:** março 2026

## Visão geral

Aplicação web monolítica em Python: FastAPI como entry point, PostgreSQL para persistência, Z-API para WhatsApp. Deploy no Google Cloud Run.

## Camadas

**Web / API:**
- Entry point: `web/app.py` (FastAPI, Uvicorn)
- Rotas: páginas HTML, API auth, onboarding, configurações, webhook, jobs
- Auth: JWT em cookie `prazu_token`, dependência `advogado_logado`
- Usado por: usuário via browser e webhook Z-API

**Lógica de negócio:**
- `web/onboarding.py` — DJEN, briefing, mensagens WhatsApp
- `prazos_calc.py` — Cálculo de prazos CPC
- `ia.py` — Briefings e resumos (Gemini)
- `cal_forense/` — Resolução de feriados por comarca

**Dados e integrações:**
- `database_gcp.py` — PostgreSQL async (asyncpg)
- `djen.py` — API DJEN
- `datajud.py` — API DataJud CNJ
- `web/email_sender.py` — Resend
- `web/zapi.py` — Z-API WhatsApp

## Fluxo de dados

**Cadastro → Dashboard:**
1. `/cadastro` → POST `/api/auth/cadastro` → JWT
2. `/onboarding` (OAB, WhatsApp, preferências) → POST `/api/onboarding/salvar`
3. Background: `_buscar_djen` (30 dias) → DataJud → `criar_ou_atualizar_processo` → `criar_prazo_processo`
4. 2 min depois: `enviar_boas_vindas` + `_enviar_resumo` via WhatsApp
5. Redirect para `/dashboard`

**Briefing diário:**
1. Cloud Scheduler → POST `/jobs/briefing`
2. `enviar_briefing_todos` filtra por `horario_briefing` e dia da semana
3. Para cada advogado: `_enviar_resumo` (Gemini ou fallback simples)
4. Z-API envia mensagem para `whatsapp_notificacao`

**Webhook WhatsApp:**
1. Z-API envia POST `/webhook/zapi`
2. `processar_mensagem_zapi` → onboarding (novo) ou `_handle_conversa` (cadastrado)
3. Comandos: `prazos`/`resumo` → resumo; `buscar` → DJEN; outros → resposta padrão

## Banco de dados

- **PostgreSQL** (Cloud SQL em prod)
- Tabelas principais: advogados, processos, prazos, comunicacoes_djen, sessions, whatsapp_events
- Schema: `migrate_fase2.sql`
- Calendário forense: SQLite local `cal_forense/calendar_v2.db` (copiado na imagem)
