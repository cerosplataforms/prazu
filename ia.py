"""
Módulo de IA — Integração com Gemini 2.0 Flash
Gera briefings e responde perguntas sobre processos.
"""

import os
import google.generativeai as genai
from datetime import date

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """Você é o PrazoBot, assistente jurídico especializado em controle de prazos processuais para advogados brasileiros.

Regras para o briefing:
- Trate o advogado como Dr(a).
- Use formato Markdown compatível com WhatsApp (*negrito*, _itálico_)
- Organize o briefing EXATAMENTE nesta ordem:
  1. 🔴 *Prazos que vencem HOJE* (lista ou "Nenhum")
  2. ⚠️ *Prazos VENCIDOS* (lista ou "Nenhum")
  3. 🟡 *Prazos próximos 7 dias* (lista com número do processo, tipo e data)
  4. 🟢 *Prazos em aberto* (todos os outros prazos futuros além de 7 dias)
  5. ✅ *Prazos cumpridos* (se houver)
  6. Resumo da carteira (total processos e prazos pendentes)
  7. Frase motivacional curta

- Liste TODOS os prazos em cada categoria, não omita nenhum
- Seja conciso, profissional e amigável
- Sempre informe: número do processo, tipo de prazo e data de vencimento
- Data de hoje: {data_hoje}
- Comarca padrão do advogado: {comarca}
"""


def _formatar_processos_contexto(processos):
    if not processos:
        return "Nenhum processo cadastrado."
    contexto = []
    for p in processos:
        info = f"Processo: {p['numero']}\n"
        info += f"  Partes: {p.get('partes', 'Não informado')}\n"
        info += f"  Vara: {p.get('vara', 'Não informado')}\n"
        info += f"  Tribunal: {p.get('tribunal', 'TJMG')}\n"
        info += f"  Comarca: {p.get('comarca', 'N/I')}\n"
        if p.get("prazos"):
            info += "  Prazos:\n"
            for pr in p["prazos"]:
                status_emoji = pr.get("status_emoji", "")
                status_texto = pr.get("status_texto", "")
                status_dj = pr.get("status_datajud", "em_aberto")
                info += f"    - {pr['tipo']} | Vence: {pr['data_fim']} | Status: {status_emoji} {status_texto}"
                if status_dj == "cumprido":
                    info += " | CUMPRIDO"
                elif status_dj == "decurso":
                    info += " | DECURSO (não cumprido)"
                elif status_dj == "vencido_verificar":
                    info += " | VENCIDO - verificar no processo"
                info += "\n"
        else:
            info += "  Prazos pendentes: nenhum\n"
        if p.get("andamentos"):
            info += "  Últimos andamentos:\n"
            for a in p["andamentos"]:
                info += f"    - {a['data']}: {a['descricao']}\n"
        contexto.append(info)
    return "\n".join(contexto)


def gerar_briefing(nome_advogado, processos, comarca="Belo Horizonte"):
    data_hoje = date.today().strftime("%d/%m/%Y")
    dias_pt = {
        "Monday": "segunda-feira", "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira", "Thursday": "quinta-feira",
        "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo",
    }
    dia = dias_pt.get(date.today().strftime("%A"), "")
    ctx = _formatar_processos_contexto(processos)

    prompt = f"""{SYSTEM_PROMPT.format(data_hoje=data_hoje, comarca=comarca)}

Gere briefing matinal para Dr(a). {nome_advogado}.
Hoje: {dia}, {data_hoje}. Comarca: {comarca}.

Processos:
{ctx}

Instruções:
1. Saudação com nome
2. Prazos HOJE com 🔴
3. Prazos VENCIDOS com ⚠️
4. Prazos próximos 7 dias com 🟡
5. Resumo da carteira
6. Frase motivacional curta
7. Seja conciso — leitura rápida no WhatsApp"""

    try:
        r = model.generate_content(prompt)
        return r.text
    except Exception as e:
        print(f"Erro briefing Gemini: {e}")
        return (
            f"Bom dia, Dr(a). {nome_advogado}!\n\n"
            f"Não consegui gerar seu briefing completo agora, "
            f"mas você tem *{len(processos)} processo(s)* monitorados.\n"
            f"Tente novamente em alguns minutos."
        )


def responder_pergunta(pergunta, nome_advogado, processos, comarca="Belo Horizonte"):
    data_hoje = date.today().strftime("%d/%m/%Y")
    ctx = _formatar_processos_contexto(processos)

    prompt = f"""{SYSTEM_PROMPT.format(data_hoje=data_hoje, comarca=comarca)}

Dr(a). {nome_advogado} perguntou: "{pergunta}"

Processos:
{ctx}

Responda de forma clara e objetiva. Se perguntarem sobre cálculo de prazo,
explique as datas (disponibilização -> publicação -> início do prazo -> vencimento).
Considere feriados de MG e a comarca {comarca}."""

    try:
        r = model.generate_content(prompt)
        return r.text
    except Exception as e:
        print(f"Erro pergunta Gemini: {e}")
        return "Desculpe, tive um problema ao processar sua pergunta. Tente novamente."
