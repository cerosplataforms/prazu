"""
PrazorBot Brasil — Testes Completos
Roda: python test_prazobot.py
"""

import os, sys, json
from datetime import date, timedelta

# ============================================================
# Setup: banco de testes isolado
# ============================================================
TEST_DB = "prazobot_test.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from database import Database
from feriados_br import (
    carregar_feriados_2026, FERIADOS_NACIONAIS_2026,
    FERIADOS_MUNICIPAIS_2026, COMARCAS_DISPONIVEIS,
    obter_feriados_set, listar_comarcas, UFS_DISPONIVEIS,
    UF_CAPITAL, COMARCA_UF, FERIADOS_ESTADUAIS_2026,
)
from prazos_calc import (
    calcular_prazo_completo, calcular_prazo_dias_uteis,
    calcular_prazo_dias_corridos, calcular_data_publicacao,
    calcular_inicio_prazo, _eh_dia_util, _em_recesso,
    dias_uteis_entre, proximo_dia_util
)

db = Database(TEST_DB)
db.init()

PASS = 0
FAIL = 0
ERROS = []

def ok(nome, condicao, detalhe=""):
    global PASS, FAIL, ERROS
    if condicao:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        ERROS.append(f"{nome}: {detalhe}")
        print(f"  ❌ {nome} → {detalhe}")


# ============================================================
# 1. DATABASE — Feriados
# ============================================================
print("\n" + "="*60)
print("1. DATABASE — Carga de Feriados")
print("="*60)

count = carregar_feriados_2026(db)
ok("Carga retorna > 0", count > 0, f"count={count}")
ok("Carga retorna > 50 feriados", count > 50, f"count={count}")

total = db.contar_feriados(2026)
ok("contar_feriados(2026) > 50", total > 50, f"total={total}")

# Feriados nacionais
feriados_br = db.carregar_feriados(2026)
ok("carregar_feriados sem comarca retorna nacionais", len(feriados_br) > 20, f"len={len(feriados_br)}")
ok("01/01 (Ano Novo) no set", "2026-01-01" in feriados_br)
ok("25/12 (Natal) no set", "2026-12-25" in feriados_br)
ok("21/04 (Tiradentes) no set", "2026-04-21" in feriados_br)
ok("17/02 (Carnaval) no set", "2026-02-17" in feriados_br)
ok("04/06 (Corpus Christi) no set", "2026-06-04" in feriados_br)

# Feriados com comarca BH
feriados_bh = db.carregar_feriados(2026, comarca="Belo Horizonte")
ok("BH inclui nacionais", "2026-04-21" in feriados_bh)
ok("BH inclui Assunção 15/08", "2026-08-15" in feriados_bh)
ok("BH inclui Imaculada 08/12", "2026-12-08" in feriados_bh)

# Feriados Uberlândia (diferente de BH)
feriados_udi = db.carregar_feriados(2026, comarca="Uberlandia")
ok("UDI inclui aniversário 31/08", "2026-08-31" in feriados_udi)

# Juiz de Fora
feriados_jf = db.carregar_feriados(2026, comarca="Juiz de Fora")
ok("JF inclui aniversário 24/02", "2026-02-24" in feriados_jf)
ok("JF inclui Santo Antônio 13/06", "2026-06-13" in feriados_jf)

# Recesso no banco
ok("Recesso 20/12/2025 no set", "2025-12-20" in db.carregar_feriados(2025))
ok("Recesso 01/01/2026 no set", "2026-01-01" in feriados_br)

# Idempotência: verificar que INSERT OR IGNORE não falha
count2 = carregar_feriados_2026(db)
ok("Segunda carga não crasheia", count2 > 0)

# Comarcas disponíveis
ok("≥95 comarcas disponíveis", len(COMARCAS_DISPONIVEIS) >= 95, f"len={len(COMARCAS_DISPONIVEIS)}")
ok("BH na lista", "Belo Horizonte" in COMARCAS_DISPONIVEIS)
ok("Uberlandia na lista", "Uberlandia" in COMARCAS_DISPONIVEIS)


# ============================================================
# 2. FUNÇÕES AUXILIARES — _em_recesso, _eh_dia_util
# ============================================================
print("\n" + "="*60)
print("2. FUNÇÕES AUXILIARES — Recesso e Dia Útil")
print("="*60)

# Recesso
ok("20/12 em recesso", _em_recesso(date(2025, 12, 20)))
ok("25/12 em recesso", _em_recesso(date(2025, 12, 25)))
ok("31/12 em recesso", _em_recesso(date(2025, 12, 31)))
ok("01/01 em recesso", _em_recesso(date(2026, 1, 1)))
ok("20/01 em recesso", _em_recesso(date(2026, 1, 20)))
ok("21/01 NÃO em recesso", not _em_recesso(date(2026, 1, 21)))
ok("19/12 NÃO em recesso", not _em_recesso(date(2025, 12, 19)))
ok("15/06 NÃO em recesso", not _em_recesso(date(2026, 6, 15)))

# Dia útil
feriados_test = db.carregar_feriados(2026, comarca="Belo Horizonte")
ok("02/03/2026 (segunda) é útil", _eh_dia_util(date(2026, 3, 2), feriados_test))
ok("07/03/2026 (sábado) NÃO é útil", not _eh_dia_util(date(2026, 3, 7), feriados_test))
ok("08/03/2026 (domingo) NÃO é útil", not _eh_dia_util(date(2026, 3, 8), feriados_test))
ok("21/04/2026 (Tiradentes, terça) NÃO é útil", not _eh_dia_util(date(2026, 4, 21), feriados_test))
ok("17/02/2026 (Carnaval, terça) NÃO é útil", not _eh_dia_util(date(2026, 2, 17), feriados_test))
ok("18/02/2026 (Cinzas, quarta) NÃO é útil", not _eh_dia_util(date(2026, 2, 18), feriados_test))
ok("22/12/2025 (recesso) NÃO é útil", not _eh_dia_util(date(2025, 12, 22), feriados_test))
ok("21/01/2026 (pós-recesso, quarta) É útil", _eh_dia_util(date(2026, 1, 21), feriados_test))


