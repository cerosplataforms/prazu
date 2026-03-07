# Prazor — Guia de Orquestração

O usuário quer **orquestrar o projeto** dando comandos de alto nível. Quando pedir para "fazer algo", interprete e execute conforme este guia.

---

## Comandos de orquestração

| O usuário diz... | O que fazer |
|------------------|-------------|
| **"Executa a fase 1"** / **"Faz a fase 1"** / **"Roda o plano da fase 1"** | Usar `mcp_task` com `gsd-executor` e o plano `.planning/phases/phase-1-mvp-telegram.md`. Ou executar as tarefas diretamente se o executor não estiver disponível. |
| **"Planeja a fase 2"** / **"Detalha a fase 2"** | Usar `mcp_task` com `gsd-planner` para criar `.planning/phases/phase-2-supabase-deploy.md` com base no ROADMAP. |
| **"Planeja a fase X"** (X = 3, 4 ou 5) | Mesmo: `gsd-planner` para a fase correspondente (Interface Web, WhatsApp, Preparar vendas). |
| **"Executa o plano"** / **"Roda o plano"** | Entender qual fase está ativa (perguntar se ambíguo). Geralmente Fase 1. Executar o plano da fase. |
| **"Verifica a fase 1"** / **"A fase 1 está pronta?"** | Usar `mcp_task` com `gsd-verifier` ou analisar goal-backward se os critérios de sucesso foram atingidos. |
| **"Status"** / **"Onde estamos?"** / **"Resumo do projeto"** | Ler ROADMAP, fase atual, checklist das entregas. Dar resumo conciso. |
| **"Migra pro Supabase"** / **"Deploy em servidor"** | Planejar (se não houver plano) e/ou executar Fase 2. |
| **"Interface web"** / **"Painel web"** | Planejar e/ou executar Fase 3. |
| **"WhatsApp"** / **"Adiciona WhatsApp"** | Planejar e/ou executar Fase 4. |
| **"Prepara pra vender"** / **"Pagamentos"** | Planejar e/ou executar Fase 5. |
| **"Debug"** / **"Tem um bug"** | Usar `mcp_task` com `gsd-debugger` se for bug complexo. Ou investigar diretamente. |
| **"Atualiza o mapeamento"** / **"Mapeia o codebase"** | Usar `mcp_task` com `gsd-codebase-mapper`. |
| **"Testes"** / **"Cobertura de testes"** | Usar `mcp_task` com `gsd-nyquist-auditor` ou rodar `python test_prazobot.py` e analisar. |

---

## Estrutura do planejamento

```
.planning/
├── PROJECT_KNOWLEDGE.md    # Visão, arquitetura, convenções
├── ROADMAP.md              # 5 fases do projeto
├── codebase/               # Mapeamento (STACK, ARCHITECTURE, CONCERNS...)
└── phases/
    ├── phase-1-mvp-telegram.md   # Plano detalhado Fase 1
    ├── phase-2-supabase-deploy.md # (a criar)
    └── ...
```

---

## Ordem das fases (ROADMAP)

1. **Fase 1** — Fechar MVP Telegram (completar comarcas)
2. **Fase 2** — Migrar SQLite → Supabase + deploy servidor
3. **Fase 3** — Interface Web
4. **Fase 4** — WhatsApp
5. **Fase 5** — Preparar para vendas

---

## Comportamento esperado

- **Proativo:** Ao receber comando vago ("faz aí"), inferir a fase/tarefa mais provável e confirmar ou executar.
- **Contexto:** Sempre consultar `.planning/` antes de executar. ROADMAP e planos de fase são fonte da verdade.
- **Commits:** Ao executar planos, preferir commits atômicos por tarefa concluída.
- **Resposta em português.**
