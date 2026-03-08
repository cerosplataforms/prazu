"""
calendar_store.py — Armazém de feriados forenses (SQLite)
=========================================================

Schema v2 normalizado com:
- Tabela `tribunais` (id, nome, sigla, justica, uf, regimento_feriados)
- Tabela `localidades` (id, tribunal_id, nome, tipo, uf)
- Tabela `eventos` (data, descricao, tipo, abrangencia, uf, tribunal_id, localidade_id, ...)

Retrocompatível: detecta automaticamente se o banco é v1 (holidays) ou v2 (eventos).

Mapeamento de tipos v2 → legado (para resolver/Telegram):
  feriado_nacional   → nacional
  feriado_estadual   → estadual_tj
  feriado_forense    → estadual_tj
  feriado_municipal  → municipal_forense
  ponto_facultativo  → suspensao_tj
  recesso            → recesso
  suspensao          → suspensao_tj
"""

import re
import sqlite3
import hashlib
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)

TIPO_LEGADO = {
    'feriado_nacional': 'nacional',
    'feriado_estadual': 'estadual_tj',
    'feriado_forense': 'estadual_tj',
    'feriado_municipal': 'municipal_forense',
    'ponto_facultativo': 'suspensao_tj',
    'recesso': 'recesso',
    'suspensao': 'suspensao_tj',
}


def _detect_schema(conn) -> int:
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if 'eventos' in tables and 'localidades' in tables:
        return 2
    if 'holidays' in tables:
        return 1
    return 0


