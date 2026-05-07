"""
Utilitário centralizado para datas e fusos horários.

Princípio: TUDO no GoJohnny usa America/Sao_Paulo como referência de negócio.
UTC é apenas para armazenamento técnico.
"""

from datetime import datetime, date, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Dict, Any


TZ_SP = ZoneInfo("America/Sao_Paulo")


def get_app_timezone() -> ZoneInfo:
    """Retorna o timezone padrão do aplicativo: America/Sao_Paulo."""
    return TZ_SP


def now_sp() -> datetime:
    """Retorna datetime.now() em America/Sao_Paulo."""
    return datetime.now(TZ_SP)


def today_sp() -> date:
    """Retorna date de hoje em America/Sao_Paulo."""
    return now_sp().date()


def local_day_range_sp(date_value: Optional[date] = None) -> Dict[str, Any]:
    """
    Retorna o intervalo completo de um dia em America/Sao_Paulo.

    Se date_value for None, usa today_sp().

    Retorna:
    {
        "data_local": date,
        "inicio_local": datetime com TZ_SP,
        "fim_local": datetime com TZ_SP,
        "after_epoch": int (timestamp epoch do início),
        "before_epoch": int (timestamp epoch do fim)
    }
    """
    if date_value is None:
        date_value = today_sp()

    inicio_local = datetime.combine(date_value, time.min, tzinfo=TZ_SP)
    fim_local = inicio_local + timedelta(days=1)

    return {
        "data_local": date_value,
        "inicio_local": inicio_local,
        "fim_local": fim_local,
        "after_epoch": int(inicio_local.timestamp()),
        "before_epoch": int(fim_local.timestamp()),
    }


def week_range_sp(reference_date: Optional[date] = None, week_start: str = "monday") -> Dict[str, Any]:
    """
    Retorna o intervalo completo de uma semana em America/Sao_Paulo.

    week_start: "monday" (padrão, segunda-feira) ou "sunday".
    Se reference_date for None, usa today_sp().

    Retorna:
    {
        "semana_inicio": date (segunda-feira ou domingo),
        "semana_fim": date (domingo ou sábado),
        "inicio_local": datetime com TZ_SP (início do primeiro dia),
        "fim_local": datetime com TZ_SP (fim do último dia),
        "after_epoch": int,
        "before_epoch": int
    }
    """
    if reference_date is None:
        reference_date = today_sp()

    # Calcular segunda-feira ou domingo da semana
    if week_start == "monday":
        # Segunda-feira é weekday() 0
        days_back = reference_date.weekday()
        semana_inicio = reference_date - timedelta(days=days_back)
        semana_fim = semana_inicio + timedelta(days=6)
    else:  # sunday
        # Domingo é weekday() 6
        days_back = (reference_date.weekday() + 1) % 7
        semana_inicio = reference_date - timedelta(days=days_back)
        semana_fim = semana_inicio + timedelta(days=6)

    inicio_local = datetime.combine(semana_inicio, time.min, tzinfo=TZ_SP)
    fim_local = datetime.combine(semana_fim + timedelta(days=1), time.min, tzinfo=TZ_SP)

    return {
        "semana_inicio": semana_inicio,
        "semana_fim": semana_fim,
        "inicio_local": inicio_local,
        "fim_local": fim_local,
        "after_epoch": int(inicio_local.timestamp()),
        "before_epoch": int(fim_local.timestamp()),
    }


def parse_user_relative_date(texto: str, reference_date: Optional[date] = None) -> Optional[date]:
    """
    Mapeia expressões simples do usuário para datas em America/Sao_Paulo.

    Suporta:
    - "hoje" -> today_sp()
    - "amanhã" -> today_sp() + 1 dia
    - "ontem" -> today_sp() - 1 dia
    - "semana atual", "essa semana" -> semana_inicio da semana atual
    - "semana que vem", "próxima semana" -> semana_inicio da próxima semana
    - "semana passada" -> semana_inicio da semana anterior

    Se texto não for reconhecido, retorna None.
    """
    if reference_date is None:
        reference_date = today_sp()

    texto_lower = texto.strip().lower()

    if texto_lower in ("hoje", "today"):
        return reference_date
    elif texto_lower in ("amanhã", "amanha", "tomorrow"):
        return reference_date + timedelta(days=1)
    elif texto_lower in ("ontem", "yesterday"):
        return reference_date - timedelta(days=1)
    elif texto_lower in ("semana atual", "essa semana", "this week"):
        week_info = week_range_sp(reference_date)
        return week_info["semana_inicio"]
    elif texto_lower in ("semana que vem", "próxima semana", "proxima semana", "next week"):
        current_week = week_range_sp(reference_date)
        return current_week["semana_inicio"] + timedelta(days=7)
    elif texto_lower in ("semana passada", "last week"):
        current_week = week_range_sp(reference_date)
        return current_week["semana_inicio"] - timedelta(days=7)

    return None


