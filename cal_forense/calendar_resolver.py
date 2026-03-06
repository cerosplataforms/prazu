"""
calendar_resolver.py — Resolvedor de dias úteis forenses
=========================================================

Ponto central de decisão. Responde:
- is_business_day(data, uf, comarca_processo) → bool
- explain(data, uf, comarca_processo) → {is_useful, reasons, confidence}
- next_business_day(data, uf, comarca_processo) → date

Precedência (o que torna NÃO útil):
  1. Fim de semana (sábado/domingo)
  2. Recesso forense (20/dez a 20/jan — CPC art. 220)
  3. Suspensão do TJ (portaria específica)
  4. Feriado nacional
  5. Feriado estadual do TJ
  6. Feriado municipal forense (provimento)

Confiança:
  - HIGH: feriado nacional, recesso, fim de semana, suspensão TJ documentada
  - MEDIUM: feriado municipal de provimento parseado
  - LOW: comarca do processo sem cobertura de feriados municipais (só nacionais + estaduais)
"""

import logging
from datetime import date, timedelta
from cal_forense import calendar_store

logger = logging.getLogger(__name__)


class CalendarResolver:
    """Resolve se uma data é dia útil forense."""

    def __init__(self, store: 'calendar_store.CalendarStore'):
        self.store = store
        self._cache = {}  # (ano, uf, comarca_processo) → set de datas

    def _get_holiday_set(self, ano: int, uf: str, comarca_processo: str) -> set:
        """Retorna set de datas de feriados (com cache)."""
        key = (ano, uf, comarca_processo)
        if key not in self._cache:
            self._cache[key] = self.store.obter_set(ano, uf, comarca_processo)
        return self._cache[key]

    def _em_recesso(self, d: date) -> bool:
        """Verifica se está no recesso forense (CPC art. 220)."""
        # 20/dez a 20/jan
        if d.month == 12 and d.day >= 20:
            return True
        if d.month == 1 and d.day <= 20:
            return True
        return False

    def is_business_day(self, d: date, uf: str = "", comarca_processo: str = "") -> bool:
        """
        Retorna True se é dia útil forense.
        """
        # 1. Fim de semana
        if d.weekday() >= 5:
            return False

        # 2. Recesso forense
        if self._em_recesso(d):
            return False

        # 3. Feriados do banco
        feriados = self._get_holiday_set(d.year, uf, comarca_processo)
        data_iso = d.isoformat()
        if data_iso in feriados:
            return False

        return True

    def explain(self, d: date, uf: str = "", comarca_processo: str = "") -> dict:
        """
        Explica por que uma data é ou não dia útil.

        Returns:
            {
                "data": "2026-04-20",
                "dia_util": False,
                "reasons": [
                    {"motivo": "Suspensão de expediente TJSP", "tipo": "suspensao_tj",
                     "fonte": "Provimento CSM 2.813/2025", "confianca": "high"}
                ],
                "confidence": "high",  # menor confiança entre as reasons
                "comarca_coberta": True,  # se a comarca do processo tem feriados municipais no banco
            }
        """
        data_iso = d.isoformat()
        reasons = []
        confidence = "high"

        # 1. Fim de semana
        if d.weekday() >= 5:
            dia = "Sabado" if d.weekday() == 5 else "Domingo"
            reasons.append({
                "motivo": dia,
                "tipo": "fim_de_semana",
                "fonte": "CPC art. 216",
                "confianca": "high",
            })

        # 2. Recesso forense
        if self._em_recesso(d):
            reasons.append({
                "motivo": "Recesso forense",
                "tipo": "recesso",
                "fonte": "CPC art. 220",
                "confianca": "high",
            })

        # 3. Feriados do banco
        db_reasons = self.store.explicar_data(data_iso, uf, comarca_processo)
        for r in db_reasons:
            reasons.append({
                "motivo": r["descricao"],
                "tipo": r["tipo"],
                "fonte": r.get("fonte", ""),
                "confianca": r.get("confianca", "high"),
            })
            if r.get("confianca") == "low":
                confidence = "low"
            elif r.get("confianca") == "medium" and confidence == "high":
                confidence = "medium"

        # Verifica cobertura da comarca do processo
        comarca_coberta = True
        if comarca_processo and uf:
            comarcas_cobertas = self.store.listar_comarcas(uf)
            if comarca_processo not in comarcas_cobertas:
                comarca_coberta = False
                if not reasons:
                    confidence = "medium"  # Sem feriados municipais = menor confiança

        dia_util = len(reasons) == 0

        return {
            "data": data_iso,
            "dia_util": dia_util,
            "reasons": reasons,
            "confidence": confidence,
            "comarca_coberta": comarca_coberta,
        }

    def next_business_day(self, d: date, uf: str = "", comarca_processo: str = "") -> date:
        """Retorna o próximo dia útil a partir de d (inclusive)."""
        current = d
        max_iter = 400  # safety
        for _ in range(max_iter):
            if self.is_business_day(current, uf, comarca_processo):
                return current
            current += timedelta(days=1)
        return current  # fallback

    def count_business_days(
        self, start: date, end: date,
        uf: str = "", comarca_processo: str = ""
    ) -> int:
        """Conta dias úteis entre start e end (exclusive)."""
        count = 0
        current = start + timedelta(days=1)
        while current <= end:
            if self.is_business_day(current, uf, comarca_processo):
                count += 1
            current += timedelta(days=1)
        return count

    def clear_cache(self):
        """Limpa cache de feriados."""
        self._cache.clear()

    def get_confidence_for(self, uf: str, comarca_processo: str) -> str:
        """
        Retorna nível de confiança geral para uma comarca.
        - high: comarca do processo tem feriados municipais forenses no banco
        - medium: só feriados estaduais/nacionais (sem municipais)
        - low: UF sem dados de TJ
        """
        if comarca_processo:
            comarcas = self.store.listar_comarcas(uf)
            if comarca_processo in comarcas:
                return "high"

        # Verifica se tem feriados estaduais
        contagem = self.store.contar(2026, uf)
        if contagem.get("estadual_tj", 0) > 0 or contagem.get("suspensao_tj", 0) > 0:
            return "medium"

        return "low"


