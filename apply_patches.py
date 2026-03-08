#!/usr/bin/env python3
"""
apply_patches.py — aplica todos os patches de segurança no web/app.py
Executar de dentro do repo: python3 scripts/apply_patches.py
"""
import re, sys
from pathlib import Path

APP = Path("web/app.py")
src = APP.read_text()

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1 — import re no topo (se não existir)
# ─────────────────────────────────────────────────────────────────────────────
if "import re" not in src:
    src = src.replace(
        "import database_gcp as db",
        "import re\nimport database_gcp as db"
    )
    print("✅ PATCH 1: import re adicionado")
else:
    print("⏩ PATCH 1: import re já existe")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2 — cadastro: senha 8 chars + regex + mensagem de e-mail duplicado
# ─────────────────────────────────────────────────────────────────────────────
OLD_CADASTRO = '''@app.post("/api/auth/cadastro")
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

NEW_CADASTRO = '''@app.post("/api/auth/cadastro")
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

if OLD_CADASTRO in src:
    src = src.replace(OLD_CADASTRO, NEW_CADASTRO)
    print("✅ PATCH 2: cadastro — senha forte + mensagem e-mail duplicado")
else:
    print("❌ PATCH 2: trecho não encontrado — verifique manualmente")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3 — onboarding/enviar-codigo: valida 11 dígitos + "9" + erro Z-API
# ─────────────────────────────────────────────────────────────────────────────
OLD_ENVIAR = '''@app.post("/api/onboarding/enviar-codigo")
async def onboarding_enviar_codigo(payload: dict, adv=Depends(advogado_logado)):
    wpp = "".join(filter(str.isdigit, payload.get("whatsapp", "")))
    if len(wpp) < 10 or len(wpp) > 11:
        raise HTTPException(400, "Número inválido.")

    fone_api = wpp if wpp.startswith("55") else f"55{wpp}"
    codigo = "".join(str(random.randint(0, 9)) for _ in range(6))
    _onboarding_codigos[wpp] = {"codigo": codigo, "exp": _t.time() + 600}

    enviado = await _zapi().enviar(fone_api,
        f"*{codigo}* é o seu código de verificação Prazu.\\n\\nVálido por 10 minutos."
    )
    if not enviado:
        raise HTTPException(500, "Não foi possível enviar o código. Verifique o número e tente novamente.")

    log.info(f"Código onboarding enviado para {wpp}")
    return {"ok": True}'''

NEW_ENVIAR = '''@app.post("/api/onboarding/enviar-codigo")
async def onboarding_enviar_codigo(payload: dict, adv=Depends(advogado_logado)):
    wpp = "".join(filter(str.isdigit, payload.get("whatsapp", "")))

    # Validação de comprimento
    if len(wpp) < 10 or len(wpp) > 11:
        raise HTTPException(400, "Número inválido. Informe DDD + número (ex: 31999990000).")

    # Avisar se parecer que falta o 9 (celular com DDD de estado que começa por 6-9)
    if len(wpp) == 10 and wpp[2] in "6789":
        raise HTTPException(400, "Celular deve ter 9 dígitos após o DDD. Verifique se o '9' está incluído.")

    fone_api = wpp if wpp.startswith("55") else f"55{wpp}"
    codigo = "".join(str(random.randint(0, 9)) for _ in range(6))
    _onboarding_codigos[wpp] = {"codigo": codigo, "exp": _t.time() + 600, "enviado_em": _t.time()}

    try:
        enviado = await _zapi().enviar(fone_api,
            f"*{codigo}* é o seu código de verificação Prazu.\\n\\nVálido por 10 minutos."
        )
    except Exception as e:
        log.error(f"Z-API erro ao enviar código para {wpp}: {e}")
        raise HTTPException(503, "Serviço de WhatsApp temporariamente indisponível. Tente novamente em alguns minutos.")

    if not enviado:
        # Z-API retornou falso — número provavelmente não existe no WhatsApp
        _onboarding_codigos.pop(wpp, None)
        raise HTTPException(422, "WhatsApp não localizado. Verifique o número digitado.")

    log.info(f"Código onboarding enviado para {wpp}")
    return {"ok": True}


@app.post("/api/onboarding/reenviar-codigo")
async def onboarding_reenviar_codigo(payload: dict, adv=Depends(advogado_logado)):
    """Reenvio com debounce de 60s no backend para evitar spam."""
    wpp = "".join(filter(str.isdigit, payload.get("whatsapp", "")))
    if len(wpp) < 10:
        raise HTTPException(400, "Número inválido.")

    reg = _onboarding_codigos.get(wpp)
    if reg:
        segundos_passados = _t.time() - reg.get("enviado_em", 0)
        if segundos_passados < 60:
            restante = int(60 - segundos_passados)
            raise HTTPException(429, f"Aguarde {restante} segundos antes de reenviar.")

    fone_api = wpp if wpp.startswith("55") else f"55{wpp}"
    codigo = "".join(str(random.randint(0, 9)) for _ in range(6))
    _onboarding_codigos[wpp] = {"codigo": codigo, "exp": _t.time() + 600, "enviado_em": _t.time()}

    try:
        enviado = await _zapi().enviar(fone_api,
            f"*{codigo}* é o seu novo código de verificação Prazu.\\n\\nVálido por 10 minutos."
        )
    except Exception:
        raise HTTPException(503, "Serviço de WhatsApp indisponível. Tente novamente.")

    if not enviado:
        _onboarding_codigos.pop(wpp, None)
        raise HTTPException(422, "WhatsApp não localizado. Verifique o número digitado.")

    log.info(f"Código reenvio para {wpp}")
    return {"ok": True}'''

