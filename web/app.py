"""
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
            "oab": f"{adv['oab_numero']}/{adv['oab_seccional']}",
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

@app.post("/webhook/evolution")
async def webhook_evolution(request: Request):
    evo_key = os.getenv("EVOLUTION_API_KEY", "")
    if evo_key and request.headers.get("apikey", "") != evo_key:
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



# ─────────────────────────────────────────────────────────
# Config endpoints (dashboard)
# ─────────────────────────────────────────────────────────

@app.post("/api/advogado/dados")
async def atualizar_dados(payload: dict, adv=Depends(advogado_logado)):
    nome = payload.get("nome", "").strip()
    if not nome:
        raise HTTPException(400, "Nome inválido")
    await db.atualizar_dados(adv["id"], nome=nome, horario_briefing=payload.get("horario_briefing","07:00"))
    return {"ok": True}


@app.post("/api/advogado/senha")
async def alterar_senha(payload: dict, adv=Depends(advogado_logado)):
    atual = payload.get("senha_atual", "")
    nova  = payload.get("senha_nova", "")
    if not db.verificar_senha(atual, adv.get("senha_hash", "")):
        raise HTTPException(400, "Senha atual incorreta")
    if len(nova) < 6:
        raise HTTPException(400, "Nova senha: mínimo 6 caracteres")
    await db.atualizar_senha(adv["id"], nova)
    return {"ok": True}


_email_codigos: dict = {}

@app.post("/api/advogado/solicitar-codigo-email")
async def solicitar_codigo_email(payload: dict, adv=Depends(advogado_logado)):
    import re, random, time as _t
    novo_email = payload.get("novo_email", "").strip().lower()
    if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", novo_email):
        raise HTTPException(400, "E-mail inválido")
    existente = await db.buscar_por_email(novo_email)
    if existente and existente["id"] != adv["id"]:
        raise HTTPException(409, "E-mail já cadastrado em outra conta")
    codigo = "".join(str(random.randint(0,9)) for _ in range(6))
    _email_codigos[adv["id"]] = {"codigo": codigo, "novo_email": novo_email, "exp": _t.time()+600}
    from web.email_sender import enviar_codigo
    await enviar_codigo(novo_email, codigo, "alteração de e-mail")
    return {"ok": True}


@app.post("/api/advogado/confirmar-email")
async def confirmar_email(payload: dict, adv=Depends(advogado_logado)):
    import time as _t
    codigo     = payload.get("codigo","").strip()
    novo_email = payload.get("novo_email","").strip().lower()
    reg        = _email_codigos.get(adv["id"])
    if not reg or _t.time() > reg["exp"]:
        raise HTTPException(400, "Código expirado. Solicite um novo.")
    if reg["codigo"] != codigo or reg["novo_email"] != novo_email:
        raise HTTPException(400, "Código incorreto")
    await db.atualizar_email(adv["id"], novo_email)
    _email_codigos.pop(adv["id"], None)
    return {"ok": True}


_wpp_codigos: dict = {}

@app.post("/api/advogado/solicitar-codigo-wpp")
async def solicitar_codigo_wpp(payload: dict, adv=Depends(advogado_logado)):
    import random, time as _t
    novo_wpp = "".join(filter(str.isdigit, payload.get("novo_whatsapp","")))
    if len(novo_wpp) < 10:
        raise HTTPException(400, "Número inválido")
    codigo = "".join(str(random.randint(0,9)) for _ in range(6))
    _wpp_codigos[adv["id"]] = {"codigo": codigo, "novo_wpp": novo_wpp, "exp": _t.time()+600}
    from web.email_sender import enviar_codigo
    await enviar_codigo(adv["email"], codigo, f"vinculação do WhatsApp {novo_wpp}")
    return {"ok": True}


@app.post("/api/advogado/confirmar-wpp")
async def confirmar_wpp(payload: dict, adv=Depends(advogado_logado)):
    import time as _t
    codigo   = payload.get("codigo","").strip()
    novo_wpp = "".join(filter(str.isdigit, payload.get("novo_whatsapp","")))
    reg      = _wpp_codigos.get(adv["id"])
    if not reg or _t.time() > reg["exp"]:
        raise HTTPException(400, "Código expirado. Solicite um novo.")
    if reg["codigo"] != codigo:
        raise HTTPException(400, "Código incorreto")
    await db.atualizar_whatsapp(adv["id"], novo_wpp, confirmado=True)
    _wpp_codigos.pop(adv["id"], None)
    return {"ok": True}


@app.post("/api/advogado/buscar-djen")
async def buscar_djen_api(adv=Depends(advogado_logado)):
    import asyncio
    from web.onboarding import _buscar_djen
    asyncio.create_task(
        _buscar_djen(adv["id"], adv.get("whatsapp"), adv["oab_numero"], adv["oab_seccional"])
    )
    return {"ok": True}

@app.get("/health")
async def health():
    try:
        return {"status": "ok", "db": await db.diagnostico()}
    except Exception as e:
        log.error(f"Health check falhou: {e}")
        raise HTTPException(503, "Banco indisponível")
