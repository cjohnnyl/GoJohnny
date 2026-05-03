"""
Leitura tolerante do JSONB de plano — Fase 1, Bloco 8.

Objetivo
  Permitir que backend e GPT funcionem com planos antigos (sem datas)
  E enriquecidos (com data_inicio, data_prova, treinos[].data) usando
  a MESMA representação interna padronizada.

Regras
  - Nenhum campo é obrigatório dentro do JSONB do plano.
  - Campos desconhecidos são preservados em `extras` (não jogados fora).
  - Erros de tipagem em campos individuais NÃO derrubam o parse — o
    campo é setado como None e o resto continua. Permite ler dados
    legados imperfeitos.
  - A versão da estrutura é detectada heuristicamente quando não
    informada explicitamente.

Campos canônicos por treino (após normalização)
  data, dia_semana, tipo, descricao, distancia_km, duracao_min,
  intensidade, objetivo, extras
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping


_CAMPOS_CANONICOS_TREINO: frozenset[str] = frozenset({
    "data", "dia_semana", "dia", "tipo", "descricao",
    "distancia_km", "duracao_min", "intensidade", "objetivo",
})


@dataclass(frozen=True)
class TreinoNormalizado:
    data: date | None
    dia_semana: str | None
    tipo: str | None
    descricao: str | None
    distancia_km: float | None
    duracao_min: int | None
    intensidade: str | None
    objetivo: str | None
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EstruturaPlanoNormalizada:
    versao: int                            # 1 = legado, 2 = enriquecido
    treinos: tuple[TreinoNormalizado, ...]
    tem_datas: bool                        # True se algum treino tem data
    tem_semanas: bool                      # True se há campo "semanas"
    bruto: Mapping[str, Any]               # JSON original, para debug


def _to_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s or None
    return str(v)


def _to_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        # int(float(...)) tolera "30.0" e "30"
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _to_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    if not isinstance(v, str):
        return None
    s = v.strip()
    if not s:
        return None
    # ISO 8601 padrão (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _normalizar_treino(item: Any) -> TreinoNormalizado:
    """Converte um item bruto do array de treinos em TreinoNormalizado.
    Aceita dict; tudo mais vira treino com extras={'_invalido': item}."""
    if not isinstance(item, dict):
        return TreinoNormalizado(
            data=None, dia_semana=None, tipo=None, descricao=None,
            distancia_km=None, duracao_min=None, intensidade=None,
            objetivo=None, extras={"_invalido": item},
        )

    # Aceita "dia_semana" (enriquecido) ou "dia" (legado).
    dia = item.get("dia_semana")
    if dia is None:
        dia = item.get("dia")

    extras = {
        k: v for k, v in item.items()
        if k not in _CAMPOS_CANONICOS_TREINO
    }

    return TreinoNormalizado(
        data=_to_date(item.get("data")),
        dia_semana=_to_str(dia),
        tipo=_to_str(item.get("tipo")),
        descricao=_to_str(item.get("descricao")),
        distancia_km=_to_float(item.get("distancia_km")),
        duracao_min=_to_int(item.get("duracao_min")),
        intensidade=_to_str(item.get("intensidade")),
        objetivo=_to_str(item.get("objetivo")),
        extras=extras,
    )


def normalizar_plano(
    plano: Mapping[str, Any] | None,
    *,
    versao_hint: int | None = None,
) -> EstruturaPlanoNormalizada:
    """Aceita o JSONB bruto de planos_semanais.plano e retorna a forma
    interna padronizada. Nunca levanta para entrada bem-formada-mas-incompleta.

    Args:
        plano: dict carregado do JSONB. Pode ser None (plano vazio).
        versao_hint: se vier explicitado pela coluna versao_estrutura,
            força a versão. Senão, é detectada via heurística.
    """
    if plano is None or plano == {}:
        return EstruturaPlanoNormalizada(
            versao=versao_hint or 1,
            treinos=tuple(),
            tem_datas=False,
            tem_semanas=False,
            bruto=plano or {},
        )

    if not isinstance(plano, Mapping):
        # Defesa extra: se vier algo absurdo (lista, string), encapsula.
        return EstruturaPlanoNormalizada(
            versao=versao_hint or 1,
            treinos=tuple(),
            tem_datas=False,
            tem_semanas=False,
            bruto={"_raw": plano},
        )

    # Lista de treinos (legada ou enriquecida)
    raw_treinos = plano.get("treinos")
    treinos: tuple[TreinoNormalizado, ...] = tuple()
    if isinstance(raw_treinos, list):
        treinos = tuple(_normalizar_treino(t) for t in raw_treinos)

    tem_datas = any(t.data is not None for t in treinos)
    tem_semanas = "semanas" in plano

    # Heurística de versão se não veio o hint.
    if versao_hint is not None:
        versao = versao_hint
    else:
        versao = 2 if (tem_datas or tem_semanas) else 1

    return EstruturaPlanoNormalizada(
        versao=versao,
        treinos=treinos,
        tem_datas=tem_datas,
        tem_semanas=tem_semanas,
        bruto=plano,
    )
