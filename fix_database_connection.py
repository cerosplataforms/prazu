#!/usr/bin/env python3
"""
Corrige a conexão do banco no Cloud Run.
Roda da pasta ~/prazu: python3 fix_database_connection.py
"""
import os, shutil

target = os.path.expanduser("~/prazu/database_gcp.py")

# Lê o arquivo atual
with open(target, "r") as f:
    content = f.read()

# Substitui a função init_db para usar socket no Cloud Run
old = '''async def init_db():
    global _pool
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "prazu")
    db_user = os.getenv("DB_USER", "prazu_user")
    db_pass = os.getenv("DB_PASSWORD", "")
    
    _pool = await asyncpg.create_pool(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pass,
        min_size=2,
        max_size=10
    )'''

new = '''async def init_db():
    global _pool
    db_name = os.getenv("DB_NAME", "prazu")
    db_user = os.getenv("DB_USER", "prazu_user")
    db_pass = os.getenv("DB_PASSWORD", "")
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        # Cloud Run usa socket Unix para Cloud SQL
        instance = "prazu-prod:southamerica-east1:prazu-db"
        socket_path = f"/cloudsql/{instance}"
        dsn = f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket_path}"
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    else:
        db_host = os.getenv("DB_HOST", "localhost")
        _pool = await asyncpg.create_pool(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            min_size=2,
            max_size=10
        )'''

if old in content:
    content = content.replace(old, new)
    with open(target, "w") as f:
        f.write(content)
    print("✅ database_gcp.py corrigido com sucesso!")
else:
    # Tenta abordagem mais simples — reescreve só a função init_db com regex
    import re
    pattern = r'async def init_db\(\):.*?(?=\nasync def |\Z)'
    replacement = new + "\n"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    if new_content != content:
        with open(target, "w") as f:
            f.write(new_content)
        print("✅ database_gcp.py corrigido via regex!")
    else:
        print("⚠️  Não encontrou o padrão exato. Vou mostrar a função init_db atual:")
        # Mostra a função atual para diagnóstico
        lines = content.split('\n')
        in_func = False
        for i, line in enumerate(lines):
            if 'async def init_db' in line:
                in_func = True
            if in_func:
                print(f"{i+1}: {line}")
                if i > 0 and in_func and line.startswith('async def ') and 'init_db' not in line:
                    break
                if in_func and i > 50:
                    break
