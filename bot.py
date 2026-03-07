"""
PrazorBot — Copiloto Juridico de Prazos
Busca processos pela OAB, calcula prazos com feriados, briefing com IA.
Lembrete diario configuravel por horario e preferencia de fim de semana.
"""
import os, logging, asyncio, re
from datetime import datetime, date, time as dtime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from ia import gerar_briefing, responder_pergunta
from database import Database
from cal_forense.calendar_store import CalendarStore
from cal_forense.calendar_resolver import CalendarResolver
from prazos_calc import calcular_prazo_completo
from djen import consultar_djen_por_oab, formatar_comunicacoes_telegram, importar_comunicacoes_para_banco, verificar_prazo_cumprido
from datajud import consultar_processo, formatar_numero_cnj

_cal_store = CalendarStore("cal_forense/calendar_v2.db")
_cal_resolver = CalendarResolver(_cal_store)

def _get_comarcas_disponiveis(uf="MG"):
    return sorted(_cal_store.listar_comarcas(uf))


# ============================================================
# PARSER DE COMARCA — extrai do nome da vara e do CNJ
# ============================================================
_TRIBUNAL_UF = {
    "8.01":"RJ","8.02":"AC","8.03":"AL","8.04":"AP","8.05":"BA","8.06":"CE",
    "8.07":"DF","8.08":"ES","8.09":"GO","8.10":"MA","8.11":"MT","8.12":"MS",
    "8.13":"MG","8.14":"PA","8.15":"PB","8.16":"PR","8.17":"PE","8.18":"PI",
    "8.19":"RJ","8.20":"RN","8.21":"RS","8.22":"RO","8.23":"RR","8.24":"SC",
    "8.25":"SE","8.26":"SP","8.27":"TO",
}

def extrair_uf_do_cnj(numero: str) -> str:
    digits = re.sub(r'\D', '', numero)
    if len(digits) != 20:
        return ""
    key = f"{digits[13]}.{digits[14:16]}"
    return _TRIBUNAL_UF.get(key, "")

def extrair_comarca_da_vara(vara: str) -> str:
    if not vara or vara == "N/I":
        return ""
    m = re.search(r'[Cc]omarca\s+de\s+(.+?)(?:\s*[-/]|$)', vara)
    if m:
        return m.group(1).strip().rstrip('.')
    m = re.search(r'(?:Vara|Juizado|Turma).*?\bde\s+([A-Z][a-záéíóúãõçê]+(?:\s+(?:de|do|da|dos|das|e)?\s*[A-Z][a-záéíóúãõçê]+)*)\s*$', vara)
    if m:
        return m.group(1).strip()
    parts = vara.split(" - ")
    if len(parts) >= 2:
        last = parts[-1].strip()
        if last and last[0].isupper() and len(last) > 3 and not any(x in last.lower() for x in ["vara","juiz","turma","seção","cível","criminal"]):
            return last.rstrip('.')
    return ""

def _resolver_comarca_processo(processo: dict) -> tuple:
    """Retorna (uf, comarca) do processo, extraindo do CNJ e da vara."""
    uf = extrair_uf_do_cnj(processo.get("numero", ""))
    comarca = processo.get("comarca") or ""
    if not comarca:
        comarca = extrair_comarca_da_vara(processo.get("vara", ""))
    return uf, comarca

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)
db = Database()

# Fuso horario BRT (UTC-3)
BRT_OFFSET = timedelta(hours=-3)