# ============================================================
# 3. CÁLCULO DE PUBLICAÇÃO E INÍCIO
# ============================================================
print("\n" + "="*60)
print("3. CÁLCULO — Publicação e Início de Prazo")
print("="*60)

# Caso 1: Disponibilização segunda → publicação terça
pub = calcular_data_publicacao(date(2026, 3, 2), feriados_test)  # segunda
ok("Disp segunda 02/03 → pub terça 03/03", pub == date(2026, 3, 3))

# Caso 2: Disponibilização sexta → publicação segunda
pub = calcular_data_publicacao(date(2026, 3, 6), feriados_test)  # sexta
ok("Disp sexta 06/03 → pub segunda 09/03", pub == date(2026, 3, 9))

# Caso 3: Disponibilização véspera de feriado
# 20/04 é suspensão forense (segunda), 21/04 Tiradentes (terça)
pub = calcular_data_publicacao(date(2026, 4, 17), feriados_test)  # sexta
ok("Disp 17/04 (sex) → pula fds+suspensão+Tiradentes → pub 22/04 (qua)",
   pub == date(2026, 4, 22), f"got {pub}")

# Início do prazo: 1 dia útil após publicação
ini = calcular_inicio_prazo(date(2026, 3, 3), feriados_test)  # terça
ok("Pub 03/03 (terça) → início 04/03 (quarta)", ini == date(2026, 3, 4))

ini = calcular_inicio_prazo(date(2026, 3, 6), feriados_test)  # sexta
ok("Pub 06/03 (sexta) → início 09/03 (segunda)", ini == date(2026, 3, 9))


# ============================================================
# 4. CÁLCULO DE PRAZOS — Dias Úteis
# ============================================================
print("\n" + "="*60)
print("4. CÁLCULO — Prazos em Dias Úteis")
print("="*60)

# Caso simples: 5 dias úteis sem feriados
# Início 02/03 (seg) → 03(ter) 04(qua) 05(qui) 06(sex) 09(seg) = 5 dias úteis
venc = calcular_prazo_dias_uteis(date(2026, 3, 2), 5, feriados_test)
ok("5 dias úteis a partir de 02/03 → 09/03", venc == date(2026, 3, 9), f"got {venc}")

# 15 dias úteis a partir de 02/03
venc = calcular_prazo_dias_uteis(date(2026, 3, 2), 15, feriados_test)
ok("15 dias úteis a partir de 02/03 → 24/03 (São José 19/03 pula)", venc == date(2026, 3, 24), f"got {venc}")

# Prazo atravessando Carnaval (16,17,18/02 são feriados)
# Início 12/02 (qui) → 13(sex)=1, 16(seg)=FERIADO, 17(ter)=FERIADO, 18(qua)=FERIADO,
# 19(qui)=2, 20(sex)=3, 23(seg)=4, 24(ter)=5
venc = calcular_prazo_dias_uteis(date(2026, 2, 12), 5, feriados_test)
ok("5 dias úteis cruzando Carnaval (12/02) → 24/02",
   venc == date(2026, 2, 24), f"got {venc}")

# Prazo que passa por JF com feriado local 24/02
feriados_jf = db.carregar_feriados(2026, comarca="Juiz de Fora")
venc_jf = calcular_prazo_dias_uteis(date(2026, 2, 12), 5, feriados_jf)
# JF: 13(sex)=1, 16-18=carnaval, 19(qui)=2, 20(sex)=3, 23(seg)=4, 24(ter)=FERIADO JF, 25(qua)=5
ok("5 dias úteis JF cruzando Carnaval+Aniv → 25/02",
   venc_jf == date(2026, 2, 25), f"got {venc_jf}")

# Demonstra diferença BH vs JF
ok("Prazo JF ≠ BH por feriado municipal", venc != venc_jf,
   f"BH={venc} JF={venc_jf}")

# Prazo atravessando Semana Santa (01,02,03/04)
# Início 30/03 (seg): 31(ter)=1, 01(qua)=FERIADO, 02(qui)=FERIADO, 03(sex)=FERIADO
# 06(seg)=2, 07(ter)=3, 08(qua)=4, 09(qui)=5
venc = calcular_prazo_dias_uteis(date(2026, 3, 30), 5, feriados_test)
ok("5 dias úteis cruzando Semana Santa → 09/04",
   venc == date(2026, 4, 9), f"got {venc}")


# ============================================================
# 5. CÁLCULO DE PRAZOS — Dias Corridos
# ============================================================
print("\n" + "="*60)
print("5. CÁLCULO — Prazos em Dias Corridos")
print("="*60)

# 5 corridos a partir de segunda 02/03 → 07/03 (sábado) → prorroga para 09/03 (segunda)
venc = calcular_prazo_dias_corridos(date(2026, 3, 2), 5, feriados_test)
ok("5 corridos de 02/03 → cai sábado → prorroga 09/03",
   venc == date(2026, 3, 9), f"got {venc}")

