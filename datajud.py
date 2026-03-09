"""
Módulo de consulta ao DataJud (CNJ) — API Pública Nacional
Consulta processos de TODOS os tribunais do Brasil via Elasticsearch.

API: https://api-publica.datajud.cnj.jus.br/
Docs: https://datajud-wiki.cnj.jus.br/api-publica/

A chave é PÚBLICA (mesma pra todo mundo, disponibilizada pelo CNJ).
Formato: POST com body Elasticsearch Query DSL.
"""

import requests
import logging
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# CHAVE PÚBLICA DO CNJ (verificar se ainda é válida em:
# https://datajud-wiki.cnj.jus.br/api-publica/acesso )
# ============================================================
DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"

HEADERS = {
    "Authorization": f"APIKey {DATAJUD_API_KEY}",
    "Content-Type": "application/json",
}

# ============================================================
# MAPEAMENTO DE TRIBUNAIS
# O número do processo CNJ contém o código do tribunal:
# NNNNNNN-DD.AAAA.J.TR.OOOO
#                    ^  ^^
#                    J  TR
# J = Justiça (5=trabalho, 8=estadual, 4=federal, etc)
# TR = Tribunal (06=CE, 26=SP, etc)
# ============================================================

TRIBUNAIS = {
    # Tribunais Superiores
    "3.00": {"alias": "api_publica_stj", "nome": "Superior Tribunal de Justiça"},
    "5.00": {"alias": "api_publica_tst", "nome": "Tribunal Superior do Trabalho"},

    # Justiça Federal (J=4)
    "4.01": {"alias": "api_publica_trf1", "nome": "TRF da 1ª Região"},
    "4.02": {"alias": "api_publica_trf2", "nome": "TRF da 2ª Região"},
    "4.03": {"alias": "api_publica_trf3", "nome": "TRF da 3ª Região"},
    "4.04": {"alias": "api_publica_trf4", "nome": "TRF da 4ª Região"},
    "4.05": {"alias": "api_publica_trf5", "nome": "TRF da 5ª Região"},
    "4.06": {"alias": "api_publica_trf6", "nome": "TRF da 6ª Região"},

    # Justiça do Trabalho (J=5)
    "5.01": {"alias": "api_publica_trt1", "nome": "TRT da 1ª Região (RJ)"},
    "5.02": {"alias": "api_publica_trt2", "nome": "TRT da 2ª Região (SP)"},
    "5.03": {"alias": "api_publica_trt3", "nome": "TRT da 3ª Região (MG)"},
    "5.04": {"alias": "api_publica_trt4", "nome": "TRT da 4ª Região (RS)"},
    "5.05": {"alias": "api_publica_trt5", "nome": "TRT da 5ª Região (BA)"},
    "5.06": {"alias": "api_publica_trt6", "nome": "TRT da 6ª Região (PE)"},
    "5.07": {"alias": "api_publica_trt7", "nome": "TRT da 7ª Região (CE)"},
    "5.08": {"alias": "api_publica_trt8", "nome": "TRT da 8ª Região (PA/AP)"},
    "5.09": {"alias": "api_publica_trt9", "nome": "TRT da 9ª Região (PR)"},
    "5.10": {"alias": "api_publica_trt10", "nome": "TRT da 10ª Região (DF/TO)"},
    "5.11": {"alias": "api_publica_trt11", "nome": "TRT da 11ª Região (AM/RR)"},
    "5.12": {"alias": "api_publica_trt12", "nome": "TRT da 12ª Região (SC)"},
    "5.13": {"alias": "api_publica_trt13", "nome": "TRT da 13ª Região (PB)"},
    "5.14": {"alias": "api_publica_trt14", "nome": "TRT da 14ª Região (RO/AC)"},
    "5.15": {"alias": "api_publica_trt15", "nome": "TRT da 15ª Região (Campinas)"},
    "5.16": {"alias": "api_publica_trt16", "nome": "TRT da 16ª Região (MA)"},
    "5.17": {"alias": "api_publica_trt17", "nome": "TRT da 17ª Região (ES)"},
    "5.18": {"alias": "api_publica_trt18", "nome": "TRT da 18ª Região (GO)"},
    "5.19": {"alias": "api_publica_trt19", "nome": "TRT da 19ª Região (AL)"},
    "5.20": {"alias": "api_publica_trt20", "nome": "TRT da 20ª Região (SE)"},
    "5.21": {"alias": "api_publica_trt21", "nome": "TRT da 21ª Região (RN)"},
    "5.22": {"alias": "api_publica_trt22", "nome": "TRT da 22ª Região (PI)"},
    "5.23": {"alias": "api_publica_trt23", "nome": "TRT da 23ª Região (MT)"},
    "5.24": {"alias": "api_publica_trt24", "nome": "TRT da 24ª Região (MS)"},

    # Justiça Estadual (J=8)
    "8.01": {"alias": "api_publica_tjac", "nome": "TJAC (Acre)"},
    "8.02": {"alias": "api_publica_tjal", "nome": "TJAL (Alagoas)"},
    "8.03": {"alias": "api_publica_tjap", "nome": "TJAP (Amapá)"},
    "8.04": {"alias": "api_publica_tjam", "nome": "TJAM (Amazonas)"},
    "8.05": {"alias": "api_publica_tjba", "nome": "TJBA (Bahia)"},
    "8.06": {"alias": "api_publica_tjce", "nome": "TJCE (Ceará)"},
    "8.07": {"alias": "api_publica_tjdft", "nome": "TJDFT (Distrito Federal)"},
    "8.08": {"alias": "api_publica_tjes", "nome": "TJES (Espírito Santo)"},
    "8.09": {"alias": "api_publica_tjgo", "nome": "TJGO (Goiás)"},
    "8.10": {"alias": "api_publica_tjma", "nome": "TJMA (Maranhão)"},
    "8.11": {"alias": "api_publica_tjmt", "nome": "TJMT (Mato Grosso)"},
    "8.12": {"alias": "api_publica_tjms", "nome": "TJMS (Mato Grosso do Sul)"},
    "8.13": {"alias": "api_publica_tjmg", "nome": "TJMG (Minas Gerais)"},
    "8.14": {"alias": "api_publica_tjpa", "nome": "TJPA (Pará)"},
    "8.15": {"alias": "api_publica_tjpb", "nome": "TJPB (Paraíba)"},
    "8.16": {"alias": "api_publica_tjpr", "nome": "TJPR (Paraná)"},
    "8.17": {"alias": "api_publica_tjpe", "nome": "TJPE (Pernambuco)"},
    "8.18": {"alias": "api_publica_tjpi", "nome": "TJPI (Piauí)"},
    "8.19": {"alias": "api_publica_tjrj", "nome": "TJRJ (Rio de Janeiro)"},
    "8.20": {"alias": "api_publica_tjrn", "nome": "TJRN (Rio Grande do Norte)"},
    "8.21": {"alias": "api_publica_tjrs", "nome": "TJRS (Rio Grande do Sul)"},
    "8.22": {"alias": "api_publica_tjro", "nome": "TJRO (Rondônia)"},
    "8.23": {"alias": "api_publica_tjrr", "nome": "TJRR (Roraima)"},
    "8.24": {"alias": "api_publica_tjsc", "nome": "TJSC (Santa Catarina)"},
    "8.25": {"alias": "api_publica_tjse", "nome": "TJSE (Sergipe)"},
    "8.26": {"alias": "api_publica_tjsp", "nome": "TJSP (São Paulo)"},
    "8.27": {"alias": "api_publica_tjto", "nome": "TJTO (Tocantins)"},

    # Justiça Eleitoral (J=6)
    "6.01": {"alias": "api_publica_tre-ac", "nome": "TRE-AC"},
    "6.02": {"alias": "api_publica_tre-al", "nome": "TRE-AL"},
    "6.03": {"alias": "api_publica_tre-ap", "nome": "TRE-AP"},
    "6.04": {"alias": "api_publica_tre-am", "nome": "TRE-AM"},
    "6.05": {"alias": "api_publica_tre-ba", "nome": "TRE-BA"},
    "6.06": {"alias": "api_publica_tre-ce", "nome": "TRE-CE"},
    "6.07": {"alias": "api_publica_tre-df", "nome": "TRE-DF"},
    "6.08": {"alias": "api_publica_tre-es", "nome": "TRE-ES"},
    "6.09": {"alias": "api_publica_tre-go", "nome": "TRE-GO"},
    "6.10": {"alias": "api_publica_tre-ma", "nome": "TRE-MA"},
    "6.11": {"alias": "api_publica_tre-mt", "nome": "TRE-MT"},
    "6.12": {"alias": "api_publica_tre-ms", "nome": "TRE-MS"},
    "6.13": {"alias": "api_publica_tre-mg", "nome": "TRE-MG"},
    "6.14": {"alias": "api_publica_tre-pa", "nome": "TRE-PA"},
    "6.15": {"alias": "api_publica_tre-pb", "nome": "TRE-PB"},
    "6.16": {"alias": "api_publica_tre-pr", "nome": "TRE-PR"},
    "6.17": {"alias": "api_publica_tre-pe", "nome": "TRE-PE"},
    "6.18": {"alias": "api_publica_tre-pi", "nome": "TRE-PI"},
    "6.19": {"alias": "api_publica_tre-rj", "nome": "TRE-RJ"},
    "6.20": {"alias": "api_publica_tre-rn", "nome": "TRE-RN"},
    "6.21": {"alias": "api_publica_tre-rs", "nome": "TRE-RS"},
    "6.22": {"alias": "api_publica_tre-ro", "nome": "TRE-RO"},
    "6.23": {"alias": "api_publica_tre-rr", "nome": "TRE-RR"},
    "6.24": {"alias": "api_publica_tre-sc", "nome": "TRE-SC"},
    "6.25": {"alias": "api_publica_tre-se", "nome": "TRE-SE"},
    "6.26": {"alias": "api_publica_tre-sp", "nome": "TRE-SP"},
    "6.27": {"alias": "api_publica_tre-to", "nome": "TRE-TO"},

    # Justiça Militar (J=9)
    "9.13": {"alias": "api_publica_tjmmg", "nome": "TJM-MG"},
    "9.21": {"alias": "api_publica_tjmrs", "nome": "TJM-RS"},
    "9.26": {"alias": "api_publica_tjmsp", "nome": "TJM-SP"},
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limpar_numero_processo(numero: str) -> str:
    """Remove caracteres não numéricos do número do processo"""
    return re.sub(r"[^0-9]", "", numero)


def extrair_tribunal_do_numero(numero: str) -> Optional[dict]:
    """
    Extrai o tribunal a partir do número CNJ do processo.
    Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
    
    Retorna o dict do tribunal ou None se não encontrado.
    """
    digits = limpar_numero_processo(numero)

    if len(digits) != 20:
        logger.warning(f"Número de processo inválido (esperado 20 dígitos): {numero} -> {digits} ({len(digits)} dígitos)")
        return None

    # J = dígito 14 (0-indexed: 13), TR = dígitos 15-16 (0-indexed: 14-15)
    j = digits[13]       # Justiça
    tr = digits[14:16]   # Tribunal

    chave = f"{j}.{tr}"
    tribunal = TRIBUNAIS.get(chave)

    if not tribunal:
        # Tenta com zero à esquerda removido
        tr_int = int(tr)
        chave_alt = f"{j}.{tr_int:02d}"
        tribunal = TRIBUNAIS.get(chave_alt)

    if tribunal:
        logger.info(f"Tribunal identificado: {tribunal['nome']} (chave: {chave})")
    else:
        logger.warning(f"Tribunal não encontrado para chave: {chave}")

    return tribunal


def formatar_numero_cnj(numero: str) -> str:
    """Formata número puro em formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO"""
    digits = limpar_numero_processo(numero)
    if len(digits) != 20:
        return numero  # retorna como está se não tem 20 dígitos

    return (
        f"{digits[0:7]}-{digits[7:9]}.{digits[9:13]}."
        f"{digits[13]}.{digits[14:16]}.{digits[16:20]}"
    )


# ============================================================
# CONSULTA À API
# ============================================================

def consultar_processo(numero_processo: str) -> Optional[dict]:
    """
    Consulta um processo pelo número CNJ na API DataJud.
    
    Retorna dict com os dados do processo ou None se não encontrado.
    """
    tribunal = extrair_tribunal_do_numero(numero_processo)
    if not tribunal:
        logger.error(f"Não foi possível identificar o tribunal para: {numero_processo}")
        return None

    alias = tribunal["alias"]
    url = f"{DATAJUD_BASE_URL}/{alias}/_search"

    # Limpa o número pra busca
    numero_limpo = limpar_numero_processo(numero_processo)

    # Query Elasticsearch — busca pelo número do processo
    body = {
        "query": {
            "match": {
                "numeroProcesso": numero_limpo
            }
        },
        "size": 1
    }

    try:
        logger.info(f"Consultando DataJud: {url}")
        logger.info(f"Número: {numero_limpo}")

        response = requests.post(
            url,
            headers=HEADERS,
            json=body,
            timeout=30,
        )

        if response.status_code != 200:
            logger.error(f"Erro HTTP {response.status_code}: {response.text[:500]}")
            return None

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])

        if not hits:
            logger.info(f"Processo não encontrado: {numero_processo}")
            return None

        # Pega o primeiro resultado
        source = hits[0].get("_source", {})

        # Parseia os dados
        resultado = parsear_processo(source, tribunal)
        return resultado

    except requests.exceptions.Timeout:
        logger.error(f"Timeout ao consultar DataJud para: {numero_processo}")
        return None
    except Exception as e:
        logger.error(f"Erro ao consultar DataJud: {e}")
        return None


