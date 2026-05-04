"""Modelo SQLAlchemy da tabela contexto_atleta — Fase 1, Bloco 10."""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ContextoAtleta(Base):
    __tablename__ = "contexto_atleta"
    __table_args__ = (
        UniqueConstraint(
            "atleta_id", "tipo", "chave",
            name="uniq_contexto_atleta_chave",
        ),
        CheckConstraint(
            "confianca >= 0 AND confianca <= 1",
            name="contexto_atleta_confianca_check",
        ),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = Column(Text, nullable=False)
    chave = Column(Text, nullable=False)
    valor = Column(Text, nullable=True)
    confianca = Column(Numeric(3, 2), nullable=False, server_default="1.0", default=1.0)
    origem = Column(Text, nullable=False)
    criado_em = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
