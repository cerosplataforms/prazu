"""
Scheduler de Briefings — roda como cron job
Envia o briefing matinal para cada advogado no horário configurado.

Uso:
  python scheduler.py          # Envia para quem está no horário agora
  python scheduler.py --force  # Força envio para todos (teste)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from database import Database
from ia import gerar_briefing

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

db = Database()
bot = Bot(token=TELEGRAM_TOKEN)


async def enviar_briefing(advogado: dict):
    """Gera e envia briefing para um advogado"""
    try:
        processos = db.listar_processos_com_prazos(advogado["id"])

        if not processos:
            logger.info(f"  → {advogado['nome']}: sem processos, pulando.")
            return

        briefing_text = gerar_briefing(
            nome_advogado=advogado["nome"],
            processos=processos,
        )

        if briefing_text:
            await bot.send_message(
                chat_id=advogado["chat_id"],
                text=briefing_text,
                parse_mode="Markdown",
            )
            logger.info(f"  ✅ Briefing enviado para Dr(a). {advogado['nome']}")
        else:
            logger.info(f"  → {advogado['nome']}: briefing vazio, pulando.")

    except Exception as e:
        logger.error(f"  ❌ Erro ao enviar para {advogado['nome']}: {e}")


async def main():
    force = "--force" in sys.argv
    hora_atual = datetime.now().strftime("%H:00")

    logger.info(f"🕐 Scheduler rodando — hora atual: {hora_atual}")

    advogados = db.listar_advogados_ativos()
    logger.info(f"📋 {len(advogados)} advogado(s) ativo(s)")

    for adv in advogados:
        horario = adv.get("horario_briefing", "07:00")

        if force or horario == hora_atual:
            logger.info(f"📤 Enviando briefing para Dr(a). {adv['nome']}...")
            await enviar_briefing(adv)
        else:
            logger.info(
                f"  ⏭️ {adv['nome']}: horário configurado {horario}, pulando."
            )

    logger.info("✅ Scheduler concluído.")


if __name__ == "__main__":
    asyncio.run(main())
