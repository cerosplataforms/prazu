"""
Feriados 2026 — Brasil (27 UFs)
Feriados nacionais, forenses, estaduais e municipais (capitais + comarcas principais).
Fontes: Portaria MGI 11.460/2025, TJMG, Diário do Comércio, calendários oficiais.

IMPORTANTE para prazos processuais:
  - Carnaval e Cinzas: ponto facultativo nacional MAS é suspensão forense
  - Corpus Christi: ponto facultativo nacional MAS é feriado/suspensão em muitos municípios
  - Recesso: 20/dez a 20/jan (CPC art. 220)
  - Suspensões forenses (portarias TJMG etc.) variam por tribunal
"""

from database import Database
from datetime import date, timedelta


# ============================================================
# FERIADOS NACIONAIS 2026 (Lei 662/1949 + posteriores)
# Aplicam-se a TODAS as comarcas de TODOS os estados
# ============================================================
FERIADOS_NACIONAIS_2026 = {
    "2026-01-01": "Confraternizacao Universal",
    "2026-04-03": "Sexta-feira Santa (Paixao de Cristo)",
    "2026-04-21": "Tiradentes",
    "2026-05-01": "Dia do Trabalho",
    "2026-09-07": "Independencia do Brasil",
    "2026-10-12": "Nossa Senhora Aparecida",
    "2026-11-02": "Finados",
    "2026-11-15": "Proclamacao da Republica",
    "2026-11-20": "Dia Nacional de Zumbi e da Consciencia Negra",
    "2026-12-25": "Natal",
}

# ============================================================
# SUSPENSÕES FORENSES NACIONAIS 2026
# Pontos facultativos que suspendem prazos na Justiça
# ============================================================
SUSPENSOES_FORENSES_2026 = {
    "2026-02-16": "Carnaval (segunda)",
    "2026-02-17": "Carnaval (terca)",
    "2026-02-18": "Quarta-feira de Cinzas",
    "2026-04-01": "Semana Santa (quarta)",
    "2026-04-02": "Semana Santa (quinta)",
    "2026-06-04": "Corpus Christi",
    "2026-10-28": "Dia do Servidor Publico",
    "2026-12-08": "Dia da Justica / Imaculada Conceicao",
}


# ============================================================
# FERIADOS ESTADUAIS 2026
# Data Magna e feriados específicos por UF
# ============================================================
FERIADOS_ESTADUAIS_2026 = {
    "AC": [
        ("2026-01-23", "Dia do Evangelico"),
        ("2026-03-08", "Dia Internacional da Mulher"),
        ("2026-06-15", "Aniversario do Acre"),
        ("2026-09-05", "Dia da Amazonia"),
        ("2026-11-17", "Tratado de Petropolis"),
    ],
    "AL": [
        ("2026-06-24", "Sao Joao"),
        ("2026-06-29", "Sao Pedro"),
        ("2026-09-16", "Emancipacao de Alagoas"),
        ("2026-11-30", "Dia do Evangelico"),
    ],
    "AP": [
        ("2026-03-19", "Dia de Sao Jose"),
        ("2026-07-25", "Sao Tiago"),
        ("2026-10-05", "Criacao do Amapa"),
        ("2026-11-30", "Dia do Evangelico (ponto facultativo)"),
    ],
    "AM": [
        ("2026-09-05", "Dia da Amazonia / Elevacao do Amazonas"),
    ],
    "BA": [
        ("2026-07-02", "Independencia da Bahia (Data Magna)"),
    ],
    "CE": [
        ("2026-03-19", "Dia de Sao Jose (padroeiro do Ceara)"),
        ("2026-03-25", "Data Magna do Ceara (abolicao no CE)"),
    ],
    "DF": [
        ("2026-04-21", "Aniversario de Brasilia / Tiradentes"),
        ("2026-11-30", "Dia do Evangelico"),
    ],
    "ES": [
        ("2026-04-28", "Dia de Nossa Senhora da Penha"),
    ],
    "GO": [],  # Sem feriado estadual divulgado
    "MA": [
        ("2026-07-28", "Adesao do Maranhao (Data Magna)"),
    ],
    "MT": [],  # Sem feriado estadual divulgado
    "MS": [
        ("2026-10-11", "Criacao do Mato Grosso do Sul (Data Magna)"),
    ],
    "MG": [],  # Sem feriado estadual divulgado (Tiradentes é nacional)
    "PA": [
        ("2026-08-15", "Adesao do Para (Data Magna)"),
    ],
    "PB": [
        ("2026-08-05", "Data Magna da Paraiba"),
    ],
    "PR": [],  # Sem feriado estadual divulgado
    "PE": [
        ("2026-03-06", "Revolucao Pernambucana de 1817 (Data Magna)"),
    ],
    "PI": [
        ("2026-10-19", "Dia do Piaui (Data Magna)"),
    ],
    "RJ": [
        ("2026-04-23", "Dia de Sao Jorge"),
    ],
    "RN": [
        ("2026-10-03", "Martires de Cunhau e Uruacu"),
    ],
    "RS": [
        ("2026-09-20", "Dia do Gaucho / Revolucao Farroupilha (Data Magna)"),
    ],
    "RO": [
        ("2026-01-04", "Data Magna de Rondonia"),
    ],
    "RR": [
        ("2026-10-05", "Criacao de Roraima"),
    ],
    "SC": [],  # Sem feriado estadual divulgado
    "SP": [
        ("2026-07-09", "Revolucao Constitucionalista de 1932 (Data Magna)"),
    ],
    "SE": [
        ("2026-07-08", "Independencia de Sergipe (Data Magna)"),
    ],
    "TO": [
        ("2026-10-05", "Criacao do Tocantins"),
        ("2026-03-18", "Autonomia do Tocantins"),
    ],
}


