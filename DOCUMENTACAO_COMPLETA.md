# Prazu — Documentação Completa

**Atualizado:** março 2026

> **Nota:** O Prazu é hoje um app web com WhatsApp. Para setup e deploy, veja [SETUP.md](SETUP.md) e [README.md](README.md). A documentação abaixo descreve o produto atual.

---

## 1. O que é o Prazu?

O **Prazu** é um SaaS para advogados brasileiros que:

- **Monitora prazos processuais** — Busca publicações no DJEN pela OAB e calcula vencimentos com feriados forenses por comarca (CPC arts. 216, 219, 220, 224)
- **Envia alertas no WhatsApp** — Boas-vindas, resumo inicial após cadastro e briefing diário no horário escolhido
- **Oferece dashboard web** — Processos, prazos urgentes, vencidos, links PJe
- **Permite recuperação de senha** — Código por e-mail (Resend)

**Site:** prazu.com.br  
**Suporte:** wa.me/5511916990578  
**Cobertura:** 63 tribunais, 2.000+ localidades, ~6.000 eventos 2026 — ver `.planning/COBERTURA_CALENDARIO.md`

---

## 2. Fluxo do usuário

1. **Cadastro** — Nome, e-mail, senha (8+ chars, letra + número)
2. **Onboarding** — OAB/UF, verificação WhatsApp (código 6 dígitos), horário do briefing, dias da semana
3. **Importação** — Sistema busca DJEN (30 dias), DataJud para cada processo, calcula prazos
4. **Dashboard** — Lista de processos com cores (verde/amarelo/vermelho), expandível para vencidos
5. **Configurações** — Nome, horário briefing, lembrete fim de semana
6. **WhatsApp** — Briefing diário + comandos `prazos` e `buscar`

---

## 3. Comandos do bot WhatsApp

| Mensagem | Resposta |
|----------|----------|
| `prazos`, `resumo`, `briefing`, `oi`, `olá`, `bom dia`, etc. | Resumo dos prazos (urgentes, 7 dias, em aberto) |
| `buscar`, `atualizar`, `djen` | Busca novas publicações no DJEN |
| Qualquer outra | Resposta padrão: comandos disponíveis + link prazu.com.br + número de suporte |

---

## 4. Testes

```bash
python test_prazobot.py
```

129 testes em `prazos_calc.py` e banco. Cobertura: feriados, recesso, dias úteis, casos CPC, múltiplos estados.

---

## 5. Documentos relacionados

- [README.md](README.md) — Visão geral e stack
- [SETUP.md](SETUP.md) — Desenvolvimento e deploy
- [.planning/PROJECT_KNOWLEDGE.md](.planning/PROJECT_KNOWLEDGE.md) — Knowledge base
- [.planning/codebase/STACK.md](.planning/codebase/STACK.md) — Stack técnico
- [.planning/codebase/ARCHITECTURE.md](.planning/codebase/ARCHITECTURE.md) — Arquitetura
