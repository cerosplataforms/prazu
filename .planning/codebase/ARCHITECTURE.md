# Architecture

**Analysis Date:** 2026-03-06

## Pattern Overview

**Overall:** Aplicação monolítica em Python com bot Telegram como orquestrador, módulos funcionais e SQLite como persistência.

**Key Characteristics:**
- Entry point único: `bot.py` (long polling)
- Scripts auxiliares: `scheduler.py`, `atualizar.py`
- Sem camada de serviços; lógica espalhada em módulos
- Banco por arquivo; `Database` e `CalendarStore` separados

## Layers

**Bot / UI:**
- Purpose: Handler de comandos, callbacks e mensagens do Telegram
- Location: `bot.py`
- Contains: Handlers assíncronos, teclados inline, fluxo de onboarding
- Depends on: `database`, `ia`, `prazos_calc`, `djen`, `datajud`, `cal_forense`
- Used by: Usuário final via Telegram

**Business Logic:**
- Purpose: Cálculo de prazos, resolução de dias úteis, briefing
- Location: `prazos_calc.py`, `ia.py`, `cal_forense/`
- Contains: Funções puras e classes (CalendarResolver, CalendarStore)
- Depends on: `cal_forense`, `database` (para `ia` buscar processos)
- Used by: `bot.py`, `scheduler.py`

**Data / Integrations:**
- Purpose: Persistência e APIs externas
- Location: `database.py`, `djen.py`, `datajud.py`
- Contains: Classe `Database`, funções de consulta DJEN/DataJud
- Depends on: `requests`, `sqlite3`
- Used by: `bot.py`, `scheduler.py`, `atualizar.py`

**Feriados:**
- Purpose: Dados de feriados nacionais, estaduais, municipais
- Location: `feriados_br.py`, `feriados_mg.py`, `cal_forense/calendar_loader.py`
- Contains: Constantes e funções de carga para banco/SQLite
- Depends on: `database` (feriados_br, feriados_mg), `CalendarStore` (loader)
- Used by: `database`, `prazos_calc` (via CalendarResolver/Store)

## Data Flow

**Busca de processos (comando /buscar):**

1. Advogado informa OAB/UF no onboarding
2. `consultar_djen_por_oab` em `djen.py` chama API DJEN → publicações
3. Extração de números CNJ únicos das publicações
4. Para cada CNJ: `consultar_processo` em `datajud.py` → dados do DataJud
5. `Database.criar_processo` salva em `prazobot.db`
6. `calcular_prazo_completo` calcula vencimentos com feriados da comarca do processo

**Briefing diário (scheduler):**

1. Cron executa `scheduler.py` no horário configurado
2. `db.listar_advogados_ativos()` → advogados com `horario_briefing` = hora atual
3. `db.listar_processos_com_prazos(adv_id)` → processos + prazos + andamentos
4. `gerar_briefing()` em `ia.py` → Groq LLM
5. `bot.send_message()` envia para cada advogado

**State Management:**
- Estado em SQLite (`prazobot.db`). Sem Redis ou cache distribuído
- Estado de conversa no `context.user_data` do python-telegram-bot

## Key Abstractions

**Database:**
- Purpose: CRUD de advogados, processos, prazos, andamentos, comunicacoes_djen, feriados
- Location: `database.py`
- Pattern: Classe com métodos que abrem/fecham conexão por operação

**CalendarStore + CalendarResolver:**
- Purpose: Fonte de feriados e decisão de dia útil forense
- Location: `cal_forense/calendar_store.py`, `cal_forense/calendar_resolver.py`
- Pattern: Store consulta SQLite; Resolver usa Store e aplica recesso, fim de semana, feriados

**prazos_calc:**
- Purpose: Cálculo CPC-compliant (arts. 216, 219, 220, 224)
- Location: `prazos_calc.py`
- Pattern: Funções que delegam dia útil ao `CalendarResolver`

## Entry Points

**bot.py:**
- Triggers: Execução direta (`python bot.py`)
- Responsabilidades: Polling Telegram, handlers, onboarding, comandos

**scheduler.py:**
- Triggers: Cron (ex.: a cada hora ou no horário dos briefings)
- Responsabilidades: Enviar briefing para advogados no horário configurado

**atualizar.py:**
- Triggers: Cron (ex.: diariamente às 3h)
- Responsabilidades: Atualizar andamentos via DataJud para todos os processos ativos

## Error Handling

**Strategy:** Try/except genérico em pontos críticos; logs com `logger.error`

**Patterns:**
- `ia.py`: catch Exception → fallback com mensagem amigável
- `djen.py`, `datajud.py`: RequestException / Timeout → log e retorno vazio ou None
- `bot.py`: `_send()` tenta `reply_text` e fallback em caso de exceção

## Cross-Cutting Concerns

**Logging:** `logging` padrão, nível via `LOG_LEVEL`
**Validation:** Parsing manual (regex, strptime); sem Pydantic ou similar
**Authentication:** Nenhuma; identidade por Telegram chat_id

---

*Architecture analysis: 2026-03-06*
