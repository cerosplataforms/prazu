# Cobertura do Calendário Forense — Prazor

**Data:** 2026-03-07 (atualizado pós-commits)  
**Fonte:** `cal_forense/calendar_v2.db` + `calendar_loader.py`  
**Projeto:** PrazorBot Brasil

---

## 1. Resumo geral

| Métrica | Valor |
|---------|-------|
| Tribunais | 63+ |
| Localidades (comarcas/foros) | 2.100+ |
| Eventos 2026 | ~6.120 |
| UFs com cobertura | 27 + DF |

### Status por UF (atualizado mar/2026)

| Status | Quantidade | UFs |
|--------|------------|-----|
| **Completo** | 17 | AC, AP, BA, DF, ES, GO, MG, MS, PE, PR, RJ, RS, SC, SE, SP |
| **Expandido** | 9 | CE, MA, PA, PB, PI, RN, TO, AL (+ TJDFT) |
| **Parcial** | 3 | MT, RO, RR |
| **Incompleto** | 1 | AM |

---

## 2. Tabela detalhada por UF (calendar_v2.db)

| UF | Localidades | Eventos 2026 | Status | Observação |
|----|-------------|--------------|--------|------------|
| AC | 22 | 57 | ✅ Completo | |
| AL | 10 | — | 🔶 Expandido | TJPB/AL |
| AM | 4 | 7 | ⚠️ Incompleto | ~70 comarcas esperadas |
| AP | 13 | 29 | ✅ Completo | |
| BA | 224 | 649 | ✅ Completo | |
| CE | 28 | — | 🔶 Expandido | TJCE 48 comarcas (commit), 28 no DB |
| DF | 1 | — | ✅ | TJDFT 16 circunscrições (Portaria 105/2025) |
| ES | 70 | 185 | ✅ Completo | |
| GO | 128 | 320 | ✅ Completo | |
| MA | 17 | — | 🔶 Expandido | TJMA 35 comarcas (Resolução-GP 131/2025) |
| MG | 389 | 989 | ✅ Completo | |
| MS | 76 | 162 | ✅ Completo | |
| MT | 80 | 186 | 🔶 Parcial | ~57% das comarcas |
| PA | 21 | — | 🔶 Expandido | TJPA 38 comarcas (Portaria 4765/2025) |
| PB | 16 | — | 🔶 Expandido | TJPB 34 comarcas (Ato Conjunto 04/2025) |
| PE | 97 | 303+ | ✅ Completo | 97 comarcas (feriados municipais oficiais) |
| PI | 19 | — | 🔶 Expandido | TJPI 30 comarcas (Provimento 59/2025) |
| PR | 168 | 354 | ✅ Completo | |
| RJ | 86 | 210 | ✅ Completo | NURCs 1-11 |
| RN | 20 | — | 🔶 Expandido | TJRN 37 comarcas (feriados municipais) |
| RO | 34 | 62 | 🔶 Parcial | ~68% das comarcas |
| RR | 10 | 33 | 🔶 Parcial | ~67% das comarcas |
| RS | 170 | 437 | ✅ Completo | |
| SC | 113 | 203 | ✅ Completo | |
| SE | 51 | 119 | ✅ Completo | |
| SP | 340 | 693 | ✅ Completo | |
| TO | 14 | — | 🔶 Expandido | TJTO 21 comarcas (Lcp 10/1996 + municipais) |

---

## 3. Expansões recentes (commits mar/2026)

| Tribunal | Comarcas/circ. | Eventos 2026 | Fonte |
|----------|----------------|--------------|--------|
| TJPE | 97 | 303 | Feriados municipais oficiais |
| TJDFT | 16 circunscrições | 24 | Portaria Conjunta 105/2025 |
| TJPB | 34 | 32 | Ato Conjunto 04/2025 + municipais |
| TJPI | 30 | 49 | Provimento 59/2025 + municipais + suspensão jan |
| TJPA | 38 | 41 | Portaria 4765/2025 + municipais |
| TJMA | 35 | 33 | Resolução-GP 131/2025 + municipais |
| TJCE | 48 | 45 | Portaria 2924/2025 + municipais |
| TJRN | 37 | 40 | Feriados municipais |
| TJTO | 21 | 35 | Lcp 10/1996 + feriados municipais |

---

## 4. Estados ainda incompletos ou parciais

### Incompleto
- **AM**: 4 comarcas — expandir TJAM (~70 esperadas).

### Parciais (completar para High)
- **MT**: 80 → ~140 comarcas
- **RO**: 34 → ~50
- **RR**: 10 → ~15

---

## 5. Fontes de dados

| Tribunal | Fonte típica | Observação |
|----------|--------------|-------------|
| TJSP | Provimento CGJ 37/2025 | 340 comarcas |
| TJMG | Site TJMG Calendário Forense | 389 comarcas |
| TJPR | Decreto Judiciário 449/2025 | |
| TJSC | Resolução GP 1/2026 + GP 4/2026 | |
| TJMT | Portaria TJMT/PRES 1915/2025 | |
| TJMS | MPMS + Portaria TJMS 983/2025 | |
| TJRS | TRF4 parcial | medium |
| TJGO | PDF geral 2026 | 128 comarcas (confiança low no loader) |
| TJRJ | NURCs 1-11 | 86 localidades |
| TJPE | portal.tjpe.jus.br | 97 comarcas, 303+ eventos |
| TJCE | Portaria 2924/2025 | 48 comarcas |
| TJMA | Resolução-GP 131/2025 | 35 comarcas |
| TJPA | Portaria 4765/2025 | 38 comarcas |
| TJPI | Provimento 59/2025 | 30 comarcas |
| TJPB | Ato Conjunto 04/2025 | 34 comarcas |
| TJRN | Feriados municipais | 37 comarcas |
| TJTO | Lcp 10/1996 + Lei 4.509/2024 + municipais | 21 comarcas |
| TJDFT | Portaria Conjunta 105/2025 | 16 circunscrições |

---

## 6. Como atualizar

### Carregar novos dados
1. **Via calendar_loader.py**: adicionar `MUNICIPAIS_TJXX`, incluir em `MUNICIPAIS_POR_TJ` e `FONTES_TJ`; rodar:
   ```bash
   python3 cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db
   ```
2. Com `--limpar` para recarregar o ano:
   ```bash
   python3 cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db --limpar
   python3 cal_forense/calendar_loader.py --db cal_forense/calendar_v2.db
   ```

### Validar cobertura
```bash
python3 -c "
from cal_forense.calendar_store import CalendarStore
s = CalendarStore('cal_forense/calendar_v2.db')
for uf in ['PE', 'CE', 'TO', 'RN', 'PA']:
    c = s.listar_comarcas(uf)
    print(f'{uf}: {len(c)} comarcas')
"
```

---

*Cobertura Prazor — calendar_v2.db — atualizado 2026-03-07*