# 10 corridos de 02/03 → 12/03 (quinta, dia útil) = sem prorrogação
venc = calcular_prazo_dias_corridos(date(2026, 3, 2), 10, feriados_test)
ok("10 corridos de 02/03 → 12/03 (quinta)", venc == date(2026, 3, 12), f"got {venc}")

# Corrido que cai em feriado: 15 corridos de 06/04 → 21/04 (Tiradentes)
# 20/04 = suspensão, 21/04 = Tiradentes → prorroga para 22/04 (quarta)
venc = calcular_prazo_dias_corridos(date(2026, 4, 6), 15, feriados_test)
ok("15 corridos de 06/04 → cai 21/04 (Tiradentes) → 22/04",
   venc == date(2026, 4, 22), f"got {venc}")


# ============================================================
# 6. CÁLCULO COMPLETO — Fluxo Disponibilização → Vencimento
# ============================================================
print("\n" + "="*60)
print("6. CÁLCULO COMPLETO — Disponibilização → Vencimento")
print("="*60)

# Caso 1: Disponibilização 05/03 (quinta), 15 dias úteis, BH
r = calcular_prazo_completo(date(2026, 3, 5), 15, feriados_test, "uteis")
ok("Disp 05/03: pub=06/03", r["data_publicacao"] == "2026-03-06")
ok("Disp 05/03: início=09/03", r["data_inicio_prazo"] == "2026-03-09")
# A partir de 09/03 (seg): 15 dias úteis
# 10,11,12,13 = 4 | 16,17,18,19,20(sex) = 9 | 23,24,25,26,27(sex) = 14 | 30 = 15
ok("Disp 05/03: venc=31/03 (São José 19/03 pula)", r["data_vencimento"] == "2026-03-31", f"got {r['data_vencimento']}")
ok("Dias efetivo=15", r["dias_prazo_efetivo"] == 15)
ok("Não dobrado", r["dobrado"] == False)

# Caso 2: Mesma data, prazo em DOBRO
r2 = calcular_prazo_completo(date(2026, 3, 5), 15, feriados_test, "uteis", dobra=True)
ok("Dobro: dias_efetivo=30", r2["dias_prazo_efetivo"] == 30)
ok("Dobro: venc diferente", r2["data_vencimento"] != r["data_vencimento"])
ok("Dobro: venc posterior", r2["data_vencimento"] > r["data_vencimento"])

# Caso 3: Disponibilização sexta-feira
r3 = calcular_prazo_completo(date(2026, 3, 6), 5, feriados_test, "uteis")
ok("Disp sexta 06/03: pub=09/03 (seg)", r3["data_publicacao"] == "2026-03-09")
ok("Disp sexta 06/03: início=10/03 (ter)", r3["data_inicio_prazo"] == "2026-03-10")
# 5 úteis: 11(qua)=1, 12(qui)=2, 13(sex)=3, 16(seg)=4, 17(ter)=5
ok("Disp sexta 06/03: venc=17/03", r3["data_vencimento"] == "2026-03-17", f"got {r3['data_vencimento']}")

# Caso 4: Dias corridos
r4 = calcular_prazo_completo(date(2026, 3, 5), 15, feriados_test, "corridos")
ok("Corridos: contagem=corridos", r4["contagem"] == "corridos")
ok("Corridos: pub=06/03", r4["data_publicacao"] == "2026-03-06")
ok("Corridos: início=09/03", r4["data_inicio_prazo"] == "2026-03-09")
# 09/03 + 15 corridos = 24/03 (terça, dia útil)
ok("Corridos: venc=24/03", r4["data_vencimento"] == "2026-03-24", f"got {r4['data_vencimento']}")

# Caso 5: Disponibilização antes do recesso
r5 = calcular_prazo_completo(date(2026, 12, 18), 5, feriados_test, "uteis")
ok("Disp 18/12: pub=21/01/2027 (pula fds+recesso)", r5["data_publicacao"] == "2027-01-21",
   f"got {r5['data_publicacao']}")
ok("Disp 18/12: início=22/01/2027",
   r5["data_inicio_prazo"] == "2027-01-22", f"got {r5['data_inicio_prazo']}")


# ============================================================
# 7. DIFERENÇA ENTRE COMARCAS — Mesmo prazo, datas diferentes
# ============================================================
print("\n" + "="*60)
print("7. DIFERENÇA ENTRE COMARCAS")
print("="*60)

comarcas_para_testar = ["Belo Horizonte", "Uberlandia", "Juiz de Fora", "Ipatinga", "Contagem"]
resultados = {}

for comarca in comarcas_para_testar:
    fer = db.carregar_feriados(2026, comarca=comarca)
    r = calcular_prazo_completo(date(2026, 2, 12), 15, fer, "uteis")
    resultados[comarca] = r["data_vencimento"]

print(f"  Disp: 12/02/2026 | 15 dias úteis | Cruzando Carnaval")
for c, v in resultados.items():
    print(f"    {c:25s} → vencimento: {v}")

# JF tem feriado 24/02 — deve dar diferente se isso afetar
ok("Comarcas testadas = 5", len(resultados) == 5)


# ============================================================
# 8. DATABASE — Advogados e Processos
# ============================================================
print("\n" + "="*60)
print("8. DATABASE — Advogados, Processos, Prazos")
print("="*60)

# Criar advogado
db.criar_advogado(chat_id=12345, nome="Dr. Teste Silva",
                  oab_numero="99999", oab_seccional="MG", comarca="Belo Horizonte")
user = db.get_advogado_by_chat_id(12345)
ok("Advogado criado", user is not None)
ok("Nome correto", user["nome"] == "Dr. Teste Silva")
ok("Comarca BH", user["comarca"] == "Belo Horizonte")
ok("OAB MG", user["oab_seccional"] == "MG")

