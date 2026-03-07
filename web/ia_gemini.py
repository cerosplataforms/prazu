"""
ia_gemini.py — Prazu Fase 2
Integração com Google Gemini (substitui ia.py com Groq).
Usa gemini-2.0-flash via REST API.
"""
import os
import logging
import httpx
from typing import Optional

log = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = """Você é o assistente jurídico da Prazu, um copiloto inteligente para advogados brasileiros.
Você ajuda advogados a monitorar prazos processuais, entender publicações do DJEN e organizar sua rotina jurídica.
Seja direto, preciso e profissional. Use linguagem jurídica adequada mas acessível.
Nunca invente prazos ou datas — só informe o que está nos dados fornecidos.
Quando não souber algo, diga claramente."""


async def gerar_briefing(advogado: dict, processos: list[dict]) -> str:
    """
    Gera o briefing diário personalizado para o advogado.
    Retorna texto formatado para WhatsApp.
    """
    from datetime import datetime
    hoje = datetime.now().strftime("%d/%m/%Y")
    nome = advogado.get("nome", "Dr(a).")
    primeiro_nome = nome.split()[0]

    if not processos:
        prompt = f"""Gere um briefing matinal para o advogado {primeiro_nome} para o dia {hoje}.
Não há prazos pendentes para hoje. Seja motivador e profissional.
Formate para WhatsApp com emojis adequados. Máximo 3 parágrafos curtos."""
    else:
        lista = []
        for p in processos[:10]:  # limita a 10 processos
            status = "🔴 URGENTE" if p.get("decurso") else (
                "🟡 Próximo" if p.get("dias_restantes", 99) <= 3 else "🟢 Em aberto"
            )
            lista.append(
                f"- {status} | {p.get('numero','?')} | "
                f"Vence: {p.get('data_fim','?')} | {p.get('tipo_prazo','Prazo')}"
            )
        lista_str = "\n".join(lista)

        prompt = f"""Gere um briefing matinal para o advogado {primeiro_nome} para o dia {hoje}.

Prazos do dia:
{lista_str}

Instruções:
- Comece com saudação e data
- Destaque urgências (🔴) primeiro
- Liste os prazos de forma clara
- Termine com frase motivacional curta
- Formate para WhatsApp com emojis
- Máximo 20 linhas no total"""

    return await _chamar_gemini(prompt)


async def responder_mensagem(mensagem: str, contexto: Optional[str] = None) -> str:
    """
    Responde uma mensagem livre do advogado sobre processos/prazos.
    """
    if contexto:
        prompt = f"""Contexto do advogado:
{contexto}

Mensagem do advogado: {mensagem}

Responda de forma direta e útil. Máximo 5 parágrafos."""
    else:
        prompt = f"""Mensagem do advogado: {mensagem}

Responda de forma direta e útil. Máximo 5 parágrafos."""

    return await _chamar_gemini(prompt)


async def resumir_publicacao(texto_publicacao: str) -> str:
    """
    Resume uma publicação do DJEN em linguagem simples.
    """
    prompt = f"""Resume esta publicação do Diário da Justiça em 3 linhas simples para um advogado.
Destaque: tipo de ato, prazo se houver, ação necessária.

Publicação:
{texto_publicacao[:2000]}"""

    return await _chamar_gemini(prompt)


async def _chamar_gemini(prompt: str) -> str:
    """Chama a API do Gemini e retorna o texto gerado."""
    if not GEMINI_API_KEY:
        log.error("GEMINI_API_KEY não configurada")
        return "⚠️ Serviço de IA temporariamente indisponível."

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            texto = data["candidates"][0]["content"]["parts"][0]["text"]
            return texto.strip()

    except httpx.TimeoutException:
        log.error("Gemini timeout")
        return "⚠️ IA demorou demais para responder. Tente novamente."
    except Exception as e:
        log.error(f"Erro Gemini: {e}")
        return "⚠️ Serviço de IA temporariamente indisponível."
