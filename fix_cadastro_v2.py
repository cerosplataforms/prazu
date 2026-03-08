#!/usr/bin/env python3
"""
fix_cadastro_v2.py — corrige 409 falso positivo no cadastro
O bug: buscar_por_email(payload.email) onde payload.email é EmailStr (objeto Pydantic),
não str puro. A query SQL não bate com o tipo e retorna linha errada.
Solução: forçar str(payload.email).lower() explicitamente.

Aplicar: cd ~/prazu && python3 fix_cadastro_v2.py
"""
from pathlib import Path
import subprocess

APP = Path("web/app.py")
src = APP.read_text()

# Localizar o bloco atual do cadastro (qualquer versão)
# e substituir pela versão corrigida

OLD = '''    # Verificar e-mail duplicado antes do insert — mensagem clara com link
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

NEW = '''    # Verificar e-mail duplicado antes do insert — forçar str puro (EmailStr é objeto Pydantic)
    email_str = str(payload.email).lower().strip()
    existente = await db.buscar_por_email(email_str)
    if existente:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")

    # Cadastro mínimo — OAB vem no onboarding
    advogado_id = await db.criar_advogado_minimo(
        nome=payload.nome,
        email=email_str,
        senha=payload.senha,
        telefone=telefone,
    )
    if not advogado_id:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")'''

if OLD in src:
    src = src.replace(OLD, NEW)
    print("✅ Fix aplicado")
else:
    # Tentar variante sem o comentário longo
    OLD2 = '''    existente = await db.buscar_por_email(payload.email)
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

    NEW2 = '''    email_str = str(payload.email).lower().strip()
    existente = await db.buscar_por_email(email_str)
    if existente:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")

    # Cadastro mínimo — OAB vem no onboarding
    advogado_id = await db.criar_advogado_minimo(
        nome=payload.nome,
        email=email_str,
        senha=payload.senha,
        telefone=telefone,
    )
    if not advogado_id:
        raise HTTPException(409, "Este e-mail já está em uso. Deseja recuperar sua senha?")'''

    if OLD2 in src:
        src = src.replace(OLD2, NEW2)
        print("✅ Fix aplicado (variante 2)")
    else:
        print("❌ Trecho não encontrado. Cole o conteúdo do cadastro para análise.")
        # Mostrar contexto atual para debug
        for i, line in enumerate(src.split('\n')):
            if 'buscar_por_email' in line and 'cadastro' not in line:
                start = max(0, i-3)
                end = min(len(src.split('\n')), i+5)
                print("Contexto encontrado:")
                print('\n'.join(f"{start+j}: {l}" for j, l in enumerate(src.split('\n')[start:end])))
        exit(1)

APP.write_text(src)

result = subprocess.run(["python3", "-m", "py_compile", "web/app.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Sintaxe OK — pronto para commit e deploy")
else:
    print(f"❌ Erro de sintaxe:\n{result.stderr}")
