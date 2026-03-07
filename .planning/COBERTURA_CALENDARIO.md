# Cobertura do Calendário Forense — Prazor

**Data:** 2026-03-06  
**Fonte:** `cal_forense/calendar_v2.db` + `calendar_loader.py`  
**Projeto:** PrazorBot Brasil

> **Nota:** PE tem 151 comarcas em `MUNICIPAIS_TJPE` no calendar_loader. O calendar_v2.db pode ter estrutura diferente; verificar se o loader popula o v2 ou se há script de import separado.

---

## 1. Resumo geral

| Métrica | Valor |
|---------|-------|
| Tribunais | 63 |
| Localidades (comarcas/foros) | 2.036 |
| Eventos 2026 | 5.683 |
| UFs com cobertura | 27 + DF |

### Status por UF

| Status | Quantidade | UFs |
|--------|------------|-----|
| **Completo** | 17 | AC, AP, BA, DF, ES, GO, MG, MS, PE, PR, RJ, RS, SC, SE, SP |
| **Parcial** | 3 | MT, RO, RR |
| **Incompleto** | 8 | AL, AM, CE, MA, PA, PB, PI, RN, TO |

---

## 2. Tabela detalhada por UF

| UF | Localidades | Eventos 2026 | Status | Observação |
|----|-------------|--------------|--------|------------|
| AC | 22 | 57 | ✅ Completo | |
| AL | 12 | 26 | ⚠️ Incompleto | ~100 comarcas esperadas |
| AM | 4 | 7 | ⚠️ Incompleto | ~70 comarcas esperadas |
| AP | 13 | 29 | ✅ Completo | |
| BA | 224 | 649 | ✅ Completo | |
| CE | 17 | 28 | ⚠️ Incompleto | ~170 comarcas esperadas |
| DF | 1 | 2 | ✅ Completo | Brasília |
| ES | 70 | 185 | ✅ Completo | |
| GO | 128 | 320 | ✅ Completo | |
| MA | 3 | 7 | ⚠️ Incompleto | ~210 comarcas esperadas |
| MG | 389 | 989 | ✅ Completo | |
| MS | 76 | 162 | ✅ Completo | |
| MT | 80 | 186 | 🔶 Parcial | ~57% das comarcas |
| PA | 3 | 5 | ⚠️ Incompleto | ~110 comarcas esperadas |
| PB | 11 | 31 | ⚠️ Incompleto | ~120 comarcas esperadas |
| PE | 151 | 402 | ✅ Completo | calendar_loader: 151 comarcas (portal.tjpe.jus.br) |
| PI | 4 | 6 | ⚠️ Incompleto | ~130 comarcas esperadas |
| PR | 168 | 354 | ✅ Completo | |
| RJ | 86 | 210 | ✅ Completo | NURCs 1-11 |
| RN | 3 | 6 | ⚠️ Incompleto | ~70 comarcas esperadas |
| RO | 34 | 62 | 🔶 Parcial | ~68% das comarcas |
| RR | 10 | 33 | 🔶 Parcial | ~67% das comarcas |
| RS | 170 | 437 | ✅ Completo | |
| SC | 113 | 203 | ✅ Completo | |
| SE | 51 | 119 | ✅ Completo | |
| SP | 340 | 693 | ✅ Completo | |
| TO | 2 | 2 | ⚠️ Incompleto | ~140 comarcas esperadas |

---

## 3. Estados incompletos — o que falta

### Alta prioridade (maior população/volume processual)

| UF | Atual | Esperado | O que fazer |
|----|-------|----------|-------------|
| ~~**PE**~~ | ~~2~~ | ~~~110~~ | ✅ **FEITO** — 151 comarcas no calendar_loader (MUNICIPAIS_TJPE) |
| **CE** | 17 | ~170 | Expandir cobertura TJCE; fonte: calendário forense TJCE |
| **MA** | 3 | ~210 | Expandir TJMA; muitas comarcas faltando |
| **TO** | 2 | ~140 | Quase vazio; priorizar comarcas principais |
| **PA** | 3 | ~110 | Expandir TJPA; Belém e principais comarcas |

### Média prioridade

| UF | Atual | Esperado | O que fazer |
|----|-------|----------|-------------|
| **AL** | 12 | ~100 | Expandir TJAL |
| **PB** | 11 | ~120 | Expandir TJPB |
| **PI** | 4 | ~130 | Expandir TJPI |
| **RN** | 3 | ~70 | Expandir TJRN |
| **AM** | 4 | ~70 | Expandir TJAM |

### Parciais (completar para High)

| UF | Atual | Esperado | O que fazer |
|----|-------|----------|-------------|
| **MT** | 80 | ~140 | Completar comarcas restantes TJMT |
| **RO** | 34 | ~50 | Completar TJRO |
| **RR** | 10 | ~15 | Completar TJRR (próximo de 100%) |

---

## 4. Estados completos (17 UFs + DF)

AC, AP, BA, DF, ES, GO, MG, MS, **PE**, PR, RJ, RS, SC, SE, SP.

---

## 5. Fontes de dados

| Tribunal | Fonte típica | Observação |
|----------|--------------|------------|
| TJSP | Provimento CGJ 37/2025 | 340 comarcas |
| TJMG | Site TJMG Calendário Forense | 389 comarcas |
| TJPR | Decreto Judiciário 449/2025 | |
| TJSC | Resolução GP 1/2026 + GP 4/2026 | |
| TJMT | Portaria TJMT/PRES 1915/2025 | |
| TJMS | MPMS + Portaria TJMS 983/2025 | |
| TJRS | TRF4 parcial | |
| TJGO | PDF geral 2026 | 128 comarcas |
| TJRJ | NURCs 1-11 | 86 localidades |
| TJPE | portal.tjpe.jus.br (14/01/2026) | ✅ 151 comarcas, 402 feriados municipais |

---

## 6. Como atualizar

### Carregar novos dados

1. **Via calendar_loader.py** (schema v1 / MUNICIPAIS_POR_TJ):
   - Adicionar `MUNICIPAIS_TJXX` em `cal_forense/calendar_loader.py`
   - Incluir em `MUNICIPAIS_POR_TJ` e `FONTES_TJ`
   - Rodar: `python cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db`

2. **Via script/import** (schema v2):
   - Inserir em `tribunais`, `localidades`, `eventos`
   - Usar `CalendarStore` ou SQL direto

### Validar cobertura

```bash
# Contagem por UF
python3 -c "
from cal_forense.calendar_store import CalendarStore
s = CalendarStore('cal_forense/calendar_v2.db')
for uf in ['PE', 'CE', 'TO']:
    c = s.listar_comarcas(uf)
    print(f'{uf}: {len(c)} comarcas')
"
```

---

## 7. Próximos passos (Fase 1)

1. [x] ~~Completar **TJPE**~~ — ✅ 151 comarcas no calendar_loader
2. [ ] Completar **TJCE** — expandir de 17 para ~170 comarcas
3. [ ] Completar **TJMA** — de 3 para ~210 comarcas
4. [ ] Completar **TJTO** — de 2 para comarcas principais
5. [ ] Completar **TJPA** — de 3 para ~110 comarcas
6. [ ] Expandir AL, PB, PI, RN, AM
7. [ ] Finalizar MT, RO, RR (parciais)
8. [ ] Atualizar este documento após cada expansão

---

*Cobertura Prazor — calendar_v2.db*