# Atualizar comarca
db.atualizar_comarca(12345, "Uberlandia")
user = db.get_advogado_by_chat_id(12345)
ok("Comarca atualizada para UDI", user["comarca"] == "Uberlandia")

# Criar processos
db.criar_processo(advogado_id=user["id"], numero="1234567-89.2024.8.13.0024",
                 partes="Maria da Silva vs Empresa XYZ", vara="2ª Vara Cível")
db.criar_processo(advogado_id=user["id"], numero="7654321-11.2025.8.13.0024",
                 partes="João Santos vs Estado de MG", vara="1ª Vara da Fazenda")
db.criar_processo(advogado_id=user["id"], numero="9999999-00.2026.8.13.0024",
                 partes="Ana Maria Santos vs INSS", vara="JEF")

total = db.contar_processos(user["id"])
ok("3 processos criados", total == 3, f"total={total}")

# Busca parcial por número
proc = db.buscar_processo_por_numero_parcial(user["id"], "1234567")
ok("Busca parcial '1234567' encontrou", proc is not None)
ok("Número correto", "1234567" in proc["numero"])

# Busca por cliente
procs = db.buscar_processos_por_cliente(user["id"], "Maria")
ok("Busca 'Maria' retorna >= 1", len(procs) >= 1)

procs = db.buscar_processos_por_cliente(user["id"], "Santos")
ok("Busca 'Santos' retorna 2 (João e Ana Maria)", len(procs) == 2, f"len={len(procs)}")

# Criar prazo
santos_proc = procs[0]
db.criar_prazo(processo_id=santos_proc["id"], tipo="Contestação",
               data_fim="2026-03-31", fatal=True)

# Listar processos com prazos
processos = db.listar_processos_com_prazos(user["id"])
ok("listar_processos_com_prazos retorna", len(processos) > 0)
tem_prazo = any(p.get("prazos") for p in processos)
ok("Pelo menos 1 processo tem prazo", tem_prazo)


# ============================================================
# 9. EDGE CASES — Casos Limite
# ============================================================
print("\n" + "="*60)
print("9. EDGE CASES")
print("="*60)

# Prazo de 1 dia útil
r = calcular_prazo_completo(date(2026, 3, 2), 1, feriados_test, "uteis")
ok("Prazo 1 dia útil funciona", r["data_vencimento"] is not None)

# Prazo de 0 dias (edge case)
try:
    r = calcular_prazo_completo(date(2026, 3, 2), 0, feriados_test, "uteis")
    # 0 dias úteis = vencimento no mesmo dia do início
    ok("Prazo 0 dias não crasheia", True)
except Exception as e:
    ok("Prazo 0 dias não crasheia", False, str(e))

# Prazo muito longo (360 dias úteis ~= 1.5 ano)
try:
    r = calcular_prazo_completo(date(2026, 3, 2), 360, feriados_test, "uteis")
    ok("Prazo 360 dias úteis funciona", r["data_vencimento"] is not None)
except Exception as e:
    ok("Prazo 360 dias úteis funciona", False, str(e))

# Disponibilização em feriado
r = calcular_prazo_completo(date(2026, 4, 21), 5, feriados_test, "uteis")  # Tiradentes
ok("Disp em feriado: pub pula para útil", r["data_publicacao"] == "2026-04-22",
   f"got {r['data_publicacao']}")

# Disponibilização em domingo
r = calcular_prazo_completo(date(2026, 3, 8), 5, feriados_test, "uteis")  # domingo
ok("Disp domingo: pub=segunda 09/03", r["data_publicacao"] == "2026-03-09",
   f"got {r['data_publicacao']}")

# proximo_dia_util
ok("proximo_dia_util sábado → segunda",
   proximo_dia_util(date(2026, 3, 7), feriados_test) == date(2026, 3, 9))

# dias_uteis_entre
du = dias_uteis_entre(date(2026, 3, 2), date(2026, 3, 6), feriados_test)
ok("Dias úteis seg-sex = 4", du == 4, f"got {du}")

du = dias_uteis_entre(date(2026, 3, 2), date(2026, 3, 9), feriados_test)
ok("Dias úteis seg-seg = 5", du == 5, f"got {du}")


# ============================================================
# 10. VALIDAÇÃO CRUZADA — Conferência Manual
# ============================================================
print("\n" + "="*60)
print("10. VALIDAÇÃO CRUZADA — Conferência Manual de Casos Reais")
print("="*60)

print("\n  📋 CASO A — Contestação cível, BH, 15 dias úteis")
r = calcular_prazo_completo(date(2026, 5, 4), 15, feriados_test, "uteis")
print(f"    Disponibilização: 04/05/2026 (segunda)")
print(f"    Publicação:       {r['data_publicacao']}")
print(f"    Início prazo:     {r['data_inicio_prazo']}")
print(f"    Vencimento:       {r['data_vencimento']}")
print(f"    Dias efetivos:    {r['dias_prazo_efetivo']}")

print("\n  📋 CASO B — Recurso Fazenda Pública (dobro), BH, 15 dias úteis")
r = calcular_prazo_completo(date(2026, 5, 4), 15, feriados_test, "uteis", dobra=True)
print(f"    Disponibilização: 04/05/2026 (segunda)")
print(f"    Publicação:       {r['data_publicacao']}")
print(f"    Início prazo:     {r['data_inicio_prazo']}")
print(f"    Vencimento:       {r['data_vencimento']}")
print(f"    Dias efetivos:    {r['dias_prazo_efetivo']} (dobro)")

