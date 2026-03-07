#!/usr/bin/env python3
"""
setup_web.py — Prazu Fase 2
Roda na raiz do projeto e cria todos os arquivos Python da pasta web/.

Uso:
  cd ~/prazu
  python3 setup_web.py
"""

import os

files = {}

# ─────────────────────────────────────────────
# web/__init__.py
# ─────────────────────────────────────────────
files["web/__init__.py"] = ""

# ─────────────────────────────────────────────
# web/auth.py
# ─────────────────────────────────────────────
files["web/auth.py"] = '''"""
web/auth.py — Prazu Fase 2
JWT para autenticação do site.
Token armazenado em cookie httpOnly.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Request

import database_gcp as db

log = logging.getLogger(__name__)

JWT_SECRET   = os.getenv("JWT_SECRET", "dev-secret-troca-em-producao")
JWT_ALGO     = "HS256"
JWT_TTL_DIAS = 30
TOKEN_COOKIE = "prazu_token"


async def criar_token_acesso(advogado: dict, request: Request) -> str:
    """Cria JWT + registra sessão no banco."""
    expira = datetime.now(timezone.utc) + timedelta(days=JWT_TTL_DIAS)
    payload = {
        "sub": str(advogado["id"]),
        "email": advogado.get("email", ""),
        "exp": expira,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    await db.criar_session(
        advogado_id=advogado["id"],
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else "",
        ttl_dias=JWT_TTL_DIAS,
    )
    return token


async def verificar_token(token: str) -> Optional[dict]:
    """Valida JWT e retorna o advogado, ou None se inválido."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        advogado_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None
    adv = await db.buscar_por_id(advogado_id)
    if not adv or not adv["ativo"]:
        return None
    return adv
'''

# ─────────────────────────────────────────────
# web/zapi.py
# ─────────────────────────────────────────────
files["web/zapi.py"] = '''"""
web/zapi.py — Prazu Fase 2
Cliente Z-API para envio de mensagens WhatsApp.
"""

import os
import logging
import httpx

log = logging.getLogger(__name__)


class ZAPI:
    def __init__(self, instance_id: str, token: str):
        self.instance_id = instance_id
        self.token = token
        self.base_url = f"https://api.z-api.io/instances/{instance_id}/token/{token}"

    async def enviar(self, phone: str, texto: str) -> bool:
        if not self.instance_id or not self.token:
            log.warning(f"Z-API não configurado. Msg para {phone}: {texto[:50]}")
            return False
        url = f"{self.base_url}/send-text"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json={"phone": phone, "message": texto})
                resp.raise_for_status()
                log.info(f"Z-API enviado para {phone} ✅")
                return True
        except httpx.HTTPStatusError as e:
            log.error(f"Z-API HTTP {e.response.status_code} para {phone}: {e.response.text[:100]}")
            return False
        except Exception as e:
            log.error(f"Z-API erro para {phone}: {e}")
            return False

    async def enviar_lista(self, phones: list, texto: str) -> int:
        import asyncio
        resultados = await asyncio.gather(
            *[self.enviar(p, texto) for p in phones], return_exceptions=True
        )
        return sum(1 for r in resultados if r is True)
'''

