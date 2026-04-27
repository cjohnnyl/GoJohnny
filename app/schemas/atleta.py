from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
import uuid


class AtletaUpdate(BaseModel):
    nome: Optional[str] = None
    apelido: Optional[str] = None
    objetivo: Optional[str] = None
    nivel: Optional[str] = None
    dias_treino: Optional[int] = None
    altura_cm: Optional[int] = None
    peso_kg: Optional[Decimal] = None
    pace_confortavel: Optional[str] = None
    maior_distancia_recente_km: Optional[Decimal] = None
    historico_dores: Optional[str] = None
    tenis_disponiveis: Optional[str] = None
    proxima_prova: Optional[str] = None
    data_proxima_prova: Optional[date] = None
    distancia_alvo_km: Optional[Decimal] = None
    observacoes: Optional[str] = None


class AtletaRead(AtletaUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
