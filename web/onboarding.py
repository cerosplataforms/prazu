"""
web/onboarding.py — Prazu Fase 2
Lógica do bot WhatsApp (Z-API) e jobs do Cloud Scheduler.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone


log = logging.getLogger(__name__)

_estados: dict = {}

def _get(phone): return _estados.get(phone, {})
def _set(phone, step, dados=None): _estados[phone] = {"step": step, "dados": dados or {}}
def _clear(phone): _estados.pop(phone, None)


async def processar_mensagem_zapi(payload: dict):
    if payload.get("type") != "ReceivedCallback": return
    phone = payload.get("phone", "").replace("+", "").replace("-", "").replace(" ", "")
    msg = payload.get("message", {})
    texto = (msg.get("text") or msg.get("body") or msg.get("caption") or "").strip()
    if not phone or not texto: return
    log.info(f"WhatsApp de {phone}: {texto[:50]}")
    adv = await db.buscar_por_whatsapp(phone)
    await db.log_whatsapp(adv["id"] if adv else None, "inbound", "mensagem", texto)
    estado = _get(phone)
    step = estado.get("step")
    if step and step.startswith("onboarding_"):
        await _handle_onboarding(phone, texto, step, estado.get("dados", {}))
    elif adv:
        await _handle_conversa(phone, adv, texto)
    else:
        await _iniciar_onboarding(phone)


async def _iniciar_onboarding(phone: str):
    await _evo_client.enviar(phone,
        "👋 Olá! Eu sou o *Prazu*, seu copiloto jurídico.\n\n"
        "Monitoro seus prazos processuais e te aviso todo dia via WhatsApp — "
        "com feriados forenses de *2.374 comarcas* em todo o Brasil.\n\n"
        "Vamos começar? Me diga seu *nome completo*."
    )
    _set(phone, "onboarding_nome")


async def _handle_onboarding(phone, texto, step, dados):
    if step == "onboarding_nome":
        dados["nome"] = texto
        await _evo_client.enviar(phone, f"Prazer, Dr(a). *{texto}*! ✨\n\nMe informe sua *OAB* com estado.\nEx: `12345/MG`")
        _set(phone, "onboarding_oab", dados)

    elif step == "onboarding_oab":
        if "/" not in texto:
            await _evo_client.enviar(phone, "Use o formato `numero/UF` — ex: `12345/MG`"); return
        num, uf = texto.split("/", 1)
        num = num.strip(); uf = uf.strip().upper().rstrip(".,;:!?")
        if len(uf) != 2:
            await _evo_client.enviar(phone, "Seccional inválida. Use a sigla do estado (MG, SP, RJ...)"); return
        existente = await db.buscar_por_oab(num, uf)
        if existente:
            await db.atualizar_whatsapp(existente["id"], phone, confirmado=True)
            _clear(phone)
            await _evo_client.enviar(phone, f"✅ OAB *{num}/{uf}* encontrada!\nOlá de volta, Dr(a). *{existente['nome']}*!\nDigite *prazos* para ver seu resumo de hoje.")
            return
        dados.update({"oab_numero": num, "oab_seccional": uf})
        await _evo_client.enviar(phone, f"OAB *{num}/{uf}* anotado! ✅\n\nAgora preciso de um *e-mail* para criar sua conta.")
        _set(phone, "onboarding_email", dados)

    elif step == "onboarding_email":
        if "@" not in texto or "." not in texto:
            await _evo_client.enviar(phone, "E-mail inválido. Digite um e-mail válido."); return
        dados["email"] = texto.lower().strip()
        await _evo_client.enviar(phone, "Ótimo! Crie uma *senha* para sua conta Prazu.\n(mínimo 6 caracteres)")
        _set(phone, "onboarding_senha", dados)

    elif step == "onboarding_senha":
        if len(texto) < 6:
            await _evo_client.enviar(phone, "Senha muito curta. Use pelo menos 6 caracteres."); return
        dados["senha"] = texto
        adv_id = await db.criar_advogado(
            nome=dados["nome"], email=dados["email"], senha=dados["senha"],
            oab_numero=dados["oab_numero"], oab_seccional=dados["oab_seccional"], whatsapp=phone,
        )
        if not adv_id:
            await _evo_client.enviar(phone, "❌ Esse e-mail já está cadastrado.\nDigite outro e-mail.")
            _set(phone, "onboarding_email", dados); return
        await db.confirmar_whatsapp(adv_id)
        _clear(phone)
        await _evo_client.enviar(phone,
            f"🎉 Conta criada, Dr(a). *{dados['nome']}*!\n\n"
            "✅ *7 dias grátis* — sem cartão de crédito\n\n"
            "Buscando seus processos no DJEN... ⏳"
        )
        asyncio.create_task(_buscar_djen(adv_id, phone, dados["oab_numero"], dados["oab_seccional"]))


async def _buscar_djen(adv_id, phone, oab_num, oab_uf):
    try:
        loop = asyncio.get_event_loop()
        from djen import consultar_djen_por_oab
        comunicacoes = await loop.run_in_executor(None, consultar_djen_por_oab, oab_num, oab_uf, 30)
        if not comunicacoes:
            await _evo_client.enviar(phone, "Nenhuma publicação encontrada nos últimos 30 dias.\nDigite *buscar* quando quiser tentar novamente.")
            return
        await _evo_client.enviar(phone,
            f"📬 Encontrei *{len(comunicacoes)} publicação(ões)* no DJEN!\n\n"
            "Acesse *prazu.com.br/dashboard* para ver os prazos calculados.\n"
            "Amanhã às *7h* você recebe seu primeiro aviso diário. ☀️"
        )
        await db.atualizar_ultima_busca_djen(adv_id)
    except Exception as e:
        log.error(f"Erro DJEN onboarding {phone}: {e}")
        await _evo_client.enviar(phone, "Não consegui buscar o DJEN agora. Digite *buscar* para tentar novamente.")


async def _handle_conversa(phone, adv, texto):
    tl = texto.lower().strip()
    if not await db.pode_usar(adv["id"]):
        await _evo_client.enviar(phone, "⚠️ Seu período de teste encerrou.\nAcesse *prazu.com.br* para assinar."); return
    if tl in ("prazos", "resumo", "briefing", "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"):
        await _enviar_resumo(phone, adv)
    elif tl in ("buscar", "atualizar", "djen"):
        await _evo_client.enviar(phone, "🔍 Buscando publicações no DJEN...")
        asyncio.create_task(_buscar_djen(adv["id"], phone, adv["oab_numero"], adv["oab_seccional"]))
    elif tl.startswith("comarca "):
        nova = texto[8:].strip()
        await db.atualizar_comarca(adv["id"], nova)
        await _evo_client.enviar(phone, f"✅ Comarca atualizada para *{nova}*")
    else:
        await _evo_client.enviar(phone, "🤔 Processando...")
        try:
            processos = await db.listar_processos_com_prazos(adv["id"])
            from ia import responder_pergunta
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, responder_pergunta, texto, adv["nome"], processos, adv.get("comarca", ""))
            await _evo_client.enviar(phone, resp)
        except Exception as e:
            log.error(f"Erro IA {phone}: {e}")
            await _evo_client.enviar(phone, "Não consegui processar sua pergunta agora. Tente novamente.")


async def _enviar_resumo(phone, adv):
    try:
        processos = await db.listar_processos_com_prazos(adv["id"])
        hoje = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        header = f"☀️ Bom dia, Dr(a). *{adv['nome']}*! ({hoje})\n\n"
        if not processos:
            await _evo_client.enviar(phone, header + "Você não tem processos monitorados ainda.\nDigite *buscar* para importar pela OAB."); return
        from ia import gerar_briefing
        loop = asyncio.get_event_loop()
        texto = await loop.run_in_executor(None, gerar_briefing, adv["nome"], processos, adv.get("comarca", ""))
        await _evo_client.enviar(phone, header + texto)
        await db.log_whatsapp(adv["id"], "outbound", "resumo", texto[:200])
    except Exception as e:
        log.error(f"Erro resumo {phone}: {e}")


# — Jobs —

async def enviar_briefing_todos() -> int:
    advogados = await db.listar_advogados_ativos()
    enviados = 0
    for adv in advogados:
        if not adv.get("whatsapp") or not adv.get("zapi_confirmado"): continue
        if not await db.pode_usar(adv["id"]): continue
        try:
            await _enviar_resumo(adv["whatsapp"], adv)
            enviados += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            log.error(f"Erro briefing {adv['nome']}: {e}")
    return enviados


async def enviar_lembrete_trial() -> int:
    advogados = await db.advogados_trial_expirando(dias=2)
    enviados = 0
    for adv in advogados:
        try:
            await _evo_client.enviar(adv["whatsapp"],
                f"⏰ Dr(a). *{adv['nome']}*, seu teste encerra em *2 dias*.\n\n"
                "Para continuar, assine em *prazu.com.br* por apenas *R$ 49,90/mês*."
            )
            enviados += 1
        except Exception as e:
            log.error(f"Erro lembrete {adv['nome']}: {e}")
    return enviados


async def monitorar_djen_todos() -> int:
    from datetime import timedelta
    advogados = await db.listar_advogados_ativos()
    notificados = 0; agora = datetime.now(timezone.utc)
    for adv in advogados:
        if not adv.get("whatsapp") or not adv.get("zapi_confirmado"): continue
        ultima = adv.get("ultima_busca_djen")
        if ultima:
            if hasattr(ultima, "tzinfo") and ultima.tzinfo is None:
                ultima = ultima.replace(tzinfo=timezone.utc)
            if (agora - ultima).days < 5: continue
        asyncio.create_task(_buscar_djen(adv["id"], adv["whatsapp"], adv["oab_numero"], adv["oab_seccional"]))
        notificados += 1
        await asyncio.sleep(1)
    return notificados
