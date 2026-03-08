"""
web/onboarding.py — Prazu Fase 2
Lógica do bot WhatsApp (Z-API) e jobs do Cloud Scheduler.
"""

import os
import logging
import asyncio
from datetime import datetime, timezone

import database_gcp as db
from web.zapi import zapi as _evo_client

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
    import re
    from datetime import datetime, date

    _TRIBUNAL_UF = {
        "8.01":"AC","8.02":"AL","8.03":"AP","8.04":"AM","8.05":"BA","8.06":"CE",
        "8.07":"DF","8.08":"ES","8.09":"GO","8.10":"MA","8.11":"MT","8.12":"MS",
        "8.13":"MG","8.14":"PA","8.15":"PB","8.16":"PR","8.17":"PE","8.18":"PI",
        "8.19":"RJ","8.20":"RN","8.21":"RS","8.22":"RO","8.23":"RR","8.24":"SC",
        "8.25":"SE","8.26":"SP","8.27":"TO",
    }
    PRAZOS_POR_TIPO = {
        "intimacao": 15, "citacao": 15, "edital": 20,
        "notificacao": 15, "lista de distribuicao": 0,
    }

    def _extrair_uf_do_cnj(numero):
        digits = re.sub(r"\D", "", numero)
        if len(digits) != 20:
            return ""
        return _TRIBUNAL_UF.get(f"{digits[13]}.{digits[14:16]}", "")

    def _extrair_comarca_da_vara(vara):
        if not vara or vara == "N/I":
            return ""
        # Padrão 1: "Comarca de Nova Lima"
        m = re.search(r"[Cc]omarca\s+de\s+(.+?)(?:\s*[-/]|$)", vara)
        if m:
            return m.group(1).strip().rstrip(".")
        # Padrão 2: "Turma/Vara/Juizado...de Belo Horizonte" — ancora no fim
        m = re.search(r"(?:Vara|Juizado|Turma).*?\bde\s+([A-Z][a-záéíóúãõçê]+(?:\s+(?:de|do|da|dos|das|e)?\s*[A-Z][a-záéíóúãõçê]+)*)\s*$", vara)
        if m:
            return m.group(1).strip()
        # Padrão 3: "Vara - Cidade" — última parte após " - "
        parts = vara.split(" - ")
        if len(parts) >= 2:
            last = parts[-1].strip()
            if last and last[0].isupper() and len(last) > 3 and not any(x in last.lower() for x in ["vara", "juiz", "turma", "seção", "cível", "criminal"]):
                return last.rstrip(".")
        return ""

    def _calcular_prazos_djen(comunicacoes, comarca, uf=""):
        from prazos_calc import calcular_prazo_completo
        hoje = date.today()
        resultados = []
        for c in comunicacoes:
            tipo = (c.get("tipo") or "").lower()
            tipo_norm = tipo.replace("\xe7\xe3o","cao").replace("\xe3o","ao")
            dias = PRAZOS_POR_TIPO.get(tipo_norm, 15)
            if dias == 0:
                c["prazo_info"] = None
                resultados.append(c)
                continue
            data_disp_str = c.get("data_disponibilizacao", "")
            if not data_disp_str:
                c["prazo_info"] = None
                resultados.append(c)
                continue
            try:
                data_disp = datetime.strptime(data_disp_str, "%Y-%m-%d").date()
            except ValueError:
                c["prazo_info"] = None
                resultados.append(c)
                continue
            resultado = calcular_prazo_completo(data_disp, dias, uf=uf, comarca_processo=comarca)
            venc = datetime.strptime(resultado["data_vencimento"], "%Y-%m-%d").date()
            dias_restantes = (venc - hoje).days
            if dias_restantes < 0:
                status, emoji = f"VENCIDO ha {abs(dias_restantes)}d", "🔴"
            elif dias_restantes == 0:
                status, emoji = "VENCE HOJE", "🔴"
            elif dias_restantes <= 3:
                status, emoji = f"Vence em {dias_restantes}d", "🟡"
            else:
                status, emoji = f"Vence em {dias_restantes}d", "🟢"
            c["prazo_info"] = {
                "dias_prazo": dias,
                "data_publicacao": resultado["data_publicacao"],
                "data_inicio": resultado["data_inicio_prazo"],
                "data_vencimento": resultado["data_vencimento"],
                "dias_restantes": dias_restantes,
                "status": status,
                "emoji": emoji,
            }
            resultados.append(c)
        return resultados

    log.info(f"_buscar_djen: adv_id={adv_id} oab={oab_num}/{oab_uf}")
    try:
        loop = asyncio.get_event_loop()
        from djen import consultar_djen_por_oab
        from datajud import consultar_processo
        comunicacoes = await loop.run_in_executor(None, consultar_djen_por_oab, oab_num, oab_uf, 90)
        if not comunicacoes:
            if phone:
                await _evo_client.enviar(phone, "Nenhuma publicacao encontrada no DJEN nos ultimos 90 dias.")
            return
        numeros_cnj = list({c["numero_processo"] for c in comunicacoes if c.get("numero_processo")})
        adv = await db.buscar_por_id(adv_id)
        comarca = adv.get("comarca", "") if adv else ""
        uf = adv.get("oab_seccional", oab_uf) if adv else oab_uf
        comunicacoes_com_prazo = _calcular_prazos_djen(comunicacoes, comarca, uf)
        processos_existentes = {p["numero"] for p in await db.listar_processos_com_prazos(adv_id)}
        novos = 0
        erros = 0
        for num_cnj in numeros_cnj:
            if num_cnj in processos_existentes:
                continue
            try:
                dados = await loop.run_in_executor(None, consultar_processo, num_cnj)
            except Exception:
                dados = None
            if dados:
                autor = ", ".join(dados.get("partes_ativo", [])) or ""
                reu = ", ".join(dados.get("partes_passivo", [])) or ""
                partes = f"{autor} vs {reu}" if autor and reu else autor or reu or "N/I"
                vara = dados.get("vara", "N/I")
                tribunal = dados.get("tribunal", "")
            else:
                erros += 1
                pub = next((c for c in comunicacoes if c.get("numero_processo") == num_cnj), {})
                vara = pub.get("orgao") or pub.get("classe") or "N/I"
                partes = pub.get("classe") or pub.get("tipo", "N/I")
                tribunal = pub.get("tribunal", "")
            comarca_proc = _extrair_comarca_da_vara(vara)
            processo_id = await db.criar_ou_atualizar_processo(
                advogado_id=adv_id, numero=num_cnj, partes=partes,
                vara=vara, tribunal=tribunal,
                comarca=comarca_proc or comarca, fonte="djen",
            )
            novos += 1
            pub = next((c for c in comunicacoes_com_prazo if c.get("numero_processo") == num_cnj), {})
            prazo_info = pub.get("prazo_info")
            if prazo_info and prazo_info.get("data_vencimento"):
                tipo_prazo = (pub.get("tipo") or "intimacao").lower()
                await db.criar_prazo_processo(
                    processo_id=processo_id,
                    tipo=tipo_prazo,
                    data_inicio=prazo_info["data_inicio"],
                    data_fim=prazo_info["data_vencimento"],
                    dias_totais=prazo_info["dias_prazo"],
                )

        for c in comunicacoes:
            existe = await db.comunicacao_djen_existe(adv_id, c["numero_processo"], c.get("data_disponibilizacao", ""))
            if not existe:
                await db.salvar_comunicacao_djen(
                    advogado_id=adv_id,
                    numero_processo=c["numero_processo"],
                    tribunal=c.get("tribunal", ""),
                    conteudo=c.get("conteudo", ""),
                    data_disponibilizacao=c.get("data_disponibilizacao", ""),
                    data_publicacao=c.get("data_publicacao", ""),
                    tipo_comunicacao=c.get("tipo", ""),
                )
        await db.atualizar_ultima_busca_djen(adv_id)
        if phone:
            msg = f"Busca DJEN concluida! {len(numeros_cnj)} processo(s) encontrado(s), {novos} novo(s) importado(s)."
            if erros:
                msg += f" {erros} sem dados no DataJud."
            msg += " Acesse o dashboard para ver seus prazos."
            await _evo_client.enviar(phone, msg)
        log.info(f"_buscar_djen OK: {novos} novos, {erros} erros")
    except Exception as e:
        log.error(f"_buscar_djen erro: {e}", exc_info=True)
        if phone:
            try:
                await _evo_client.enviar(phone, "Erro ao buscar processos. Tente novamente em alguns minutos.")
            except Exception:
                pass

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



async def enviar_boas_vindas(adv: dict) -> None:
    """Enviada uma unica vez, ~2 min apos o primeiro acesso ao dashboard."""
    phone = adv.get("whatsapp_notificacao") or adv.get("whatsapp")
    if not phone:
        return
    tratamento = adv.get("tratamento") or "Dr(a)."
    nome = adv["nome"].split()[0]
    try:
        saudacao = (
            f"👋 Ola, {tratamento} *{nome}*!\n\n"
            f"Acabou de chegar aqui o seu primeiro resumo de prazos da Prazu. 🎉\n\n"
            f"Me salva na sua agenda — todo dia eu vou te enviar um resumo "
            f"dos seus processos para que voce *nunca mais perca um prazo*. ⚖️\n\n"
            f"──────────────────\n"
        )
        await _evo_client.enviar(phone, saudacao)
        import asyncio as _asyncio
        await _asyncio.sleep(1)
        await _enviar_resumo(phone, adv)
        await db.log_whatsapp(adv["id"], "outbound", "boas_vindas", "primeiro resumo enviado")
    except Exception as e:
        log.error(f"Erro boas_vindas {phone}: {e}")

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
