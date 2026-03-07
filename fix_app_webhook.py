#!/usr/bin/env python3
"""
fix_app_webhook.py — corrige o endpoint do webhook no web/app.py
Troca a rota /webhook/zapi pela /webhook/evolution com validação correta.

Uso:
  cd ~/prazu
  python3 fix_app_webhook.py
"""

with open("web/app.py") as f:
    content = f.read()

OLD = '''\
@app.post("/webhook/zapi")
async def webhook_zapi(request: Request):
    zapi_token = os.getenv("ZAPI_TOKEN", "")
    if zapi_token and request.headers.get("x-zapi-token", "") != zapi_token:'''

NEW = '''\
@app.post("/webhook/evolution")
async def webhook_evolution(request: Request):
    evo_key = os.getenv("EVOLUTION_API_KEY", "")
    if evo_key and request.headers.get("apikey", "") != evo_key:'''

if OLD not in content:
    print("❌ Trecho não encontrado — cole manualmente (veja abaixo)")
    print("""
Substitua no web/app.py:

  @app.post("/webhook/zapi")
  async def webhook_zapi(request: Request):
      zapi_token = os.getenv("ZAPI_TOKEN", "")
      if zapi_token and request.headers.get("x-zapi-token", "") != zapi_token:

Por:

  @app.post("/webhook/evolution")
  async def webhook_evolution(request: Request):
      evo_key = os.getenv("EVOLUTION_API_KEY", "")
      if evo_key and request.headers.get("apikey", "") != evo_key:

E mais abaixo, substitua:
  from web.onboarding import processar_mensagem_zapi
  await processar_mensagem_zapi(payload)

Por:
  from web.onboarding import processar_mensagem_zapi
  await processar_mensagem_zapi(payload)
""")
else:
    content = content.replace(OLD, NEW)

    # Troca o log interno
    content = content.replace(
        'log.warning("Webhook Z-API: token inválido")',
        'log.warning("Webhook Evolution: apikey inválida")'
    )

    with open("web/app.py", "w") as f:
        f.write(content)
    print("✅ web/app.py corrigido — rota /webhook/evolution ativa")
    print("   Pode commitar agora!")
