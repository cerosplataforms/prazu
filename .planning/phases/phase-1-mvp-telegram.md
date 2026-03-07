# Fase 1 — Fechar MVP Telegram (completar todas as comarcas)

**Roadmap:** `.planning/ROADMAP.md`  
**Projeto:** PrazorBot Brasil / Prazor  
**Critério de sucesso:** 27 UFs + DF com cobertura High/Medium documentada; nenhum tribunal Low em uso ativo; testes multi-estado passando.

**Atualizado:** 2026-03-06 — pós-commits (3e60927, e323162, 4611e8e, 9d58dc0). TJRJ ✅, TJPE ✅, TJGO expandido.

---

## Objetivo

Garantir cobertura nacional do calendário forense para que o bot funcione em qualquer tribunal/comarca do Brasil.

---

## Contexto técnico

| Artefato | Função |
|----------|--------|
| `cal_forense/calendar_loader.py` | Carrega NACIONAIS, RECESSO, ESTADUAIS, SUSPENSOES_TJ, MUNICIPAIS_POR_TJ |
| `cal_forense/calendar_store.py` | Store SQLite (schema v1 holidays ou v2 eventos/localidades) |
| `cal_forense/calendar_resolver.py` | Resolução de dia útil (usado por `prazos_calc`) |
| `feriados_br.py` + `database.py` | Sistema legado de feriados (CONCERNS: duplicado) |
| `test_prazobot.py` | Testes que usam `feriados_br` e `database.carregar_feriados` |

---

## Tarefas (ordem de dependência)

### Wave 1 — Dados de tribunais (paralelizáveis)

#### Tarefa 1.1: Completar TJPE — feriados nacionais e recessos 2026 ✅ FEITO

**Arquivos:** `cal_forense/calendar_loader.py`

**Status:** Complemento TJPE 2026 feito (commit 9d58dc0). NACIONAIS e RECESSO globais cobrem PE. SUSPENSOES_TJ["TJPE"] com São João e N.S. Carmo.

**Verificação:**
```bash
python -c "
from datetime import date
from cal_forense.calendar_store import CalendarStore
from cal_forense.calendar_resolver import CalendarResolver
s = CalendarStore('cal_forense/calendar_v2.db')
r = CalendarResolver(s)
# 01/01 e 20/12 devem ser não-úteis para PE
assert not r.is_business_day(date(2026,1,1), 'PE', 'Recife')
assert not r.is_business_day(date(2026,12,20), 'PE', 'Recife')
print('OK TJPE recesso')
"
```

**Critério de aceite:** PE tem comarcas com feriados nacionais, recesso e suspensões TJPE; 01/01 e 20/12 não são dias úteis em Recife.

---

#### Tarefa 1.2: Completar TJRJ — feriados municipais NURCs 1–11 ✅ FEITO

**Arquivos:** `cal_forense/calendar_v2.db`

**Status:** TJRJ completo (commit 4611e8e). 86 localidades, 257 eventos, NURCs 1-11. Dados no calendar_v2.db (schema v2).

**Verificação:**
```bash
python -c "
from cal_forense.calendar_store import CalendarStore
s = CalendarStore('cal_forense/calendar_v2.db')
c = s.listar_comarcas('RJ')
assert 'Angra dos Reis' in c or 'Rio de Janeiro' in c
print('OK TJRJ comarcas')
"
```

**Critério de aceite:** RJ tem comarcas NURC 7 e 8 com feriados municipais; `/feriados` para comarca do RJ retorna eventos.

---

#### Tarefa 1.3: Elevar TJGO para confiança High ✅ PARCIAL

**Arquivos:** `cal_forense/calendar_v2.db`

**Status:** TJGO expandido para 128 localidades no calendar_v2.db (era 4). O calendar_loader.py ainda tem TJGO com 4 comarcas e confiança `low`; o banco v2 tem dados mais completos. Validar se FONTES_TJ no loader precisa ser atualizado.

**Verificação:**
```bash
grep -A1 '"TJGO"' cal_forense/calendar_loader.py | grep high
python cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db --limpar 2>/dev/null; python cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db
```

**Critério de aceite:** TJGO com ≥15 comarcas e confiança `high`; loader executa sem erro.

---

#### Tarefa 1.4: Validar tribunais Medium e subir para High onde possível

**Arquivos:** `cal_forense/calendar_loader.py`

**Ação:**
- Revisar TJRS (medium): verificar se há fonte oficial (Portaria TJRS, Resolução) para subir para high.
- TJSC, TJMT, TJMS já estão `high` no código; validar que dados estão corretos e fontes citadas.
- Se TJRS tiver fonte documentada, atualizar FONTES_TJ["TJRS"] para `high`.

**Verificação:**
```bash
grep confianca cal_forense/calendar_loader.py | grep -E "TJRS|TJSC|TJMT|TJMS"
```

**Critério de aceite:** Nenhum tribunal em uso ativo com confiança Low; TJRS high se houver fonte.

---

### Wave 2 — Unificação feriados (depende de Wave 1 estável)

#### Tarefa 2.1: Unificar sistema feriados_br vs cal_forense

