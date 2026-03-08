#!/usr/bin/env python3
"""
fix_cadastro.py — fix cirúrgico para o 500 no /api/auth/cadastro
Não depende de 'import re' — usa only built-ins.
Aplicar: cd ~/prazu && python3 fix_cadastro.py
"""
from pathlib import Path

APP = Path("web/app.py")
src = APP.read_text()

# ── Detectar qual versão está no arquivo ────────────────────────────────────
tem_patch = "8 caracteres" in src
tem_re    = "import re" in src

print(f"Estado atual: patch={'SIM' if tem_patch else 'NÃO'}, import re={'SIM' if tem_re else 'NÃO'}")

# ── Substituição 1: versão ORIGINAL (6 chars, sem re) ───────────────────────
OLD_V1 = '''@app.post("/api/auth/cadastro")
async def cadastro(payload: CadastroRequest, request: Request):
    if len(payload.senha) < 6:
        raise HTTPException(400, "Senha deve ter pelo menos 6 caracteres.")

    telefone = None
    if payload.telefone:
        telefone = "".join(filter(str.isdigit, payload.telefone))
        if len(telefone) < 10: telefone = None

    # Cadastro mínimo — OAB vem no onboarding
    advogado_id = await db.criar_advogado_minimo(
        nome=payload.nome,
        email=payload.email,
        senha=payload.senha,
        telefone=telefone,
    )
    if not advogado_id:
        raise HTTPException(409, "E-mail já cadastrado.")'''

# ── Substituição 2: versão PATCHEADA com re (pode ter re quebrado) ───────────
OLD_V2 = '''@app.post("/api/auth/cadastro")
async def cadastro(payload: CadastroRequest, request: Request):
    # Senha forte: mínimo 8 chars, ao menos 1 letra e 1 número
    if len(payload.senha) < 8:
        raise HTTPException(400, "Senha deve ter pelo menos 8 caracteres.")
    if not re.search(r\'[A-Za-z]\', payload.senha) or not re.search(r\'[0-9]\', payload.senha):
        raise HTTPException(400, "Senha deve conter ao menos uma letra e um número.")

    telefone = None
    if payload.telefone:
        telefone = "".join(filter(str.isdigit, payload.telefone))
        if len(telefone) < 10: telefone = None

    # Verificar e-mail duplicado antes do insert (mensagem clara)
    existente = await db.buscar_por_email(payload.email)
    if existente:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")

    # Cadastro mínimo — OAB vem no onboarding
    advogado_id = await db.criar_advogado_minimo(
        nome=payload.nome,
        email=payload.email,
        senha=payload.senha,
        telefone=telefone,
    )
    if not advogado_id:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")'''

# ── Nova versão: sem import re, usa any() + str.isalpha/isdigit ─────────────
NEW = '''@app.post("/api/auth/cadastro")
async def cadastro(payload: CadastroRequest, request: Request):
    # Senha forte: mínimo 8 chars, ao menos 1 letra e 1 número (sem import re)
    if len(payload.senha) < 8:
        raise HTTPException(400, "Senha deve ter pelo menos 8 caracteres.")
    if not any(c.isalpha() for c in payload.senha):
        raise HTTPException(400, "Senha deve conter ao menos uma letra e um número.")
    if not any(c.isdigit() for c in payload.senha):
        raise HTTPException(400, "Senha deve conter ao menos uma letra e um número.")

    telefone = None
    if payload.telefone:
        telefone = "".join(filter(str.isdigit, payload.telefone))
        if len(telefone) < 10: telefone = None

    # Verificar e-mail duplicado antes do insert — mensagem clara com link
    existente = await db.buscar_por_email(payload.email)
    if existente:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")

    # Cadastro mínimo — OAB vem no onboarding
    advogado_id = await db.criar_advogado_minimo(
        nome=payload.nome,
        email=payload.email,
        senha=payload.senha,
        telefone=telefone,
    )
    if not advogado_id:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")'''

# ── Aplicar ──────────────────────────────────────────────────────────────────
if OLD_V1 in src:
    src = src.replace(OLD_V1, NEW)
    print("✅ Patch aplicado sobre versão original (6 chars)")
elif OLD_V2 in src:
    src = src.replace(OLD_V2, NEW)
    print("✅ Patch aplicado sobre versão com re.search")
else:
    print("❌ Nenhum dos trechos encontrado — cole o conteúdo atual do cadastro para análise")
    exit(1)

APP.write_text(src)

# ── Verificar sintaxe ─────────────────────────────────────────────────────────
import subprocess
result = subprocess.run(["python3", "-m", "py_compile", "web/app.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Sintaxe OK — pronto para commit e deploy")
else:
    print(f"❌ Erro de sintaxe: {result.stderr}")
