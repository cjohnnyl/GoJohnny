"""Schemas Pydantic para eventos de treino — ETAPA 3, FASE 3.1."""

from pydantic import BaseModel, Field
from datetime import date, time
from typing import Optional
import uuid


class EventoTreinoBase(BaseModel):
    """Base de um evento de treino."""
    titulo: str = Field(description="Título do evento (ex: Treino leve)")
    descricao: str = Field(description="Descrição detalhada (ex: 8km ritmo leve)")
    data: date = Field(description="Data do evento em ISO 8601")
    hora: time = Field(description="Hora de início em HH:MM")
    duracao_min: int = Field(ge=5, le=480, description="Duração em minutos (5-480)")


class EventoTreinoCreate(EventoTreinoBase):
    """Evento para criar (sem ID)."""
    pass


class EventoTreinoRead(EventoTreinoBase):
    """Evento para leitura (com ID)."""
    id: Optional[uuid.UUID] = None
    atleta_id: Optional[uuid.UUID] = None


class CalendarioPreview(BaseModel):
    """Preview de calendário com lista de eventos."""
    atleta_apelido: str
    total_eventos: int
    eventos: list[EventoTreinoRead] = Field(default_factory=list)
    periodo_inicio: Optional[date] = None
    periodo_fim: Optional[date] = None
