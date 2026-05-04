"""Schemas de request/response para POST /sessao/iniciar - Fase 1, Bloco 2."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.atleta import AtletaRead
from app.schemas.plano_semanal import PlanoSemanalRead


class SessaoIniciarRequest(BaseModel):
    apelido: str = Field(
        min_length=1,
        max_length=80,
        description=(
            "Apelido do atleta. O GPT pergunta isso direto no inicio. "
            "Se nao houver match, status = 'novo' e o GPT segue para o "
            "onboarding sem chamar mais APIs."
        ),
    )


class FlagsResponse(BaseModel):
    """Subconjunto de feature flags que importa para a sessao."""
    usar_datas_reais: bool = False
    usar_contexto_atleta: bool = False
    usar_google_calendar: bool = False
    usar_strava: bool = False


class SessaoIniciarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Literal["novo", "existente"]
    atleta: Optional[AtletaRead] = None
    plano_atual: Optional[PlanoSemanalRead] = None
    contexto_resumo: dict[str, dict[str, str]] = Field(default_factory=dict)
    flags: FlagsResponse
    instrucao_continuacao: str = Field(
        description=(
            "Texto curto orientando o Custom GPT sobre como continuar a "
            "conversa. Inclui se o usuario e novo, tem plano ativo, ou "
            "esta elegivel para upgrade de funcionalidades novas."
        ),
    )
