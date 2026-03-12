# Prazu — Lacunas de Segurança e Prevenção de Ataques

**Auditado em:** março 2026

---

## O que já existe

| Item | Status |
|------|--------|
| SQL parametrizado (asyncpg $1, $2) | ✅ Sem injeção SQL |
| JWT em cookie HttpOnly + Secure (prod) | ✅ Cookie protegido |
| SameSite=Lax | ✅ Mitiga CSRF parcial |
| Webhook Z-API: validação opcional (ZAPI_WEBHOOK_SECRET) | ⚠️ Só se configurado |
| Jobs: validação SCHEDULER_SECRET em prod | ⚠️ Só se configurado |
| /api/docs desabilitado em produção | ✅ |
| Senhas com bcrypt | ✅ |
| Recuperação de senha: não revela se email existe | ✅ |

---

## Lacunas por prioridade

### 🔴 CRÍTICO

#### 1. Sem rate limiting
- **Risco:** Brute force em login, cadastro em massa, spam de recuperação de senha, DoS no webhook
- **Endpoints afetados:** `/api/auth/login`, `/api/auth/cadastro`, `/api/auth/recuperar-senha/*`, `/webhook/zapi`
- **Solução:** Middleware de rate limit (ex.: `slowapi`, ou Redis para IP + rota)
- **Exemplo:** Máx 5 tentativas de login por IP/minuto; 3 recuperações de senha/hora

#### 2. Webhook Z-API sem proteção obrigatória
- **Risco:** Se `ZAPI_WEBHOOK_SECRET` não estiver definido, qualquer um pode POST em `/webhook/zapi` e disparar fluxos (onboarding, resumos, IA)
- **Solução:** Tornar `ZAPI_WEBHOOK_SECRET` obrigatório em produção; rejeitar 401 se ausente

#### 3. Jobs sem proteção quando SCHEDULER_SECRET vazio
- **Risco:** Qualquer um pode chamar `/jobs/briefing`, `/jobs/djen` etc. e executar tarefas em massa
- **Solução:** Exigir `SCHEDULER_SECRET` em produção; retornar 403 se header incorreto ou variável vazia

---

### 🟠 ALTO

#### 4. XSS no dashboard
- **Risco:** Dados de processos (partes, número, comarca) vêm do banco e são injetados via `innerHTML` em template literals. Se houver HTML/script malicioso (ex.: via DJEN/DataJud ou cadastro manual futuro), pode executar
- **Arquivos:** `dashboard.html` (linhas 319, 367, 420)
- **Solução:** Escapar HTML antes de inserir (ex.: `textContent` em vez de `innerHTML`, ou função `escapeHtml(str)`)

#### 5. Falta de headers de segurança
- **Risco:** Clickjacking, MIME sniffing, XSS amplificado
- **Headers ausentes:**
  - `X-Frame-Options: DENY` ou `SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy` (politica restritiva)
- **Solução:** Middleware que adicione esses headers em todas as respostas

#### 6. Validação fraca em várias APIs
- **Endpoints:** `salvar_configuracoes`, `alterar_senha`, `recuperar_senha_redefinir`, payloads de onboarding
- **Risco:** Nome com 10.000 caracteres, horário inválido, tipos incorretos
- **Solução:** Usar Pydantic para todos os payloads; limites de tamanho; whitelist para `horario_briefing`

#### 7. Inconsistência de política de senha
- **Alterar senha:** mínimo 6 caracteres
- **Cadastro / recuperação:** mínimo 8 + letra + número
- **Solução:** Unificar em 8 caracteres, letra e número, em todos os fluxos

---

### 🟡 MÉDIO

#### 8. CORS não configurado explicitamente
- **Risco:** FastAPI usa padrão; em produção é melhor restringir origins
- **Solução:** `add_middleware(CORSMiddleware, allow_origins=["https://prazu.com.br"], allow_credentials=True)`

#### 9. Códigos de verificação em memória
- **Risco:** `_reset_codigos`, `_email_codigos`, `_wpp_codigos` — perdidos em restart; não funcionam com múltiplas instâncias
- **Solução:** Redis ou tabela no banco com TTL

#### 10. Logs com dados sensíveis
- **Risco:** `log.info(f"WhatsApp de {phone}: {texto[:50]}")` — pode logar conteúdo sensível
- **Solução:** Mascarar phone (ex.: `55*******99`); evitar logar corpo de mensagens em produção

#### 11. Timeout em chamadas externas
- **Risco:** DJEN, DataJud, Gemini, Resend, Z-API — sem timeout explícito em alguns pontos; pode travar worker
- **Solução:** Timeout em todas as chamadas HTTP (ex.: 30s)

---

### 🟢 BAIXO

#### 12. Sem HSTS
- **Solução:** Header `Strict-Transport-Security: max-age=31536000` (Cloud Run já serve HTTPS)

#### 13. DataJud API key
- **Status:** Pode estar em env; se hardcoded, mover para variável de ambiente

---

## Estrutura recomendada (checklist)

```
Segurança Prazu
├── [ ] Rate limiting (slowapi ou similar)
├── [ ] Headers de segurança (middleware)
├── [ ] CORS explícito
├── [ ] Webhook secret obrigatório em prod
├── [ ] Scheduler secret obrigatório em prod
├── [ ] Escape XSS no dashboard
├── [ ] Pydantic em todos os payloads
├── [ ] Política de senha unificada
├── [ ] Códigos de verificação em Redis/DB
├── [ ] Logs sem dados sensíveis
└── [ ] Timeouts em todas as integrações
```

---

## Ordem sugerida de implementação

1. **Webhook + Scheduler** — Exigir secrets em prod (rápido, alto impacto)
2. **Headers de segurança** — Middleware (rápido)
3. **Rate limiting** — Login e recuperação de senha primeiro
4. **XSS** — Escape no dashboard
5. **Validação** — Pydantic e limites
6. **Senha** — Unificar para 8 chars
