#!/usr/bin/env python3
"""
fix_logout_v2.py
Aplicar: cd ~/prazu && python3 fix_logout_v2.py
"""
from pathlib import Path
import subprocess

# ── Fix 1: database_gcp.py — adicionar delete_session ────────────────────────
DB = Path("database_gcp.py")
src_db = DB.read_text()

if "delete_session" in src_db:
    print("⚠️  delete_session já existe")
else:
    # Inserir após validar_session
    idx = src_db.find("async def validar_session(")
    next_func = src_db.find("\nasync def ", idx + 1)
    if next_func == -1:
        next_func = len(src_db)

    NEW_FUNC = '''

async def delete_session(token: str) -> None:
    """Remove sessão do banco no logout."""
    try:
        async with _pool.acquire() as conn:
            await conn.execute("DELETE FROM sessions WHERE token = $1", token)
    except Exception as e:
        log.warning(f"Erro ao deletar sessão: {e}")
'''
    src_db = src_db[:next_func] + NEW_FUNC + src_db[next_func:]
    DB.write_text(src_db)
    print("✅ delete_session adicionado em database_gcp.py")

# ── Fix 2: app.py — middleware no-cache + logout limpa banco ─────────────────
APP = Path("web/app.py")
src_app = APP.read_text()

# Middleware no-cache
if "no_cache_html" in src_app:
    print("⚠️  Middleware no-cache já existe")
else:
    NO_CACHE = '''
@app.middleware("http")
async def no_cache_html(request, call_next):
    response = await call_next(request)
    if "text/html" in response.headers.get("content-type", ""):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

'''
    insert_at = src_app.find('\n@app.get("/")')
    src_app = src_app[:insert_at] + NO_CACHE + src_app[insert_at:]
    print("✅ Middleware no-cache adicionado")

# Logout limpa banco
OLD_LOGOUT = '''@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        await db.delete_session(token)
    r = RedirectResponse("/login")
    r.delete_cookie(TOKEN_COOKIE, path="/")
    r.headers["Cache-Control"] = "no-store"
    return r'''

OLD_LOGOUT_ORIGINAL = '''@app.get("/logout")
async def logout():
    r = RedirectResponse("/login")
    r.delete_cookie(TOKEN_COOKIE)
    return r'''

if "await db.delete_session" in src_app:
    print("⚠️  Logout já atualizado")
elif OLD_LOGOUT_ORIGINAL in src_app:
    src_app = src_app.replace(OLD_LOGOUT_ORIGINAL, OLD_LOGOUT)
    print("✅ Logout atualizado — apaga sessão do banco")
else:
    print("⚠️  Trecho do logout não encontrado")

APP.write_text(src_app)

# ── Sintaxe ───────────────────────────────────────────────────────────────────
for f in ["web/app.py", "database_gcp.py"]:
    r = subprocess.run(["python3", "-m", "py_compile", f], capture_output=True, text=True)
    print(f"{'✅' if r.returncode == 0 else '❌'} Sintaxe {'OK' if r.returncode == 0 else 'ERRO'} — {f}")
    if r.returncode != 0:
        print(r.stderr)
