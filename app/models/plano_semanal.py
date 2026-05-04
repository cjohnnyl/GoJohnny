import uuid
from sqlalchemy import Column, Numeric, Date, Text, DateTime, ForeignKey, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class PlanoSemanal(Base):
    __tablename__ = "planos_semanais"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(UUID(as_uuid=True), ForeignKey("public.atletas.id"))
    semana_inicio = Column(Date)
    objetivo_semana = Column(Text)
    volume_planejado_km = Column(Numeric)
    status = Column(Text)
    plano = Column(JSONB, nullable=False)
    # Enriquecimento aditivo (Fase 1, Bloco 6) - todos opcionais
    data_inicio = Column(Date, nullable=True)
    data_prova = Column(Date, nullable=True)
    dias_treino_json = Column(JSONB, nullable=True)
    versao_estrutura = Column(SmallInteger, nullable=False, server_default="1", default=1)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
