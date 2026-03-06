"""
Database module — SQLite para PrazorBot MVP (Minas Gerais)
Inclui feriados, comarcas, tribunais e cálculo de prazos.
"""

import sqlite3
from datetime import datetime, date, timedelta


class Database:
    def __init__(self, db_path="prazobot.db"):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS advogados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                oab_numero TEXT NOT NULL,
                oab_seccional TEXT NOT NULL,
                comarca TEXT DEFAULT '',
                horario_briefing TEXT DEFAULT '07:00',
                lembrete_fds INTEGER DEFAULT 0,
                ultima_busca_djen TEXT DEFAULT '',
                ativo INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT (datetime('now', 'localtime'))
            );
            CREATE TABLE IF NOT EXISTS processos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                advogado_id INTEGER NOT NULL,
                numero TEXT NOT NULL,
                partes TEXT,
                vara TEXT,
                tribunal TEXT DEFAULT 'TJMG',
                comarca TEXT,
                materia TEXT,
                classe TEXT,
                assunto TEXT,
                status TEXT DEFAULT 'ativo',
                fonte TEXT DEFAULT 'manual',
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (advogado_id) REFERENCES advogados(id)
            );
            CREATE TABLE IF NOT EXISTS prazos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processo_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                data_inicio TEXT,
                data_fim TEXT NOT NULL,
                data_fim_util TEXT,
                dias_totais INTEGER,
                contagem TEXT DEFAULT 'uteis',
                fatal INTEGER DEFAULT 0,
                cumprido INTEGER DEFAULT 0,
                notificado INTEGER DEFAULT 0,
                notificado_3d INTEGER DEFAULT 0,
                notificado_1d INTEGER DEFAULT 0,
                notificado_hoje INTEGER DEFAULT 0,
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (processo_id) REFERENCES processos(id)
            );
            CREATE TABLE IF NOT EXISTS andamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processo_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                descricao TEXT NOT NULL,
                notificado INTEGER DEFAULT 0,
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (processo_id) REFERENCES processos(id)
            );
            CREATE TABLE IF NOT EXISTS feriados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                descricao TEXT NOT NULL,
                tipo TEXT NOT NULL,
                comarca TEXT,
                tribunal TEXT,
                ano INTEGER NOT NULL,
                UNIQUE(data, tipo, comarca, tribunal)
            );
            CREATE TABLE IF NOT EXISTS comunicacoes_djen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                advogado_id INTEGER NOT NULL,
                numero_processo TEXT,
                tribunal TEXT,
                conteudo TEXT,
                data_disponibilizacao TEXT,
                data_publicacao TEXT,
                tipo_comunicacao TEXT,
                lida INTEGER DEFAULT 0,
                importada_em TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (advogado_id) REFERENCES advogados(id)
            );
        """)
        conn.commit()
        conn.close()

    # --- Advogados ---

    def criar_advogado(self, chat_id, nome, oab_numero, oab_seccional, comarca="", horario_briefing="07:00", lembrete_fds=0):
        conn = self._conn()
        conn.execute(
            "INSERT OR REPLACE INTO advogados (chat_id, nome, oab_numero, oab_seccional, comarca, horario_briefing, lembrete_fds) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (chat_id, nome, oab_numero, oab_seccional, comarca, horario_briefing, lembrete_fds),
        )
        conn.commit()
        conn.close()

    def get_advogado_by_chat_id(self, chat_id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM advogados WHERE chat_id = ?", (chat_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def listar_advogados_ativos(self):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM advogados WHERE ativo = 1").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def atualizar_horario(self, chat_id, horario):
        conn = self._conn()
        conn.execute("UPDATE advogados SET horario_briefing = ? WHERE chat_id = ?", (horario, chat_id))
        conn.commit()
        conn.close()

    def atualizar_comarca(self, chat_id, comarca):
        conn = self._conn()
        conn.execute("UPDATE advogados SET comarca = ? WHERE chat_id = ?", (comarca, chat_id))
        conn.commit()
        conn.close()

    def atualizar_lembrete_fds(self, chat_id, lembrete_fds):
        conn = self._conn()
        conn.execute("UPDATE advogados SET lembrete_fds = ? WHERE chat_id = ?", (lembrete_fds, chat_id))
        conn.commit()
        conn.close()

    # --- Processos ---

    def criar_processo(self, advogado_id, numero, partes, vara, tribunal="TJMG", comarca=None, fonte="manual"):
        conn = self._conn()
        cursor = conn.execute(
            "INSERT INTO processos (advogado_id, numero, partes, vara, tribunal, comarca, fonte) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (advogado_id, numero, partes, vara, tribunal, comarca, fonte),
        )
        conn.commit()
        processo_id = cursor.lastrowid
        conn.close()
        return processo_id

    def listar_processos(self, advogado_id):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM processos WHERE advogado_id = ? AND status = 'ativo' ORDER BY criado_em DESC",
            (advogado_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def contar_processos(self, advogado_id):
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) as total FROM processos WHERE advogado_id = ? AND status = 'ativo'",
            (advogado_id,),
        ).fetchone()
        conn.close()
        return row["total"]

    def listar_processos_com_prazos(self, advogado_id):
        conn = self._conn()
        processos = conn.execute(
            "SELECT * FROM processos WHERE advogado_id = ? AND status = 'ativo'",
            (advogado_id,),
        ).fetchall()
        resultado = []
        for p in processos:
            p_dict = dict(p)
            prazos = conn.execute(
                "SELECT * FROM prazos WHERE processo_id = ? AND cumprido = 0 ORDER BY data_fim ASC",
                (p["id"],),
            ).fetchall()
            p_dict["prazos"] = [dict(pr) for pr in prazos]
            andamentos = conn.execute(
                "SELECT * FROM andamentos WHERE processo_id = ? ORDER BY data DESC LIMIT 5",
                (p["id"],),
            ).fetchall()
            p_dict["andamentos"] = [dict(a) for a in andamentos]
            resultado.append(p_dict)
        conn.close()
        return resultado

    def buscar_processo_por_numero_parcial(self, advogado_id, termo):
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM processos WHERE advogado_id = ? AND numero LIKE ? AND status = 'ativo'",
            (advogado_id, f"%{termo}%"),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def buscar_processos_por_cliente(self, advogado_id, nome_cliente):
        conn = self._conn()
        processos = conn.execute(
            "SELECT * FROM processos WHERE advogado_id = ? AND UPPER(partes) LIKE ? AND status = 'ativo'",
            (advogado_id, f"%{nome_cliente.upper()}%"),
        ).fetchall()
        resultado = []
        for p in processos:
            p_dict = dict(p)
            prazos = conn.execute(
                "SELECT * FROM prazos WHERE processo_id = ? AND cumprido = 0 ORDER BY data_fim ASC",
                (p["id"],),
            ).fetchall()
            p_dict["prazos"] = [dict(pr) for pr in prazos]
            resultado.append(p_dict)
        conn.close()
        return resultado

    def processo_existe(self, advogado_id, numero):
        conn = self._conn()
        row = conn.execute(
            "SELECT id FROM processos WHERE advogado_id = ? AND numero = ? AND status = 'ativo'",
            (advogado_id, numero),
        ).fetchone()
        conn.close()
        return row is not None

    # --- Prazos ---

    def criar_prazo(self, processo_id, tipo, data_fim, fatal=False, data_inicio=None, data_fim_util=None, dias_totais=None, contagem="uteis"):
        conn = self._conn()
        conn.execute(
            "INSERT INTO prazos (processo_id, tipo, data_fim, fatal, data_inicio, data_fim_util, dias_totais, contagem) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (processo_id, tipo, data_fim, 1 if fatal else 0, data_inicio, data_fim_util, dias_totais, contagem),
        )
        conn.commit()
        conn.close()

    def listar_prazos_processo(self, processo_id):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM prazos WHERE processo_id = ? AND cumprido = 0 ORDER BY data_fim ASC",
            (processo_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def listar_prazos_advogado(self, advogado_id, dias=7):
        conn = self._conn()
        hoje = date.today().isoformat()
        limite = (date.today() + timedelta(days=dias)).isoformat()
        rows = conn.execute("""
            SELECT p.*, pr.numero as processo_numero, pr.partes, pr.vara, pr.tribunal
            FROM prazos p
            JOIN processos pr ON p.processo_id = pr.id
            WHERE pr.advogado_id = ? AND p.cumprido = 0
            AND p.data_fim >= ? AND p.data_fim <= ?
            ORDER BY p.data_fim ASC
        """, (advogado_id, hoje, limite)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Feriados ---

    def inserir_feriado(self, data, descricao, tipo, comarca=None, tribunal=None, ano=None):
        if ano is None:
            ano = int(data[:4])
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO feriados (data, descricao, tipo, comarca, tribunal, ano) VALUES (?, ?, ?, ?, ?, ?)",
                (data, descricao, tipo, comarca, tribunal, ano),
            )
            conn.commit()
        except Exception:
            pass
        conn.close()

    def carregar_feriados(self, ano, comarca=None, tribunal=None):
        conn = self._conn()
        query = "SELECT data FROM feriados WHERE ano = ? AND (tipo = 'nacional' OR tipo = 'forense'"
        params = [ano]
        if comarca:
            query += " OR (tipo = 'municipal' AND UPPER(comarca) = UPPER(?))"
            params.append(comarca)
        if tribunal:
            query += " OR (tipo = 'tribunal' AND tribunal = ?)"
            params.append(tribunal)
        query += ")"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return {row["data"] for row in rows}

    def contar_feriados(self, ano=None):
        if ano is None:
            ano = date.today().year
        conn = self._conn()
        row = conn.execute("SELECT COUNT(*) as total FROM feriados WHERE ano = ?", (ano,)).fetchone()
        conn.close()
        return row["total"]

    # --- Comunicações DJEN ---

    def salvar_comunicacao(self, advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao=None, tipo_comunicacao=None):
        conn = self._conn()
        conn.execute(
            "INSERT INTO comunicacoes_djen (advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao, tipo_comunicacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (advogado_id, numero_processo, tribunal, conteudo, data_disponibilizacao, data_publicacao, tipo_comunicacao),
        )
        conn.commit()
        conn.close()

    def listar_comunicacoes_novas(self, advogado_id, limite=10):
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM comunicacoes_djen WHERE advogado_id = ? AND lida = 0 ORDER BY data_disponibilizacao DESC LIMIT ?",
            (advogado_id, limite),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Andamentos ---

    def criar_andamento(self, processo_id, data, descricao):
        conn = self._conn()
        conn.execute(
            "INSERT INTO andamentos (processo_id, data, descricao) VALUES (?, ?, ?)",
            (processo_id, data, descricao),
        )
        conn.commit()
        conn.close()

    # --- Notificações de prazo ---

    def marcar_prazo_notificado(self, prazo_id, nivel):
        """Marca prazo como notificado para um nível (3d, 1d, hoje)."""
        col_map = {"3d": "notificado_3d", "1d": "notificado_1d", "hoje": "notificado_hoje"}
        col = col_map.get(nivel)
        if not col:
            return
        conn = self._conn()
        conn.execute(f"UPDATE prazos SET {col} = 1 WHERE id = ?", (prazo_id,))
        conn.commit()
        conn.close()

    def atualizar_ultima_busca(self, chat_id):
        conn = self._conn()
        conn.execute("UPDATE advogados SET ultima_busca_djen = datetime('now','localtime') WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()

    def comunicacao_existe(self, advogado_id, numero_processo, data_disponibilizacao):
        conn = self._conn()
        row = conn.execute(
            "SELECT id FROM comunicacoes_djen WHERE advogado_id = ? AND numero_processo = ? AND data_disponibilizacao = ?",
            (advogado_id, numero_processo, data_disponibilizacao)).fetchone()
        conn.close()
        return row is not None
