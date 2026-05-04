from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
import uuid


class AtletaCreate(BaseModel):
    nome: str
    apelido: str
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
    # Feature flags (Fase 1, Bloco 5)
    usar_datas_reais: Optional[bool] = False
    usar_contexto_atleta: Optional[bool] = False
    usar_google_calendar: Optional[bool] = False
    usar_strava: Optional[bool] = False
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None


class AtletaFlagsUpdate(BaseModel):
    """Endpoint dedicado de feature flags - opt-in explicito."""
    usar_datas_reais: Optional[bool] = None
    usar_contexto_atleta: Optional[bool] = None
    usar_google_calendar: Optional[bool] = None
    usar_strava: Optional[bool] = None
