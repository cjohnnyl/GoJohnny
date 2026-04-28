import uuid
from sqlalchemy import Column, Integer, Numeric, Date, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Checkin(Base):
    __tablename__ = "checkins"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(UUID(as_uuid=True), ForeignKey("public.atletas.id"))
    semana_inicio = Column(Date)
    treinos_planejados = Column(Integer)
    treinos_realizados = Column(Integer)
    volume_planejado_km = Column(Numeric)
    volume_realizado_km = Column(Numeric)
    pace_medio = Column(Text)
    cansaco_0_10 = Column(Integer)
    dores = Column(Text)
    sono = Column(Text)
    sensacao_geral = Column(Text)
    observacoes = Column(Text)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