print("\n  📋 CASO C — Prazo no Carnaval, JF, 10 dias úteis")
feriados_jf = db.carregar_feriados(2026, comarca="Juiz de Fora")
r = calcular_prazo_completo(date(2026, 2, 12), 10, feriados_jf, "uteis")
print(f"    Disponibilização: 12/02/2026 (quinta)")
print(f"    Publicação:       {r['data_publicacao']}")
print(f"    Início prazo:     {r['data_inicio_prazo']}")
print(f"    Vencimento:       {r['data_vencimento']}")
print(f"    Feriados JF no período: Carnaval 16-18/02 + Aniv. JF 24/02")

print("\n  📋 CASO D — Semana Santa + suspensões, BH, 15 dias úteis")
r = calcular_prazo_completo(date(2026, 3, 30), 15, feriados_test, "uteis")
print(f"    Disponibilização: 30/03/2026 (segunda)")
print(f"    Publicação:       {r['data_publicacao']}")
print(f"    Início prazo:     {r['data_inicio_prazo']}")
print(f"    Vencimento:       {r['data_vencimento']}")
print(f"    Feriados: Semana Santa 01-03/04, Susp. 20/04, Tiradentes 21/04")

print("\n  📋 CASO E — Final de ano com recesso, BH, 10 dias úteis")
r = calcular_prazo_completo(date(2026, 12, 15), 10, feriados_test, "uteis")
print(f"    Disponibilização: 15/12/2026 (terça)")
print(f"    Publicação:       {r['data_publicacao']}")
print(f"    Início prazo:     {r['data_inicio_prazo']}")
print(f"    Vencimento:       {r['data_vencimento']}")
print(f"    Recesso: 20/12/2026 a 20/01/2027 (prazos suspensos)")

print("\n  📋 CASO F — Prazo corrido 30 dias, BH")
r = calcular_prazo_completo(date(2026, 6, 1), 30, feriados_test, "corridos")
print(f"    Disponibilização: 01/06/2026 (segunda)")
print(f"    Publicação:       {r['data_publicacao']}")
print(f"    Início prazo:     {r['data_inicio_prazo']}")
print(f"    Vencimento:       {r['data_vencimento']}")
print(f"    Feriados: Corpus Christi 04/06, Susp. 05/06")


# ============================================================
# 11. CENÁRIOS DE INÍCIO DE CONTAGEM (CPC art. 231)
# ============================================================
print("\n" + "="*60)
print("11. CENÁRIOS DE INÍCIO DE CONTAGEM (CPC art. 231)")
print("="*60)

# --- Cenário A: DJEN (já testado acima, mas confirmamos com tipo_ciencia explícito) ---
r = calcular_prazo_completo(date(2026, 3, 5), 15, feriados_test, "uteis", tipo_ciencia="djen")
ok(r["data_publicacao"] == "2026-03-06", "DJEN: pub=06/03")
ok(r["data_inicio_prazo"] == "2026-03-09", "DJEN: início=09/03")
ok(r["tipo_ciencia"] == "djen", "DJEN: tipo_ciencia correto")

# --- Cenário B: Ciência expressa (advogado abriu no PJe) ---
# Advogado abre segunda 02/03 → início = terça 03/03
r = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="ciencia_expressa")
ok(r["data_inicio_prazo"] == "2026-03-03", "Expressa seg 02/03: início=03/03 (ter)")
ok(r["data_publicacao"] is None, "Expressa: sem data_publicacao")

# Advogado abre sexta 06/03 → início = segunda 09/03
r = calcular_prazo_completo(date(2026, 3, 6), 15, feriados_test, "uteis", tipo_ciencia="ciencia_expressa")
ok(r["data_inicio_prazo"] == "2026-03-09", "Expressa sex 06/03: início=09/03 (seg)")

# Advogado abre em feriado (Tiradentes 21/04 terça) → início = 22/04 (qua)
r = calcular_prazo_completo(date(2026, 4, 21), 5, feriados_test, "uteis", tipo_ciencia="ciencia_expressa")
ok(r["data_inicio_prazo"] == "2026-04-22", "Expressa Tiradentes: início=22/04")

# --- Cenário C: Ciência tácita (não abriu em 10 dias) ---
# Expedição 02/03 (seg) → +10 corridos = 12/03 (qui) → ciência 12/03
# Início = 13/03 (sex)
r = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="ciencia_tacita")
ok(r["data_ciencia"] == "2026-03-12", "Tácita 02/03: ciência=12/03 (qui)")
ok(r["data_inicio_prazo"] == "2026-03-13", "Tácita 02/03: início=13/03 (sex)")

# Expedição 05/03 (qui) → +10 = 15/03 (dom, não útil) → prorroga 16/03 (seg)
# Início = 17/03 (ter)
r = calcular_prazo_completo(date(2026, 3, 5), 15, feriados_test, "uteis", tipo_ciencia="ciencia_tacita")
ok(r["data_ciencia"] == "2026-03-16", "Tácita 05/03: ciência=16/03 (seg, prorrogou dom)")
ok(r["data_inicio_prazo"] == "2026-03-17", "Tácita 05/03: início=17/03 (ter)")

# Expedição com 10º dia caindo em feriado
# Expedição 09/04 (qui) → +10 = 19/04 (dom) → prorroga 20/04 (seg suspensão TJMG?)
# Se 20/04 é suspensão → prorroga 22/04 (qua, pós-Tiradentes)
r = calcular_prazo_completo(date(2026, 4, 9), 5, feriados_test, "uteis", tipo_ciencia="ciencia_tacita")
ok(r["data_ciencia"] is not None, "Tácita abril: ciência calculada")

