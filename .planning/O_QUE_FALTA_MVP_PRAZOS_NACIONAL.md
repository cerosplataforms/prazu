# O que falta para o MVP ficar seguro em prazos no território nacional

**Objetivo:** Deixar claro o que ainda falta para o cálculo de prazos ser **confiável em qualquer comarca do Brasil**, sem risco de errar vencimento por falta de feriado municipal/estadual.

**Referências:** `.planning/COBERTURA_CALENDARIO.md`, `.planning/phases/phase-1-mvp-telegram.md`, `cal_forense/calendar_resolver.py` (confidence).

---

## 1. O que já está “seguro” hoje

| Aspecto | Situação |
|--------|----------|
| **Regras CPC** | Implementadas em `prazos_calc.py`: art. 216 (feriados da comarca do processo), 219 (dias úteis), 220 (recesso 20/dez–20/jan), 224 (excluir dia do começo, incluir do vencimento). |
| **Feriados nacionais + recesso** | Sempre considerados em todo o território (NACIONAIS_2026 + RECESSO no calendar_loader; aplicados a qualquer UF/comarca). |
| **17 UFs + DF “completas”** | AC, AP, BA, DF, ES, GO, MG, MS, PE, PR, RJ, RS, SC, SE, SP têm muitas comarcas e feriados municipais no `calendar_v2.db`. Para essas UFs, o risco de errar prazo por falta de feriado municipal é **baixo** nas comarcas cobertas. |
| **Comarca desconhecida** | Se a comarca não está no banco, o sistema usa só nacionais + estaduais (quando existem); o `CalendarResolver` marca confiança **medium** e o bot pode informar “comarca sem cobertura municipal”. |
| **Testes** | 129 testes passando; multi-estado (MG, SP, RJ, BA, RS, PE, CE, PR, SC, PA, GO, ES, DF) coberto em `test_prazobot.py`. |

Ou seja: **onde há dados (17 UFs + DF), o motor está correto**. O risco nacional está em **comarcas/estados com poucos ou nenhum dado**.

---

## 2. O que falta para “MVP seguro no território nacional”

Dividido em: **dados (calendário)**, **comportamento e avisos**, **confiança por tribunal** e **validação**.

---

### 2.1 Dados — Estados incompletos (8 UFs)

Hoje **8 UFs** estão marcadas como **incompletas**: poucas comarcas e/ou poucos eventos. Nesses estados, para muitas comarcas o sistema usa **apenas feriados nacionais** (e estaduais quando existem). Feriados **municipais** faltam → risco de **considerar dia útil quando naquele município é feriado** → prazo vencendo um dia antes do correto.

| UF | Comarcas no banco | Ordem de magnitude esperada | Prioridade para MVP “seguro” |
|----|--------------------|----------------------------|------------------------------|
| **CE** | 17 | ~170 | **Alta** — volume e importância regional |
| **MA** | 3 | ~210 | **Alta** |
| **TO** | 2 | ~140 | **Alta** — hoje quase vazio |
| **PA** | 3 | ~110 | **Alta** |
| **AL** | 12 | ~100 | Média |
| **PB** | 11 | ~120 | Média |
| **PI** | 4 | ~130 | Média |
| **RN** | 3 | ~70 | Média |
| **AM** | 4 | ~70 | Média |

**O que falta:** Incluir no `calendar_loader.py` (e depois no `calendar_v2.db`) as comarcas e feriados municipais oficiais de cada TJ (TJCE, TJMA, TJTO, TJPA, TJAL, TJPB, TJPI, TJRN, TJAM), a partir de calendários forenses / portarias / resoluções publicadas pelos tribunais.

**Fonte de verdade:** `.planning/COBERTURA_CALENDARIO.md` — seção “O que fazer” por UF.

---

### 2.2 Dados — Estados parciais (3 UFs)

| UF | Situação | O que falta |
|----|----------|-------------|
| **MT** | 80 comarcas | Completar até ~140 (comarcas restantes TJMT). |
| **RO** | 34 comarcas | Completar até ~50 (TJRO). |
| **RR** | 10 comarcas | Completar até ~15 (TJRR). |

Completar esses três reduz o número de comarcas “sem municipais” nesses estados.

---

### 2.3 Confiança por tribunal (TJGO e TJRS)

- **TJGO** está com `confianca: "low"` no `calendar_loader.py`, mesmo com 128 localidades no `calendar_v2.db`.  
  **Falta:** Alinhar loader e banco (fonte documentada) e marcar TJGO como `high` se os dados forem oficiais.
- **TJRS** está `medium` (fonte “TRF4 parcial”).  
  **Falta:** Se houver portaria/resolução do TJRS com calendário forense, usar como fonte e passar para `high`.

Objetivo do MVP: **nenhum tribunal em uso ativo com confiança low**; RS em `high` se houver fonte.

---

### 2.4 Avisos e transparência ao usuário

