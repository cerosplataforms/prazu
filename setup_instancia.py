#!/usr/bin/env python3
"""
setup_instancia.py — Prazu Fase 2
Cria a instância WhatsApp na Evolution API e exibe o QR Code no terminal.

Pré-requisito:
  EVOLUTION_URL e EVOLUTION_API_KEY no .env

Uso:
  cd ~/prazu
  python3 setup_instancia.py
"""

import os, asyncio, base64, sys
from dotenv import load_dotenv
load_dotenv()

EVOLUTION_URL      = os.getenv("EVOLUTION_URL", "").rstrip("/")
EVOLUTION_API_KEY  = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "prazu")
PRAZU_URL          = os.getenv("PRAZU_URL", "")   # URL do Cloud Run do Prazu

if not EVOLUTION_URL or not EVOLUTION_API_KEY:
    print("❌ Configure EVOLUTION_URL e EVOLUTION_API_KEY no .env antes de rodar.")
    sys.exit(1)

WEBHOOK_URL = f"{PRAZU_URL}/webhook/evolution" if PRAZU_URL else ""


async def main():
    import httpx

    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
    }

    print(f"\n→ Criando instância \'{EVOLUTION_INSTANCE}\' na Evolution API...")

    # Cria instância
    payload = {
        "instanceName": EVOLUTION_INSTANCE,
        "integration": "WHATSAPP-BAILEYS",
        "qrcode": True,
    }
    if WEBHOOK_URL:
        payload["webhook"] = {
            "url": WEBHOOK_URL,
            "byEvents": False,
            "base64": False,
            "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
        }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{EVOLUTION_URL}/instance/create",
            json=payload,
            headers=headers,
        )

    data = r.json()
    if r.status_code not in (200, 201):
        # Instância pode já existir — tudo bem
        if "already" in str(data).lower() or r.status_code == 409:
            print("  ⚠️  Instância já existe, buscando QR Code...")
        else:
            print(f"  ❌ Erro ao criar instância: {data}")
            sys.exit(1)
    else:
        print(f"  ✅ Instância criada!")

    # Aguarda um segundo e busca o QR Code
    await asyncio.sleep(2)

    print("\n→ Buscando QR Code...")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{EVOLUTION_URL}/instance/connect/{EVOLUTION_INSTANCE}",
            headers=headers,
        )
    qr_data = r.json()
    qr_base64 = (
        qr_data.get("base64")
        or qr_data.get("qrcode", {}).get("base64")
        or ""
    )

    if not qr_base64:
        print("  ❌ QR Code não disponível. A instância pode já estar conectada.")
        print(f"     Resposta: {qr_data}")

        # Verifica status
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{EVOLUTION_URL}/instance/fetchInstances",
                headers=headers,
            )
        for inst in r.json():
            name = inst.get("instance", {}).get("instanceName", "")
            state = inst.get("instance", {}).get("state", "")
            if name == EVOLUTION_INSTANCE:
                print(f"  Status da instância: {state}")
                if state == "open":
                    print("  ✅ WhatsApp já conectado!")
        return

    # Salva QR Code como imagem
    qr_clean = qr_base64.split(",")[-1]  # remove "data:image/png;base64,"
    qr_bytes = base64.b64decode(qr_clean)
    qr_path = "qrcode_prazu.png"
    with open(qr_path, "wb") as f:
        f.write(qr_bytes)

    print(f"\n✅ QR Code salvo em: {qr_path}")
    print("\n📱 Abra esse arquivo e escaneie com o WhatsApp:")
    print(f"   open {qr_path}")
    print("\nAguardando conexão (60 segundos)...")

    # Polling até conectar
    for i in range(12):
        await asyncio.sleep(5)
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{EVOLUTION_URL}/instance/fetchInstances",
                headers=headers,
            )
        for inst in r.json():
            name = inst.get("instance", {}).get("instanceName", "")
            state = inst.get("instance", {}).get("state", "")
            if name == EVOLUTION_INSTANCE and state == "open":
                print("\n✅ WhatsApp conectado com sucesso!")

                if WEBHOOK_URL:
                    print(f"   Webhook configurado: {WEBHOOK_URL}")
                else:
                    print("   ⚠️  PRAZU_URL não definido no .env")
                    print("      Configure o webhook manualmente após o deploy do Prazu:")
                    print(f"      python3 -c \"")
                    print(f"        import asyncio")
                    print(f"        from web.evolution import evolution")
                    print(f"        asyncio.run(evolution.configurar_webhook(\'https://SUA_URL/webhook/evolution\'))")
                    print(f"      \"")
                return
        print(f"  Aguardando... ({(i+1)*5}s)")

    print("\n⚠️  Tempo esgotado. Escaneie o QR Code e rode novamente.")


asyncio.run(main())
