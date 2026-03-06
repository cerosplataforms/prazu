# Codebase Concerns

**Analysis Date:** 2026-03-06

## Tech Debt

**Sistema duplo de feriados (feriados_br vs cal_forense):**
- Issue: Dois sistemas coexistindo: `feriados_br.py` + `database.feriados` e `cal_forense.CalendarStore` + `CalendarResolver`. `prazos_calc` usa `cal_forense`; `test_prazobot` e `database` usam carga via `feriados_br`.
- Files: `feriados_br.py`, `feriados_mg.py`, `database.py`, `cal_forense/`, `prazos_calc.py`, `test_prazobot.py`
- Impact: Risco de divergência de feriados entre módulos; manutenção duplicada
- Fix approach: Unificar em `cal_forense` e migrar `database.feriados` para uso do CalendarStore ou abandonar tabela `feriados` em `database` se obsoleta

**Testes desatualizados em relação a prazos_calc:**
- Issue: `test_prazobot.py` importa `_em_recesso` de `prazos_calc`, mas `_em_recesso` está em `CalendarResolver` (método privado). Também passa `feriados_test` (set) para `_eh_dia_util` e funções de cálculo, enquanto `prazos_calc` espera `(d, uf, comarca_processo)`.
- Files: `test_prazobot.py`, `prazos_calc.py`, `cal_forense/calendar_resolver.py`
- Impact: Testes podem falhar em import ou por assinatura incorreta
- Fix approach: Atualizar `test_prazobot.py` para usar `(uf, comarca)` em vez de set de feriados; extrair `_em_recesso` para função de módulo ou importar de `calendar_resolver` se necessário

**Parâmetro deprecated em prazos_calc:**
- Issue: `feriados=None` mantido em várias funções "para retrocompat"; ignorado internamente
- Files: `prazos_calc.py`
- Impact: Confusão e chamadas legadas possivelmente incorretas
- Fix approach: Remover parâmetro após migrar testes e callers; ou documentar como deprecated e emitir warning

## Security Considerations

**API key DataJud hardcoded:**
- Risk: Chave pública do CNJ em `datajud.py` (linha 25). Se a chave expirar ou for revogada, quebra consultas.
- Files: `datajud.py`
- Current mitigation: Chave pública oficial do CNJ
- Recommendations: Mover para env var (ex.: `DATAJUD_API_KEY`) para facilitar atualização sem alterar código

**Secrets em .env:**
- Risk: `.env` não versionado; tokens Telegram e Groq em arquivo local
- Files: `.env`
- Current mitigation: `.gitignore` exclui `.env`
- Recommendations: Usar variáveis de ambiente no host; nunca commitar `.env`

## Performance Bottlenecks

**Consulta DataJud por processo:**
- Problem: `atualizar_todos_processos` consulta o DataJud um a um para cada processo ativo
- Files: `datajud.py`, `atualizar.py`
- Cause: Sem batch; N requisições HTTP para N processos
- Improvement path: Verificar se DataJud suporta batch; adicionar rate limiting/throttling; executar em horário de baixo tráfego

**CalendarResolver cache sem TTL:**
- Problem: `_cache` em memória por (ano, uf, comarca) nunca expira
- Files: `cal_forense/calendar_resolver.py`
- Cause: Uso em long-running process (bot) pode acumular entradas
- Improvement path: LRU ou limite de tamanho; em prática pode ser aceitável para poucos anos/estados

## Fragile Areas

**Parsing de comarca/vara:**
- Files: `bot.py` — `extrair_comarca_da_vara`, `_resolver_comarca_processo`
- Why fragile: Regex e heurísticas para extrair comarca de texto livre; formatos variam por tribunal
- Safe modification: Adicionar testes com exemplos reais; fallback para comarca vazia
- Test coverage: Sem testes automatizados específicos

**Estrutura de resposta das APIs DJEN e DataJud:**
- Files: `djen.py`, `datajud.py`
- Why fragile: APIs externas podem mudar schema; parsing assume campos específicos
- Safe modification: Validar campos antes de usar; logging de estruturas inesperadas
- Test coverage: Sem mocks; testes não cobrem integração com APIs reais

## Scaling Limits

**SQLite:**
- Current capacity: Adequado para uso single-user/single-process
- Limit: Concorrência de escrita; um writer por vez
- Scaling path: Migrar para PostgreSQL se houver múltiplos workers ou alto volume

**Cron para scheduler:**
- Current capacity: Execução por hora (ou intervalo fixo)
- Limit: Não escala horizontalmente; um processo por execução
- Scaling path: Manter para MVP; considerar fila (Celery, etc.) se necessário

## Dependencies at Risk

**python-telegram-bot:**
- Risk: Breaking changes entre versões (v20→v21)
- Impact: Handlers e estrutura do Application podem mudar
- Migration plan: Fixar versão em requirements.txt; acompanhar changelog

**Groq API:**
- Risk: Rate limits, mudança de modelo ou de preço
- Impact: Briefings e perguntas falham ou ficam mais caros
- Migration plan: Fallback de mensagem quando API falha (já existe em `ia.py`); considerar outro provedor como backup

## Missing Critical Features

**Sem CI/CD:**
- Problem: Sem pipeline de testes, lint ou deploy
- Blocks: Garantia de qualidade em commits; deploy automatizado

**Sem versionamento de banco:**
- Problem: Migrations manuais; schema em `db.init()` sem histórico
- Blocks: Evolução segura do schema em produção

## Test Coverage Gaps

**Bot (bot.py):**
- What's not tested: Handlers, callbacks, fluxo de onboarding
- Files: `bot.py`
- Risk: Regressões em UX e fluxos principais
- Priority: Medium

**Integrações DJEN e DataJud:**
- What's not tested: Parsing de respostas, tratamento de erros HTTP
- Files: `djen.py`, `datajud.py`
- Risk: Falhas silenciosas ou exceções não tratadas
- Priority: High (dados críticos para prazos)

**IA (ia.py):**
- What's not tested: Formatação de contexto, fallback em erro
- Files: `ia.py`
- Risk: Briefing mal formatado ou vazio
- Priority: Medium

---

*Concerns audit: 2026-03-06*