def formatar_explicacao_telegram(resultado: dict) -> str:
    """
    Formata resultado do explain() para Telegram.
    """
    d = resultado["data"]
    # Converte YYYY-MM-DD para DD/MM/YYYY
    partes = d.split("-")
    data_fmt = f"{partes[2]}/{partes[1]}/{partes[0]}"

    if resultado["dia_util"]:
        msg = f"✅ *{data_fmt}* é *dia útil*"
        if not resultado["comarca_coberta"]:
            msg += "\n\n⚠️ _Comarca do processo sem cobertura de feriados municipais forenses._"
            msg += "\n_Apenas feriados nacionais e estaduais considerados._"
    else:
        msg = f"❌ *{data_fmt}* *NÃO é dia útil*\n"
        for r in resultado["reasons"]:
            tipo_emoji = {
                "fim_de_semana": "📅",
                "recesso": "🏖",
                "nacional": "🇧🇷",
                "estadual_tj": "🏛",
                "suspensao_tj": "⚖️",
                "municipal_forense": "🏘",
            }.get(r["tipo"], "📌")
            msg += f"\n{tipo_emoji} *{r['motivo']}*"
            if r.get("fonte"):
                msg += f"\n   _Fonte: {r['fonte']}_"

    # Confiança
    conf = resultado["confidence"]
    if conf == "high":
        msg += "\n\n🟢 Confianca: *alta*"
    elif conf == "medium":
        msg += "\n\n🟡 Confianca: *media* — verifique feriados municipais"
    else:
        msg += "\n\n🔴 Confianca: *baixa* — recomenda-se verificacao manual"

    return msg


# ============================================================
# TESTE
# ============================================================
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    test_db = "test_resolver.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    store = calendar_store.CalendarStore(test_db)

    # Carrega alguns feriados
    store.inserir_feriado("2026-01-01", "Ano Novo", "nacional")
    store.inserir_feriado("2026-04-20", "Suspensao expediente", "suspensao_tj",
                          uf="SP", tribunal="TJSP", fonte="Provimento CSM 2.813/2025")
    store.inserir_feriado("2026-01-25", "Aniversario de SP", "municipal_forense",
                          uf="SP", comarca="Sao Paulo", tribunal="TJSP",
                          fonte="Provimento CSM 2.813/2025")

    resolver = CalendarResolver(store)

    # Teste: segunda-feira normal
    d1 = date(2026, 3, 2)
    assert resolver.is_business_day(d1, "SP", "Sao Paulo") == True
    print(f"✅ {d1} é dia útil")

    # Teste: sábado
    d2 = date(2026, 3, 7)
    assert resolver.is_business_day(d2) == False
    print(f"✅ {d2} (sábado) não é útil")

    # Teste: recesso
    d3 = date(2026, 1, 10)
    assert resolver.is_business_day(d3) == False
    print(f"✅ {d3} (recesso) não é útil")

    # Teste: suspensão TJSP
    d4 = date(2026, 4, 20)
    assert resolver.is_business_day(d4, "SP") == False
    r = resolver.explain(d4, "SP", "Sao Paulo")
    print(f"✅ {d4} (suspensão TJSP): {r['reasons'][0]['motivo']}")

    # Teste: aniversário SP (municipal)
    d5 = date(2026, 1, 25)
    r5 = resolver.explain(d5, "SP", "Sao Paulo")
    assert not r5["dia_util"]
    print(f"✅ {d5} (aniv SP): não é útil — recesso + municipal")

    # Teste: formatar Telegram
    msg = formatar_explicacao_telegram(r)
    print(f"\nTelegram:\n{msg}")

    # Próximo útil
    prox = resolver.next_business_day(date(2026, 4, 18), "SP", "Sao Paulo")
    print(f"\n✅ Próximo útil após 18/04: {prox}")

    store.close()
    os.remove(test_db)
    print("\n✅ CalendarResolver OK")
