from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import date, datetime
from decimal import Decimal
import uuid


class PlanoSemanalCreate(BaseModel):
    apelido: str
    semana_inicio: date
    objetivo_semana: Optional[str] = None
    volume_planejado_km: Optional[Decimal] = None
    status: Optional[str] = None
    plano: Any


class PlanoSemanalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    atleta_id: uuid.UUID
    semana_inicio: Optional[date] = None
    objetivo_semana: Optional[str] = None
    volume_planejado_km: Optional[Decimal] = None
    status: Optional[str] = None
    plano: Optional[Any] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
