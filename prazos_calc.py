"""
Motor de Calculo de Prazos Processuais - Nacional
Regras: CPC arts. 216, 219, 220, 224

Usa cal_forense.CalendarResolver para verificar dias uteis,
considerando feriados da comarca DO PROCESSO (nao do advogado).
"""

from datetime import date, timedelta
from cal_forense.calendar_store import CalendarStore
from cal_forense.calendar_resolver import CalendarResolver

_store = None
_resolver = None


def _get_resolver(db_path="cal_forense/calendar_v2.db"):
    global _store, _resolver
    if _resolver is None:
        _store = CalendarStore(db_path)
        _resolver = CalendarResolver(_store)
    return _resolver


def _eh_dia_util(d, uf="", comarca_processo=""):
    return _get_resolver().is_business_day(d, uf, comarca_processo)


def _em_recesso(d):
    """Recesso forense 20/dez a 20/jan (CPC art. 220). Exposto para testes."""
    return _get_resolver()._em_recesso(d)


def calcular_prazo_dias_uteis(data_inicio, dias, uf="", comarca_processo="", feriados=None):
    """CPC art. 224: exclui dia do comeco, inclui dia do vencimento."""
    d = data_inicio
    contados = 0
    while contados < dias:
        d += timedelta(days=1)
        if _eh_dia_util(d, uf, comarca_processo):
            contados += 1
    return d


def calcular_prazo_dias_corridos(data_inicio, dias, uf="", comarca_processo="", feriados=None):
    """Dias corridos. Se vencimento cair em dia nao util, prorroga."""
    d = data_inicio + timedelta(days=dias)
    while not _eh_dia_util(d, uf, comarca_processo):
        d += timedelta(days=1)
    return d


def calcular_data_publicacao(data_disponibilizacao, uf="", comarca_processo="", feriados=None):
    """DJEN: publicacao no 1o dia util seguinte. CPC art. 224 par. 2."""
    d = data_disponibilizacao + timedelta(days=1)
    while not _eh_dia_util(d, uf, comarca_processo):
        d += timedelta(days=1)
    return d


def calcular_inicio_prazo(data_publicacao, uf="", comarca_processo="", feriados=None):
    """Prazo comeca no 1o dia util apos publicacao. CPC art. 224 par. 3."""
    d = data_publicacao + timedelta(days=1)
    while not _eh_dia_util(d, uf, comarca_processo):
        d += timedelta(days=1)
    return d


def calcular_prazo_completo(
    data_disponibilizacao,
    dias_prazo,
    uf="",
    comarca_processo="",
    contagem="uteis",
    dobra=False,
    feriados=None,
):
    """
    Calcula prazo completo a partir da disponibilizacao no DJEN.

    comarca_processo = comarca onde o processo tramita (CPC art. 216).
    feriados = DEPRECATED, mantido para retrocompat, ignorado.
    """
    dias_efetivo = dias_prazo * 2 if dobra else dias_prazo

    data_pub = calcular_data_publicacao(data_disponibilizacao, uf, comarca_processo)
    data_ini = calcular_inicio_prazo(data_pub, uf, comarca_processo)

    if contagem == "uteis":
        data_venc = calcular_prazo_dias_uteis(data_ini, dias_efetivo, uf, comarca_processo)
    else:
        data_venc = calcular_prazo_dias_corridos(data_ini, dias_efetivo, uf, comarca_processo)

    confidence = _get_resolver().get_confidence_for(uf, comarca_processo)

    return {
        "data_disponibilizacao": data_disponibilizacao.isoformat(),
        "data_publicacao": data_pub.isoformat(),
        "data_inicio_prazo": data_ini.isoformat(),
        "data_vencimento": data_venc.isoformat(),
        "dias_prazo": dias_prazo,
        "dias_prazo_efetivo": dias_efetivo,
        "contagem": contagem,
        "dobrado": dobra,
        "uf": uf,
        "comarca_processo": comarca_processo,
        "confidence": confidence,
    }


def dias_uteis_entre(data1, data2, uf="", comarca_processo="", feriados=None):
    """Conta dias uteis entre duas datas (exclusive data1, inclusive data2)."""
    contagem = 0
    d = data1
    while d < data2:
        d += timedelta(days=1)
        if _eh_dia_util(d, uf, comarca_processo):
            contagem += 1
    return contagem


def proximo_dia_util(d, uf="", comarca_processo="", feriados=None):
    """Retorna proximo dia util a partir de d (inclusive)."""
    while not _eh_dia_util(d, uf, comarca_processo):
        d += timedelta(days=1)
    return d
