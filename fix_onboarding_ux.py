#!/usr/bin/env python3
"""
fix_onboarding_ux.py — correções de UX no onboarding
1. Endpoint /api/onboarding/verificar-oab para checar duplicata na etapa 1
2. Placeholder email no cadastro.html
Aplicar: cd ~/prazu && python3 fix_onboarding_ux.py
"""
from pathlib import Path
import subprocess

# ── Fix 1: adicionar endpoint verificar-oab no app.py ─────────────────────
APP = Path("web/app.py")
src = APP.read_text()

OLD = '''@app.post("/api/onboarding/enviar-codigo")'''
NEW = '''@app.post("/api/onboarding/verificar-oab")
async def onboarding_verificar_oab(payload: dict, adv=Depends(advogado_logado)):
    """Verifica se OAB já está cadastrada — chamado na etapa 1 antes de avançar."""
    oab_numero = re.sub(r'\\D', '', str(payload.get("oab_numero", "")).strip())
    oab_seccional = str(payload.get("oab_seccional", "")).strip().upper()
    if not oab_numero or not oab_seccional or len(oab_seccional) != 2:
        raise HTTPException(400, "OAB inválida.")
    existente = await db.buscar_por_oab(oab_numero, oab_seccional)
    if existente and existente["id"] != adv["id"]:
        raise HTTPException(409, "Esta OAB já possui um monitoramento ativo. Entre em contato com o suporte se for você.")
    return {"ok": True}

@app.post("/api/onboarding/enviar-codigo")'''

if OLD in src:
    src = src.replace(OLD, NEW)
    APP.write_text(src)
    print("✅ Endpoint /api/onboarding/verificar-oab adicionado")
else:
    print("❌ Ponto de inserção não encontrado em app.py")

r = subprocess.run(["python3", "-m", "py_compile", "web/app.py"], capture_output=True, text=True)
print(f"{'✅ app.py sintaxe OK' if r.returncode == 0 else '❌ Erro: ' + r.stderr}")

# ── Fix 2: placeholder email no cadastro.html ──────────────────────────────
CADASTRO = Path("web/templates/cadastro.html")
if CADASTRO.exists():
    c = CADASTRO.read_text()
    if "escritorio" in c.lower() or "ana@" in c.lower():
        c = c.replace('ana@escritorio', 'voce@email.com')
        c = c.replace('Ana@escritorio', 'voce@email.com')
        c = c.replace('ana@escritório', 'voce@email.com')
        # busca genérica
        import re as _re
        c = _re.sub(r'placeholder="[^"]*escritorio[^"]*"', 'placeholder="voce@email.com"', c, flags=_re.IGNORECASE)
        c = _re.sub(r'placeholder="ana@[^"]*"', 'placeholder="voce@email.com"', c, flags=_re.IGNORECASE)
        CADASTRO.write_text(c)
        print("✅ Placeholder email corrigido em cadastro.html")
    else:
        print("⚠️  Placeholder 'escritorio' não encontrado — verifique manualmente")
        # mostra placeholders de email existentes
        import re as _re
        matches = _re.findall(r'placeholder="[^"]*email[^"]*"', c, _re.IGNORECASE)
        print(f"   Placeholders de email encontrados: {matches}")
else:
    print("❌ cadastro.html não encontrado")