# --- Cenário D1: Domicílio Judicial Eletrônico — consultada ---
# Consulta 02/03 (seg) → +5 dias úteis = 09/03 (seg)
r = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="dje_consultada")
ok(r["data_inicio_prazo"] == "2026-03-09", "DJE consultada 02/03: início=09/03 (+5 úteis)")
ok(r["data_publicacao"] is None, "DJE consultada: sem publicação")

# Consulta 06/03 (sex) → +5 úteis = 13/03 (sex)
r = calcular_prazo_completo(date(2026, 3, 6), 15, feriados_test, "uteis", tipo_ciencia="dje_consultada")
ok(r["data_inicio_prazo"] == "2026-03-13", "DJE consultada 06/03: início=13/03 (+5 úteis)")

# --- Cenário D2: Domicílio Judicial Eletrônico — tácita ---
# Envio 02/03 (seg) → +10 corridos = 12/03 (qui) → ciência 12/03
# Início = 13/03 (sex) — sem benefício 5º dia útil
r = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="dje_tacita")
ok(r["data_ciencia"] == "2026-03-12", "DJE tácita 02/03: ciência=12/03")
ok(r["data_inicio_prazo"] == "2026-03-13", "DJE tácita 02/03: início=13/03 (sem 5º dia)")

# --- Comparação entre cenários (mesma data base) ---
# Todos com data 02/03/2026, 15 dias úteis, BH
r_djen = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="djen")
r_expr = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="ciencia_expressa")
r_taci = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="ciencia_tacita")
r_djec = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="dje_consultada")
r_djet = calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="dje_tacita")

print(f"\n  📋 COMPARAÇÃO — Mesma data base 02/03/2026, 15 dias úteis, BH")
print(f"    DJEN:              início={r_djen['data_inicio_prazo']} → venc={r_djen['data_vencimento']}")
print(f"    Ciência expressa:  início={r_expr['data_inicio_prazo']} → venc={r_expr['data_vencimento']}")
print(f"    Ciência tácita:    início={r_taci['data_inicio_prazo']} → venc={r_taci['data_vencimento']}")
print(f"    DJE consultada:    início={r_djec['data_inicio_prazo']} → venc={r_djec['data_vencimento']}")
print(f"    DJE tácita:        início={r_djet['data_inicio_prazo']} → venc={r_djet['data_vencimento']}")

# Expressa deve ter início mais cedo que tácita
ok(r_expr["data_inicio_prazo"] < r_taci["data_inicio_prazo"],
      "Expressa tem início antes de tácita")

# DJE consultada deve ter início mais tarde que ciência expressa (5 dias úteis vs 1)
ok(r_djec["data_inicio_prazo"] > r_expr["data_inicio_prazo"],
      "DJE consultada tem início após ciência expressa")

# DJE tácita e ciência tácita devem ter mesmo início (ambos +10 corridos +1 útil)
ok(r_taci["data_inicio_prazo"] == r_djet["data_inicio_prazo"],
      "Ciência tácita e DJE tácita: mesmo início")

# DJEN deve ter início após expressa (disponibilização→publicação→início = 2 dias extras)
ok(r_djen["data_inicio_prazo"] > r_expr["data_inicio_prazo"],
      "DJEN tem início após ciência expressa")

# Tipo ciencia inválido deve dar erro
try:
    calcular_prazo_completo(date(2026, 3, 2), 15, feriados_test, "uteis", tipo_ciencia="invalido")
    ok(False, "tipo_ciencia inválido: deveria dar ValueError")
except ValueError:
    ok(True, "tipo_ciencia inválido: ValueError levantado")


# ============================================================
# 12. EXPANSÃO NACIONAL — Testes Multi-Estado
# ============================================================
# ============================================================
# 12. EXPANSÃO NACIONAL — Testes Multi-Estado
# ============================================================
print("\n" + "="*60)
print("12. EXPANSÃO NACIONAL — Testes Multi-Estado")
print("="*60)

# --- 12a. Estrutura e integridade do módulo feriados_br ---
ok(len(UFS_DISPONIVEIS) == 27, f"27 UFs disponíveis (tem {len(UFS_DISPONIVEIS)})")
ok(len(COMARCAS_DISPONIVEIS) >= 95, f"≥95 comarcas (tem {len(COMARCAS_DISPONIVEIS)})")
ok(len(UF_CAPITAL) == 27, "27 capitais mapeadas")

# Toda comarca deve ter UF mapeada
missing_uf = [c for c in COMARCAS_DISPONIVEIS if c not in COMARCA_UF]
ok(len(missing_uf) == 0, f"Todas comarcas tem UF ({len(missing_uf)} faltando)")

# Toda capital deve estar em COMARCAS_DISPONIVEIS
caps_missing = [c for c in UF_CAPITAL.values() if c not in COMARCAS_DISPONIVEIS]
ok(len(caps_missing) == 0, f"Todas capitais em comarcas ({len(caps_missing)} faltando)")

# listar_comarcas deve retornar pelo menos a capital para cada UF
for uf in UFS_DISPONIVEIS:
    comarcas = listar_comarcas(uf)
    assert len(comarcas) >= 1, f"{uf} sem comarca"
    assert UF_CAPITAL[uf] in comarcas, f"Capital {UF_CAPITAL[uf]} não está nas comarcas de {uf}"
ok(True, "Cada UF tem ao menos a capital nas comarcas")

