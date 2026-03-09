#!/usr/bin/env python3
"""
fix_db_socket.py — usa DB_HOST como connection name no Cloud SQL
O socket estava hardcoded para prazu-db (prod), ignorando DB_HOST do secret.
Aplicar: cd ~/prazu && python3 fix_db_socket.py
"""
from pathlib import Path
import subprocess

F = Path("database_gcp.py")
src = F.read_text()

OLD = '''    if os.getenv("ENVIRONMENT") == "production":
        socket_path = "/cloudsql/prazu-prod:southamerica-east1:prazu-db"
        _pool = await asyncpg.create_pool(
            host=socket_path, database=db_name, user=db_user, password=db_pass,
            min_size=2, max_size=10, command_timeout=30,
        )'''

NEW = '''    if os.getenv("ENVIRONMENT") == "production":
        db_host = os.getenv("DB_HOST", "prazu-prod:southamerica-east1:prazu-db")
        socket_path = f"/cloudsql/{db_host}"
        _pool = await asyncpg.create_pool(
            host=socket_path, database=db_name, user=db_user, password=db_pass,
            min_size=2, max_size=10, command_timeout=30,
        )'''

if OLD in src:
    src = src.replace(OLD, NEW)
    F.write_text(src)
    print("✅ Fix aplicado — socket agora usa DB_HOST")
else:
    print("❌ Trecho não encontrado")
    exit(1)

r = subprocess.run(["python3", "-m", "py_compile", "database_gcp.py"], capture_output=True, text=True)
print(f"{'✅ Sintaxe OK' if r.returncode == 0 else '❌ Erro: ' + r.stderr}")
