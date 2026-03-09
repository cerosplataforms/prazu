#!/usr/bin/env python3
"""
fix_data_djen.py — converte data_disponibilizacao de str para datetime.date
Aplicar: cd ~/prazu && python3 fix_data_djen.py
"""
from pathlib import Path
import subprocess

DB = Path("database_gcp.py")
src = DB.read_text()

OLD = '''async def comunicacao_djen_existe(advogado_id, numero_processo, data_disponibilizacao):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM comunicacoes_djen WHERE advogado_id=$1 AND numero_processo=$2 AND data_disponibilizacao=$3",
            advogado_id, numero_processo, data_disponibilizacao,
        )
        return row is not None'''

NEW = '''async def comunicacao_djen_existe(advogado_id, numero_processo, data_disponibilizacao):
    from datetime import date
    # asyncpg exige datetime.date, não str
    if isinstance(data_disponibilizacao, str):
        try:
            data_disponibilizacao = date.fromisoformat(data_disponibilizacao[:10])
        except (ValueError, TypeError):
            data_disponibilizacao = date.today()
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM comunicacoes_djen WHERE advogado_id=$1 AND numero_processo=$2 AND data_disponibilizacao=$3",
            advogado_id, numero_processo, data_disponibilizacao,
        )
        return row is not None'''

if OLD in src:
    src = src.replace(OLD, NEW)
    DB.write_text(src)
    print("✅ Fix aplicado em comunicacao_djen_existe")
else:
    print("❌ Trecho não encontrado")
    exit(1)

# Verificar salvar_comunicacao_djen também
OLD2 = '''async def salvar_comunicacao_djen(advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao="", tipo_comunicacao=""):
    async with _pool.acquire() as conn:'''

NEW2 = '''async def salvar_comunicacao_djen(advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao="", tipo_comunicacao=""):
    from datetime import date
    if isinstance(data_disponibilizacao, str):
        try:
            data_disponibilizacao = date.fromisoformat(data_disponibilizacao[:10])
        except (ValueError, TypeError):
            data_disponibilizacao = date.today()
    async with _pool.acquire() as conn:'''

if OLD2 in src:
    src = src.replace(OLD2, NEW2)
    DB.write_text(src)
    print("✅ Fix aplicado em salvar_comunicacao_djen")
else:
    print("⚠️  salvar_comunicacao_djen — trecho não encontrado, pode já estar correto")

r = subprocess.run(["python3", "-m", "py_compile", "database_gcp.py"], capture_output=True, text=True)
print(f"{'✅ Sintaxe OK' if r.returncode == 0 else '❌ Erro: ' + r.stderr}")
