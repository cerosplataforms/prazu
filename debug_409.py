#!/usr/bin/env python3
"""
debug_409.py — adiciona log temporário antes do 409 no onboarding_salvar
Aplicar: cd ~/prazu && python3 debug_409.py
"""
from pathlib import Path
import subprocess

F = Path("web/app.py")
src = F.read_text()

OLD = '''    # Verificar OAB duplicada ANTES do insert (mensagem clara)
    existente_oab = await db.buscar_por_oab(oab_numero, oab_seccional)
    if existente_oab and existente_oab["id"] != adv["id"]:
        raise HTTPException(409, "Esta OAB já possui um monitoramento ativo. Entre em contato com o suporte se for você.")'''

NEW = '''    # Verificar OAB duplicada ANTES do insert (mensagem clara)
    existente_oab = await db.buscar_por_oab(oab_numero, oab_seccional)
    log.warning(f"DEBUG 409 — oab={oab_numero}/{oab_seccional} adv_id={adv['id']} existente_oab={existente_oab}")
    if existente_oab and existente_oab["id"] != adv["id"]:
        raise HTTPException(409, "Esta OAB já possui um monitoramento ativo. Entre em contato com o suporte se for você.")'''

if OLD in src:
    src = src.replace(OLD, NEW)
    F.write_text(src)
    print("✅ Log debug adicionado")
else:
    print("❌ Trecho não encontrado")
    exit(1)

r = subprocess.run(["python3", "-m", "py_compile", "web/app.py"], capture_output=True, text=True)
print(f"{'✅ Sintaxe OK' if r.returncode == 0 else '❌ Erro: ' + r.stderr}")