def parsear_processo(source: dict, tribunal: dict) -> dict:
    """
    Parseia o JSON retornado pela API DataJud em um formato limpo.
    
    A estrutura do DataJud segue o Modelo Nacional de Interoperabilidade (MNI).
    Campos principais estão em 'dadosBasicos' e movimentações em 'movimentos'.
    """
    dados = source.get("dadosBasicos", source)

    # Dados básicos
    numero = dados.get("numero", "")
    numero_formatado = formatar_numero_cnj(numero) if numero else ""

    classe = dados.get("classe", dados.get("classeProcessual", ""))
    classe_nome = ""
    if isinstance(classe, dict):
        classe_nome = classe.get("nome", str(classe.get("codigo", "")))
    elif classe:
        classe_nome = str(classe)

    assuntos = []
    for assunto in dados.get("assuntos", []):
        if isinstance(assunto, dict):
            assuntos.append(assunto.get("nome", str(assunto.get("codigo", ""))))
        else:
            assuntos.append(str(assunto))

    # Órgão julgador — campo correto é "nome", não "nomeOrgao"
    orgao = dados.get("orgaoJulgador", source.get("orgaoJulgador", {}))
    vara = ""
    if isinstance(orgao, dict):
        vara = orgao.get("nome", orgao.get("nomeOrgao", ""))
    elif isinstance(orgao, str):
        vara = orgao

    # Data de ajuizamento
    data_ajuizamento = dados.get("dataAjuizamento", "")

    # Grau
    grau = dados.get("grau", "")

    # Nível de sigilo
    sigilo = dados.get("nivelSigilo", 0)

    # Partes (polo ativo e passivo)
    partes_ativo = []
    partes_passivo = []

    for polo in dados.get("popilos", dados.get("polo", [])):
        # A estrutura varia entre tribunais
        if isinstance(polo, dict):
            tipo_polo = polo.get("polo", polo.get("tipoPolo", ""))
            partes_polo = polo.get("parte", [])
            if isinstance(partes_polo, dict):
                partes_polo = [partes_polo]

            for parte in partes_polo:
                nome = parte.get("nome", parte.get("nomeCompleto", "Não identificado"))
                if "AT" in str(tipo_polo).upper() or "ATIVO" in str(tipo_polo).upper():
                    partes_ativo.append(nome)
                elif "PA" in str(tipo_polo).upper() or "PASSIVO" in str(tipo_polo).upper():
                    partes_passivo.append(nome)

    # Movimentações (últimas 10)
    movimentos_raw = source.get("movimentos", source.get("movimento", []))
    movimentos = []

    if isinstance(movimentos_raw, list):
        # Ordena por data (mais recente primeiro)
        for mov in movimentos_raw:
            if isinstance(mov, dict):
                data_mov = mov.get("dataHora", mov.get("data", ""))
                nome_mov = mov.get("nome", "")

                # Movimentos complementares
                complementos = []
                for comp in mov.get("complementosTabelados", mov.get("complemento", [])):
                    if isinstance(comp, dict):
                        complementos.append(comp.get("descricao", comp.get("nome", "")))
                    elif isinstance(comp, str):
                        complementos.append(comp)

                movimentos.append({
                    "data": data_mov,
                    "descricao": nome_mov,
                    "complementos": complementos,
                    "codigo": mov.get("codigo", mov.get("movimentoNacional", {}).get("codigoNacional", "")),
                })

        # Ordena por data decrescente
        movimentos.sort(key=lambda x: x.get("data", ""), reverse=True)

    # Datamart (metadados estatísticos do CNJ)
    datamart = source.get("datamart", {})
    situacao_atual = datamart.get("situacao_atual", "") if isinstance(datamart, dict) else ""
    fase_atual = datamart.get("fase_atual", "") if isinstance(datamart, dict) else ""

    return {
        "numero": numero_formatado or numero,
        "numero_limpo": limpar_numero_processo(numero),
        "tribunal": tribunal["nome"],
        "classe": classe_nome,
        "assuntos": assuntos,
        "vara": vara,
        "data_ajuizamento": data_ajuizamento,
        "grau": grau,
        "sigilo": sigilo,
        "partes_ativo": partes_ativo,
        "partes_passivo": partes_passivo,
        "situacao": situacao_atual,
        "fase": fase_atual,
        "movimentos": movimentos[:10],  # últimos 10
        "raw": source,  # dados brutos pra debug
    }


