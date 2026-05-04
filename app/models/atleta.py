import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Atleta(Base):
    __tablename__ = "atletas"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(Text)
    apelido = Column(Text, unique=True, index=True)
    objetivo = Column(Text)
    nivel = Column(Text)
    dias_treino = Column(Integer)
    altura_cm = Column(Integer)
    peso_kg = Column(Numeric)
    pace_confortavel = Column(Text)
    maior_distancia_recente_km = Column(Numeric)
    historico_dores = Column(Text)
    tenis_disponiveis = Column(Text)
    proxima_prova = Column(Text)
    data_proxima_prova = Column(Date)
    distancia_alvo_km = Column(Numeric)
    observacoes = Column(Text)
    # Feature flags (Fase 1, Bloco 5) - default false para usuarios existentes
    usar_datas_reais = Column(Boolean, nullable=False, server_default="false", default=False)
    usar_contexto_atleta = Column(Boolean, nullable=False, server_default="false", default=False)
    usar_google_calendar = Column(Boolean, nullable=False, server_default="false", default=False)
    usar_strava = Column(Boolean, nullable=False, server_default="false", default=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
