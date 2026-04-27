import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, Text, DateTime
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
    criado_em = Column(DateTime(timezone=True))
    atualizado_em = Column(DateTime(timezone=True))
