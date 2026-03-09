#!/usr/bin/env python3
"""
fix_processo_upsert.py — corrige race condition no criar_ou_atualizar_processo
Usa INSERT ON CONFLICT para evitar duplicate key em buscas paralelas.
Aplicar: cd ~/prazu && python3 fix_processo_upsert.py
"""
from pathlib import Path
import subprocess

DB = Path("database_gcp.py")
src = DB.read_text()

OLD = '''async def criar_ou_atualizar_processo(advogado_id, numero, partes="", vara="", tribunal="", comarca="", fonte="djen"):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM processos WHERE advogado_id=$1 AND numero=$2", advogado_id, numero)
        if row:
            return row["id"]
        row = await conn.fetchrow(
            "INSERT INTO processos (advogado_id, numero, partes, vara, tribunal, comarca, fonte) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id",
            advogado_id, numero, partes, vara, tribunal, comarca, fonte,
        )
        return row["id"]'''

NEW = '''async def criar_ou_atualizar_processo(advogado_id, numero, partes="", vara="", tribunal="", comarca="", fonte="djen"):
    async with _pool.acquire() as conn:
        # ON CONFLICT evita race condition quando duas buscas DJEN rodam em paralelo
        row = await conn.fetchrow(
            """
            INSERT INTO processos (advogado_id, numero, partes, vara, tribunal, comarca, fonte)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            ON CONFLICT (advogado_id, numero) DO UPDATE
                SET partes = EXCLUDED.partes,
                    vara = EXCLUDED.vara,
                    tribunal = EXCLUDED.tribunal,
                    comarca = EXCLUDED.comarca,
                    atualizado_em = NOW()
            RETURNING id
            """,
            advogado_id, numero, partes, vara, tribunal, comarca, fonte,
        )
        return row["id"]'''

if OLD in src:
    src = src.replace(OLD, NEW)
    DB.write_text(src)
    print("✅ Fix aplicado em criar_ou_atualizar_processo")
else:
    print("❌ Trecho não encontrado")
    exit(1)

r = subprocess.run(["python3", "-m", "py_compile", "database_gcp.py"], capture_output=True, text=True)
print(f"{'✅ Sintaxe OK' if r.returncode == 0 else '❌ Erro: ' + r.stderr}")
