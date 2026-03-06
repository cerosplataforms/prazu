# Prazor — Roadmap GSD

**Projeto:** PrazorBot Brasil / Prazor  
**Versão:** 1.0  
**Data:** 2026-03-06  
**Alinhamento:** PROJECT_KNOWLEDGE.md, visão 3 anos

---

## Visão geral

Roadmap em 5 fases para evolução do PrazorBot até produto pronto para vendas. Cada fase tem objetivo, critérios de sucesso e entregas.

---

## Fase 1 — Fechar MVP Telegram (completar todas as comarcas)

**Objetivo:** Garantir cobertura nacional do calendário forense para que o bot funcione em qualquer tribunal/comarca do Brasil.

**Contexto atual (PROJECT_KNOWLEDGE §11):**
- 63 tribunais cadastrados
- 1.971 localidades
- 5.444 eventos
- Lacunas: TJPE, TJRJ e outros tribunais com cobertura parcial (TJGO Low, TJSC/TJMT/TJMS/TJRS Medium)

**Entregas:**
- [ ] Completar TJPE: feriados nacionais + recessos jan/dez 2026
- [ ] Completar TJRJ: feriados municipais NURCs 7 e 8
- [ ] Elevar TJGO para confiança High (completar feriados)
- [ ] Validar tribunais em Medium e subir para High onde possível
- [ ] Unificar sistema de feriados (feriados_br vs cal_forense — ver CONCERNS.md)
- [ ] Documentar lista de tribunais/comarcas com cobertura completa

**Critérios de sucesso:**
- Todas as 27 UFs + DF com cobertura High ou Medium documentada
- Nenhum tribunal com confiança Low em uso ativo
- Testes passando para múltiplos estados (SP, RJ, BA, RS, PE, CE, PR, SC, PA, GO, ES, DF, MG)

**Artefatos de referência:** `.planning/codebase/CONCERNS.md`, `cal_forense/calendar_loader.py`

---

## Fase 2 — Migrar SQLite para Supabase e deploy em servidor real

**Objetivo:** Sair do Mac local e rodar em infraestrutura escalável; banco gerenciado em nuvem.

**Contexto atual:**
- SQLite local (prazobot.db, calendar_v2.db)
- Deploy local (Mac), sem alta disponibilidade
- CONCERNS.md indica limite de concorrência do SQLite

**Entregas:**
- [ ] Criar projeto Supabase (PostgreSQL)
- [ ] Migrar schema de `database.py` para Supabase
- [ ] Migrar schema de `cal_forense` (tribunais, localidades, eventos) para Supabase
- [ ] Refatorar `database.py` para usar cliente Supabase/psycopg2
- [ ] Refatorar `cal_forense/calendar_store.py` para Supabase
- [ ] Configurar env vars: `SUPABASE_URL`, `SUPABASE_KEY`
- [ ] Script de migração de dados (se houver dados existentes)
- [ ] Deploy do bot em servidor (VPS, Railway, Render ou similar)
- [ ] Scheduler e jobs rodando no servidor (APScheduler ou cron do host)
- [ ] Logs e monitoramento básico

**Critérios de sucesso:**
- Bot rodando 24/7 em servidor
- Banco em Supabase com backups
- Comandos do bot funcionando normalmente
- Briefing automático e monitoramento DJEN operando

**Artefatos de referência:** `database.py`, `cal_forense/calendar_store.py`, CONCERNS.md (Scaling Limits)

---

## Fase 3 — Interface Web

**Objetivo:** Oferecer painel web para advogados acessarem processos, prazos e briefing sem depender só do Telegram.

**Entregas:**
- [ ] Escolher stack web (ex.: FastAPI + React, ou Next.js full-stack)
- [ ] Autenticação (login com Telegram ou email/senha)
- [ ] Dashboard: resumo de prazos, processos, status
- [ ] Visualização de briefing em formato web
- [ ] Listagem de processos e prazos
- [ ] Cálculo manual de prazo (equivalente a /calcular)
- [ ] Configurações de comarca e horário de briefing
- [ ] Integração com mesma base Supabase
- [ ] Deploy da aplicação web (Vercel, Netlify ou junto ao backend)

**Critérios de sucesso:**
- Advogado consegue usar o Prazor só pela web se quiser
- Dados sincronizados entre Telegram e Web
- UX mínima viável (não precisa ser perfeita)

**Artefatos de referência:** `bot.py` (comandos e fluxos), `ia.py` (briefing)

---

## Fase 4 — WhatsApp

**Objetivo:** Canal WhatsApp para atingir advogados que preferem WhatsApp a Telegram (maior penetração no Brasil).

**Entregas:**
- [ ] Avaliar integração: WhatsApp Business API (Meta) ou Twilio/outro gateway
- [ ] Conta WhatsApp Business API aprovada
- [ ] Adaptar handlers de comando para mensagens WhatsApp
- [ ] Fluxo de onboarding via WhatsApp (equivalente ao /start)
- [ ] Briefing diário via WhatsApp
- [ ] Comandos principais: buscar, meus_processos, briefing, calcular, config
- [ ] Sincronizar usuários entre Telegram e WhatsApp (mesmo advogado, múltiplos canais)
- [ ] Testes de carga e rate limits da API

**Critérios de sucesso:**
- Advogado cadastrado pode receber briefing e interagir via WhatsApp
- Mesma base de dados e lógica compartilhada com Telegram
- Custo de API dentro do orçamento

**Artefatos de referência:** `bot.py`, `scheduler.py`, PROJECT_KNOWLEDGE (Ano 1 — briefing matinal)

---

## Fase 5 — Preparar para vendas

**Objetivo:** Produto pronto para cobrança, onboarding de clientes pagantes e métricas de negócio.

**Entregas:**
- [ ] Definição de planos (ex.: free, pro, escritório)
- [ ] Integração de pagamento (Stripe, Mercado Pago ou similar)
- [ ] Checkout e gestão de assinaturas
- [ ] Limites por plano (ex.: X processos no free, ilimitado no pro)
- [ ] Portal do cliente: ver plano, faturamento, upgrade/downgrade
- [ ] Landpage de vendas com proposta de valor
- [ ] Fluxo de cadastro pago (cartão, boleto)
- [ ] Termos de uso e política de privacidade
- [ ] Métricas: MRR, churn, conversão free→pago
- [ ] Suporte básico (email/chat)

**Critérios de sucesso:**
- Cliente consegue assinar e pagar pelo Prazor
- Renovação automática funcionando
- Dados de vendas rastreáveis (MRR, conversão)

**Artefatos de referência:** PROJECT_KNOWLEDGE (Roadmap 3 anos, Moat, Meta Ano 1)

---

## Ordem de execução

```
Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5
  │         │         │         │         │
  ▼         ▼         ▼         ▼         ▼
MVP      Infra     Web      WhatsApp   Vendas
completo  real
```

Cada fase deve ser concluída (critérios de sucesso atendidos) antes de iniciar a próxima. Dentro de cada fase, usar `/gsd:plan-phase` para detalhar tarefas e `/gsd:execute-plan` para execução.

---

## Dependências entre fases

| De → Para | Dependência |
|-----------|-------------|
| Fase 1 → 2 | Calendário completo garante que migração não perca cobertura |
| Fase 2 → 3 | Web precisa do banco Supabase para escalar |
| Fase 2 → 4 | WhatsApp usa a mesma infra e banco |
| Fase 3,4 → 5 | Canais funcionando antes de cobrar |

---

*Roadmap GSD v1.0 — Prazor*