**Arquivos:** `database.py`, `test_prazobot.py`, `feriados_br.py` (opcional deprecar)

**Ação (CONCERNS.md):**
- Fazer `database.carregar_feriados` usar `CalendarStore`/`CalendarResolver` em vez de tabela `feriados` populada por `feriados_br`.
- Atualizar `test_prazobot.py`: usar `(uf, comarca)` e `CalendarResolver` em vez de set de feriados; importar `_em_recesso` de `calendar_resolver` ou equivalente.
- Remover parâmetro `feriados=None` deprecado de `prazos_calc` ou documentar e emitir warning.
- Decisão: manter `feriados_br` apenas como fonte de dados para migração inicial, ou abandonar tabela `feriados` em `database` e passar a depender só de `cal_forense`.

**Verificação:**
```bash
python test_prazobot.py 2>&1 | tail -20
```

**Critério de aceite:** Testes passam; `prazos_calc` e `database` usam única fonte (cal_forense); sem divergência feriados_br/cal_forense.

---

### Wave 3 — Documentação e testes multi-estado

#### Tarefa 3.1: Documentar cobertura completa ✅ FEITO

**Arquivos:** `.planning/COBERTURA_CALENDARIO.md`

**Status:** Documento criado com tabela por UF, estados incompletos listados (AL, AM, CE, MA, PA, PB, PE, PI, RN, TO), parciais (MT, RO, RR) e próximos passos. PROJECT_KNOWLEDGE §11 atualizado.

---

#### Tarefa 3.2: Testes multi-estado passando

**Arquivos:** `test_prazobot.py` ou `tests/test_multi_estado.py` (novo)

**Ação:**
- Garantir testes para: SP, RJ, BA, RS, PE, CE, PR, SC, PA, GO, ES, DF, MG.
- Cada estado: `calcular_prazo_completo` ou `is_business_day` com comarca representativa; verificar que feriados locais são respeitados.

**Verificação:**
```bash
python test_prazobot.py 2>&1 | grep -E "PASS|FAIL"
# Ou: pytest tests/test_multi_estado.py -v
```

**Critério de aceite:** Todos os testes passam; 13+ estados cobertos por testes automatizados.

---

### Wave 1b — Estados incompletos (pós-documentação)

Ver `.planning/COBERTURA_CALENDARIO.md` para detalhes.

**Alta prioridade:** PE (2→~110), CE (17→~170), MA (3→~210), TO (2→~140), PA (3→~110)  
**Média:** AL, PB, PI, RN, AM  
**Parciais:** MT, RO, RR (completar)

---

## Resumo de arquivos a modificar

| Arquivo | Alterações |
|---------|------------|
| `cal_forense/calendar_loader.py` | TJPE, TJRJ, TJGO em MUNICIPAIS_POR_TJ; FONTES_TJ; SUSPENSOES_TJ se necessário |
| `database.py` | `carregar_feriados` usando CalendarStore ou remoção |
| `test_prazobot.py` | Usar CalendarResolver; assinaturas (uf, comarca) |
| `prazos_calc.py` | Remover/deprecar parâmetro `feriados` |
| `.planning/COBERTURA_CALENDARIO.md` | Novo documento |
| `.planning/PROJECT_KNOWLEDGE.md` | Atualizar §11 |

---

## Verificações globais (critérios de sucesso)

```bash
# 1. Loader roda sem erro
python cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db --limpar
python cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db

# 2. Testes passam
python test_prazobot.py

# 3. Nenhum Low em uso ativo
grep -E "low|Low" cal_forense/calendar_loader.py
# (TJGO deve estar high após Tarefa 1.3)

# 4. Comarcas por UF
python -c "
from cal_forense.calendar_store import CalendarStore
s = CalendarStore('cal_forense/calendar_v2.db')
ufs = ['SP','MG','RJ','PR','SC','RS','PE','CE','BA','PA','GO','ES','DF']
for uf in ufs:
    c = s.listar_comarcas(uf)
    print(f'{uf}: {len(c)} comarcas')
"
```

---

## Estimativa de esforço (opcional)

| Tarefa | Esforço Claude | Observação |
|--------|----------------|------------|
| 1.1 TJPE | 15–30 min | Depende de lista de comarcas PE |
| 1.2 TJRJ | 30–60 min | Pesquisa NURC 7; fontes oficiais |
| 1.3 TJGO | 30–45 min | Expandir comarcas + fontes |
| 1.4 Medium→High | 15–20 min | Revisão e validação |
| 2.1 Unificação | 45–60 min | Refatoração database + testes |
| 3.1 Documentação | 20–30 min | Redação e atualização |
| 3.2 Testes multi-estado | 30–45 min | Cobertura 13 estados |
| **Total** | ~3–4,5 h | |

---

## Dependências entre tarefas

```
1.1 TJPE ──┐
1.2 TJRJ ──┼──> 2.1 Unificação ──> 3.1 Doc ──> 3.2 Testes
1.3 TJGO ──┤
1.4 Medium ┘
```

Wave 1 pode ser executado em paralelo. Wave 2 depende de dados estáveis. Wave 3 depende de 2.1 e 1.x.

---

*Plano Fase 1 — Prazor MVP Telegram v1.0*