class CalendarStore:
    """Gerencia o banco de feriados forenses. Suporta schema v1 e v2."""

    def __init__(self, db_path: str = "calendar_v2.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.schema = _detect_schema(self.conn)
        if self.schema == 0:
            raise RuntimeError(f"Banco {db_path} sem schema reconhecido")
        logger.info(f"CalendarStore: {db_path} schema v{self.schema}")

    # ==========================================================
    # CONSULTA
    # ==========================================================
    def obter_feriados(self, ano=2026, uf=None, comarca=None) -> list[dict]:
        if self.schema == 2:
            return self._obter_v2(ano, uf, comarca)
        return self._obter_v1(ano, uf, comarca)

    def _obter_v2(self, ano, uf, comarca):
        params = [ano]
        filters = ["(e.abrangencia = 'nacional')"]

        if uf:
            filters.append(
                "(e.abrangencia IN ('estadual','tribunal') AND (e.uf = ? OR e.uf IS NULL) AND e.tribunal_id IN (SELECT id FROM tribunais WHERE uf = ?))")
            params.append(uf)
            params.append(uf)
            # Pega também suspensões do TJ (ex: Carnaval TJMG salvo como abrangencia=municipal)
            filters.append(
                "(e.abrangencia = 'municipal' AND e.uf = ? AND e.localidade_id IS NULL)")
            params.append(uf)
        if comarca and uf:
            filters.append(
                "(e.abrangencia = 'municipal' AND e.uf = ? AND l.nome = ?)")
            params.append(uf)
            params.append(comarca)

        sql = f"""
            SELECT e.data, e.descricao, e.tipo, e.abrangencia, e.uf,
                   e.tribunal_id, e.fonte, e.confianca,
                   COALESCE(l.nome, '') as comarca
            FROM eventos e
            LEFT JOIN localidades l ON e.localidade_id = l.id
            WHERE e.ano = ? AND ({' OR '.join(filters)})
            ORDER BY e.data
        """
        return [self._row_to_dict(r) for r in self.conn.execute(sql, params)]

    def _obter_v1(self, ano, uf, comarca):
        params = [ano]
        tf = "tipo IN ('nacional','recesso')"
        if uf:
            tf += " OR (tipo IN ('estadual_tj','suspensao_tj') AND uf = ?)"
            params.append(uf)
        if comarca:
            tf += " OR (tipo = 'municipal_forense' AND uf = ? AND comarca = ?)"
            params.append(uf or "")
            params.append(comarca)

        rows = self.conn.execute(f"""
            SELECT data, descricao, tipo, uf, comarca, tribunal, fonte, confianca
            FROM holidays WHERE ano = ? AND ({tf}) ORDER BY data
        """, params).fetchall()
        return [dict(r) for r in rows]

    def obter_set(self, ano=2026, uf=None, comarca=None) -> set:
        return {f["data"] for f in self.obter_feriados(ano, uf, comarca)}

    # ----------------------------------------------------------
    def explicar_data(self, data, uf=None, comarca=None) -> list[dict]:
        if self.schema == 2:
            return self._explicar_v2(data, uf, comarca)
        return self._explicar_v1(data, uf, comarca)

    def _explicar_v2(self, data, uf, comarca):
        """
        Retorna razões para uma data não ser útil.
        Lógica de filtro por tribunal:
          - nacionais sem tribunal_id (genéricos) → 1 registro
          - tribunal da UF solicitada (e.uf = uf) → apenas o TJ local
          - municipais da comarca solicitada
        """
        import unicodedata

        # Nacional genérico (tribunal_id IS NULL)
        filters = ["(e.abrangencia = 'nacional' AND e.tribunal_id IS NULL AND e.tipo != 'recesso')"]
        params = [data]

        if uf:
            # TJ da UF: eventos estaduais/tribunal vinculados à UF (exceto recesso — tratado pelo resolver)
            filters.append(
                "(e.abrangencia IN ('estadual','tribunal') AND e.uf = ? AND e.tipo != 'recesso')")
            params.append(uf)

        if comarca and uf:
            filters.append(
                "(e.abrangencia = 'municipal' AND (e.uf = ? OR e.uf IS NULL) AND l.nome = ?)")
            params.append(uf)
            params.append(comarca)

        sql = f"""
            SELECT e.data, e.descricao, e.tipo, e.abrangencia, e.uf,
                   e.tribunal_id, e.fonte, e.confianca,
                   COALESCE(l.nome, '') as comarca
            FROM eventos e
            LEFT JOIN localidades l ON e.localidade_id = l.id
            WHERE e.data = ? AND ({' OR '.join(filters)})
            ORDER BY
                CASE e.tipo
                    WHEN 'suspensao' THEN 1
                    WHEN 'feriado_nacional' THEN 2
                    WHEN 'feriado_estadual' THEN 3
                    WHEN 'feriado_forense' THEN 4
                    WHEN 'ponto_facultativo' THEN 5
                    WHEN 'feriado_municipal' THEN 6
                    WHEN 'recesso' THEN 7
                END
        """
        rows = [self._row_to_dict(r) for r in self.conn.execute(sql, params)]

        # Deduplica por (descricao base normalizada, tipo legado)
        def _base_desc(s):
            s = s.strip().lower()
            s = re.sub(r'\s*\(.*?\)', '', s)
            s = re.sub(r'[\s-]+', ' ', s).strip()
            s = unicodedata.normalize('NFD', s)
            s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
            return s

        seen = {}
        deduped = []
        for r in rows:
            key = (_base_desc(r['descricao']), r['tipo'])
            if key not in seen:
                seen[key] = True
                deduped.append(r)
        return deduped

    def _explicar_v1(self, data, uf, comarca):
        params = [data]
        tf = "tipo IN ('nacional','recesso')"
        if uf:
            tf += " OR (tipo IN ('estadual_tj','suspensao_tj') AND uf = ?)"
            params.append(uf)
        if comarca:
            tf += " OR (tipo = 'municipal_forense' AND uf = ? AND comarca = ?)"
            params.append(uf or "")
            params.append(comarca)
        rows = self.conn.execute(f"""
            SELECT data, descricao, tipo, uf, comarca, tribunal, fonte, confianca
            FROM holidays WHERE data = ? AND ({tf})
            ORDER BY CASE tipo
                WHEN 'suspensao_tj' THEN 1 WHEN 'nacional' THEN 2
                WHEN 'estadual_tj' THEN 3 WHEN 'municipal_forense' THEN 4
                WHEN 'recesso' THEN 5 END
        """, params).fetchall()
        return [dict(r) for r in rows]

    # ----------------------------------------------------------
    def contar(self, ano=2026, uf=None) -> dict:
        if self.schema == 2:
            params = [ano]
            w = "ano = ?"
            if uf:
                w += " AND (uf = ? OR abrangencia = 'nacional')"
                params.append(uf)
            rows = self.conn.execute(f"""
                SELECT tipo, COUNT(*) as total FROM eventos WHERE {w} GROUP BY tipo
            """, params).fetchall()
            result = {}
            for r in rows:
                leg = TIPO_LEGADO.get(r['tipo'], r['tipo'])
                result[leg] = result.get(leg, 0) + r['total']
            return result
        else:
            params = [ano]
            w = "ano = ?"
            if uf:
                w += " AND (uf = ? OR uf = '')"
                params.append(uf)
            rows = self.conn.execute(f"""
                SELECT tipo, COUNT(*) as total FROM holidays WHERE {w} GROUP BY tipo
            """, params).fetchall()
            return {r["tipo"]: r["total"] for r in rows}

    def listar_comarcas(self, uf: str) -> list[str]:
        if self.schema == 2:
            rows = self.conn.execute("""
                SELECT DISTINCT l.nome FROM localidades l
                JOIN eventos e ON e.localidade_id = l.id
                WHERE l.uf = ? AND e.abrangencia = 'municipal'
                ORDER BY l.nome
            """, (uf,)).fetchall()
            return [r['nome'] for r in rows]
        else:
            rows = self.conn.execute("""
                SELECT DISTINCT comarca FROM holidays
                WHERE uf = ? AND tipo = 'municipal_forense' AND comarca != ''
                ORDER BY comarca
            """, (uf,)).fetchall()
            return [r["comarca"] for r in rows]

    def listar_fontes(self, ano=2026) -> list[dict]:
        if self.schema == 2:
            return [dict(r) for r in self.conn.execute(
                "SELECT id, nome, sigla, regimento_feriados as fonte FROM tribunais ORDER BY id")]
        else:
            return [dict(r) for r in self.conn.execute(
                "SELECT * FROM holiday_sources WHERE ano = ? ORDER BY data_carga DESC", (ano,))]

    # ==========================================================
    # INSERÇÃO (compatibilidade / testes)
    # ==========================================================
    def inserir_feriado(self, data, descricao, tipo, uf="", comarca="",
                        tribunal="", fonte="", confianca="high") -> bool:
        if self.schema == 2:
            return self._inserir_v2(data, descricao, tipo, uf, comarca, tribunal, fonte, confianca)
        return self._inserir_v1(data, descricao, tipo, uf, comarca, tribunal, fonte, confianca)

    def _inserir_v2(self, data, descricao, tipo, uf, comarca, tribunal, fonte, confianca):
        ano = int(data[:4])
        tipo_rev = {v: k for k, v in TIPO_LEGADO.items()}
        tipo_v2 = tipo_rev.get(tipo, tipo)
        abr = 'municipal' if 'municipal' in tipo else ('nacional' if 'nacional' in tipo else 'tribunal')
        h = hashlib.md5(f"{data}{descricao}{comarca}{tribunal}".encode()).hexdigest()[:16]
        try:
            self.conn.execute("""
                INSERT OR IGNORE INTO eventos
                (data,ano,descricao,tipo,abrangencia,uf,tribunal_id,
                 suspende_prazo,suspende_expediente,suspende_eletronico,meio_expediente,
                 fonte,confianca,hash)
                VALUES (?,?,?,?,?,?,?,1,1,1,0,?,?,?)
            """, (data, ano, descricao, tipo_v2, abr, uf, tribunal, fonte, confianca, h))
            self.conn.commit()
            return self.conn.total_changes > 0
        except sqlite3.Error as e:
            logger.error(f"Erro inserir {data}: {e}")
            return False

    def _inserir_v1(self, data, descricao, tipo, uf, comarca, tribunal, fonte, confianca):
        ano = int(data[:4])
        h = hashlib.sha256(f"{data}|{tipo}|{uf}|{comarca}".encode()).hexdigest()[:16]
        try:
            self.conn.execute("""
                INSERT OR IGNORE INTO holidays
                (data,ano,descricao,tipo,uf,comarca,tribunal,fonte,confianca,hash)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (data, ano, descricao, tipo, uf, comarca, tribunal, fonte, confianca, h))
            self.conn.commit()
            return self.conn.total_changes > 0
        except sqlite3.Error as e:
            logger.error(f"Erro inserir {data}: {e}")
            return False

    # ==========================================================
    # HELPERS
    # ==========================================================
    def _row_to_dict(self, r) -> dict:
        return {
            'data': r['data'],
            'descricao': r['descricao'],
            'tipo': TIPO_LEGADO.get(r['tipo'], 'estadual_tj'),
            'uf': r['uf'] or '',
            'comarca': r['comarca'] or '',
            'tribunal': r['tribunal_id'] or '',
            'fonte': r['fonte'] or '',
            'confianca': r['confianca'] or 'high',
        }

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import os
    for db in ["calendar_v2.db", "calendar.db"]:
        if os.path.exists(db):
            store = CalendarStore(db)
            f = store.obter_feriados(2026, "SP", "São Paulo")
            print(f"{db} (v{store.schema}): SP/São Paulo = {len(f)} feriados")
            print(f"  Comarcas SP: {len(store.listar_comarcas('SP'))}")
            store.close()
            break
    print("✅ OK")
