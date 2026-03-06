# Codebase Structure

**Analysis Date:** 2026-03-06

## Directory Layout

```
prazu/
├── bot.py                 # Bot Telegram (entry point principal)
├── database.py            # SQLite — advogados, processos, prazos, andamentos
├── prazos_calc.py         # Motor de cálculo de prazos CPC
├── feriados_br.py         # Feriados 2026 (27 UFs, comarcas)
├── feriados_mg.py         # Feriados MG (legado/parcial)
├── djen.py                # API REST DJEN (comunicaapi.pje.jus.br)
├── datajud.py             # API DataJud CNJ
├── ia.py                  # Integração Groq (briefing, perguntas)
├── scheduler.py           # Cron de briefings
├── atualizar.py           # Atualização noturna via DataJud
├── test_prazobot.py       # Testes manuais (~144 casos)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── SETUP.md
├── GUIA-COMPLETO.md
├── GUIA-PASSO-A-PASSO.md
├── cal_forense/           # Motor forense de feriados
│   ├── __init__.py
│   ├── calendar_store.py  # Armazém SQLite de eventos
│   ├── calendar_resolver.py  # Resolvedor de dias úteis
│   ├── calendar_loader.py # Loader nacional (1.057 comarcas)
│   ├── calendar_v2.db     # Banco v2 (eventos)
│   └── calendar.db        # Banco legado (se existir)
├── prazobot.db            # Banco principal (runtime)
├── calendar.db            # Banco raiz (possível duplicata)
└── venv/                  # Ambiente virtual
```

## Directory Purposes

**Raiz:**
- Scripts Python principais e de apoio
- Configuração e documentação

**cal_forense:**
- Motor de feriados forenses
- Schema v2 normalizado (tribunais, localidades, eventos)
- Retrocompatível com schema v1 (holidays)

## Key File Locations

**Entry Points:**
- `bot.py`: Bot Telegram
- `scheduler.py`: Envio de briefings
- `atualizar.py`: Atualização de processos

**Configuration:**
- `.env.example`: Template de variáveis
- `requirements.txt`: Dependências

**Core Logic:**
- `prazos_calc.py`: Cálculo de prazos
- `cal_forense/calendar_resolver.py`: Dia útil forense
- `ia.py`: Briefing e perguntas com IA

**Testing:**
- `test_prazobot.py`: Testes em arquivo único

## Naming Conventions

**Files:**
- snake_case: `prazos_calc.py`, `calendar_store.py`

**Directories:**
- snake_case: `cal_forense`

**Funções/variáveis:**
- snake_case: `calcular_prazo_completo`, `consultar_djen_por_oab`

## Where to Add New Code

**Nova feature de comando no bot:**
- Handler em `bot.py`
- Lógica reutilizável em módulo apropriado (`djen`, `datajud`, `prazos_calc`)

**Novo módulo de integração:**
- Novo arquivo na raiz (ex.: `tribunal_x.py`)
- Import em `bot.py` onde for usado

**Novo tipo de feriado/evento:**
- `cal_forense/calendar_loader.py` ou `feriados_br.py`
- Ou inserção direta em `calendar_store`/banco

**Testes:**
- Adicionar em `test_prazobot.py` ou criar `tests/` (não existe hoje)

## Special Directories

**venv/:**
- Ambiente virtual Python
- Gerado; não versionado

**cal_forense/:**
- Código + bancos SQLite (calendar_v2.db, calendar.db)
- calendar_v2.db: gerado por `calendar_loader.py`; pode ser versionado ou gerado em deploy

---

*Structure analysis: 2026-03-06*