def weekday_date_for_week(
    dia_semana: str,
    semana_inicio: date
) -> Optional[date]:
    """
    Dado um nome de dia da semana e a data de início da semana (segunda-feira),
    retorna a data correspondente naquela semana.

    dia_semana: "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"
    semana_inicio: data de segunda-feira (esperado)

    Retorna a data daquele dia naquela semana, ou None se dia_semana inválido.
    """
    dias_mapa = {
        "segunda": 0,
        "terça": 1,
        "terca": 1,
        "quarta": 2,
        "quinta": 3,
        "sexta": 4,
        "sábado": 5,
        "sabado": 5,
        "domingo": 6,
    }

    offset = dias_mapa.get(dia_semana.strip().lower())
    if offset is None:
        return None

    return semana_inicio + timedelta(days=offset)


def normalize_date_to_sp(dt_input: Any) -> datetime:
    """
    Converte qualquer datetime para America/Sao_Paulo (timezone-aware).

    Se já for timezone-aware, converte para TZ_SP.
    Se for naive, assume UTC e depois converte.
    Se for date, converte para datetime em TZ_SP 00:00.
    """
    if isinstance(dt_input, date) and not isinstance(dt_input, datetime):
        return datetime.combine(dt_input, time.min, tzinfo=TZ_SP)

    if isinstance(dt_input, datetime):
        if dt_input.tzinfo is None:
            # Assume UTC para naive datetimes
            dt_input = dt_input.replace(tzinfo=dt_timezone.utc)
        # Converte para São Paulo
        return dt_input.astimezone(TZ_SP)

    raise ValueError(f"Tipo inválido para normalize_date_to_sp: {type(dt_input)}")


def to_utc_epoch(dt_local: datetime) -> int:
    """
    Converte um datetime timezone-aware (preferentemente em TZ_SP)
    para timestamp epoch UTC.
    """
    if dt_local.tzinfo is None:
        raise ValueError("datetime deve ser timezone-aware")
    return int(dt_local.timestamp())


def format_date_pt(date_value: date) -> str:
    """
    Formata uma data em português brasileiro: "dd/mm/yyyy"
    Exemplo: "06/05/2026"
    """
    return date_value.strftime("%d/%m/%Y")


def format_datetime_pt(dt_value: datetime) -> str:
    """
    Formata um datetime em português brasileiro: "dd/mm/yyyy HH:MM"
    Exemplo: "06/05/2026 06:48"
    """
    return dt_value.strftime("%d/%m/%Y %H:%M")


def get_weekday_name_pt(date_value: date) -> str:
    """
    Retorna o nome do dia da semana em português.
    Exemplo: 0 (segunda) -> "segunda"
    """
    nomes = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    return nomes[date_value.weekday()]


def get_weekday_abbr_pt(date_value: date) -> str:
    """
    Retorna a abreviação do dia da semana em português.
    Exemplo: 0 (segunda) -> "seg"
    """
    abreviacoes = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    return abreviacoes[date_value.weekday()]


def format_date_with_weekday_pt(date_value: date) -> str:
    """
    Formata data com dia da semana em português.
    Exemplo: "segunda, 06/05/2026"
    """
    weekday = get_weekday_name_pt(date_value)
    date_str = format_date_pt(date_value)
    return f"{weekday}, {date_str}"


def format_time_pt(dt_value: datetime) -> str:
    """
    Formata apenas a hora em português.
    Exemplo: "06:48"
    """
    return dt_value.strftime("%H:%M")
