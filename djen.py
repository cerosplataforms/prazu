"""
Módulo de consulta ao DJEN (Diário de Justiça Eletrônico Nacional)
Via API REST pública: https://comunicaapi.pje.jus.br/api/v1/comunicacao

Sem Selenium. Usa requests direto. Rápido e confiável.

Parâmetros descobertos:
  - numeroOab + uf -> filtra por advogado (ex: numeroOab=189751&uf=MG)
  - siglaTribunal -> filtra por tribunal (ex: TJMG, TRT2)
  - pagina + itensPorPagina -> paginação
"""

import logging
import re
import requests
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

API_URL = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
TIMEOUT = 20
MAX_RESULTS = 200


def consultar_djen_por_oab(
    numero_oab: str,
    estado: str = "MG",
    dias_retroativos: int = 365,
) -> list[dict]:
    oab_limpo = re.sub(r"[^0-9]", "", str(numero_oab))
    estado_upper = estado.upper()
    data_limite = date.today() - timedelta(days=dias_retroativos)
    oab_com_uf = f"{estado_upper}{oab_limpo}"

    logger.info(f"DJEN API: Consultando OAB {oab_limpo}/{estado_upper} (ultimos {dias_retroativos}d)")

    comunicacoes = []
    pagina = 1
    itens_por_pagina = 50

    try:
        while len(comunicacoes) < MAX_RESULTS:
            params = {
                "numeroOab": oab_com_uf,
                "pagina": pagina,
                "itensPorPagina": itens_por_pagina,
            }

            resp = requests.get(API_URL, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "success" or not data.get("items"):
                break

            items = data["items"]
            logger.info(f"DJEN API: Pagina {pagina}, {len(items)} itens (total server: {data.get('count', '?')})")

            encontrou_antigo = False
            for item in items:
                com = _parsear_item_api(item)
                if not com:
                    continue

                if com["data_disponibilizacao"]:
                    try:
                        dt = datetime.strptime(com["data_disponibilizacao"], "%Y-%m-%d").date()
                        if dt < data_limite:
                            encontrou_antigo = True
                            break
                    except ValueError:
                        pass

                comunicacoes.append(com)

                if len(comunicacoes) >= MAX_RESULTS:
                    break

            if encontrou_antigo or len(items) < itens_por_pagina:
                break

            pagina += 1

            if pagina > 10:
                break

    except requests.RequestException as e:
        logger.error(f"DJEN API: Erro de rede: {e}")
    except Exception as e:
        logger.error(f"DJEN API: Erro: {e}")

    logger.info(f"DJEN API: {len(comunicacoes)} publicacoes OAB {oab_limpo}/{estado_upper} (ultimos {dias_retroativos}d)")
    return comunicacoes


def consultar_djen_por_processo(numero_cnj: str, dias_retroativos: int = 30) -> list[dict]:
    numero_limpo = re.sub(r"[^0-9]", "", numero_cnj)
    logger.info(f"DJEN API: Consultando processo {numero_cnj}")

    try:
        params = {"pagina": 1, "itensPorPagina": 50}
        resp = requests.get(API_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        comunicacoes = []
        if data.get("items"):
            for item in data["items"]:
                proc_num = str(item.get("numero_processo", ""))
                if numero_limpo in proc_num or numero_cnj in item.get("numeroprocessocommascara", ""):
                    com = _parsear_item_api(item)
                    if com:
                        comunicacoes.append(com)

        logger.info(f"DJEN API: {len(comunicacoes)} publicacoes processo {numero_cnj}")
        return comunicacoes

    except Exception as e:
        logger.error(f"DJEN API: Erro: {e}")
        return []


def _parsear_item_api(item: dict) -> dict | None:
    if not item:
        return None

    numero_formatado = item.get("numeroprocessocommascara", "")
    if not numero_formatado:
        num = str(item.get("numero_processo", ""))
        if len(num) == 20:
            numero_formatado = f"{num[:7]}-{num[7:9]}.{num[9:13]}.{num[13]}.{num[14:16]}.{num[16:]}"
        else:
            numero_formatado = num

    texto = item.get("texto", "")
    if texto:
        texto = re.sub(r'<[^>]+>', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        texto = texto[:500]

    return {
        "numero_processo": numero_formatado,
        "tribunal": item.get("siglaTribunal", ""),
        "conteudo": texto,
        "data_disponibilizacao": item.get("data_disponibilizacao", ""),
        "data_publicacao": "",
        "tipo": item.get("tipoComunicacao", "publicacao"),
        "caderno": item.get("meio", ""),
        "orgao": item.get("nomeOrgao", ""),
        "classe": item.get("nomeClasse", ""),
        "link": item.get("link", ""),
        "destinatarios": item.get("destinatarios", []),
        "advogados": item.get("destinatarioadvogados", []),
        "id_djen": item.get("id"),
        "ativo": item.get("ativo", True),
    }


# ============================================================
# INTEGRACAO COM BOT
# ============================================================
def formatar_comunicacoes_telegram(comunicacoes: list[dict], limite: int = 5) -> str:
    if not comunicacoes:
        return "Nenhuma publicacao encontrada no DJEN nos ultimos 30 dias."

    total = len(comunicacoes)
    msg = f"*{total} publicacao(oes) no DJEN (ultimos 30 dias):*\n\n"

    for i, c in enumerate(comunicacoes[:limite], 1):
        data = c.get("data_disponibilizacao", "")
        if data and "-" in data:
            try:
                data = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                pass

        msg += f"*{i}.* `{c['numero_processo']}`\n"

        if c.get("tribunal"):
            msg += f"   {c['tribunal']}"
            if c.get("orgao"):
                msg += f" - {c['orgao'][:50]}"
            msg += "\n"

        # Comarca usada no cálculo do prazo
        comarca_proc = c.get("comarca_processo", "")
        uf_proc = c.get("uf_processo", "")
        if comarca_proc:
            msg += f"   📍 {comarca_proc}/{uf_proc}\n"

        if data:
            msg += f"   Disp: {data}\n"

        if c.get("tipo"):
            msg += f"   {c['tipo']}\n"

        if c.get("classe"):
            msg += f"   {c['classe'][:60]}\n"

        # Prazo calculado
        pi = c.get("prazo_info")
        if pi:
            venc = pi.get("data_vencimento", "")
            if venc and "-" in venc:
                try:
                    venc = datetime.strptime(venc, "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError:
                    pass
            emoji = pi.get("emoji", "📅")
            status = pi.get("status", "")
            msg += f"   {emoji} Prazo: *{venc}* — {status}\n"
            if not comarca_proc:
                msg += f"   ⚠️ _Comarca não identificada — usando padrão_\n"

        if c.get("link"):
            msg += f"   [Ver no PJe]({c['link']})\n"

        if c.get("conteudo"):
            resumo = c["conteudo"][:120]
            msg += f"   _{resumo}..._\n"

        msg += "\n"

    if total > limite:
        msg += f"_... e mais {total - limite} publicacao(oes). Use /publicacoes para ver todas._"

    return msg


def importar_comunicacoes_para_banco(db, advogado_id: int, comunicacoes: list[dict]) -> int:
    novos = 0
    for c in comunicacoes:
        try:
            conn = db._conn()
            existing = conn.execute(
                "SELECT id FROM comunicacoes_djen WHERE advogado_id = ? AND numero_processo = ? AND data_disponibilizacao = ?",
                (advogado_id, c["numero_processo"], c.get("data_disponibilizacao", "")),
            ).fetchone()
            conn.close()

            if existing:
                continue

            db.salvar_comunicacao(
                advogado_id=advogado_id,
                numero_processo=c["numero_processo"],
                tribunal=c.get("tribunal", ""),
                conteudo=c.get("conteudo", ""),
                data_disponibilizacao=c.get("data_disponibilizacao", ""),
                data_publicacao=c.get("data_publicacao", ""),
                tipo_comunicacao=c.get("tipo", ""),
            )
            novos += 1
        except Exception as e:
            logger.error(f"Erro salvar comunicacao: {e}")
    return novos


DATAJUD_API_KEY = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

TRIBUNAL_DATAJUD = {
    "TJMG": "tjmg", "TJSP": "tjsp", "TJRJ": "tjrj", "TJPR": "tjpr",
    "TJRS": "tjrs", "TJSC": "tjsc", "TJBA": "tjba", "TJPE": "tjpe",
    "TJCE": "tjce", "TJGO": "tjgo", "TJPA": "tjpa", "TJMA": "tjma",
    "TJMT": "tjmt", "TJMS": "tjms", "TJES": "tjes", "TJAL": "tjal",
    "TJSE": "tjse", "TJRN": "tjrn", "TJPB": "tjpb", "TJPI": "tjpi",
    "TJAM": "tjam", "TJRO": "tjro", "TJAC": "tjac", "TJAP": "tjap",
    "TJRR": "tjrr", "TJTO": "tjto", "TJDFT": "tjdft",
    "TRT1": "trt1", "TRT2": "trt2", "TRT3": "trt3", "TRT4": "trt4",
    "TRT5": "trt5", "TRT6": "trt6", "TRT7": "trt7", "TRT8": "trt8",
    "TRT9": "trt9", "TRT10": "trt10", "TRT11": "trt11", "TRT12": "trt12",
    "TRT13": "trt13", "TRT14": "trt14", "TRT15": "trt15",
    "TRT16": "trt16", "TRT17": "trt17", "TRT18": "trt18",
    "TRT19": "trt19", "TRT20": "trt20", "TRT21": "trt21",
    "TRT22": "trt22", "TRT23": "trt23", "TRT24": "trt24",
    "TRF1": "trf1", "TRF2": "trf2", "TRF3": "trf3", "TRF4": "trf4",
    "TRF5": "trf5", "TRF6": "trf6",
    "TST": "tst", "STJ": "stj", "STF": "stf",
    "STM": "stm", "TJMMG": "tjmmg", "TJMSP": "tjmsp", "TJMRS": "tjmrs",
    "TSE": "tse",
    "TRE-MG": "tre-mg", "TRE-SP": "tre-sp", "TRE-RJ": "tre-rj",
    "TREMG": "tre-mg", "TRESP": "tre-sp", "TRERJ": "tre-rj",
}

MOVS_MANIFESTACAO = {
    "petição", "peticao", "juntada de petição", "juntada de peticao",
    "juntada de documento", "juntada", "contestação", "contestacao",
    "réplica", "replica", "impugnação", "impugnacao",
    "embargos de declaração", "embargos de declaracao",
    "recurso", "agravo", "apelação", "apelacao",
    "contrarrazões", "contrarrazoes", "manifestação", "manifestacao",
    "documento",
}

MOVS_DECURSO = {
    "decurso de prazo", "certidão de decurso de prazo",
    "certidao de decurso de prazo",
}


def consultar_datajud_processo(numero_cnj: str, tribunal: str = "") -> dict | None:
    numero_limpo = re.sub(r"[^0-9]", "", numero_cnj)

    alias = TRIBUNAL_DATAJUD.get(tribunal, "")
    if not alias and len(numero_limpo) == 20:
        j = numero_limpo[13]
        tr = numero_limpo[14:16]
        if j == "8":
            uf_map = {
                "13": "tjmg", "26": "tjsp", "19": "tjrj", "16": "tjpr",
                "21": "tjrs", "24": "tjsc", "05": "tjba", "17": "tjpe",
                "06": "tjce", "09": "tjgo", "14": "tjpa", "10": "tjma",
                "11": "tjmt", "12": "tjms", "08": "tjes", "02": "tjal",
                "25": "tjse", "20": "tjrn", "15": "tjpb", "18": "tjpi",
                "04": "tjam", "22": "tjro", "01": "tjac", "03": "tjap",
                "23": "tjrr", "27": "tjto", "07": "tjdft",
            }
            alias = uf_map.get(tr, "")
        elif j == "5":
            alias = f"trt{int(tr)}"
        elif j == "4":
            alias = f"trf{int(tr)}"

    if not alias:
        logger.warning(f"DataJud: Tribunal nao mapeado para {numero_cnj} ({tribunal})")
        return None

    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{alias}/_search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": DATAJUD_API_KEY,
    }
    body = {
        "query": {"match": {"numeroProcesso": numero_limpo}},
        "_source": ["numeroProcesso", "classe", "orgaoJulgador", "movimentos",
                     "dataAjuizamento", "assuntos"],
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            logger.info(f"DataJud: Nenhum resultado para {numero_cnj}")
            return None

        source = hits[0]["_source"]
        movimentos = source.get("movimentos", [])
        movimentos.sort(key=lambda m: m.get("dataHora", ""), reverse=True)

        logger.info(f"DataJud: {numero_cnj} -> {len(movimentos)} movimentacoes")

        return {
            "numero_processo": numero_cnj,
            "classe": source.get("classe", {}).get("nome", ""),
            "orgao": source.get("orgaoJulgador", {}).get("nome", ""),
            "data_ajuizamento": source.get("dataAjuizamento", ""),
            "assuntos": [a.get("nome", "") for a in source.get("assuntos", [])],
            "movimentos": movimentos,
            "total_movimentos": len(movimentos),
        }

    except requests.RequestException as e:
        logger.error(f"DataJud: Erro rede {numero_cnj}: {e}")
        return None
    except Exception as e:
        logger.error(f"DataJud: Erro {numero_cnj}: {e}")
        return None


def verificar_prazo_cumprido(
    numero_cnj: str,
    tribunal: str,
    data_intimacao: str,
    data_vencimento: str,
) -> dict:
    """
    Verifica se o prazo de uma intimação foi cumprido consultando DataJud.
    
    Lógica:
    - cumprido: juntada/petição após a intimação
    - decurso: certidão de decurso no DataJud
    - vencido_verificar: venceu sem decurso e sem juntada
    - em_aberto: prazo ainda não venceu
    """
    resultado = {
        "status": "sem_dados",
        "manifestacao": None,
        "data_manifestacao": None,
    }

    datajud = consultar_datajud_processo(numero_cnj, tribunal)
    if not datajud or not datajud.get("movimentos"):
        return resultado

    try:
        dt_intimacao = datetime.strptime(data_intimacao, "%Y-%m-%d")
    except (ValueError, TypeError):
        return resultado

    try:
        dt_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d")
    except (ValueError, TypeError):
        dt_vencimento = None

    hoje = datetime.now()

    for mov in datajud["movimentos"]:
        data_mov_str = mov.get("dataHora", "")[:10]
        if not data_mov_str:
            continue

        try:
            dt_mov = datetime.strptime(data_mov_str, "%Y-%m-%d")
        except ValueError:
            continue

        # Só olha movimentações APÓS a intimação
        if dt_mov <= dt_intimacao:
            continue

        nome_mov = (mov.get("nome") or "").lower()

        # Verifica se é manifestação (prazo cumprido)
        for termo in MOVS_MANIFESTACAO:
            if termo in nome_mov:
                data_fmt = dt_mov.strftime("%d/%m/%Y")
                nome_display = mov.get("nome", "Manifestacao")
                resultado["status"] = "cumprido"
                resultado["manifestacao"] = f"{nome_display} em {data_fmt}"
                resultado["data_manifestacao"] = data_mov_str
                logger.info(f"DataJud verificacao: {numero_cnj} → CUMPRIDO ({nome_display} em {data_fmt})")
                return resultado

        # Verifica decurso de prazo
        for termo in MOVS_DECURSO:
            if termo in nome_mov:
                resultado["status"] = "decurso"
                resultado["manifestacao"] = f"Decurso em {dt_mov.strftime('%d/%m/%Y')}"
                resultado["data_manifestacao"] = data_mov_str
                logger.info(f"DataJud verificacao: {numero_cnj} → DECURSO")
                return resultado

    # Nenhuma movimentação relevante encontrada
    if dt_vencimento and hoje > dt_vencimento:
        resultado["status"] = "vencido_verificar"
        logger.info(f"DataJud verificacao: {numero_cnj} → VENCIDO_VERIFICAR (sem juntada nem decurso)")
    else:
        resultado["status"] = "em_aberto"
        logger.info(f"DataJud verificacao: {numero_cnj} → EM_ABERTO")
    return resultado


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Uso:")
        print("  python djen.py NUMERO_OAB UF")
        print("  python djen.py --processo NUMERO_CNJ")
        sys.exit(1)

    if sys.argv[1] == "--processo":
        numero = sys.argv[2] if len(sys.argv) > 2 else ""
        resultados = consultar_djen_por_processo(numero)
    else:
        oab = sys.argv[1]
        uf = sys.argv[2] if len(sys.argv) > 2 else "MG"
        print(f"\nDJEN: OAB {oab}/{uf} (ultimos 30 dias)\n")
        resultados = consultar_djen_por_oab(oab, uf, dias_retroativos=30)

    if resultados:
        print(f"\n{len(resultados)} resultado(s):\n")
        for i, r in enumerate(resultados, 1):
            print(f"{i}. {r['numero_processo']}")
            print(f"   Tribunal: {r['tribunal']}")
            print(f"   Disponibilizacao: {r['data_disponibilizacao']}")
            print(f"   Tipo: {r['tipo']}")
            print()
    else:
        print("\nNenhum resultado encontrado.")
