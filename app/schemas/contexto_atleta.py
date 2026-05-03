"""Schemas Pydantic da tabela contexto_atleta — Fase 1, Bloco 10."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ContextoAtletaBase(BaseModel):
    tipo: str = Field(
        description="Categoria do contexto. Ex: objetivo, historico, preferencia.",
    )
    chave: str = Field(
        description="Identificador da informação dentro do tipo.",
    )
    valor: Optional[str] = None
    confianca: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)
    origem: str = Field(
        description="De onde veio o dado. Ex: onboarding, checkin, manual.",
    )


class ContextoAtletaCreate(ContextoAtletaBase):
    apelido: str = Field(description="Apelido do atleta dono do contexto.")


class ContextoAtletaRead(ContextoAtletaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    atleta_id: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime
