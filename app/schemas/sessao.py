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


class ContextoResumo(BaseModel):
    """Contexto enriquecido de memórias para o início da sessão."""
    model_config = ConfigDict(from_attributes=True)

    memorias_relevantes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Memórias mais relevantes do atleta (alertas/orientações)"
    )
    ultima_semana: Optional[dict[str, Any]] = Field(
        default=None,
        description="Resumo semanal mais recente se existir"
    )
    alertas_treinador: list[str] = Field(
        default_factory=list,
        description="Lista de alertas textuais do treinador"
    )
    preferencias: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Preferências do atleta"
    )
    objetivo: Optional[dict[str, Any]] = Field(
        default=None,
        description="Objetivo principal do atleta se existir"
    )


class SessaoIniciarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Literal["novo", "existente"]
    atleta: Optional[AtletaRead] = None
    plano_atual: Optional[PlanoSemanalRead] = None
    contexto_resumo: ContextoResumo = Field(default_factory=ContextoResumo)
    flags: FlagsResponse
    instrucao_continuacao: str = Field(
        description=(
            "Texto curto orientando o Custom GPT sobre como continuar a "
            "conversa. Inclui se o usuario e novo, tem plano ativo, ou "
            "esta elegivel para upgrade de funcionalidades novas."
        ),
    )
