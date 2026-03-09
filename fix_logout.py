#!/usr/bin/env python3
"""
fix_logout.py — 2 fixes:
1. Logout apaga sessão do banco (não só o cookie)
2. Headers no-cache em todas as TemplateResponse

Aplicar: cd ~/prazu && python3 fix_logout.py
"""
from pathlib import Path
import subprocess

# ── Fix 1: database_gcp.py — adicionar delete_session ────────────────────────
DB = Path("database_gcp.py")
src_db = DB.read_text()

OLD_DB = '''            "INSERT INTO sessions (advogado_id, token, user_agent, ip, expira_em, criado_em) VALUES ($1,$2,$3,$4,$5,NOW())",'''

# Verificar se delete_session já existe
if "delete_session" in src_db:
    print("⚠️  delete_session já existe em database_gcp.py")
else:
    # Adicionar função delete_session após a função criar_sessao
    # Procura o final da função criar_sessao
    INJECT_AFTER = "async def criar_sessao("
    idx = src_db.find(INJECT_AFTER)
    if idx == -1:
        print("❌ Não encontrei criar_sessao em database_gcp.py")
    else:
        # Encontrar o próximo async def depois de criar_sessao
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

# ── Fix 2: app.py — logout apaga sessão + no-cache headers ───────────────────
APP = Path("web/app.py")
src_app = APP.read_text()

# Fix logout
OLD_LOGOUT = '''@app.get("/logout")
async def logout():
    r = RedirectResponse("/login")
    r.delete_cookie(TOKEN_COOKIE)
    return r'''

NEW_LOGOUT = '''@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        await db.delete_session(token)
    r = RedirectResponse("/login")
    r.delete_cookie(TOKEN_COOKIE, path="/")
    r.headers["Cache-Control"] = "no-store"
    return r'''

if OLD_LOGOUT in src_app:
    src_app = src_app.replace(OLD_LOGOUT, NEW_LOGOUT)
    print("✅ Logout atualizado — apaga sessão do banco")
else:
    print("⚠️  Trecho do logout não encontrado — verifique manualmente")

# Fix no-cache — adicionar headers em todas as TemplateResponse das páginas principais
# Abordagem: adicionar middleware de no-cache para rotas HTML
NO_CACHE_MIDDLEWARE = '''
@app.middleware("http")
async def no_cache_html(request, call_next):
    response = await call_next(request)
    if "text/html" in response.headers.get("content-type", ""):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

'''

# Inserir após os imports e antes do primeiro @app.get
if "no_cache_html" in src_app:
    print("⚠️  Middleware no-cache já existe")
else:
    # Inserir antes da primeira rota
    first_route = src_app.find('\n@app.get("/")')
    if first_route == -1:
        first_route = src_app.find('\n@app.get("/cadastro")')
    if first_route != -1:
        src_app = src_app[:first_route] + NO_CACHE_MIDDLEWARE + src_app[first_route:]
        print("✅ Middleware no-cache adicionado")
    else:
        print("⚠️  Não encontrei ponto de inserção para middleware")

APP.write_text(src_app)

# ── Verificar sintaxe ─────────────────────────────────────────────────────────
for f in ["web/app.py", "database_gcp.py"]:
    result = subprocess.run(["python3", "-m", "py_compile", f], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Sintaxe OK — {f}")
    else:
        print(f"❌ Erro de sintaxe em {f}:\n{result.stderr}")