- O `CalendarResolver` já expõe **confidence** (high/medium/low) e **comarca_coberta**.
- O bot já mostra no `/feriados` algo como “Feriados considerados: nacionais + estaduais + municipais (confidence)”.
- **Falta (recomendado para “seguro”):**
  - No **briefing** ou no **cálculo de prazo**: quando a comarca for **não coberta** (confidence medium) ou **low**, exibir aviso claro, por exemplo:  
    “⚠️ Comarca X não tem feriados municipais no nosso calendário. Consideramos só nacionais e estaduais. Confira no tribunal.”
  - Opcional: comando ou resposta que diga explicitamente “sua comarca tem cobertura completa” ou “sua comarca tem cobertura parcial”.

Assim o advogado **sabe quando deve conferir no tribunal**, em vez de confiar cegamente.

---

### 2.5 Unificação feriados (evitar divergência)

- Hoje existem **duas fontes**: `feriados_br.py` + tabela `feriados` no `database` (usado em testes e legado) e **cal_forense** (`calendar_v2.db`) usado no cálculo em produção.
- Os testes já foram ajustados para usar `cal_forense` (UF + comarca).
- **Falta (plano Fase 1):** Fazer `database.carregar_feriados` usar apenas `CalendarStore`/`CalendarResolver` (ou deprecar essa tabela) para não haver divergência entre “o que o teste usa” e “o que o bot usa”.

Isso não melhora a cobertura geográfica, mas **reduz risco de bug** (um caminho com feriado antigo, outro com o novo).

---

### 2.6 Validação e testes

- Testes multi-estado já passam para 13+ UFs.
- **Falta (recomendado):**
  - Incluir nos testes **pelo menos uma comarca** de cada UF incompleta (CE, MA, TO, PA, AL, PB, PI, RN, AM) e validar que:
    - o cálculo não quebra;
    - a confiança retornada é **medium** ou **low** quando a comarca não tiver municipais.
  - Opcional: um teste que verifica “para cada UF, existe ao menos uma comarca no banco” (para não regredir cobertura).

---

## 3. Checklist objetivo — “MVP seguro em prazos no território nacional”

Interpretação possível de “seguro”:

- [ ] **Cobertura mínima por UF:** Nenhuma UF com 0 comarcas no banco (hoje TO e PA têm 2 e 3; melhorar).
- [ ] **Alta prioridade atendida:** CE, MA, TO, PA com número razoável de comarcas e feriados municipais (ex.: CE ~100+, MA ~50+, TO e PA com capitais e principais comarcas).
- [ ] **Parciais fechadas:** MT, RO, RR completos ou quase (≥90% das comarcas oficiais).
- [ ] **Confiança:** Nenhum tribunal em uso com confiança **low**; TJRS em **high** se houver fonte.
- [ ] **Aviso ao usuário:** Quando a comarca for sem cobertura municipal (ou confiança medium/low), o bot exibe aviso explícito no cálculo e/ou no briefing.
- [ ] **Fonte única:** Cálculo e listagem de feriados usam só `cal_forense` (sem divergência com `feriados_br`/tabela `feriados`).
- [ ] **Testes:** Testes multi-estado incluindo UFs incompletas e verificação de confidence.

---

## 4. Priorização sugerida (para fechar o MVP “seguro”)

| Prioridade | O quê | Impacto | Esforço (ordem de grandeza) |
|------------|--------|---------|-----------------------------|
| **P0** | Aviso no bot quando comarca não coberta (confidence medium/low) | Usuário sabe quando conferir no tribunal | Baixo (1–2 h) |
| **P0** | TJGO confiança high (dados já no v2) | Remove “low” em uso | Baixo (~30 min) |
| **P1** | Completar CE (expandir para ~100+ comarcas) | Maior UF incompleta | Alto (pesquisa + loader) |
| **P1** | Completar TO e PA (capitais + principais) | Evita risco em 2 estados quase vazios | Médio |
| **P1** | Completar MA (principais comarcas) | MA com volume relevante | Médio–Alto |
| **P2** | AL, PB, PI, RN, AM (expandir) | Cobre Nordeste e Norte | Médio cada |
| **P2** | MT, RO, RR (fechar parciais) | Elimina “parcial” | Médio |
| **P2** | Unificação feriados (database + cal_forense) | Consistência e menos bugs | Médio (já em parte feito nos testes) |
| **P3** | TJRS high (se houver fonte oficial) | Confiança total em RS | Baixo se a fonte existir |
| **P3** | Testes para UFs incompletas + confidence | Garante que não regride | Baixo |

---

## 5. Resumo em uma frase

**Para o MVP ficar seguro quanto a prazos no território nacional falta:**  
(1) **dados** — completar comarcas/feriados municipais nas **8 UFs incompletas** (em especial CE, MA, TO, PA) e fechar as **3 parciais** (MT, RO, RR);  
(2) **transparência** — avisar o usuário quando a comarca **não tiver cobertura municipal** (confidence medium/low);  
(3) **confiança** — tirar TJGO de “low” e, se possível, TJRS para “high”;  
(4) **consistência** — usar uma única fonte de feriados (cal_forense) em todo o fluxo;  
(5) **testes** — incluir UFs incompletas e checagem de confidence nos testes automatizados.

Com isso, o sistema fica **seguro** no sentido de: regras CPC corretas em todo o país; onde houver dados, o cálculo é confiável; onde não houver, o usuário é avisado e pode conferir no tribunal.
