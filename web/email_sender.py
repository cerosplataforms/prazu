"""
web/email_sender.py — Prazu
Envia e-mails transacionais via Resend (fallback SMTP).
"""

import os, logging, asyncio
log = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM     = os.getenv("EMAIL_FROM", "noreply@prazu.com.br")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Prazu")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")


async def enviar_codigo(destinatario: str, codigo: str, motivo: str = "verificação"):
    assunto = f"Seu código Prazu: {codigo}"
    html = f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:480px;margin:0 auto;padding:2rem;background:#f8faff;border-radius:12px">
      <h2 style="color:#2563EB;font-size:1.4rem;margin:0 0 1rem">prazu</h2>
      <p style="color:#1a2340;font-size:0.95rem;margin:0 0 0.5rem">Código para <strong>{motivo}</strong>:</p>
      <div style="font-size:2.5rem;font-weight:800;letter-spacing:.3em;
                  background:#fff;padding:1.25rem;text-align:center;
                  border-radius:10px;color:#2563EB;margin:1.25rem 0;
                  border:2px solid #e5e9f2">
        {codigo}
      </div>
      <p style="color:#64748B;font-size:.85rem;margin:0">
        Expira em 10 minutos.<br>Se não foi você, ignore este e-mail.
      </p>
      <hr style="border:none;border-top:1px solid #e5e9f2;margin:1.5rem 0 1rem">
      <p style="color:#94a3b8;font-size:.75rem;margin:0">
        Prazu — Monitoramento de prazos processuais<br>
        <a href="https://prazu.com.br" style="color:#2563EB;text-decoration:none">prazu.com.br</a>
      </p>
    </div>
    """
    loop = asyncio.get_event_loop()
    if RESEND_API_KEY:
        await loop.run_in_executor(None, _resend, destinatario, assunto, html)
    elif SMTP_USER:
        await loop.run_in_executor(None, _smtp, destinatario, assunto, html)
    else:
        log.error(f"Nenhum provedor de email configurado. Código {codigo} para {destinatario} não enviado.")


def _resend(para, assunto, html):
    import requests
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
            "to": [para],
            "subject": assunto,
            "html": html,
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        log.info(f"Resend → {para}: OK ({r.json().get('id','')})")
    else:
        log.error(f"Resend → {para}: ERRO {r.status_code} {r.text}")
        raise Exception(f"Resend error: {r.status_code}")


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
