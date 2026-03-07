"""
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