# ============================================================
# HELPERS
# ============================================================
def _horario_buttons():
    """Gera teclado de horarios de 6h a 22h."""
    rows = []
    row = []
    for h in range(6, 23):
        label = f"{h:02d}:00"
        row.append(InlineKeyboardButton(label, callback_data=f"set_hora_{h:02d}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _sim_nao_fds():
    """Botoes sim/nao para lembrete no fim de semana."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Sim, me lembre", callback_data="fds_sim"),
         InlineKeyboardButton("Nao, so dias uteis", callback_data="fds_nao")]
    ])


async def _send(update, text, **kw):
    """Envia mensagem de forma segura."""
    try:
        return await update.message.reply_text(text, **kw)
    except Exception:
        return await update.message.reply_text(text)


# ============================================================
# /start — Onboarding conversacional
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = db.get_advogado_by_chat_id(chat_id)

    if user:
        total = db.contar_processos(user["id"])
        hora = user.get("horario_briefing", "07:00")
        fds = "sim" if user.get("lembrete_fds", 0) else "nao"
        await _send(update,
            f"Ola, Dr(a). {user['nome']}! Bom te ver de volta.\n\n"
            f"OAB: *{user.get('oab_numero', '?')}/{user.get('oab_seccional', '?')}*\n"
            f"Processos: *{total}*\n"
            f"Lembrete diario: *{hora}* (fds: {fds})\n\n"
            f"O que precisa hoje?\n\n"
            f"/briefing — Resumo agora\n"
            f"/buscar — Atualizar processos\n"
            f"/calcular — Calcular prazo\n"
            f"/config — Mudar horario do lembrete\n"
            f"/ajuda — Todos os comandos\n\n"
            f"Ou me pergunte qualquer coisa!",
            parse_mode="Markdown")
    else:
        await _send(update,
            "Ola! Eu sou o *PrazorBot*, seu copiloto juridico.\n\n"
            "Monitoro seus prazos processuais e te lembro todo dia "
            "dos vencimentos, considerando feriados forenses "
            "de *1.700+ comarcas* em todo o Brasil.\n\n"
            "Vamos configurar? Me diga seu *nome completo*.\n\n"
            "Exemplo: `Maria Silva`",
            parse_mode="Markdown")
        context.user_data["step"] = "aguardando_nome"


# ============================================================
# Onboarding — fluxo conversacional
# ============================================================
async def handle_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # --- NOME ---
    if step == "aguardando_nome":
        context.user_data["nome"] = text
        await _send(update,
            f"Prazer, Dr(a). {text}!\n\n"
            f"Agora me diga seu *numero da OAB* com a seccional.\n\n"
            f"Exemplo: `12345/MG`",
            parse_mode="Markdown")
        context.user_data["step"] = "aguardando_oab"

    # --- OAB ---
    elif step == "aguardando_oab":
        if "/" not in text:
            await _send(update, "Use o formato `numero/UF`\nExemplo: `12345/MG`", parse_mode="Markdown")
            return
        numero, seccional = text.split("/", 1)
        numero = numero.strip()
        seccional = seccional.strip().upper().rstrip(".,;:!?")
        if len(seccional) != 2:
            await _send(update, "Seccional invalida. Use a sigla do estado (MG, SP, RJ...).")
            return
        context.user_data["oab_numero"] = numero
        context.user_data["oab_seccional"] = seccional
        await _send(update,
            f"OAB *{numero}/{seccional}* — anotado!\n\n"
            f"Agora vamos configurar seu *lembrete diario*.\n"
            f"Que horas voce quer receber o resumo dos seus prazos?\n\n"
            f"Escolha o horario:",
            parse_mode="Markdown")
        await update.message.reply_text(
            "Horario do lembrete:",
            reply_markup=_horario_buttons())
        context.user_data["step"] = "aguardando_horario"

    # --- COMARCA (texto livre, se pedir) ---
    elif step == "aguardando_comarca_texto":
        db.atualizar_comarca(chat_id, text)
        await _send(update, f"Comarca atualizada: *{text}*", parse_mode="Markdown")
        context.user_data["step"] = None


# --- Callback: horario do lembrete ---
async def handle_set_hora_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    hora = q.data.replace("set_hora_", "")
    context.user_data["horario_escolhido"] = f"{hora}:00"

    await q.edit_message_text(
        f"Lembrete configurado para *{hora}:00* todos os dias.\n\n"
        f"Voce quer receber o lembrete nos *fins de semana* tambem?\n"
        f"(sabado e domingo)",
        parse_mode="Markdown",
        reply_markup=_sim_nao_fds())
    context.user_data["step"] = "aguardando_fds"


# --- Callback: fim de semana ---
async def handle_fds_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    fds = 1 if q.data == "fds_sim" else 0
    horario = context.user_data.get("horario_escolhido", "07:00")
    chat_id = q.message.chat_id
    step = context.user_data.get("step")

    # Se é onboarding (novo usuario) → cadastra
    if step == "aguardando_fds" and context.user_data.get("oab_numero"):
        uf = context.user_data.get("oab_seccional", "MG")
        db.criar_advogado(
            chat_id=chat_id,
            nome=context.user_data["nome"],
            oab_numero=context.user_data["oab_numero"],
            oab_seccional=uf,
            comarca="",
            horario_briefing=horario,
            lembrete_fds=fds)
        context.user_data["step"] = None

        fds_txt = "inclusive fins de semana" if fds else "somente dias uteis"
        await q.edit_message_text(
            f"Tudo configurado, Dr(a). {context.user_data['nome']}!\n\n"
            f"OAB: *{context.user_data['oab_numero']}/{uf}*\n"
            f"Lembrete: *{horario}* ({fds_txt})\n\n"
            f"Agora vou buscar suas publicacoes no DJEN...\n"
            f"Aguarde!",
            parse_mode="Markdown")

        # Busca automatica
        await _buscar_e_salvar_from_bot(
            context.bot, chat_id,
            context.user_data["oab_numero"], uf)

        # Agenda o lembrete
        _agendar_lembrete(context.application, chat_id, horario, fds)

    # Se é reconfig via /config
    elif step == "reconfig_fds":
        db.atualizar_horario(chat_id, horario)
        db.atualizar_lembrete_fds(chat_id, fds)
        context.user_data["step"] = None

        fds_txt = "inclusive fins de semana" if fds else "somente dias uteis"
        await q.edit_message_text(
            f"Lembrete atualizado!\n\n"
            f"Horario: *{horario}*\n"
            f"Fim de semana: *{'sim' if fds else 'nao'}*\n\n"
            f"Voce recebera o resumo dos seus prazos {fds_txt}.",
            parse_mode="Markdown")

        _agendar_lembrete(context.application, chat_id, horario, fds)


# ============================================================
# LEMBRETE DIÁRIO — Scheduler
# ============================================================
def _agendar_lembrete(app, chat_id, horario_str, lembrete_fds):
    """Agenda job diario de briefing para um usuario."""
    job_name = f"briefing_{chat_id}"

    # Remove job anterior se existir
    jobs = app.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()

    hora = int(horario_str.split(":")[0])
    # Converte BRT → UTC (BRT = UTC-3)
    hora_utc = (hora + 3) % 24

    app.job_queue.run_daily(
        _job_briefing_diario,
        time=dtime(hour=hora_utc, minute=0, second=0),
        name=job_name,
        data={"chat_id": chat_id, "lembrete_fds": lembrete_fds},
    )
    logger.info(f"Lembrete agendado: chat_id={chat_id} hora={horario_str} BRT (UTC {hora_utc}:00) fds={lembrete_fds}")


async def _job_briefing_diario(context: ContextTypes.DEFAULT_TYPE):
    """Executado pelo job_queue. Envia briefing se for dia permitido."""
    data = context.job.data
    chat_id = data["chat_id"]
    lembrete_fds = data.get("lembrete_fds", 0)

    # Verifica dia da semana
    hoje = datetime.now() + BRT_OFFSET
    dia_semana = hoje.weekday()  # 0=seg ... 6=dom
    if dia_semana >= 5 and not lembrete_fds:
        logger.info(f"Briefing pulado (fim de semana, fds desligado) para {chat_id}")
        return

    user = db.get_advogado_by_chat_id(chat_id)
    if not user:
        return

    processos = db.listar_processos_com_prazos(user["id"])
    if not processos:
        # Envia lembrete mesmo sem processos
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Bom dia, Dr(a). {user['nome']}!\n\n"
                 f"Voce nao tem processos monitorados ainda.\n"
                 f"Use /buscar para importar pela OAB!",
            parse_mode="Markdown")
        return

    comarca = user.get("comarca", "")
    uf = user.get("oab_seccional", "MG")

    # Consulta DJEN para prazos atuais
    loop = asyncio.get_event_loop()
    try:
        comunicacoes = await loop.run_in_executor(
            None, consultar_djen_por_oab, user["oab_numero"], user["oab_seccional"], 30)
        if comunicacoes:
            comunicacoes = _calcular_prazos_djen(comunicacoes, comarca, uf)
            for proc in processos:
                prazos_proc = []
                for c in comunicacoes:
                    if c.get("numero_processo") == proc.get("numero") and c.get("prazo_info"):
                        pi = c["prazo_info"]
                        prazos_proc.append({
                            "tipo": c.get("tipo", "intimacao"),
                            "data_fim": pi["data_vencimento"],
                            "data_fim_util": pi["data_vencimento"],
                            "fatal": True, "contagem": "uteis",
                            "status_emoji": pi["emoji"],
                            "status_texto": pi["status"],
                        })
                if prazos_proc and isinstance(proc, dict):
                    proc["prazos"] = prazos_proc
    except Exception as e:
        logger.warning(f"Erro DJEN no lembrete: {e}")

    texto = await loop.run_in_executor(None, gerar_briefing, user["nome"], processos, comarca)

    hoje_fmt = hoje.strftime("%d/%m/%Y")
    header = f"Bom dia, Dr(a). {user['nome']}! ({hoje_fmt})\n\n"

    try:
        await context.bot.send_message(chat_id=chat_id, text=header + texto, parse_mode="Markdown")
    except Exception:
        await context.bot.send_message(chat_id=chat_id, text=header + texto)

    logger.info(f"Lembrete diario enviado para {user['nome']} ({chat_id})")


def _restaurar_lembretes(app):
    """Restaura jobs de lembrete para todos os usuarios ativos ao iniciar."""
    advogados = db.listar_advogados_ativos()
    for adv in advogados:
        horario = adv.get("horario_briefing", "07:00")
        fds = adv.get("lembrete_fds", 0)
        _agendar_lembrete(app, adv["chat_id"], horario, fds)
    logger.info(f"Restaurados {len(advogados)} lembrete(s) diario(s)")

    # Agenda verificação de prazos urgentes a cada 3 horas
    app.job_queue.run_repeating(
        _job_notificacao_urgente,
        interval=10800,  # 3 horas
        first=60,        # começa 1 min após o boot
        name="notificacao_urgente",
    )
    logger.info("Notificacoes de prazo urgente agendadas (a cada 3h)")

    # Agenda monitoramento DJEN 1x por dia (14h UTC = 11h BRT)
    app.job_queue.run_daily(
        _job_monitorar_djen,
        time=dtime(hour=14, minute=0, second=0),
        name="monitorar_djen",
    )
    logger.info("Monitoramento DJEN agendado (diario 11h BRT, busca a cada 5 dias por usuario)")


# ============================================================
# NOTIFICAÇÕES DE PRAZO URGENTE
# ============================================================
async def _job_notificacao_urgente(context: ContextTypes.DEFAULT_TYPE):
    """Verifica prazos vencendo em 3 dias, 1 dia, e hoje. Notifica se ainda não notificou."""
    advogados = db.listar_advogados_ativos()
    hoje = date.today()

    for adv in advogados:
        try:
            processos = db.listar_processos_com_prazos(adv["id"])
            if not processos:
                continue

            alertas = []
            for proc in processos:
                for prazo in proc.get("prazos", []):
                    if prazo.get("cumprido"):
                        continue
                    try:
                        venc = datetime.strptime(prazo["data_fim"], "%Y-%m-%d").date()
                    except (ValueError, KeyError):
                        continue

                    dias = (venc - hoje).days
                    fatal_txt = "⚡ FATAL" if prazo.get("fatal") else ""
                    tipo = prazo.get("tipo", "Prazo")
                    num = proc.get("numero", "?")[:25]

                    if dias == 0 and not prazo.get("notificado_hoje"):
                        alertas.append(f"🔴 *VENCE HOJE* {fatal_txt}\n   `{num}`\n   {tipo}")
                        db.marcar_prazo_notificado(prazo["id"], "hoje")
                    elif dias == 1 and not prazo.get("notificado_1d"):
                        alertas.append(f"🟡 *Vence AMANHÃ* {fatal_txt}\n   `{num}`\n   {tipo}")
                        db.marcar_prazo_notificado(prazo["id"], "1d")
                    elif dias == 3 and not prazo.get("notificado_3d"):
                        alertas.append(f"🟡 Vence em *3 dias* {fatal_txt}\n   `{num}`\n   {tipo}")
                        db.marcar_prazo_notificado(prazo["id"], "3d")

            if alertas:
                msg = f"⚠️ *Alerta de Prazos, Dr(a). {adv['nome']}!*\n\n"
                msg += "\n\n".join(alertas)
                msg += "\n\n_Use /briefing para detalhes completos._"
                try:
                    await context.bot.send_message(chat_id=adv["chat_id"], text=msg, parse_mode="Markdown")
                except Exception:
                    await context.bot.send_message(chat_id=adv["chat_id"], text=msg)
                logger.info(f"Alerta urgente enviado para {adv['nome']}: {len(alertas)} prazo(s)")

        except Exception as e:
            logger.error(f"Erro notificacao urgente {adv['nome']}: {e}")


# ============================================================
# MONITORAMENTO DJEN — busca novas publicações automaticamente
# ============================================================
async def _job_monitorar_djen(context: ContextTypes.DEFAULT_TYPE):
    """
    Roda 1x por dia. Para cada advogado, verifica se faz 5+ dias
    desde a última busca e, se sim, consulta o DJEN.
    Notifica sobre publicações novas encontradas.
    """
    advogados = db.listar_advogados_ativos()
    hoje = datetime.now()
    loop = asyncio.get_event_loop()

    for adv in advogados:
        try:
            ultima = adv.get("ultima_busca_djen", "")
            if ultima:
                try:
                    dt_ultima = datetime.strptime(ultima, "%Y-%m-%d %H:%M:%S")
                    dias_desde = (hoje - dt_ultima).days
                    if dias_desde < 5:
                        continue  # Ainda não passou 5 dias
                except ValueError:
                    pass  # Formato inválido, busca mesmo

            logger.info(f"Monitoramento DJEN: buscando para {adv['nome']} (OAB {adv['oab_numero']}/{adv['oab_seccional']})")

            comunicacoes = await loop.run_in_executor(
                None, consultar_djen_por_oab, adv["oab_numero"], adv["oab_seccional"], 15)

            if not comunicacoes:
                db.atualizar_ultima_busca(adv["chat_id"])
                continue

            # Filtra só as novas (que não existem no banco)
            novas = []
            for c in comunicacoes:
                num = c.get("numero_processo", "").strip()
                data_disp = c.get("data_disponibilizacao", "")
                if num and data_disp and not db.comunicacao_existe(adv["id"], num, data_disp):
                    novas.append(c)

            if not novas:
                db.atualizar_ultima_busca(adv["chat_id"])
                logger.info(f"  {adv['nome']}: sem publicações novas")
                continue

            # Calcula prazos das novas
            comarca = adv.get("comarca", "")
            uf = adv.get("oab_seccional", "")
            novas = _calcular_prazos_djen(novas, comarca, uf)

            # Importa processos novos se necessário
            numeros_novos = set()
            for c in novas:
                num = c.get("numero_processo", "").strip()
                if num and len(num) >= 20:
                    numeros_novos.add(num)

            if numeros_novos:
                await _importar_processos(adv, novas, numeros_novos, loop)

            # Salva comunicações
            try:
                importar_comunicacoes_para_banco(db, adv["id"], novas)
            except Exception:
                pass

            # Monta alerta
            msg = f"📩 *Novas publicações encontradas, Dr(a). {adv['nome']}!*\n\n"
            for i, c in enumerate(novas[:5], 1):
                num = c.get("numero_processo", "?")
                tipo = c.get("tipo", "Publicação")
                pi = c.get("prazo_info")
                msg += f"*{i}.* `{num}`\n   {tipo}"
                if pi:
                    venc = datetime.strptime(pi["data_vencimento"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    msg += f"\n   Prazo: *vence {venc}* ({pi['status']})"
                msg += "\n\n"

            if len(novas) > 5:
                msg += f"_... e mais {len(novas)-5} publicação(ões)._\n\n"
            msg += "_Use /djen para ver detalhes completos._"

            try:
                await context.bot.send_message(chat_id=adv["chat_id"], text=msg, parse_mode="Markdown")
            except Exception:
                await context.bot.send_message(chat_id=adv["chat_id"], text=msg)

            logger.info(f"  {adv['nome']}: {len(novas)} nova(s) publicação(ões) notificadas")
            db.atualizar_ultima_busca(adv["chat_id"])

        except Exception as e:
            logger.error(f"Erro monitoramento DJEN {adv['nome']}: {e}")


# ============================================================
# /config — Reconfigurar lembrete
# ============================================================
async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    hora_atual = user.get("horario_briefing", "07:00")
    fds = "sim" if user.get("lembrete_fds", 0) else "nao"
    await _send(update,
        f"*Configuracao do lembrete diario*\n\n"
        f"Horario atual: *{hora_atual}*\n"
        f"Fim de semana: *{fds}*\n\n"
        f"Escolha o novo horario:",
        parse_mode="Markdown")
    await update.message.reply_text(
        "Novo horario:",
        reply_markup=_horario_buttons())
    context.user_data["step"] = "reconfig_hora"


async def handle_reconfig_hora_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Chamado quando /config e usuario escolhe novo horario."""
    q = update.callback_query
    await q.answer()
    hora = q.data.replace("set_hora_", "")
    context.user_data["horario_escolhido"] = f"{hora}:00"

    await q.edit_message_text(
        f"Novo horario: *{hora}:00*\n\n"
        f"Quer receber nos *fins de semana* tambem?",
        parse_mode="Markdown",
        reply_markup=_sim_nao_fds())
    context.user_data["step"] = "reconfig_fds"


# ============================================================
# /buscar
# ============================================================
async def buscar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = db.get_advogado_by_chat_id(chat_id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    await _send(update, f"Buscando publicacoes para OAB {user['oab_numero']}/{user['oab_seccional']}...")
    await _buscar_e_salvar_msg(update, chat_id, user["oab_numero"], user["oab_seccional"])


async def _buscar_e_salvar_msg(update, chat_id, numero_oab, estado_oab):
    """Busca via DJEN e manda resultado como reply."""
    user = db.get_advogado_by_chat_id(chat_id)
    if not user:
        return
    loop = asyncio.get_event_loop()
    comunicacoes = await loop.run_in_executor(
        None, consultar_djen_por_oab, numero_oab, estado_oab)

    if not comunicacoes:
        await _send(update,
            "Nao encontrei publicacoes no DJEN para essa OAB.\n\n"
            "Possiveis motivos:\n"
            "- Nao ha publicacoes recentes\n"
            "- O site pode estar fora do ar\n\n"
            "Use /adicionar para cadastrar processos manualmente.")
        return

    numeros_cnj = set()
    for c in comunicacoes:
        num = c.get("numero_processo", "").strip()
        if num and len(num) >= 20:
            numeros_cnj.add(num)

    if not numeros_cnj:
        await _send(update,
            f"Encontrei {len(comunicacoes)} publicacao(oes), "
            f"mas sem numeros CNJ validos.\n"
            f"Use /adicionar para cadastrar manualmente.")
        return

    await _send(update,
        f"*{len(comunicacoes)}* publicacao(oes), *{len(numeros_cnj)}* processo(s).\n"
        f"Consultando DataJud...", parse_mode="Markdown")

    novos, erros = await _importar_processos(user, comunicacoes, numeros_cnj, loop)

    try:
        importar_comunicacoes_para_banco(db, user["id"], comunicacoes)
    except Exception as e:
        logger.error(f"Erro salvar comunicacoes: {e}")

    total = db.contar_processos(user["id"])
    msg = f"*{novos} processo(s) importados!* Total: *{total}*\n\n"
    if erros:
        msg += f"_({erros} sem detalhes no DataJud)_\n"
    msg += "Use /meus\\_processos para ver.\nUse /briefing para o resumo com IA!"
    await _send(update, msg, parse_mode="Markdown")
    db.atualizar_ultima_busca(chat_id)


async def _buscar_e_salvar_from_bot(bot, chat_id, numero_oab, estado_oab):
    """Busca via DJEN e envia resultado direto pelo bot (sem update)."""
    user = db.get_advogado_by_chat_id(chat_id)
    if not user:
        return
    loop = asyncio.get_event_loop()
    comunicacoes = await loop.run_in_executor(
        None, consultar_djen_por_oab, numero_oab, estado_oab)

    if not comunicacoes:
        await bot.send_message(chat_id=chat_id,
            text="Nao encontrei publicacoes no DJEN agora.\n"
                 "Use /buscar mais tarde ou /adicionar manualmente.")
        return

    numeros_cnj = {c.get("numero_processo", "").strip()
                   for c in comunicacoes
                   if c.get("numero_processo", "").strip() and len(c.get("numero_processo", "")) >= 20}

    if not numeros_cnj:
        await bot.send_message(chat_id=chat_id,
            text=f"Encontrei {len(comunicacoes)} publicacao(oes), sem numeros CNJ validos.")
        return

    novos, erros = await _importar_processos(user, comunicacoes, numeros_cnj, loop)

    try:
        importar_comunicacoes_para_banco(db, user["id"], comunicacoes)
    except Exception:
        pass

    total = db.contar_processos(user["id"])
    await bot.send_message(chat_id=chat_id,
        text=f"*{novos} processo(s) importados!* Total: *{total}*\n\n"
             f"Use /meus\\_processos para ver.\nUse /briefing para o resumo!",
        parse_mode="Markdown")


async def _importar_processos(user, comunicacoes, numeros_cnj, loop):
    novos = erros = 0
    atuais = {p["numero"] for p in db.listar_processos(user["id"])}

    for num_cnj in numeros_cnj:
        if num_cnj in atuais:
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

        # Extrai comarca do nome da vara e UF do CNJ
        comarca = extrair_comarca_da_vara(vara)
        uf_proc = extrair_uf_do_cnj(num_cnj)

        db.criar_processo(
            advogado_id=user["id"], numero=num_cnj,
            partes=partes, vara=vara, tribunal=tribunal,
            comarca=comarca, fonte="djen+datajud")
        novos += 1

        if comarca:
            logger.info(f"Processo {num_cnj}: comarca={comarca}, uf={uf_proc}")

    return novos, erros


# ============================================================
# /calcular
# ============================================================
async def calcular_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    args = context.args
    if not args or len(args) < 2:
        await _send(update,
            "*Calcular prazo com feriados forenses*\n\n"
            "Uso: `/calcular DD/MM/AAAA DIAS`\n\n"
            "Exemplos:\n"
            "`/calcular 05/03/2026 15` — 15 dias uteis\n"
            "`/calcular 05/03/2026 15 corridos` — dias corridos\n"
            "`/calcular 05/03/2026 15 dobro` — prazo em dobro\n\n"
            f"Comarca: *{user.get('comarca', 'N/I')}*\n"
            "Use /comarca para alterar.",
            parse_mode="Markdown")
        return
    try:
        data_disp = datetime.strptime(args[0], "%d/%m/%Y").date()
    except ValueError:
        await _send(update, "Data invalida. Use DD/MM/AAAA")
        return
    try:
        dias = int(args[1])
    except ValueError:
        await _send(update, "Informe o numero de dias (ex: 15)")
        return
    contagem = "uteis"
    dobra = False
    if len(args) > 2:
        extra = args[2].lower()
        if "corrido" in extra:
            contagem = "corridos"
        if "dobro" in extra or "dobra" in extra:
            dobra = True
    comarca = user.get("comarca", "")
    uf = user.get("oab_seccional", "MG")
    resultado = calcular_prazo_completo(data_disp, dias, uf=uf, comarca_processo=comarca, contagem=contagem, dobra=dobra)
    dobro_txt = " *(em dobro)*" if dobra else ""
    fmt = lambda iso: datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")

    conf = resultado.get("confidence", "?")
    msg = (
        f"*Calculo de Prazo*{dobro_txt}\n"
        f"Comarca: *{comarca or uf}*\n\n"
        f"Disponibilizacao: `{args[0]}`\n"
        f"Publicacao: `{fmt(resultado['data_publicacao'])}`\n"
        f"Inicio do prazo: `{fmt(resultado['data_inicio_prazo'])}`\n"
        f"Prazo: *{resultado['dias_prazo_efetivo']} dias {contagem}*\n"
        f"*Vencimento: `{fmt(resultado['data_vencimento'])}`*\n\n"
        f"_Feriados considerados: nacionais + estaduais + municipais ({conf})_"
    )
    if conf in ("medium", "low"):
        msg += "\n\n⚠️ _Confira o calendário completo no tribunal: esta comarca pode não ter feriados municipais no nosso banco._"
    await _send(update, msg, parse_mode="Markdown")


# ============================================================
# /comarca
# ============================================================
async def comarca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    uf = user.get("oab_seccional", "MG")
    comarcas = _get_comarcas_disponiveis(uf)[:20]
    kb = []
    row = []
    for c in comarcas:
        row.append(InlineKeyboardButton(c, callback_data=f"mudar_comarca_{c}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("Outra...", callback_data="comarca_outra")])
    await _send(update,
        f"Comarca atual: *{user.get('comarca', 'N/I')}*\nSelecione:",
        parse_mode="Markdown")
    await update.message.reply_text("Comarcas:", reply_markup=InlineKeyboardMarkup(kb))


async def handle_mudar_comarca_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "comarca_outra":
        await q.edit_message_text("Digite o nome da comarca:")
        context.user_data["step"] = "aguardando_comarca_texto"
        return
    if q.data.startswith("mudar_comarca_"):
        comarca = q.data.replace("mudar_comarca_", "")
        db.atualizar_comarca(q.message.chat_id, comarca)
        await q.edit_message_text(
            f"Comarca atualizada: *{comarca}*\n"
            f"Prazos serao calculados com feriados desta comarca.",
            parse_mode="Markdown")


# ============================================================
# /adicionar
# ============================================================
async def adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    await _send(update, "Envie o *numero CNJ* do processo.\nEx: `1234567-89.2024.8.13.0001`", parse_mode="Markdown")
    context.user_data["step"] = "aguardando_processo_numero"


async def handle_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    text = update.message.text.strip()
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if step == "aguardando_processo_numero":
        context.user_data["proc_num"] = text
        await _send(update, "Partes? Ex: `Maria vs Empresa X` (ou `-`)", parse_mode="Markdown")
        context.user_data["step"] = "aguardando_partes"
    elif step == "aguardando_partes":
        context.user_data["proc_partes"] = text if text != "-" else "Nao informado"
        await _send(update, "Vara? Ex: `2a Vara Civel` (ou `-`)", parse_mode="Markdown")
        context.user_data["step"] = "aguardando_vara"
    elif step == "aguardando_vara":
        vara = text if text != "-" else "Nao informado"
        db.criar_processo(advogado_id=user["id"], numero=context.user_data["proc_num"],
                         partes=context.user_data["proc_partes"], vara=vara)
        context.user_data["step"] = None
        await _send(update, f"Processo cadastrado!\n`{context.user_data['proc_num']}`", parse_mode="Markdown")


# ============================================================
# /meus_processos
# ============================================================
async def meus_processos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    processos = db.listar_processos(user["id"])
    if not processos:
        await _send(update, "Nenhum processo. Use /buscar!")
        return
    msg = f"*{len(processos)} processo(s):*\n\n"
    for i, p in enumerate(processos[:15], 1):
        prazos = db.listar_prazos_processo(p["id"])
        prazo_info = ""
        if prazos:
            dias = (datetime.strptime(prazos[0]["data_fim"], "%Y-%m-%d").date() - datetime.now().date()).days
            if dias < 0:
                prazo_info = f"\n   🔴 VENCIDO ha {abs(dias)}d"
            elif dias == 0:
                prazo_info = "\n   🔴 VENCE HOJE"
            elif dias <= 3:
                prazo_info = f"\n   🟡 Prazo em {dias}d"
            elif dias <= 7:
                prazo_info = f"\n   🟢 Prazo em {dias}d"

        # Monta linha de detalhes (omite N/I)
        partes = p.get("partes", "") or ""
        vara = p.get("vara", "") or ""
        tribunal = p.get("tribunal", "") or ""
        detalhes = ""
        if partes and partes != "N/I" and partes != "Nao informado":
            detalhes += f"\n   {partes[:60]}"
        if vara and vara != "N/I" and vara != "Nao informado":
            detalhes += f"\n   {vara[:50]}"
        if tribunal and not detalhes:
            detalhes += f"\n   {tribunal}"

        msg += f"*{i}.* `{p['numero']}`{detalhes}{prazo_info}\n\n"
    if len(processos) > 15:
        msg += f"_... e mais {len(processos)-15}._"
    await _send(update, msg, parse_mode="Markdown")


# ============================================================
# /prazo
# ============================================================
async def prazo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    args = context.args
    if not args:
        await _send(update,
            "*Como usar /prazo:*\n\n"
            "Buscar por cliente:\n`/prazo Maria Silva`\n\n"
            "Adicionar prazo:\n`/prazo 1234567 15/03/2026 Contestacao`",
            parse_mode="Markdown")
        return

    primeiro = args[0]
    parece_numero = any(c.isdigit() for c in primeiro) and len(primeiro) > 4

    if not parece_numero:
        nome_cliente = " ".join(args)
        processos = db.buscar_processos_por_cliente(user["id"], nome_cliente)
        if not processos:
            await _send(update, f"Nenhum processo com cliente *{nome_cliente}*.", parse_mode="Markdown")
            return
        texto = f"Processos com *{nome_cliente}*:\n\n"
        for p in processos:
            texto += f"`{p['numero']}`\n{p.get('partes','')}\n{p.get('vara','')}\n"
            if p.get("prazos"):
                for pr in p["prazos"]:
                    fatal_str = "FATAL" if pr.get("fatal") else ""
                    texto += f"  {fatal_str} {pr['tipo']} — vence {pr['data_fim']}\n"
            else:
                texto += "  Sem prazos pendentes\n"
            texto += "\n"
        await _send(update, texto, parse_mode="Markdown")
        return

    if len(args) < 3:
        await _send(update, "Uso: `/prazo 1234567 15/03/2026 Contestacao`", parse_mode="Markdown")
        return
    try:
        data_fim = datetime.strptime(args[1], "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        await _send(update, "Data invalida. Use DD/MM/AAAA")
        return
    processo = db.buscar_processo_por_numero_parcial(user["id"], args[0])
    if not processo:
        await _send(update, f"Processo `{args[0]}` nao encontrado.", parse_mode="Markdown")
        return
    tipo = " ".join(args[2:])
    context.user_data.update({"pz_pid": processo["id"], "pz_num": processo["numero"],
                              "pz_tipo": tipo, "pz_data": data_fim, "pz_disp": args[1]})
    kb = [[InlineKeyboardButton("Fatal", callback_data="fatal_sim"),
           InlineKeyboardButton("Dilatorio", callback_data="fatal_nao")]]
    await _send(update,
        f"`{processo['numero']}`\n{args[1]} — {tipo}\n\nE *fatal*?",
        parse_mode="Markdown")
    await update.message.reply_text("Tipo:", reply_markup=InlineKeyboardMarkup(kb))


async def handle_fatal_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pid = context.user_data.get("pz_pid")
    if not pid:
        await q.edit_message_text("Tente /prazo de novo")
        return
    fatal = q.data == "fatal_sim"
    db.criar_prazo(processo_id=pid, tipo=context.user_data.get("pz_tipo",""),
                   data_fim=context.user_data.get("pz_data",""), fatal=fatal)
    e = "FATAL" if fatal else "Dilatorio"
    await q.edit_message_text(
        f"Prazo salvo! {e}\n`{context.user_data.get('pz_num','')}`\n{context.user_data.get('pz_disp','')}",
        parse_mode="Markdown")
    for k in ["pz_pid","pz_num","pz_tipo","pz_data","pz_disp"]:
        context.user_data.pop(k, None)


# ============================================================
# /briefing
# ============================================================
async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    processos = db.listar_processos_com_prazos(user["id"])
    if not processos:
        await _send(update, "Nenhum processo. Use /buscar!")
        return
    await _send(update, "Gerando briefing... Consultando DJEN...")
    comarca = user.get("comarca", "")
    uf = user.get("oab_seccional", "MG")

    loop = asyncio.get_event_loop()
    try:
        comunicacoes = await loop.run_in_executor(
            None, consultar_djen_por_oab, user["oab_numero"], user["oab_seccional"], 30)
        if comunicacoes:
            comunicacoes = _calcular_prazos_djen(comunicacoes, comarca, uf)
            for proc in processos:
                prazos_proc = []
                for c in comunicacoes:
                    if c.get("numero_processo") == proc.get("numero") and c.get("prazo_info"):
                        pi = c["prazo_info"]
                        prazos_proc.append({
                            "tipo": c.get("tipo", "intimacao"),
                            "data_fim": pi["data_vencimento"],
                            "data_fim_util": pi["data_vencimento"],
                            "fatal": True, "contagem": "uteis",
                            "status_emoji": pi["emoji"],
                            "status_texto": pi["status"],
                        })
                if prazos_proc and isinstance(proc, dict):
                    proc["prazos"] = prazos_proc
    except Exception as e:
        logger.warning(f"Erro DJEN no briefing: {e}")

    texto = await loop.run_in_executor(None, gerar_briefing, user["nome"], processos, comarca)
    try:
        await _send(update, texto, parse_mode="Markdown")
    except Exception:
        await _send(update, texto)


# ============================================================
# /feriados
# ============================================================
async def feriados_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    comarca = user.get("comarca", "")
    uf = user.get("oab_seccional", "MG")
    feriados_lista = _cal_store.obter_feriados(2026, uf, comarca)
    if not feriados_lista:
        await _send(update, f"Nenhum feriado para {comarca or uf}/2026.")
        return
    msg = f"*Feriados 2026 — {comarca or uf}*\n\n"
    for fer in feriados_lista[:25]:
        d = datetime.strptime(fer["data"], "%Y-%m-%d").strftime("%d/%m")
        msg += f"`{d}` — {fer['descricao']}\n"
    if len(feriados_lista) > 25:
        msg += f"\n_... e mais {len(feriados_lista)-25} feriados._"
    msg += f"\n\n_Total: {len(feriados_lista)} feriados/suspensoes._"
    conf = _cal_resolver.get_confidence_for(uf, comarca)
    if conf in ("medium", "low"):
        msg += "\n\n⚠️ _Confira o calendário completo no tribunal: esta comarca pode não ter feriados municipais no nosso banco._"
    await _send(update, msg, parse_mode="Markdown")


# ============================================================
# /djen
# ============================================================
PRAZOS_POR_TIPO = {
    "intimação": 15, "citação": 15, "edital": 20,
    "notificação": 15, "lista de distribuição": 0,
}


def _calcular_prazos_djen(comunicacoes, comarca_padrao, uf_padrao=""):
    hoje = date.today()
    resultados = []
    for c in comunicacoes:
        tipo = (c.get("tipo") or "").lower()
        dias = PRAZOS_POR_TIPO.get(tipo, 15)
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

        # Usa comarca do processo (extraída do orgao/CNJ), com fallback na comarca do advogado
        uf_proc = extrair_uf_do_cnj(c.get("numero_processo", "")) or uf_padrao
        comarca_proc = extrair_comarca_da_vara(c.get("orgao", "")) or comarca_padrao
        c["comarca_processo"] = comarca_proc  # guarda para exibir no /djen
        c["uf_processo"] = uf_proc

        resultado = calcular_prazo_completo(data_disp, dias, uf=uf_proc, comarca_processo=comarca_proc)
        venc = datetime.strptime(resultado["data_vencimento"], "%Y-%m-%d").date()
        dias_restantes = (venc - hoje).days
        if dias_restantes < 0:
            status, emoji = f"VENCIDO ha {abs(dias_restantes)}d", "🔴"
        elif dias_restantes == 0:
            status, emoji = "VENCE HOJE", "🔴"
        elif dias_restantes <= 3:
            status, emoji = f"Vence em {dias_restantes}d", "🟡"
        elif dias_restantes <= 7:
            status, emoji = f"Vence em {dias_restantes}d", "🟡"
        else:
            status, emoji = f"Vence em {dias_restantes}d", "🟢"

        c["prazo_info"] = {
            "dias_prazo": dias,
            "data_publicacao": resultado["data_publicacao"],
            "data_inicio": resultado["data_inicio_prazo"],
            "data_vencimento": resultado["data_vencimento"],
            "dias_restantes": dias_restantes,
            "status": status, "emoji": emoji, "datajud": None,
        }
        try:
            verif = verificar_prazo_cumprido(
                c["numero_processo"], c.get("tribunal", ""),
                c["data_disponibilizacao"], resultado["data_vencimento"])
            c["prazo_info"]["datajud"] = verif
            if verif["status"] == "cumprido":
                c["prazo_info"]["emoji"] = "✅"
                c["prazo_info"]["status"] = f"Cumprido — {verif['manifestacao']}"
            elif verif["status"] == "decurso":
                c["prazo_info"]["emoji"] = "🔴"
                c["prazo_info"]["status"] = f"Decurso — {verif['manifestacao']}"
        except Exception:
            pass
        resultados.append(c)
    return resultados


async def djen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    await _send(update,
        f"Consultando DJEN para OAB {user['oab_numero']}/{user['oab_seccional']}...")
    try:
        loop = asyncio.get_event_loop()
        comunicacoes = await loop.run_in_executor(
            None, consultar_djen_por_oab, user["oab_numero"], user["oab_seccional"], 30)
        if not comunicacoes:
            await _send(update, "Nenhuma publicacao encontrada no DJEN.")
            return
        comarca = user.get("comarca", "")
        uf = user.get("oab_seccional", "")
        comunicacoes = _calcular_prazos_djen(comunicacoes, comarca, uf)
        novos = importar_comunicacoes_para_banco(db, user["id"], comunicacoes)
        msg = formatar_comunicacoes_telegram(comunicacoes)
        if novos:
            msg += f"\n_{novos} nova(s) publicacao(oes) salva(s)._"
        try:
            await _send(update, msg, parse_mode="Markdown")
        except Exception:
            await _send(update, msg)
    except Exception as e:
        logger.error(f"Erro /djen: {e}")
        await _send(update, f"Erro ao consultar DJEN.\n{str(e)[:100]}")


# ============================================================
# /publicacoes
# ============================================================
async def publicacoes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start primeiro")
        return
    comunicacoes = db.listar_comunicacoes_novas(user["id"], limite=10)
    if not comunicacoes:
        await _send(update, "Nenhuma publicacao salva. Use /djen!")
        return
    msg = "*Ultimas publicacoes DJEN:*\n\n"
    for i, c in enumerate(comunicacoes, 1):
        data = c.get("data_disponibilizacao", "")
        if data and "-" in data:
            try:
                data = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                pass
        msg += f"*{i}.* `{c.get('numero_processo', 'N/I')}`\n"
        if data:
            msg += f"   {data}\n"
        if c.get("tipo_comunicacao"):
            msg += f"   {c['tipo_comunicacao']}\n"
        msg += "\n"
    await _send(update, msg, parse_mode="Markdown")


# ============================================================
# /ajuda
# ============================================================
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send(update,
        "*PrazorBot — Copiloto Juridico*\n\n"
        "/start — Cadastro\n"
        "/buscar — Importar processos pela OAB\n"
        "/adicionar — Cadastrar manualmente\n"
        "/prazo — Buscar cliente ou adicionar prazo\n"
        "/calcular — *Calcular prazo com feriados*\n"
        "/meus\\_processos — Ver processos\n"
        "/briefing — Briefing com IA agora\n"
        "/djen — Consultar publicacoes DJEN\n"
        "/feriados — Ver feriados da sua comarca\n"
        "/comarca — Alterar comarca\n"
        "/config — Horario e preferencias do lembrete\n"
        "/ajuda — Esta mensagem\n\n"
        "Ou me pergunte qualquer coisa!",
        parse_mode="Markdown")


# ============================================================
# Mensagens livres
# ============================================================
async def handle_mensagem_livre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")
    if step in ("aguardando_nome", "aguardando_oab", "aguardando_comarca_texto"):
        await handle_onboarding(update, context)
        return
    if step in ("aguardando_processo_numero", "aguardando_partes", "aguardando_vara"):
        await handle_cadastro(update, context)
        return

    user = db.get_advogado_by_chat_id(update.effective_chat.id)
    if not user:
        await _send(update, "Use /start para comecar!")
        return
    processos = db.listar_processos_com_prazos(user["id"])
    if not processos:
        await _send(update, "Use /buscar para importar seus processos primeiro!")
        return
    await _send(update, "Pensando...")
    comarca = user.get("comarca", "")
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(None, responder_pergunta,
                                      update.message.text.strip(), user["nome"], processos, comarca)
    try:
        await _send(update, resp, parse_mode="Markdown")
    except Exception:
        await _send(update, resp)


# ============================================================
# Main
# ============================================================
def main():
    db.init()
    logger.info(f"Calendario forense: cal_forense/calendar_v2.db (schema v{_cal_store.schema})")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Restaura lembretes de todos os usuarios ativos
    _restaurar_lembretes(app)

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar_command))
    app.add_handler(CommandHandler("adicionar", adicionar))
    app.add_handler(CommandHandler("prazo", prazo_command))
    app.add_handler(CommandHandler("calcular", calcular_command))
    app.add_handler(CommandHandler("meus_processos", meus_processos))
    app.add_handler(CommandHandler("briefing", briefing_command))
    app.add_handler(CommandHandler("feriados", feriados_command))
    app.add_handler(CommandHandler("comarca", comarca_command))
    app.add_handler(CommandHandler("config", config_command))
    app.add_handler(CommandHandler("djen", djen_command))
    app.add_handler(CommandHandler("publicacoes", publicacoes_command))
    app.add_handler(CommandHandler("ajuda", ajuda))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_fatal_cb, pattern="^fatal_"))
    app.add_handler(CallbackQueryHandler(handle_set_hora_cb, pattern="^set_hora_"))
    app.add_handler(CallbackQueryHandler(handle_fds_cb, pattern="^fds_"))
    app.add_handler(CallbackQueryHandler(handle_mudar_comarca_cb, pattern="^(mudar_comarca_|comarca_outra)"))

    # Mensagens livres
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mensagem_livre))

    logger.info("PrazorBot iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