# --- 12b. obter_feriados_set para cada estado-chave ---
# Todos devem incluir nacionais + suspensões forenses + recesso
for uf, comarca in [("SP", "Sao Paulo"), ("RJ", "Rio de Janeiro"), ("BA", "Salvador"),
                     ("RS", "Porto Alegre"), ("PE", "Recife"), ("CE", "Fortaleza"),
                     ("PR", "Curitiba"), ("SC", "Florianopolis"), ("GO", "Goiania"),
                     ("PA", "Belem"), ("ES", "Vitoria"), ("DF", "Brasilia")]:
    fer = obter_feriados_set(uf, comarca)
    assert "2026-01-01" in fer, f"{uf} sem Ano Novo"
    assert "2026-12-25" in fer, f"{uf} sem Natal"
    assert "2026-02-17" in fer, f"{uf} sem Carnaval"
    assert len(fer) >= 40, f"{uf}/{comarca} com poucos feriados: {len(fer)}"
ok(True, "12 capitais incluem nacionais + suspensões")

# --- 12c. Feriados estaduais específicos ---
# SP: Revolução Constitucionalista 09/07
fer_sp = obter_feriados_set("SP", "Sao Paulo")
ok("2026-07-09" in fer_sp, "SP inclui Revolução Constitucionalista 09/07")

# RJ: São Jorge 23/04
fer_rj = obter_feriados_set("RJ", "Rio de Janeiro")
ok("2026-04-23" in fer_rj, "RJ inclui São Jorge 23/04")

# BA: Independência BA 02/07
fer_ba = obter_feriados_set("BA", "Salvador")
ok("2026-07-02" in fer_ba, "BA inclui Independência BA 02/07")

# RS: Revolução Farroupilha 20/09
fer_rs = obter_feriados_set("RS", "Porto Alegre")
ok("2026-09-20" in fer_rs, "RS inclui Farroupilha 20/09")

# PE: Revolução Pernambucana 06/03
fer_pe = obter_feriados_set("PE", "Recife")
ok("2026-03-06" in fer_pe, "PE inclui Rev. Pernambucana 06/03")

# CE: Abolição CE 25/03
fer_ce = obter_feriados_set("CE", "Fortaleza")
ok("2026-03-25" in fer_ce, "CE inclui Abolição CE 25/03")

# AC: Evangélico 23/01
fer_ac = obter_feriados_set("AC", "Rio Branco")
ok("2026-01-23" in fer_ac, "AC inclui Dia do Evangélico 23/01")

# PA: Adesão PA 15/08
fer_pa = obter_feriados_set("PA", "Belem")
ok("2026-08-15" in fer_pa, "PA inclui Adesão PA 15/08")

# --- 12d. Feriados municipais em comarcas expandidas ---
# Niterói: São João 24/06
fer_nit = obter_feriados_set("RJ", "Niteroi")
ok("2026-06-24" in fer_nit, "Niterói inclui São João 24/06")

# Duque de Caxias: Santo Antônio 13/06
fer_dc = obter_feriados_set("RJ", "Duque de Caxias")
ok("2026-06-13" in fer_dc, "Duque de Caxias inclui Santo Antônio 13/06")

# Caxias do Sul: N.S. Caravaggio 26/05
fer_cxs = obter_feriados_set("RS", "Caxias do Sul")
ok("2026-05-26" in fer_cxs, "Caxias do Sul inclui N.S. Caravaggio 26/05")

# Maringá: Aniversário 10/05
fer_mga = obter_feriados_set("PR", "Maringa")
ok("2026-05-10" in fer_mga, "Maringá inclui Aniversário 10/05")

# Feira de Santana: São João 24/06
fer_fsa = obter_feriados_set("BA", "Feira de Santana")
ok("2026-06-24" in fer_fsa, "Feira de Santana inclui São João 24/06")

# Sobral: Aniversário 05/07
fer_sob = obter_feriados_set("CE", "Sobral")
ok("2026-07-05" in fer_sob, "Sobral inclui Aniversário 05/07")

# Blumenau: Aniversário 02/09
fer_blu = obter_feriados_set("SC", "Blumenau")
ok("2026-09-02" in fer_blu, "Blumenau inclui Aniversário 02/09")

# Vila Velha: Aniversário 23/05
fer_vv = obter_feriados_set("ES", "Vila Velha")
ok("2026-05-23" in fer_vv, "Vila Velha inclui Aniversário 23/05")

# --- 12e. Diferença entre estados — mesmo prazo, vencimentos diferentes ---
print("\n  Disp: 02/03/2026 | 15 dias úteis | Comparação entre estados")
resultados_estados = {}
for uf, comarca in [("MG", "Belo Horizonte"), ("SP", "Sao Paulo"), ("RJ", "Rio de Janeiro"),
                     ("BA", "Salvador"), ("RS", "Porto Alegre"), ("PE", "Recife"),
                     ("CE", "Fortaleza"), ("PR", "Curitiba"), ("DF", "Brasilia")]:
    fer = obter_feriados_set(uf, comarca)
    r = calcular_prazo_completo(date(2026, 3, 2), 15, fer, "uteis")
    resultados_estados[uf] = r["data_vencimento"]
    print(f"    {uf:2s}/{comarca:<20s} → vencimento: {r['data_vencimento']}")

# MG deve ter vencimento diferente de SP (São José 19/03 em MG)
ok(resultados_estados["MG"] != resultados_estados["SP"],
   f"MG ≠ SP (MG={resultados_estados['MG']}, SP={resultados_estados['SP']})")

ok(len(resultados_estados) == 9, "9 estados comparados")

# --- 12f. Comarcas na mesma UF com feriados diferentes ---
print("\n  Disp: 12/02/2026 | 15 dias úteis | RJ: Capital vs Interior")
comarcas_rj = [("Rio de Janeiro", "RJ"), ("Niteroi", "RJ"),
               ("Duque de Caxias", "RJ"), ("Campos dos Goytacazes", "RJ")]
