import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class AtletaMemoria(Base):
    __tablename__ = "atleta_memorias"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(UUID(as_uuid=True), ForeignKey("public.atletas.id"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    chave = Column(String(255), nullable=False)
    valor_texto = Column(Text, nullable=True)
    valor_json = Column(JSONB, nullable=True)
    origem = Column(String(50), nullable=False)
    importancia = Column(Integer, nullable=False, server_default="3", default=3)
    confianca = Column(Numeric(3, 2), nullable=False, server_default="1.0", default=1.0)
    semana_inicio = Column(Date, nullable=True)
    ativo = Column(Boolean, nullable=False, server_default="true", default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