# ─────────────────────────────────────────────
# web/app.py
# ─────────────────────────────────────────────
files["web/app.py"] = '''"""
web/app.py — Prazu Fase 2
Servidor FastAPI principal. Roda no Cloud Run.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

import database_gcp as db
from web.auth import criar_token_acesso, verificar_token, TOKEN_COOKIE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger(__name__)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"Prazu iniciando — {ENVIRONMENT}")
    await db.init_db()
    log.info(f"Banco OK — {await db.diagnostico()}")
    yield
    await db.close_db()


app = FastAPI(title="Prazu", version="2.0.0", lifespan=lifespan,
              docs_url="/api/docs" if ENVIRONMENT != "production" else None, redoc_url=None)

templates = Jinja2Templates(directory="web/templates")
if os.path.exists("web/static"):
    app.mount("/static", StaticFiles(directory="web/static"), name="static")


# — Auth dependencies —

async def advogado_logado(request: Request):
    token = request.cookies.get(TOKEN_COOKIE)
    if not token:
        raise HTTPException(307, headers={"Location": "/login"})
    adv = await verificar_token(token)
    if not adv:
        raise HTTPException(307, headers={"Location": "/login"})
    return adv

async def advogado_logado_opcional(request: Request):
    token = request.cookies.get(TOKEN_COOKIE)
    if not token: return None
    return await verificar_token(token)


# — Páginas —

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request, adv=Depends(advogado_logado_opcional)):
    if adv: return RedirectResponse("/dashboard")
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/cadastro", response_class=HTMLResponse)
async def pagina_cadastro(request: Request, adv=Depends(advogado_logado_opcional)):
    if adv: return RedirectResponse("/dashboard")
    return templates.TemplateResponse("cadastro.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def pagina_login(request: Request, adv=Depends(advogado_logado_opcional)):
    if adv: return RedirectResponse("/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, adv=Depends(advogado_logado)):
    if not await db.pode_usar(adv["id"]): return RedirectResponse("/plano-expirado")
    processos = await db.listar_processos_com_prazos(adv["id"])
    trial_dias = None
    if adv["status"] == "trial" and adv.get("trial_fim"):
        from datetime import datetime, timezone
        trial_fim = adv["trial_fim"]
        if hasattr(trial_fim, "tzinfo") and trial_fim.tzinfo is None:
            trial_fim = trial_fim.replace(tzinfo=timezone.utc)
        trial_dias = max(0, (trial_fim - datetime.now(timezone.utc)).days)
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "advogado": adv,
        "processos": processos, "trial_dias": trial_dias,
    })

@app.get("/plano-expirado", response_class=HTMLResponse)
async def plano_expirado(request: Request):
    return templates.TemplateResponse("plano_expirado.html", {"request": request})

@app.get("/logout")
async def logout():
    r = RedirectResponse("/login")
    r.delete_cookie(TOKEN_COOKIE)
    return r


# — API Auth —

class CadastroRequest(BaseModel):
    nome: str; email: EmailStr; senha: str
    oab_numero: str; oab_seccional: str; whatsapp: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr; senha: str

@app.post("/api/auth/cadastro")
async def cadastro(payload: CadastroRequest, request: Request):
    if len(payload.oab_seccional) != 2:
        raise HTTPException(400, "Seccional OAB inválida.")
    if len(payload.senha) < 6:
        raise HTTPException(400, "Senha deve ter pelo menos 6 caracteres.")
    whatsapp = None
    if payload.whatsapp:
        whatsapp = "".join(filter(str.isdigit, payload.whatsapp))
        if len(whatsapp) < 10: whatsapp = None
    advogado_id = await db.criar_advogado(
        nome=payload.nome, email=payload.email, senha=payload.senha,
        oab_numero=payload.oab_numero, oab_seccional=payload.oab_seccional.upper(),
        whatsapp=whatsapp,
    )
    if not advogado_id:
        raise HTTPException(409, "Email ou OAB já cadastrado")
    adv = await db.buscar_por_id(advogado_id)
    token = await criar_token_acesso(adv, request)
    response = JSONResponse({"ok": True, "redirect": "/dashboard"})
    response.set_cookie(TOKEN_COOKIE, token, httponly=True,
                        secure=ENVIRONMENT == "production", samesite="lax",
                        max_age=30 * 24 * 3600)
    log.info(f"Novo cadastro: {payload.email} OAB {payload.oab_numero}/{payload.oab_seccional}")
    return response

@app.post("/api/auth/login")
async def login(payload: LoginRequest, request: Request):
    adv = await db.buscar_por_email(payload.email)
    if not adv or not db.verificar_senha(payload.senha, adv.get("senha_hash", "")):
        raise HTTPException(401, "Email ou senha incorretos")
    if not adv["ativo"]:
        raise HTTPException(403, "Conta desativada")
    await db.atualizar_last_seen(adv["id"])
    token = await criar_token_acesso(adv, request)
    response = JSONResponse({"ok": True, "redirect": "/dashboard"})
    response.set_cookie(TOKEN_COOKIE, token, httponly=True,
                        secure=ENVIRONMENT == "production", samesite="lax",
                        max_age=30 * 24 * 3600)
    log.info(f"Login: {payload.email}")
    return response


# — API Advogado —

@app.get("/api/advogado/me")
async def me(adv=Depends(advogado_logado)):
    return {"id": adv["id"], "nome": adv["nome"], "email": adv["email"],
            "oab": f"{adv[\'oab_numero\']}/{adv[\'oab_seccional\']}",
            "comarca": adv["comarca"], "whatsapp": adv["whatsapp"],
            "zapi_confirmado": adv["zapi_confirmado"], "status": adv["status"],
            "trial_fim": str(adv["trial_fim"]) if adv.get("trial_fim") else None}

@app.get("/api/advogado/processos")
async def meus_processos(adv=Depends(advogado_logado)):
    return {"processos": await db.listar_processos_com_prazos(adv["id"])}

@app.post("/api/advogado/comarca")
async def atualizar_comarca(payload: dict, adv=Depends(advogado_logado)):
    comarca = payload.get("comarca", "").strip()
    if not comarca: raise HTTPException(400, "Comarca inválida")
    await db.atualizar_comarca(adv["id"], comarca)
    return {"ok": True}


# — Webhook Z-API —

@app.post("/webhook/zapi")
async def webhook_zapi(request: Request):
    zapi_token = os.getenv("ZAPI_TOKEN", "")
    if zapi_token and request.headers.get("x-zapi-token", "") != zapi_token:
        raise HTTPException(401, "Token inválido")
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Payload inválido")
    from web.onboarding import processar_mensagem_zapi
    await processar_mensagem_zapi(payload)
    return {"ok": True}


# — Jobs Cloud Scheduler —

SCHEDULER_SECRET = os.getenv("SCHEDULER_SECRET", "")

def validar_scheduler(request: Request):
    if ENVIRONMENT == "production":
        if SCHEDULER_SECRET and request.headers.get("x-scheduler-secret", "") != SCHEDULER_SECRET:
            raise HTTPException(403, "Acesso negado")

@app.post("/jobs/briefing")
async def job_briefing(request: Request):
    validar_scheduler(request)
    from web.onboarding import enviar_briefing_todos
    enviados = await enviar_briefing_todos()
    log.info(f"job_briefing: {enviados} enviados")
    return {"ok": True, "enviados": enviados}

@app.post("/jobs/expirar-trials")
async def job_expirar_trials(request: Request):
    validar_scheduler(request)
    expirados = await db.expirar_trials_vencidos()
    return {"ok": True, "expirados": expirados}

@app.post("/jobs/djen")
async def job_djen(request: Request):
    validar_scheduler(request)
    from web.onboarding import monitorar_djen_todos
    return {"ok": True, "notificados": await monitorar_djen_todos()}

@app.post("/jobs/lembrete-trial")
async def job_lembrete_trial(request: Request):
    validar_scheduler(request)
    from web.onboarding import enviar_lembrete_trial
    return {"ok": True, "enviados": await enviar_lembrete_trial()}

@app.get("/health")
async def health():
    try:
        return {"status": "ok", "db": await db.diagnostico()}
    except Exception as e:
        log.error(f"Health check falhou: {e}")
        raise HTTPException(503, "Banco indisponível")
'''