# ============================================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================================

def buscar_e_formatar(numero_processo: str) -> str:
    """
    Busca o processo e retorna uma string formatada pro briefing/bot.
    """
    resultado = consultar_processo(numero_processo)

    if not resultado:
        return f"❌ Processo {numero_processo} não encontrado no DataJud."

    # Formata as partes
    autor = ", ".join(resultado["partes_ativo"]) if resultado["partes_ativo"] else "Não identificado"
    reu = ", ".join(resultado["partes_passivo"]) if resultado["partes_passivo"] else "Não identificado"

    # Formata assuntos
    assuntos = ", ".join(resultado["assuntos"]) if resultado["assuntos"] else "Não informado"

    # Formata movimentos
    movs_str = ""
    for mov in resultado["movimentos"][:5]:
        data = mov["data"][:10] if mov["data"] else "S/D"
        desc = mov["descricao"]
        complemento = f" — {', '.join(mov['complementos'])}" if mov["complementos"] else ""
        movs_str += f"  📌 {data}: {desc}{complemento}\n"

    if not movs_str:
        movs_str = "  Nenhuma movimentação encontrada.\n"

    texto = (
        f"📋 *Processo {resultado['numero']}*\n"
        f"🏛️ {resultado['tribunal']}\n"
        f"⚖️ Vara: {resultado['vara']}\n"
        f"📂 Classe: {resultado['classe']}\n"
        f"📝 Assunto: {assuntos}\n"
        f"👤 Autor: {autor}\n"
        f"👥 Réu: {reu}\n"
    )

    if resultado["data_ajuizamento"]:
        texto += f"📅 Ajuizamento: {resultado['data_ajuizamento'][:10]}\n"

    if resultado["situacao"]:
        texto += f"📊 Situação: {resultado['situacao']}\n"

    if resultado["fase"]:
        texto += f"🔄 Fase: {resultado['fase']}\n"

    texto += f"\n📌 *Últimas movimentações:*\n{movs_str}"

    return texto


