"""
Atualizador noturno — roda via cron toda madrugada
Consulta o DataJud pra cada processo cadastrado e atualiza o banco local.

Uso:
  python atualizar.py          # Atualiza todos os processos
  python atualizar.py --teste  # Atualiza só o primeiro processo (teste)

Cron sugerido (todo dia às 3h da manhã):
  0 3 * * * cd /caminho/prazo-bot && venv/bin/python atualizar.py >> atualizar.log 2>&1
"""

import sys
import logging
from database import Database
from datajud import atualizar_todos_processos, consultar_processo, atualizar_processo_no_banco

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    db = Database()
    db.init()

    modo_teste = "--teste" in sys.argv

    if modo_teste:
        # Testa com o primeiro processo do banco
        conn = db._conn()
        proc = conn.execute(
            "SELECT id, numero FROM processos WHERE status = 'ativo' LIMIT 1"
        ).fetchone()
        conn.close()

        if not proc:
            print("❌ Nenhum processo cadastrado no banco.")
            return

        proc = dict(proc)
        print(f"🧪 Modo teste — consultando: {proc['numero']}")
        sucesso = atualizar_processo_no_banco(db, proc["id"], proc["numero"])
        print(f"{'✅ Sucesso' if sucesso else '❌ Falhou'}")

    else:
        atualizados, erros = atualizar_todos_processos(db)
        print(f"\n📊 Resultado: {atualizados} atualizados, {erros} erros")


if __name__ == "__main__":
    main()