if OLD_ENVIAR in src:
    src = src.replace(OLD_ENVIAR, NEW_ENVIAR)
    print("✅ PATCH 3: enviar-codigo + reenviar-codigo com debounce")
else:
    print("❌ PATCH 3: trecho não encontrado — verifique manualmente")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 4 — onboarding/salvar: limpa OAB + verifica duplicata antes do insert
# ─────────────────────────────────────────────────────────────────────────────
OLD_SALVAR = '''@app.post("/api/onboarding/salvar")
async def onboarding_salvar(payload: dict, adv=Depends(advogado_logado)):
    oab_numero = str(payload.get("oab_numero", "")).strip()
    oab_seccional = str(payload.get("oab_seccional", "")).strip().upper()
    tratamento = str(payload.get("tratamento", "Dr(a).")).strip()
    wpp_notif = "".join(filter(str.isdigit, payload.get("whatsapp_notificacao", "")))
    horario = str(payload.get("horario_briefing", "07:00")).strip()
    briefing_dias = str(payload.get("briefing_dias", "uteis")).strip()

    if not oab_numero or not oab_seccional or len(oab_seccional) != 2:
        raise HTTPException(400, "OAB inválida.")
    if len(wpp_notif) < 10:
        raise HTTPException(400, "WhatsApp inválido.")

    # Confirma que o código foi verificado
    reg = _onboarding_codigos.get(wpp_notif)
    if not reg or _t.time() > reg["exp"]:
        raise HTTPException(400, "Verificação do WhatsApp expirada. Volte e reenvie o código.")
    _onboarding_codigos.pop(wpp_notif, None)

    lembrete_fds = briefing_dias == "todos"

    ok = await db.salvar_onboarding(
        advogado_id=adv["id"],
        oab_numero=oab_numero,
        oab_seccional=oab_seccional,
        tratamento=tratamento,
        whatsapp_notificacao=wpp_notif,
        horario_briefing=horario,
        lembrete_fds=lembrete_fds,
    )
    if not ok:
        raise HTTPException(409, "OAB já cadastrada em outra conta.")'''

NEW_SALVAR = '''@app.post("/api/onboarding/salvar")
async def onboarding_salvar(payload: dict, adv=Depends(advogado_logado)):
    # Limpeza automática da OAB (remove pontos, traços, espaços)
    oab_numero    = re.sub(r\'\\D\', \'\', str(payload.get("oab_numero", "")).strip())
    oab_seccional = str(payload.get("oab_seccional", "")).strip().upper()
    tratamento    = str(payload.get("tratamento", "Dr(a).")).strip()
    wpp_notif     = "".join(filter(str.isdigit, payload.get("whatsapp_notificacao", "")))
    horario       = str(payload.get("horario_briefing", "07:00")).strip()
    briefing_dias = str(payload.get("briefing_dias", "uteis")).strip()

    if not oab_numero or not oab_seccional or len(oab_seccional) != 2:
        raise HTTPException(400, "OAB inválida. Informe número e estado (ex: 12345/MG).")
    if len(wpp_notif) < 10:
        raise HTTPException(400, "WhatsApp inválido.")

    # Verificar OAB duplicada ANTES do insert (mensagem clara)
    existente_oab = await db.buscar_por_oab(oab_numero, oab_seccional)
    if existente_oab and existente_oab["id"] != adv["id"]:
        raise HTTPException(409, "Esta OAB já possui um monitoramento ativo. Entre em contato com o suporte se for você.")

    # Confirma que o código foi verificado
    reg = _onboarding_codigos.get(wpp_notif)
    if not reg or _t.time() > reg["exp"]:
        raise HTTPException(400, "Verificação do WhatsApp expirada. Volte e reenvie o código.")
    _onboarding_codigos.pop(wpp_notif, None)

    lembrete_fds = briefing_dias == "todos"

    ok = await db.salvar_onboarding(
        advogado_id=adv["id"],
        oab_numero=oab_numero,
        oab_seccional=oab_seccional,
        tratamento=tratamento,
        whatsapp_notificacao=wpp_notif,
        horario_briefing=horario,
        lembrete_fds=lembrete_fds,
    )
    if not ok:
        raise HTTPException(409, "Esta OAB já possui um monitoramento ativo.")'''

if OLD_SALVAR in src:
    src = src.replace(OLD_SALVAR, NEW_SALVAR)
    print("✅ PATCH 4: onboarding/salvar — limpeza OAB + duplicata clara")
else:
    print("❌ PATCH 4: trecho não encontrado — verifique manualmente")

# ─────────────────────────────────────────────────────────────────────────────
# Escrever resultado
# ─────────────────────────────────────────────────────────────────────────────
APP.write_text(src)
print("\n✅ web/app.py atualizado com sucesso.")