def atualizar_processo_no_banco(db, processo_id: int, numero: str) -> bool:
    """
    Consulta o DataJud e atualiza os dados do processo no banco local.
    Retorna True se houve atualização, False caso contrário.
    """
    resultado = consultar_processo(numero)

    if not resultado:
        return False

    try:
        # Atualiza dados básicos do processo
        conn = db._conn()

        # Atualiza partes se não tinha
        autor = ", ".join(resultado["partes_ativo"]) if resultado["partes_ativo"] else ""
        reu = ", ".join(resultado["partes_passivo"]) if resultado["partes_passivo"] else ""
        partes = f"{autor} vs {reu}" if autor and reu else autor or reu

        if partes:
            conn.execute(
                "UPDATE processos SET partes = ? WHERE id = ? AND (partes IS NULL OR partes = '')",
                (partes, processo_id),
            )

        # Atualiza vara
        if resultado["vara"]:
            conn.execute(
                "UPDATE processos SET vara = ? WHERE id = ? AND (vara IS NULL OR vara = '')",
                (resultado["vara"], processo_id),
            )

        # Atualiza classe e assunto
        if resultado["classe"]:
            conn.execute(
                "UPDATE processos SET classe = ? WHERE id = ?",
                (resultado["classe"], processo_id),
            )

        if resultado["assuntos"]:
            conn.execute(
                "UPDATE processos SET assunto = ? WHERE id = ?",
                (", ".join(resultado["assuntos"]), processo_id),
            )

        # Insere novos andamentos
        for mov in resultado["movimentos"]:
            data = mov["data"][:10] if mov["data"] else ""
            desc = mov["descricao"]
            if mov["complementos"]:
                desc += f" — {', '.join(mov['complementos'])}"

            if not data or not desc:
                continue

            # Verifica se já existe
            existing = conn.execute(
                "SELECT id FROM andamentos WHERE processo_id = ? AND data = ? AND descricao = ?",
                (processo_id, data, desc),
            ).fetchone()

            if not existing:
                conn.execute(
                    "INSERT INTO andamentos (processo_id, data, descricao) VALUES (?, ?, ?)",
                    (processo_id, data, desc),
                )
                logger.info(f"  Novo andamento: {data} - {desc[:50]}...")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Erro ao atualizar banco: {e}")
        return False


