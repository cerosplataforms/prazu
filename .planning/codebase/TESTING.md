# Testing Patterns

**Analysis Date:** 2026-03-06

## Test Framework

**Runner:**
- Nenhum (pytest, unittest não usados)
- Script manual: `test_prazobot.py`

**Assertion Library:**
- Função `ok(nome, condicao, detalhe="")` que imprime ✅/❌ e acumula PASS/FAIL

**Run Commands:**
```bash
python test_prazobot.py              # Roda todos os testes
```

## Test File Organization

**Location:**
- Arquivo único `test_prazobot.py` na raiz

**Naming:**
- `test_prazobot.py` — prefixo `test_`

**Structure:**
- 12 seções numeradas
- Setup: banco de teste `prazobot_test.db` (removido antes de rodar)
- Variáveis globais `PASS`, `FAIL`, `ERROS`

## Test Structure

**Suite Organization:**
```python
def ok(nome, condicao, detalhe=""):
    global PASS, FAIL, ERROS
    if condicao:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        ERROS.append(f"{nome}: {detalhe}")
        print(f"  ❌ {nome} → {detalhe}")

# Seções:
# 1. DATABASE — Carga de Feriados
# 2. FUNÇÕES AUXILIARES — Recesso e Dia Útil
# 3. CÁLCULO — Publicação e Início
# 4. CÁLCULO — Prazos em Dias Úteis
# 5. CÁLCULO — Prazos em Dias Corridos
# 6. CÁLCULO COMPLETO
# 7. Diferença entre comarcas MG
# 8. DATABASE — Advogados, Processos, Prazos
# 9. Edge cases
# 10. Validação cruzada
# 11. Cenários CPC art. 231
# 12. Expansão nacional (multi-estado)
```

**Patterns:**
- Banco isolado `prazobot_test.db`
- Uso de `db.carregar_feriados()`, `carregar_feriados_2026(db)` para dados
- Comparação de datas e valores esperados

## Mocking

**Framework:** Nenhum

**Patterns:**
- Sem mocks; testes dependem de `feriados_br`, `database`, `prazos_calc`
- Testes de integração com banco real (SQLite em arquivo local)

**What to Mock:**
- APIs externas (DJEN, DataJud, Groq) não são mockadas nos testes atuais

**What NOT to Mock:**
- Lógica de cálculo e banco são testados integrados

## Fixtures and Factories

**Test Data:**
- Feriados carregados via `carregar_feriados_2026(db)` e `db.carregar_feriados(ano, comarca)`
- Datas hardcoded em assertions

**Location:**
- Dados inline em `test_prazobot.py` e em `feriados_br.py`

## Coverage

**Requirements:** Nenhum target definido

**View Coverage:** Nenhum comando de coverage configurado

## Test Types

**Unit Tests:**
- Testes de funções de cálculo (publicação, início, dias úteis, dias corridos)
- Testes de `_em_recesso`, `_eh_dia_util` (com interface legacy)

**Integration Tests:**
- Carga de feriados no banco
- CRUD de advogados, processos, prazos
- Cálculo end-to-end com comarcas reais

**E2E Tests:**
- Não utilizados

## Compatibilidade com prazos_calc / cal_forense

**Observação:** O `test_prazobot.py` importa `_em_recesso` e `_eh_dia_util` de `prazos_calc`, e passa `feriados_test` (set) para `_eh_dia_util` e funções de cálculo. O `prazos_calc` atual usa `CalendarResolver` com assinatura `(d, uf, comarca_processo)` e não exporta `_em_recesso`. Isso pode causar falhas de import ou de assinatura. Ver CONCERNS.md.

---

*Testing analysis: 2026-03-06*