# ─────────────────────────────────────────────
# web/onboarding.py  (versão compacta mas completa)
# ─────────────────────────────────────────────
files["web/onboarding.py"] = '''"""
web/onboarding.py — Prazu Fase 2
Lógica do bot WhatsApp (Z-API) e jobs do Cloud Scheduler.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone

import database_gcp as db
from web.zapi import ZAPI

log = logging.getLogger(__name__)
zapi = ZAPI(instance_id=os.getenv("ZAPI_INSTANCE", ""), token=os.getenv("ZAPI_TOKEN", ""))

_estados: dict = {}

def _get(phone): return _estados.get(phone, {})
def _set(phone, step, dados=None): _estados[phone] = {"step": step, "dados": dados or {}}
def _clear(phone): _estados.pop(phone, None)


async def processar_mensagem_zapi(payload: dict):
    if payload.get("type") != "ReceivedCallback": return
    phone = payload.get("phone", "").replace("+", "").replace("-", "").replace(" ", "")
    msg = payload.get("message", {})
    texto = (msg.get("text") or msg.get("body") or msg.get("caption") or "").strip()
    if not phone or not texto: return
    log.info(f"WhatsApp de {phone}: {texto[:50]}")
    adv = await db.buscar_por_whatsapp(phone)
    await db.log_whatsapp(adv["id"] if adv else None, "inbound", "mensagem", texto)
    estado = _get(phone)
    step = estado.get("step")
    if step and step.startswith("onboarding_"):
        await _handle_onboarding(phone, texto, step, estado.get("dados", {}))
    elif adv:
        await _handle_conversa(phone, adv, texto)
    else:
        await _iniciar_onboarding(phone)


async def _iniciar_onboarding(phone: str):
    await zapi.enviar(phone,
        "👋 Olá! Eu sou o *Prazu*, seu copiloto jurídico.\\n\\n"
        "Monitoro seus prazos processuais e te aviso todo dia via WhatsApp — "
        "com feriados forenses de *2.374 comarcas* em todo o Brasil.\\n\\n"
        "Vamos começar? Me diga seu *nome completo*."
    )
    _set(phone, "onboarding_nome")


async def _handle_onboarding(phone, texto, step, dados):
    if step == "onboarding_nome":
        dados["nome"] = texto
        await zapi.enviar(phone, f"Prazer, Dr(a). *{texto}*! ✨\\n\\nMe informe sua *OAB* com estado.\\nEx: `12345/MG`")
        _set(phone, "onboarding_oab", dados)

    elif step == "onboarding_oab":
        if "/" not in texto:
            await zapi.enviar(phone, "Use o formato `numero/UF` — ex: `12345/MG`"); return
        num, uf = texto.split("/", 1)
        num = num.strip(); uf = uf.strip().upper().rstrip(".,;:!?")
        if len(uf) != 2:
            await zapi.enviar(phone, "Seccional inválida. Use a sigla do estado (MG, SP, RJ...)"); return
        existente = await db.buscar_por_oab(num, uf)
        if existente:
            await db.atualizar_whatsapp(existente["id"], phone, confirmado=True)
            _clear(phone)
            await zapi.enviar(phone, f"✅ OAB *{num}/{uf}* encontrada!\\nOlá de volta, Dr(a). *{existente[\'nome\']}*!\\nDigite *prazos* para ver seu resumo de hoje.")
            return
        dados.update({"oab_numero": num, "oab_seccional": uf})
        await zapi.enviar(phone, f"OAB *{num}/{uf}* anotado! ✅\\n\\nAgora preciso de um *e-mail* para criar sua conta.")
        _set(phone, "onboarding_email", dados)

    elif step == "onboarding_email":
        if "@" not in texto or "." not in texto:
            await zapi.enviar(phone, "E-mail inválido. Digite um e-mail válido."); return
        dados["email"] = texto.lower().strip()
        await zapi.enviar(phone, "Ótimo! Crie uma *senha* para sua conta Prazu.\\n(mínimo 6 caracteres)")
        _set(phone, "onboarding_senha", dados)

    elif step == "onboarding_senha":
        if len(texto) < 6:
            await zapi.enviar(phone, "Senha muito curta. Use pelo menos 6 caracteres."); return
        dados["senha"] = texto
        adv_id = await db.criar_advogado(
            nome=dados["nome"], email=dados["email"], senha=dados["senha"],
            oab_numero=dados["oab_numero"], oab_seccional=dados["oab_seccional"], whatsapp=phone,
        )
        if not adv_id:
            await zapi.enviar(phone, "❌ Esse e-mail já está cadastrado.\\nDigite outro e-mail.")
            _set(phone, "onboarding_email", dados); return
        await db.confirmar_whatsapp(adv_id)
        _clear(phone)
        await zapi.enviar(phone,
            f"🎉 Conta criada, Dr(a). *{dados[\'nome\']}*!\\n\\n"
            "✅ *7 dias grátis* — sem cartão de crédito\\n\\n"
            "Buscando seus processos no DJEN... ⏳"
        )
        asyncio.create_task(_buscar_djen(adv_id, phone, dados["oab_numero"], dados["oab_seccional"]))


async def _buscar_djen(adv_id, phone, oab_num, oab_uf):
    try:
        loop = asyncio.get_event_loop()
        from djen import consultar_djen_por_oab
        comunicacoes = await loop.run_in_executor(None, consultar_djen_por_oab, oab_num, oab_uf, 30)
        if not comunicacoes:
            await zapi.enviar(phone, "Nenhuma publicação encontrada nos últimos 30 dias.\\nDigite *buscar* quando quiser tentar novamente.")
            return
        await zapi.enviar(phone,
            f"📬 Encontrei *{len(comunicacoes)} publicação(ões)* no DJEN!\\n\\n"
            "Acesse *prazu.com.br/dashboard* para ver os prazos calculados.\\n"
            "Amanhã às *7h* você recebe seu primeiro aviso diário. ☀️"
        )
        await db.atualizar_ultima_busca_djen(adv_id)
    except Exception as e:
        log.error(f"Erro DJEN onboarding {phone}: {e}")
        await zapi.enviar(phone, "Não consegui buscar o DJEN agora. Digite *buscar* para tentar novamente.")


async def _handle_conversa(phone, adv, texto):
    tl = texto.lower().strip()
    if not await db.pode_usar(adv["id"]):
        await zapi.enviar(phone, "⚠️ Seu período de teste encerrou.\\nAcesse *prazu.com.br* para assinar."); return
    if tl in ("prazos", "resumo", "briefing", "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"):
        await _enviar_resumo(phone, adv)
    elif tl in ("buscar", "atualizar", "djen"):
        await zapi.enviar(phone, "🔍 Buscando publicações no DJEN...")
        asyncio.create_task(_buscar_djen(adv["id"], phone, adv["oab_numero"], adv["oab_seccional"]))
    elif tl.startswith("comarca "):
        nova = texto[8:].strip()
        await db.atualizar_comarca(adv["id"], nova)
        await zapi.enviar(phone, f"✅ Comarca atualizada para *{nova}*")
    else:
        await zapi.enviar(phone, "🤔 Processando...")
        try:
            processos = await db.listar_processos_com_prazos(adv["id"])
            from ia import responder_pergunta
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, responder_pergunta, texto, adv["nome"], processos, adv.get("comarca", ""))
            await zapi.enviar(phone, resp)
        except Exception as e:
            log.error(f"Erro IA {phone}: {e}")
            await zapi.enviar(phone, "Não consegui processar sua pergunta agora. Tente novamente.")


async def _enviar_resumo(phone, adv):
    try:
        processos = await db.listar_processos_com_prazos(adv["id"])
        hoje = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        header = f"☀️ Bom dia, Dr(a). *{adv[\'nome\']}*! ({hoje})\\n\\n"
        if not processos:
            await zapi.enviar(phone, header + "Você não tem processos monitorados ainda.\\nDigite *buscar* para importar pela OAB."); return
        from ia import gerar_briefing
        loop = asyncio.get_event_loop()
        texto = await loop.run_in_executor(None, gerar_briefing, adv["nome"], processos, adv.get("comarca", ""))
        await zapi.enviar(phone, header + texto)
        await db.log_whatsapp(adv["id"], "outbound", "resumo", texto[:200])
    except Exception as e:
        log.error(f"Erro resumo {phone}: {e}")


# — Jobs —

async def enviar_briefing_todos() -> int:
    advogados = await db.listar_advogados_ativos()
    enviados = 0
    for adv in advogados:
        if not adv.get("whatsapp") or not adv.get("zapi_confirmado"): continue
        if not await db.pode_usar(adv["id"]): continue
        try:
            await _enviar_resumo(adv["whatsapp"], adv)
            enviados += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            log.error(f"Erro briefing {adv[\'nome\']}: {e}")
    return enviados


async def enviar_lembrete_trial() -> int:
    advogados = await db.advogados_trial_expirando(dias=2)
    enviados = 0
    for adv in advogados:
        try:
            await zapi.enviar(adv["whatsapp"],
                f"⏰ Dr(a). *{adv[\'nome\']}*, seu teste encerra em *2 dias*.\\n\\n"
                "Para continuar, assine em *prazu.com.br* por apenas *R$ 49,90/mês*."
            )
            enviados += 1
        except Exception as e:
            log.error(f"Erro lembrete {adv[\'nome\']}: {e}")
    return enviados


async def monitorar_djen_todos() -> int:
    from datetime import timedelta
    advogados = await db.listar_advogados_ativos()
    notificados = 0; agora = datetime.now(timezone.utc)
    for adv in advogados:
        if not adv.get("whatsapp") or not adv.get("zapi_confirmado"): continue
        ultima = adv.get("ultima_busca_djen")
        if ultima:
            if hasattr(ultima, "tzinfo") and ultima.tzinfo is None:
                ultima = ultima.replace(tzinfo=timezone.utc)
            if (agora - ultima).days < 5: continue
        asyncio.create_task(_buscar_djen(adv["id"], adv["whatsapp"], adv["oab_numero"], adv["oab_seccional"]))
        notificados += 1
        await asyncio.sleep(1)
    return notificados
'''

# ─────────────────────────────────────────────
# Cria os arquivos
# ─────────────────────────────────────────────
created = []
for path, content in files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    # Não sobrescreve se já existir (seguro)
    if os.path.exists(path):
        print(f"  ⚠️  já existe, pulando: {path}")
        continue
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    created.append(path)
    print(f"  ✅ criado: {path}")

print(f"\n{'─'*40}")
print(f"✅ {len(created)} arquivo(s) criado(s).")
if created:
    print("\nPróximo passo — rode no terminal:")
    print("  git add web/")
    print('  git commit -m "feat: FastAPI + auth JWT + bot WhatsApp + jobs"')
    print("  git push")