# ============================================================
# SCRIPT DE ATUALIZAÇÃO (roda via cron)
# ============================================================

def atualizar_todos_processos(db):
    """
    Consulta o DataJud para todos os processos ativos no banco
    e atualiza os andamentos. Roda via cron (ex: toda madrugada).
    """
    from database import Database

    conn = db._conn()
    processos = conn.execute(
        "SELECT p.id, p.numero, a.nome as advogado_nome "
        "FROM processos p "
        "JOIN advogados a ON p.advogado_id = a.id "
        "WHERE p.status = 'ativo'"
    ).fetchall()
    conn.close()

    logger.info(f"🔄 Atualizando {len(processos)} processos via DataJud...")

    atualizados = 0
    erros = 0

    for proc in processos:
        proc = dict(proc)
        logger.info(f"  Consultando: {proc['numero']} (Dr(a). {proc['advogado_nome']})")

        try:
            sucesso = atualizar_processo_no_banco(db, proc["id"], proc["numero"])
            if sucesso:
                atualizados += 1
            else:
                logger.warning(f"  ⚠️ Não encontrado no DataJud: {proc['numero']}")
        except Exception as e:
            logger.error(f"  ❌ Erro: {e}")
            erros += 1

    logger.info(f"✅ Atualização concluída: {atualizados} atualizados, {erros} erros")
    return atualizados, erros


# ============================================================
# TESTE RÁPIDO
# ============================================================

if __name__ == "__main__":
    """
    Teste rápido: python datajud.py NUMERO_DO_PROCESSO
    Exemplo: python datajud.py 1234567-89.2024.8.06.0001
    """
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Uso: python datajud.py NUMERO_DO_PROCESSO")
        print("Exemplo: python datajud.py 1234567-89.2024.8.06.0001")
        sys.exit(1)

    numero = sys.argv[1]
    print(f"\n🔍 Consultando processo: {numero}\n")

    texto = buscar_e_formatar(numero)
    print(texto)
