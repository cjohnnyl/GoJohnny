"""
Engine de calendário do GoJohnny — Fase 1, Bloco 7.

Recebe (data_inicio, data_prova, dias_treino) e devolve um calendário
determinístico de treinos, agrupado por semana ISO (segunda como início).

Princípios:
  - Pura função: mesmas entradas → mesmas saídas. Sem dependência de
    relógio, sem efeito colateral.
  - Validação rigorosa de entrada com mensagens claras.
  - Tolerância a variações de input nos dias (acentos, abreviações).
  - Sem treino antes de data_inicio nem depois de data_prova.
  - Semana 1 é a semana ISO que contém data_inicio.

A serialização para JSON/HTTP é responsabilidade do caller.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import groupby
from typing import Sequence
from zoneinfo import ZoneInfo


TIMEZONE_BRASIL = ZoneInfo("America/Sao_Paulo")


# Tupla na ordem do weekday() do Python (0=segunda ... 6=domingo).
# Versão SEM acento usada como chave canônica interna.
_NOMES_NORMALIZADOS: tuple[str, ...] = (
    "segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo",
)

# Versão COM acento usada na saída user-facing.
_NOMES_CANONICOS: tuple[str, ...] = (
    "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo",
)

# Apelidos aceitos. Chaves SEMPRE em forma normalizada (sem acento, lowercase).
# Valor = índice do weekday (0=segunda ... 6=domingo).
_APELIDOS: dict[str, int] = {
    # segunda
    "segunda": 0, "seg": 0, "segunda-feira": 0, "segunda feira": 0,
    # terça
    "terca": 1, "ter": 1, "terca-feira": 1, "terca feira": 1,
    # quarta
    "quarta": 2, "qua": 2, "quarta-feira": 2, "quarta feira": 2,
    # quinta
    "quinta": 3, "qui": 3, "quinta-feira": 3, "quinta feira": 3,
    # sexta
    "sexta": 4, "sex": 4, "sexta-feira": 4, "sexta feira": 4,
    # sábado
    "sabado": 5, "sab": 5, "sabado-feira": 5, "sabado feira": 5,
    # domingo
    "domingo": 6, "dom": 6,
}


def _normalizar(s: str) -> str:
    """Lowercase, strip e remoção de acentos (NFD + filtro de marcas)."""
    if not isinstance(s, str):
        raise TypeError(
            f"Dia da semana deve ser str, recebido {type(s).__name__}"
        )
    s = s.strip().lower()
    s = "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if unicodedata.category(ch) != "Mn"
    )
    return s


def normalizar_dia_da_semana(dia: str) -> int:
    """Converte um nome de dia em pt-BR para weekday Python (0=segunda).

    Tolera acentos, abreviações de 3 letras e formas com '-feira'.
    Levanta ValueError se não reconhecer.
    """
    chave = _normalizar(dia)
    if chave in _APELIDOS:
        return _APELIDOS[chave]
    raise ValueError(
        f"Dia da semana não reconhecido: {dia!r}. "
        f"Aceito: segunda, terça, quarta, quinta, sexta, sábado, domingo "
        f"(com ou sem acento; abreviações: seg, ter, qua, qui, sex, sab, dom)."
    )


def nome_canonico_do_weekday(weekday: int) -> str:
    """0..6 -> 'segunda'..'domingo' (com acento)."""
    if not (0 <= weekday <= 6):
        raise ValueError(f"weekday inválido: {weekday}")
    return _NOMES_CANONICOS[weekday]


# --------------------------------------------------------------------------- #
# Estruturas de saída                                                          #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class TreinoCalendario:
    """Um treino dentro do calendário gerado."""
    data: date
    dia_semana: str        # nome canônico com acento ("terça", "sábado"…)
    numero_semana: int     # 1-based; 1 = semana que contém data_inicio
    eh_dia_da_prova: bool  # True se data == data_prova


@dataclass(frozen=True)
class SemanaCalendario:
    """Agrupamento ISO por semana (segunda → domingo)."""
    numero: int
    segunda: date
    domingo: date
    treinos: tuple[TreinoCalendario, ...]


@dataclass(frozen=True)
class CalendarioPlano:
    """Calendário completo gerado a partir das entradas."""
    data_inicio: date
    data_prova: date
    dias_treino_canonicos: tuple[str, ...]
    treinos: tuple[TreinoCalendario, ...]
    semanas: tuple[SemanaCalendario, ...]

    @property
    def total_treinos(self) -> int:
        return len(self.treinos)

    @property
    def total_semanas(self) -> int:
        return len(self.semanas)


# --------------------------------------------------------------------------- #
# Função principal                                                             #
# --------------------------------------------------------------------------- #

def _segunda_da_semana(d: date) -> date:
    """Retorna a segunda-feira da semana ISO em que d cai."""
    return d - timedelta(days=d.weekday())


def gerar_calendario(
    *,
    data_inicio: date,
    data_prova: date,
    dias_treino: Sequence[str],
) -> CalendarioPlano:
    """Monta um calendário de treinos entre data_inicio e data_prova
    (inclusive em ambas), apenas nos dias da semana indicados.

    Raises:
        ValueError: se data_inicio > data_prova, dias_treino vazio,
                    ou algum nome de dia não puder ser normalizado.
    """
    if not isinstance(data_inicio, date) or isinstance(data_inicio, datetime):
        raise TypeError("data_inicio deve ser date (não datetime).")
    if not isinstance(data_prova, date) or isinstance(data_prova, datetime):
        raise TypeError("data_prova deve ser date (não datetime).")
    if not dias_treino:
        raise ValueError("dias_treino não pode ser vazio.")
    if data_inicio > data_prova:
        raise ValueError(
            f"data_inicio ({data_inicio.isoformat()}) é posterior a "
            f"data_prova ({data_prova.isoformat()})."
        )

    # Normaliza, deduplica e ordena os índices dos dias.
    indices: list[int] = sorted({normalizar_dia_da_semana(d) for d in dias_treino})
    canonicos: tuple[str, ...] = tuple(nome_canonico_do_weekday(i) for i in indices)

    segunda_base = _segunda_da_semana(data_inicio)

    treinos: list[TreinoCalendario] = []
    cursor = data_inicio
    while cursor <= data_prova:
        if cursor.weekday() in indices:
            numero_semana = (
                (_segunda_da_semana(cursor) - segunda_base).days // 7
            ) + 1
            treinos.append(
                TreinoCalendario(
                    data=cursor,
                    dia_semana=nome_canonico_do_weekday(cursor.weekday()),
                    numero_semana=numero_semana,
                    eh_dia_da_prova=(cursor == data_prova),
                )
            )
        cursor += timedelta(days=1)

    # Agrupa em semanas. Mesmo se não houver treino numa semana intermediária
    # ela não aparece (escolha consciente: economizar payload). O numero da
    # semana ainda reflete a posição correta a partir do início.
    semanas: list[SemanaCalendario] = []
    for numero, grupo in groupby(treinos, key=lambda t: t.numero_semana):
        grupo_tup = tuple(grupo)
        segunda = segunda_base + timedelta(days=(numero - 1) * 7)
        domingo = segunda + timedelta(days=6)
        semanas.append(
            SemanaCalendario(
                numero=numero,
                segunda=segunda,
                domingo=domingo,
                treinos=grupo_tup,
            )
        )

    return CalendarioPlano(
        data_inicio=data_inicio,
        data_prova=data_prova,
        dias_treino_canonicos=canonicos,
        treinos=tuple(treinos),
        semanas=tuple(semanas),
    )


def hoje_sao_paulo() -> date:
    """Data corrente em America/Sao_Paulo. Útil para outros services."""
    return datetime.now(TIMEZONE_BRASIL).date()
