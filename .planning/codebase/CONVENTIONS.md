# Coding Conventions

**Analysis Date:** 2026-03-06

## Naming Patterns

**Files:**
- snake_case: `prazos_calc.py`, `calendar_store.py`, `calendar_resolver.py`

**Functions:**
- snake_case: `calcular_prazo_completo`, `consultar_djen_por_oab`, `gerar_briefing`
- Prefixo `_` para internas: `_eh_dia_util`, `_get_resolver`, `_send`

**Variables:**
- snake_case: `data_disponibilizacao`, `comarca_processo`, `horario_briefing`

**Types:**
- Sem type hints sistemáticos; uso esporádico em `datajud.py` (`Optional`, `dict`)
- Classes em PascalCase: `Database`, `CalendarStore`, `CalendarResolver`

## Code Style

**Formatting:**
- Sem configuração explícita (black, ruff, etc.)
- Indentação 4 espaços
- Linhas em geral < 100 caracteres

**Linting:**
- Nenhum linter configurado no projeto

## Import Organization

**Order:**
1. stdlib: `os`, `logging`, `asyncio`, `re`, `datetime`
2. Third-party: `telegram`, `dotenv`, `requests`
3. Local: `ia`, `database`, `prazos_calc`, `djen`, `datajud`

**Path Aliases:**
- Nenhum; imports relativos ao pacote ou relativos: `from cal_forense.calendar_store import CalendarStore`

## Error Handling

**Patterns:**
- `try/except` com `logger.error` em pontos de integração (APIs, envio de mensagem)
- Retorno de `None` ou lista vazia em falhas de API
- Fallback amigável em `ia.py` quando Groq falha

## Logging

**Framework:** `logging` padrão

**Patterns:**
- `logger = logging.getLogger(__name__)` em cada módulo
- `logger.info`, `logger.warning`, `logger.error`
- Nível via `LOG_LEVEL` (default INFO)

## Comments

**When to Comment:**
- Docstrings em módulos e funções principais
- Comentários em seções com marcadores `# ====`
- Comentários explicativos em regras CPC/forenses

**Docstrings:**
- Docstrings em módulos (`"""..."""`)
- Docstrings em funções públicas (ex.: `calcular_prazo_completo`)

## Function Design

**Size:**
- Funções longas em `bot.py` (handlers); modularização em helpers

**Parameters:**
- Parâmetros posicionais para essenciais; `uf=""`, `comarca_processo=""` para opcionais
- Parâmetro `feriados=None` mantido em `prazos_calc` para retrocompatibilidade (deprecated)

**Return Values:**
- dict para resultados estruturados (ex.: `calcular_prazo_completo`)
- list para listas
- None em falhas

## Module Design

**Exports:**
- Sem `__all__` explícito
- Export implícito pelo que é importável

**Barrel Files:**
- `cal_forense/__init__.py` mínimo (apenas docstring/pacote)

---

*Convention analysis: 2026-03-06*