# ============================================================
# SUSPENSÕES FORENSES ESTADUAIS (TJMG e outros tribunais)
# Portarias de suspensão de prazos — varia por tribunal
# Inicialmente mapeado: TJMG (Portaria 1764/2026)
# ============================================================
SUSPENSOES_ESTADUAIS_2026 = {
    "MG": [
        ("2026-03-19", "Dia de Sao Jose (suspensao TJMG)"),
        ("2026-04-20", "Suspensao forense TJMG"),
        ("2026-06-05", "Suspensao forense pos-Corpus Christi TJMG"),
        ("2026-10-30", "Suspensao forense TJMG"),
        ("2026-12-07", "Suspensao forense TJMG"),
    ],
}


# ============================================================
# FERIADOS MUNICIPAIS POR COMARCA (capitais + cidades principais)
# ============================================================
FERIADOS_MUNICIPAIS_2026 = {
    # --- ACRE ---
    "Rio Branco": [
        ("2026-12-28", "Aniversario de Rio Branco"),
    ],

    # --- ALAGOAS ---
    "Maceio": [
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- AMAPÁ ---
    "Macapa": [
        ("2026-02-04", "Aniversario de Macapa"),
    ],

    # --- AMAZONAS ---
    "Manaus": [
        ("2026-10-24", "Aniversario de Manaus"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- BAHIA ---
    "Salvador": [
        ("2026-06-24", "Sao Joao"),
        ("2026-12-08", "N.S. Conceicao da Praia"),
    ],
    "Feira de Santana": [
        ("2026-06-24", "Sao Joao"),
        ("2026-07-26", "Senhora Santana"),
    ],
    "Vitoria da Conquista": [
        ("2026-08-15", "N.S. das Vitorias"),
        ("2026-11-09", "Aniversario de Vitoria da Conquista"),
    ],
    "Camacari": [
        ("2026-09-28", "Aniversario de Camacari"),
    ],
    "Ilheus": [
        ("2026-06-28", "Aniversario de Ilheus"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],
    "Itabuna": [
        ("2026-06-13", "Santo Antonio"),
    ],

    # --- CEARÁ ---
    "Fortaleza": [
        ("2026-08-15", "N.S. da Assuncao"),
    ],
    "Caucaia": [
        ("2026-08-15", "N.S. dos Prazeres"),
        ("2026-10-15", "Aniversario de Caucaia"),
    ],
    "Juazeiro do Norte": [
        ("2026-11-02", "Romaria de Finados (coincide com Finados nacional)"),
    ],
    "Sobral": [
        ("2026-07-05", "Aniversario de Sobral"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- DISTRITO FEDERAL ---
    "Brasilia": [],  # Feriados já cobertos no estadual (DF)

    # --- ESPÍRITO SANTO ---
    "Vitoria": [
        ("2026-09-08", "Aniversario de Vitoria / N.S. da Vitoria"),
    ],
    "Vila Velha": [
        ("2026-05-23", "Aniversario de Vila Velha"),
    ],
    "Serra": [
        ("2026-12-26", "Aniversario de Serra"),
    ],
    "Cariacica": [
        ("2026-04-20", "Aniversario de Cariacica"),
    ],

    # --- GOIÁS ---
    "Goiania": [
        ("2026-05-24", "N.S. Auxiliadora"),
        ("2026-10-24", "Aniversario de Goiania"),
    ],
    "Aparecida de Goiania": [
        ("2026-05-11", "Aniversario de Aparecida de Goiania"),
    ],
    "Anapolis": [
        ("2026-07-31", "Aniversario de Anapolis"),
    ],

    # --- MARANHÃO ---
    "Sao Luis": [
        ("2026-06-29", "Sao Pedro"),
        ("2026-09-08", "Aniversario de Sao Luis / Natividade N.S."),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- MATO GROSSO ---
    "Cuiaba": [
        ("2026-04-08", "Aniversario de Cuiaba"),
    ],

    # --- MATO GROSSO DO SUL ---
    "Campo Grande": [],  # Sem feriado municipal divulgado

    # --- MINAS GERAIS (migrado do feriados_mg.py) ---
    "Belo Horizonte": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-08-15", "Assuncao de Nossa Senhora"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Uberlandia": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-08-15", "N.S. da Abadia"),
        ("2026-08-31", "Aniversario de Uberlandia"),
    ],
    "Contagem": [
        ("2026-04-11", "Jubileu N.S. das Dores"),
        ("2026-06-04", "Corpus Christi"),
    ],
    "Juiz de Fora": [
        ("2026-02-24", "Aniversario de Juiz de Fora"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antonio"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Betim": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Montes Claros": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-07-03", "Aniversario de Montes Claros"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Ribeirao das Neves": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Uberaba": [
        ("2026-04-28", "Aniversario de Uberaba"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Governador Valadares": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antonio"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Ipatinga": [
        ("2026-04-29", "Aniversario de Ipatinga"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Sete Lagoas": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Divinopolis": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antonio"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Santa Luzia": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-13", "Santa Luzia"),
    ],
    "Pocos de Caldas": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-11-06", "Aniversario de Pocos de Caldas"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Patos de Minas": [
        ("2026-05-24", "Aniversario de Patos de Minas"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Teofilo Otoni": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-07", "Aniversario de Teofilo Otoni"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Barbacena": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-07", "Aniversario de Barbacena"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Sabara": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-07-17", "Aniversario de Sabara"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Varginha": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-10-07", "Aniversario de Varginha"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Conselheiro Lafaiete": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-09-17", "Aniversario de Cons. Lafaiete"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Lavras": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-06-13", "Santo Antonio"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Nova Lima": [
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Itajuba": [
        ("2026-03-19", "Sao Jose"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],
    "Passos": [
        ("2026-03-19", "Sao Jose"),
        ("2026-06-04", "Corpus Christi"),
        ("2026-12-08", "Imaculada Conceicao"),
    ],

    # --- PARÁ ---
    "Belem": [
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],
    "Ananindeua": [
        ("2026-01-03", "Aniversario de Ananindeua"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],
    "Santarem": [
        ("2026-06-22", "Aniversario de Santarem"),
    ],
    "Maraba": [
        ("2026-04-05", "Aniversario de Maraba"),
    ],

    # --- PARAÍBA ---
    "Joao Pessoa": [
        ("2026-06-24", "Sao Joao"),
        ("2026-08-05", "N.S. das Neves / Aniversario JP"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- PARANÁ ---
    "Curitiba": [
        ("2026-09-08", "N.S. da Luz dos Pinhais"),
    ],
    "Londrina": [
        ("2026-06-12", "Sagrado Coracao de Jesus"),
        ("2026-12-10", "Aniversario de Londrina"),
    ],
    "Maringa": [
        ("2026-05-10", "Aniversario de Maringa"),
        ("2026-08-15", "N.S. da Gloria"),
    ],
    "Ponta Grossa": [
        ("2026-09-15", "Aniversario de Ponta Grossa"),
    ],
    "Cascavel": [
        ("2026-11-14", "Aniversario de Cascavel"),
    ],
    "Foz do Iguacu": [
        ("2026-06-10", "Aniversario de Foz do Iguacu"),
    ],

    # --- PERNAMBUCO ---
    "Recife": [
        ("2026-06-24", "Sao Joao"),
        ("2026-07-16", "N.S. do Carmo"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],
    "Jaboatao dos Guararapes": [
        ("2026-01-15", "Santo Amaro"),
        ("2026-05-04", "Aniversario de Jaboatao"),
        ("2026-06-24", "Sao Joao"),
    ],
    "Olinda": [
        ("2026-06-24", "Sao Joao"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],
    "Caruaru": [
        ("2026-05-18", "Aniversario de Caruaru"),
        ("2026-06-24", "Sao Joao"),
    ],
    "Petrolina": [
        ("2026-09-21", "Aniversario de Petrolina"),
    ],

    # --- PIAUÍ ---
    "Teresina": [
        ("2026-08-16", "Aniversario de Teresina"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- RIO DE JANEIRO ---
    "Rio de Janeiro": [
        ("2026-01-20", "Sao Sebastiao"),
    ],
    "Niteroi": [
        ("2026-06-24", "Sao Joao"),
        ("2026-11-22", "Aniversario de Niteroi"),
    ],
    "Sao Goncalo": [
        ("2026-09-22", "Aniversario de Sao Goncalo"),
    ],
    "Duque de Caxias": [
        ("2026-06-13", "Santo Antonio"),
        ("2026-08-25", "Dia de Duque de Caxias"),
    ],
    "Nova Iguacu": [
        ("2026-06-13", "Santo Antonio"),
    ],
    "Campos dos Goytacazes": [
        ("2026-01-15", "Santo Amaro"),
        ("2026-08-06", "Sao Salvador"),
    ],
    "Petropolis": [
        ("2026-03-16", "Aniversario de Petropolis"),
    ],
    "Volta Redonda": [
        ("2026-07-17", "Aniversario de Volta Redonda"),
    ],

    # --- RIO GRANDE DO NORTE ---
    "Natal": [
        ("2026-12-25", "Aniversario de Natal (coincide com Natal nacional)"),
    ],

    # --- RIO GRANDE DO SUL ---
    "Porto Alegre": [
        ("2026-02-02", "N.S. dos Navegantes"),
    ],
    "Caxias do Sul": [
        ("2026-05-26", "N.S. de Caravaggio"),
    ],
    "Pelotas": [
        ("2026-07-07", "Aniversario de Pelotas"),
    ],
    "Canoas": [
        ("2026-06-27", "Aniversario de Canoas"),
    ],
    "Santa Maria": [
        ("2026-05-17", "Aniversario de Santa Maria"),
    ],

    # --- RONDÔNIA ---
    "Porto Velho": [
        ("2026-01-24", "Aniversario de Porto Velho / Sao Francisco de Sales"),
        ("2026-10-02", "Criacao de Porto Velho / Santa Terezinha"),
    ],

    # --- RORAIMA ---
    "Boa Vista": [
        ("2026-06-09", "Aniversario de Boa Vista"),
    ],

    # --- SANTA CATARINA ---
    "Florianopolis": [
        ("2026-03-23", "Emancipacao de Florianopolis"),
    ],
    "Joinville": [
        ("2026-03-09", "Aniversario de Joinville"),
    ],
    "Blumenau": [
        ("2026-09-02", "Aniversario de Blumenau"),
    ],
    "Chapeco": [
        ("2026-08-25", "Aniversario de Chapeco"),
    ],

    # --- SÃO PAULO ---
    "Sao Paulo": [
        ("2026-01-25", "Aniversario de Sao Paulo"),
    ],
    "Guarulhos": [
        ("2026-12-08", "Aniversario de Guarulhos / Imaculada Conceicao"),
    ],
    "Campinas": [
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],
    "Sao Bernardo do Campo": [
        ("2026-08-20", "Aniversario de SBC"),
    ],
    "Santo Andre": [
        ("2026-04-08", "Aniversario de Santo Andre"),
    ],
    "Ribeirao Preto": [
        ("2026-01-20", "Sao Sebastiao"),
        ("2026-06-19", "Aniversario de Ribeirao Preto"),
    ],
    "Sao Jose dos Campos": [
        ("2026-03-19", "Sao Jose"),
        ("2026-07-27", "Aniversario de SJC"),
    ],
    "Sorocaba": [
        ("2026-08-15", "Aniversario de Sorocaba"),
    ],
    "Osasco": [
        ("2026-02-19", "Emancipacao de Osasco"),
        ("2026-06-13", "Santo Antonio"),
    ],

    # --- SERGIPE ---
    "Aracaju": [
        ("2026-03-17", "Aniversario de Aracaju"),
        ("2026-12-08", "N.S. Imaculada Conceicao"),
    ],

    # --- TOCANTINS ---
    "Palmas": [
        ("2026-05-20", "Aniversario de Palmas"),
    ],
}


# ============================================================
# MAPA UF → CAPITAL (para default quando comarca não informada)
# ============================================================
UF_CAPITAL = {
    "AC": "Rio Branco",    "AL": "Maceio",        "AP": "Macapa",
    "AM": "Manaus",        "BA": "Salvador",       "CE": "Fortaleza",
    "DF": "Brasilia",      "ES": "Vitoria",        "GO": "Goiania",
    "MA": "Sao Luis",      "MT": "Cuiaba",         "MS": "Campo Grande",
    "MG": "Belo Horizonte","PA": "Belem",          "PB": "Joao Pessoa",
    "PR": "Curitiba",      "PE": "Recife",         "PI": "Teresina",
    "RJ": "Rio de Janeiro","RN": "Natal",          "RS": "Porto Alegre",
    "RO": "Porto Velho",   "RR": "Boa Vista",      "SC": "Florianopolis",
    "SP": "Sao Paulo",     "SE": "Aracaju",        "TO": "Palmas",
}

# Mapa inverso: comarca → UF
COMARCA_UF = {}
for uf, capital in UF_CAPITAL.items():
    COMARCA_UF[capital] = uf
# Adicionar comarcas MG (não-capital)
_COMARCAS_MG = [
    "Uberlandia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros",
    "Ribeirao das Neves", "Uberaba", "Governador Valadares", "Ipatinga",
    "Sete Lagoas", "Divinopolis", "Santa Luzia", "Pocos de Caldas",
    "Patos de Minas", "Teofilo Otoni", "Barbacena", "Sabara", "Varginha",
    "Conselheiro Lafaiete", "Lavras", "Nova Lima", "Itajuba", "Passos",
]
for c in _COMARCAS_MG:
    COMARCA_UF[c] = "MG"
# Adicionar comarcas SP (não-capital)
_COMARCAS_SP = [
    "Guarulhos", "Campinas", "Sao Bernardo do Campo", "Santo Andre",
    "Ribeirao Preto", "Sao Jose dos Campos", "Sorocaba", "Osasco",
]
for c in _COMARCAS_SP:
    COMARCA_UF[c] = "SP"
# Outras comarcas não-capital
_COMARCAS_EXTRAS = {
    # BA
    "Feira de Santana": "BA", "Vitoria da Conquista": "BA", "Camacari": "BA",
    "Ilheus": "BA", "Itabuna": "BA",
    # RJ
    "Niteroi": "RJ", "Sao Goncalo": "RJ", "Duque de Caxias": "RJ",
    "Nova Iguacu": "RJ", "Campos dos Goytacazes": "RJ",
    "Petropolis": "RJ", "Volta Redonda": "RJ",
    # RS
    "Caxias do Sul": "RS", "Pelotas": "RS", "Canoas": "RS", "Santa Maria": "RS",
    # PE
    "Jaboatao dos Guararapes": "PE", "Olinda": "PE", "Caruaru": "PE", "Petrolina": "PE",
    # CE
    "Caucaia": "CE", "Juazeiro do Norte": "CE", "Sobral": "CE",
    # PR
    "Londrina": "PR", "Maringa": "PR", "Ponta Grossa": "PR",
    "Cascavel": "PR", "Foz do Iguacu": "PR",
    # SC
    "Joinville": "SC", "Blumenau": "SC", "Chapeco": "SC",
    # PA
    "Ananindeua": "PA", "Santarem": "PA", "Maraba": "PA",
    # GO
    "Aparecida de Goiania": "GO", "Anapolis": "GO",
    # ES
    "Vila Velha": "ES", "Serra": "ES", "Cariacica": "ES",
}
COMARCA_UF.update(_COMARCAS_EXTRAS)


# Todas as comarcas disponíveis
COMARCAS_DISPONIVEIS = sorted(FERIADOS_MUNICIPAIS_2026.keys())

# Todas as UFs
UFS_DISPONIVEIS = sorted(UF_CAPITAL.keys())


# ============================================================
# FUNÇÕES DE CONSULTA (sem banco de dados)
# ============================================================

def obter_feriados_set(uf: str, comarca: str = None, ano: int = 2026) -> set:
    """
    Retorna um set de datas ISO (ex: {"2026-01-01", "2026-02-17"})
    com TODOS os feriados aplicáveis para uma UF/comarca.

    Inclui: nacionais + suspensões forenses + estaduais + municipais + recesso.

    Args:
        uf: sigla da UF (ex: "MG", "SP")
        comarca: nome da comarca (ex: "Belo Horizonte"). Se None, usa capital.
        ano: ano dos feriados (default 2026)

    Returns:
        set de strings ISO date
    """
    feriados = set()

    # 1. Nacionais
    for data in FERIADOS_NACIONAIS_2026:
        feriados.add(data)

    # 2. Suspensões forenses nacionais
    for data in SUSPENSOES_FORENSES_2026:
        feriados.add(data)

    # 3. Estaduais
    estaduais = FERIADOS_ESTADUAIS_2026.get(uf, [])
    for data, _ in estaduais:
        feriados.add(data)

    # 4. Suspensões estaduais (portarias tribunais)
    susp_est = SUSPENSOES_ESTADUAIS_2026.get(uf, [])
    for data, _ in susp_est:
        feriados.add(data)

    # 5. Municipais
    if comarca is None:
        comarca = UF_CAPITAL.get(uf, "")
    municipais = FERIADOS_MUNICIPAIS_2026.get(comarca, [])
    for data, _ in municipais:
        feriados.add(data)

    # 6. Recesso forense (20/dez a 20/jan)
    d = date(ano - 1, 12, 20)
    fim = date(ano, 1, 20)
    while d <= fim:
        feriados.add(d.isoformat())
        d += timedelta(days=1)

    return feriados


def listar_comarcas(uf: str = None) -> list:
    """
    Lista comarcas disponíveis.
    Se uf informada, filtra por estado.
    """
    if uf is None:
        return COMARCAS_DISPONIVEIS

    resultado = []
    for comarca in COMARCAS_DISPONIVEIS:
        comarca_uf = COMARCA_UF.get(comarca)
        if comarca_uf == uf:
            resultado.append(comarca)

    # Se não encontrou nenhuma mas tem capital, retorna pelo menos a capital
    if not resultado:
        capital = UF_CAPITAL.get(uf)
        if capital and capital in FERIADOS_MUNICIPAIS_2026:
            resultado.append(capital)

    return sorted(resultado)


def obter_uf_comarca(comarca: str) -> str:
    """Retorna a UF de uma comarca, ou '' se não encontrada."""
    return COMARCA_UF.get(comarca, "")


# ============================================================
# FUNÇÃO DE CARGA NO BANCO (compatível com database.py existente)
# ============================================================

def carregar_feriados_2026(db: Database):
    """
    Carrega todos os feriados de 2026 no banco de dados.
    Compatível com feriados_mg.py (mesma assinatura).
    """
    count = 0

    # Nacionais
    for data, desc in FERIADOS_NACIONAIS_2026.items():
        db.inserir_feriado(data, desc, "nacional", ano=2026)
        count += 1

    # Suspensões forenses nacionais
    for data, desc in SUSPENSOES_FORENSES_2026.items():
        db.inserir_feriado(data, desc, "forense", ano=2026)
        count += 1

    # Recesso
    d = date(2025, 12, 20)
    fim = date(2026, 1, 20)
    while d <= fim:
        db.inserir_feriado(d.isoformat(), "Recesso Forense", "forense", ano=d.year)
        d += timedelta(days=1)
        count += 1

    # Estaduais
    for uf, feriados in FERIADOS_ESTADUAIS_2026.items():
        for data, desc in feriados:
            db.inserir_feriado(data, desc, "estadual", comarca=uf, ano=2026)
            count += 1

    # Suspensões estaduais
    for uf, feriados in SUSPENSOES_ESTADUAIS_2026.items():
        for data, desc in feriados:
            db.inserir_feriado(data, desc, "forense", comarca=uf, ano=2026)
            count += 1

    # Municipais
    for comarca, feriados in FERIADOS_MUNICIPAIS_2026.items():
        for data, desc in feriados:
            db.inserir_feriado(data, desc, "municipal", comarca=comarca, ano=2026)
            count += 1

    return count
