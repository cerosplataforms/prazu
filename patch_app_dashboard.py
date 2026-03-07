# Cole este arquivo em ~/prazu/ e rode: python3 patch_app_dashboard.py
# Ele aplica 3 correções no web/app.py:
# 1. Adiciona coluna 'tratamento' na tabela advogados (via ALTER TABLE)
# 2. Passa primeiro_nome, tratamento e buscar_djen_auto para o template
# 3. Salva tratamento no endpoint /api/advogado/dados

import re

with open('web/app.py', 'r') as f:
    content = f.read()

# ── Correção 1: bloco do dashboard ──
old_dashboard = '''@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, adv=Depends(advogado_logado)):
    if not await db.pode_usar(adv["id"]): return RedirectResponse("/plano-expirado")
    processos = await db.listar_processos_com_prazos(adv["id"])
    trial_dias = None
    if adv["status"] == "trial" and adv.get("trial_fim"):
        from datetime import datetime, timezone
        trial_fim = adv["trial_fim"]
        if hasattr(trial_fim, "tzinfo") and trial_fim.tzinfo is None:
            trial_fim = trial_fim.replace(tzinfo=timezone.utc)
        trial_dias = max(0, (trial_fim - datetime.now(timezone.utc)).days)
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "advogado": adv,
        "processos": processos, "trial_dias": trial_dias,
    })'''

new_dashboard = '''@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, adv=Depends(advogado_logado)):
    if not await db.pode_usar(adv["id"]): return RedirectResponse("/plano-expirado")
    processos = await db.listar_processos_com_prazos(adv["id"])
    trial_dias = None
    if adv["status"] == "trial" and adv.get("trial_fim"):
        from datetime import datetime, timezone
        trial_fim = adv["trial_fim"]
        if hasattr(trial_fim, "tzinfo") and trial_fim.tzinfo is None:
            trial_fim = trial_fim.replace(tzinfo=timezone.utc)
        trial_dias = max(0, (trial_fim - datetime.now(timezone.utc)).days)
    # Primeiro nome ignorando títulos
    _titulos = {'dr', 'dra', 'dr.', 'dra.', 'prof', 'prof.', 'me', 'me.', 'excelência', 'excelencia'}
    _partes = adv["nome"].split()
    primeiro_nome = next((p for p in _partes if p.lower().rstrip('.') not in _titulos), _partes[0])
    tratamento = adv.get("tratamento") or "Dr(a)."
    buscar_djen_auto = not adv.get("ultima_busca_djen")
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "advogado": adv,
        "processos": processos, "trial_dias": trial_dias,
        "primeiro_nome": primeiro_nome,
        "tratamento": tratamento,
        "buscar_djen_auto": buscar_djen_auto,
    })'''

if old_dashboard in content:
    content = content.replace(old_dashboard, new_dashboard)
    print("✅ bloco dashboard atualizado")
else:
    print("⚠️  bloco dashboard NÃO encontrado — verifique manualmente")

# ── Correção 2: endpoint /api/advogado/dados — salvar tratamento ──
old_dados = '''@app.post("/api/advogado/dados")
async def atualizar_dados(payload: dict, adv=Depends(advogado_logado)):
    nome = payload.get("nome", "").strip()
    if not nome:
        raise HTTPException(400, "Nome inválido")
    await db.atualizar_dados(adv["id"], nome=nome, horario_briefing=payload.get("horario_briefing","07:00"))
    return {"ok": True}'''

new_dados = '''@app.post("/api/advogado/dados")
async def atualizar_dados(payload: dict, adv=Depends(advogado_logado)):
    nome = payload.get("nome", "").strip()
    if not nome:
        raise HTTPException(400, "Nome inválido")
    tratamento = payload.get("tratamento", "").strip()
    await db.atualizar_dados(adv["id"], nome=nome, horario_briefing=payload.get("horario_briefing","07:00"), tratamento=tratamento)
    return {"ok": True}'''

if old_dados in content:
    content = content.replace(old_dados, new_dados)
    print("✅ endpoint /api/advogado/dados atualizado")
else:
    print("⚠️  endpoint dados NÃO encontrado — verifique manualmente")

with open('web/app.py', 'w') as f:
    f.write(content)

print("\nPróximo passo: adicionar coluna tratamento no banco e atualizar db.atualizar_dados()")
print("Rode no psql:")
print("  ALTER TABLE advogados ADD COLUMN IF NOT EXISTS tratamento TEXT DEFAULT 'Dr(a).';")
