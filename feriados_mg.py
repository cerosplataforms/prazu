"""
Feriados 2026 — Minas Gerais (Fonte: Calendário Oficial TJMG)
Nacionais, forenses, municipais das 25 maiores comarcas.
"""

from database import Database


# ============================================================
# FERIADOS NACIONAIS E FORENSES 2026 (aplicam a TODAS comarcas MG)
# ============================================================
FERIADOS_NACIONAIS_2026 = {
    "2026-01-01": "Confraternização Universal",
    "2026-02-16": "Carnaval (segunda-feira)",
    "2026-02-17": "Carnaval (terça-feira)",
    "2026-02-18": "Quarta-feira de Cinzas",
    "2026-03-19": "Dia de São José (padroeiro de diversas comarcas)",
    "2026-04-01": "Semana Santa (quarta-feira)",
    "2026-04-02": "Semana Santa (quinta-feira)",
    "2026-04-03": "Sexta-feira Santa",
    "2026-04-20": "Suspensão forense (Portaria 1764/2026)",
    "2026-04-21": "Tiradentes",
    "2026-05-01": "Dia do Trabalho",
    "2026-06-04": "Corpus Christi",
    "2026-06-05": "Suspensão forense (Portaria 1764/2026)",
    "2026-07-09": "Dia da Revolução Constitucionalista",
    "2026-09-07": "Independência do Brasil",
    "2026-10-12": "Nossa Senhora Aparecida",
    "2026-10-28": "Dia do Servidor Público",
    "2026-10-30": "Suspensão forense (Portaria 1764/2026)",
    "2026-11-02": "Finados",
    "2026-11-15": "Proclamação da República",
    "2026-12-07": "Suspensão forense (Portaria 1764/2026)",
    "2026-12-08": "Dia da Justiça / Imaculada Conceição",
    "2026-12-25": "Natal",
}

# ============================================================
# RECESSO FORENSE
# ============================================================
RECESSO_2025_2026 = {
    "inicio": "2025-12-20",
    "fim": "2026-01-20",
    "nota": "Prazos SUSPENSOS de 20/dez/2025 a 20/jan/2026 (Res. 244/2016 CNJ)"
}

# ============================================================
# FERIADOS MUNICIPAIS POR COMARCA (25 maiores de MG)
# ============================================================
FERIADOS_MUNICIPAIS_2026 = {
    "Belo Horizonte": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-08-15", "Assunção de Nossa Senhora"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Uberlândia": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-08-15", "Assunção de Nossa Senhora"),
        ("2026-08-31", "Aniversário de Uberlândia"),
    ],
    "Contagem": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antônio"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Juiz de Fora": [
        ("2026-02-24", "Aniversário de Juiz de Fora"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antônio"),
    ],
    "Betim": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-11-20", "Dia da Consciência Negra"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Montes Claros": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-07-12", "Aniversário de Montes Claros"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Ribeirão das Neves": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Uberaba": [
        ("2026-03-19", "São José"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-10-19", "Aniversário de Uberaba"),
    ],
    "Governador Valadares": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-30", "Aniversário de Gov. Valadares"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Ipatinga": [
        ("2026-04-29", "Aniversário de Ipatinga"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Sete Lagoas": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antônio"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Divinópolis": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-01", "Aniversário de Divinópolis"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Santa Luzia": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceição"),
        ("2026-12-13", "Santa Luzia"),
    ],
    "Ibirité": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-08-15", "Assunção de Nossa Senhora"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Poços de Caldas": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-11-06", "Aniversário de Poços de Caldas"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Patos de Minas": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-24", "São João"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Teófilo Otoni": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-07", "Aniversário de Teófilo Otoni"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Barbacena": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-07", "Aniversário de Barbacena"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Sabará": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-07-17", "Aniversário de Sabará"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Varginha": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-10-07", "Aniversário de Varginha"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Conselheiro Lafaiete": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-17", "Aniversário de Cons. Lafaiete"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Lavras": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antônio"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Nova Lima": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Itajubá": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-03-19", "São José"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
    "Passos": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-03-19", "São José"),
        ("2026-12-08", "Imaculada Conceição"),
    ],
}

# Comarcas disponíveis para seleção
COMARCAS_DISPONIVEIS = sorted(FERIADOS_MUNICIPAIS_2026.keys())


def carregar_feriados_2026(db: Database):
    """Carrega todos os feriados de 2026 no banco de dados."""
    count = 0

    # Nacionais/forenses
    for data, desc in FERIADOS_NACIONAIS_2026.items():
        db.inserir_feriado(data, desc, "nacional", ano=2026)
        count += 1

    # Recesso (cada dia de 20/dez a 20/jan)
    from datetime import date, timedelta
    d = date(2025, 12, 20)
    fim = date(2026, 1, 20)
    while d <= fim:
        db.inserir_feriado(d.isoformat(), "Recesso Forense", "forense", ano=d.year)
        d += timedelta(days=1)
        count += 1

    # Municipais
    for comarca, feriados in FERIADOS_MUNICIPAIS_2026.items():
        for data, desc in feriados:
            db.inserir_feriado(data, desc, "municipal", comarca=comarca, ano=2026)
            count += 1

    return count