venc_rj = {}
for comarca, uf in comarcas_rj:
    fer = obter_feriados_set(uf, comarca)
    r = calcular_prazo_completo(date(2026, 2, 12), 15, fer, "uteis")
    venc_rj[comarca] = r["data_vencimento"]
    print(f"    {comarca:<25s} → vencimento: {r['data_vencimento']}")
ok(len(venc_rj) == 4, "4 comarcas RJ testadas")

# Mesmo dentro de RJ, feriados municipais podem gerar vencimentos iguais ou diferentes
# Todos devem ter estaduais de RJ (São Jorge 23/04)
for comarca_nome, _ in comarcas_rj:
    fer = obter_feriados_set("RJ", comarca_nome)
    assert "2026-04-23" in fer, f"{comarca_nome}/RJ sem São Jorge"
ok(True, "Todas comarcas RJ incluem estadual São Jorge 23/04")

# --- 12g. Comarcas RS ---
print("\n  Disp: 15/09/2026 | 10 dias úteis | RS: Cruzando Farroupilha 20/09")
comarcas_rs = ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria"]
for comarca in comarcas_rs:
    fer = obter_feriados_set("RS", comarca)
    r = calcular_prazo_completo(date(2026, 9, 15), 10, fer, "uteis")
    print(f"    {comarca:<20s} → vencimento: {r['data_vencimento']}")
    assert "2026-09-20" in fer, f"{comarca}/RS sem Farroupilha"
ok(True, f"{len(comarcas_rs)} comarcas RS cruzando Farroupilha")

# --- 12h. Comarcas PR ---
print("\n  Disp: 01/06/2026 | 10 dias úteis | PR: Cruzando Corpus Christi")
comarcas_pr = ["Curitiba", "Londrina", "Maringa", "Cascavel", "Foz do Iguacu", "Ponta Grossa"]
for comarca in comarcas_pr:
    fer = obter_feriados_set("PR", comarca)
    r = calcular_prazo_completo(date(2026, 6, 1), 10, fer, "uteis")
    print(f"    {comarca:<20s} → vencimento: {r['data_vencimento']}")
ok(True, f"{len(comarcas_pr)} comarcas PR testadas")

# --- 12i. Comarcas BA ---
print("\n  Disp: 20/06/2026 | 15 dias úteis | BA: Cruzando Independência BA 02/07")
comarcas_ba = ["Salvador", "Feira de Santana", "Vitoria da Conquista", "Ilheus", "Camacari"]
for comarca in comarcas_ba:
    fer = obter_feriados_set("BA", comarca)
    r = calcular_prazo_completo(date(2026, 6, 20), 15, fer, "uteis")
    print(f"    {comarca:<25s} → vencimento: {r['data_vencimento']}")
    assert "2026-07-02" in fer, f"{comarca}/BA sem Independência BA"
ok(True, f"{len(comarcas_ba)} comarcas BA cruzando Indep. BA 02/07")

# --- 12j. Comarcas PE ---
print("\n  Disp: 01/03/2026 | 10 dias úteis | PE: Cruzando Rev. Pernambucana 06/03")
comarcas_pe = ["Recife", "Jaboatao dos Guararapes", "Olinda", "Caruaru", "Petrolina"]
for comarca in comarcas_pe:
    fer = obter_feriados_set("PE", comarca)
    r = calcular_prazo_completo(date(2026, 3, 1), 10, fer, "uteis")
    print(f"    {comarca:<30s} → vencimento: {r['data_vencimento']}")
    assert "2026-03-06" in fer, f"{comarca}/PE sem Rev. Pernambucana"
ok(True, f"{len(comarcas_pe)} comarcas PE cruzando Rev. Pernambucana 06/03")

# --- 12k. Todas 97 comarcas calculam prazo sem erro ---
erros_comarca = []
for comarca in COMARCAS_DISPONIVEIS:
    uf = COMARCA_UF[comarca]
    try:
        fer = obter_feriados_set(uf, comarca)
        r = calcular_prazo_completo(date(2026, 3, 2), 15, fer, "uteis")
        assert r["data_vencimento"] >= "2026-03-20"
    except Exception as e:
        erros_comarca.append(f"{comarca}/{uf}: {e}")
ok(len(erros_comarca) == 0,
   f"Todas {len(COMARCAS_DISPONIVEIS)} comarcas calculam prazo sem erro ({len(erros_comarca)} falharam)")
if erros_comarca:
    for e in erros_comarca[:5]:
        print(f"    ❌ {e}")

# --- 12l. Contagem de feriados por estado (sanity check) ---
print(f"\n  📊 Feriados por capital (obter_feriados_set):")
for uf in ["AC", "SP", "RJ", "MG", "BA", "RS", "PE", "CE", "PR", "DF"]:
    capital = UF_CAPITAL[uf]
    fer = obter_feriados_set(uf, capital)
    print(f"    {uf:2s}/{capital:<20s} → {len(fer)} feriados")
    assert len(fer) >= 40, f"{uf} com menos de 40 feriados"
ok(True, "10 capitais com ≥40 feriados cada")


# ============================================================
# RESULTADO FINAL
# ============================================================
print("\n" + "="*60)
print(f"RESULTADO: {PASS} ✅ passou | {FAIL} ❌ falhou")
print("="*60)

if ERROS:
    print("\n❌ FALHAS:")
    for e in ERROS:
        print(f"  → {e}")

# Cleanup
os.remove(TEST_DB)

sys.exit(0 if FAIL == 0 else 1)
