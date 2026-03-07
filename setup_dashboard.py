#!/usr/bin/env python3
"""
setup_dashboard.py — Prazu Fase 2
Injeta os endpoints de configuração no web/app.py
e cria web/email_sender.py.

Uso:
  cd ~/prazu
  python3 setup_dashboard.py
"""

import os

# ── 1. Verifica dashboard ────────────────────────────────
dash = "web/templates/dashboard.html"
print(f"  {'✅' if os.path.exists(dash) else '❌'} {dash}")

# ── 2. Injeta endpoints no app.py ────────────────────────
app_path = "web/app.py"

ENDPOINTS = '''

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
    if not re.match(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", novo_email):
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
'''

if os.path.exists(app_path):
    with open(app_path) as f:
        content = f.read()
    if "/api/advogado/dados" in content:
        print("  ⚠️  Endpoints já existem em app.py — pulando")
    else:
        content = content.replace('@app.get("/health")', ENDPOINTS + '\n@app.get("/health")')
        with open(app_path, "w") as f:
            f.write(content)
        print("  ✅ Endpoints injetados em web/app.py")
else:
    print(f"  ❌ {app_path} não encontrado")

# ── 3. Cria email_sender.py ──────────────────────────────
ep = "web/email_sender.py"
if not os.path.exists(ep):
    with open(ep, "w") as f:
        f.write('''"""
web/email_sender.py — Prazu Fase 2
Envia e-mails transacionais (códigos de verificação).
Configure EMAIL_PROVIDER no .env: "smtp" ou "sendgrid"
"""

import os, logging, asyncio
log = logging.getLogger(__name__)

EMAIL_PROVIDER  = os.getenv("EMAIL_PROVIDER", "smtp")
EMAIL_FROM      = os.getenv("EMAIL_FROM", "noreply@prazu.com.br")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Prazu")
SENDGRID_KEY    = os.getenv("SENDGRID_API_KEY", "")
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER       = os.getenv("SMTP_USER", "")
SMTP_PASS       = os.getenv("SMTP_PASS", "")


async def enviar_codigo(destinatario: str, codigo: str, motivo: str = "verificação"):
    assunto = f"Seu código Prazu: {codigo}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#1D4ED8;font-size:1.4rem">prazu</h2>
      <p>Código para <strong>{motivo}</strong>:</p>
      <div style="font-size:2.5rem;font-weight:800;letter-spacing:.3em;
                  background:#EFF4FF;padding:1.25rem;text-align:center;
                  border-radius:10px;color:#1D4ED8;margin:1.25rem 0">
        {codigo}
      </div>
      <p style="color:#64748B;font-size:.85rem">
        Expira em 10 minutos.<br>Se não foi você, ignore este e-mail.
      </p>
    </div>
    """
    loop = asyncio.get_event_loop()
    if EMAIL_PROVIDER == "sendgrid" and SENDGRID_KEY:
        await loop.run_in_executor(None, _sendgrid, destinatario, assunto, html)
    else:
        await loop.run_in_executor(None, _smtp, destinatario, assunto, html)


def _sendgrid(para, assunto, html):
    import sendgrid
    from sendgrid.helpers.mail import Mail
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_KEY)
    r = sg.send(Mail(from_email=(EMAIL_FROM, EMAIL_FROM_NAME), to_emails=para, subject=assunto, html_content=html))
    log.info(f"SendGrid → {para}: {r.status_code}")


def _smtp(para, assunto, html):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
    msg["To"]      = para
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.ehlo(); s.starttls(); s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(EMAIL_FROM, para, msg.as_string())
    log.info(f"SMTP → {para}: OK")
''')
    print("  ✅ web/email_sender.py criado")
else:
    print("  ⚠️  web/email_sender.py já existe — pulando")

print("""
────────────────────────────────────────
✅ Pronto!

Adicione no .env:
  EMAIL_PROVIDER=smtp
  EMAIL_FROM=noreply@prazu.com.br
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=seu@gmail.com
  SMTP_PASS=sua_senha_de_app  ← senha de app do Google, não a conta

Próximo passo:
  git add web/
  git commit -m "feat: site - dashboard branco + configurações do advogado"
  git push
""")
