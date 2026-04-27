from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
import uuid


class CheckinCreate(BaseModel):
    apelido: str
    semana_inicio: date
    treinos_planejados: Optional[int] = None
    treinos_realizados: Optional[int] = None
    volume_planejado_km: Optional[Decimal] = None
    volume_realizado_km: Optional[Decimal] = None
    pace_medio: Optional[str] = None
    cansaco_0_10: Optional[int] = None
    dores: Optional[str] = None
    sono: Optional[str] = None
    sensacao_geral: Optional[str] = None
    observacoes: Optional[str] = None


class CheckinRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    atleta_id: uuid.UUID
    semana_inicio: Optional[date] = None
    treinos_planejados: Optional[int] = None
    treinos_realizados: Optional[int] = None
    volume_planejado_km: Optional[Decimal] = None
    volume_realizado_km: Optional[Decimal] = None
    pace_medio: Optional[str] = None
    cansaco_0_10: Optional[int] = None
    dores: Optional[str] = None
    sono: Optional[str] = None
    sensacao_geral: Optional[str] = None
    observacoes: Optional[str] = None
    criado_em: Optional[datetime] = None
