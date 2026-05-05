import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EventoGooglePublicado(Base):
    __tablename__ = "calendario_eventos_google"
    __table_args__ = (
        UniqueConstraint(
            "atleta_id",
            "hash_evento",
            name="uniq_calendario_eventos_google_hash",
        ),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id"),
        nullable=False,
        index=True,
    )
    hash_evento = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, server_default="publicado", default="publicado")
    google_event_id = Column(String(255), nullable=True)
    titulo = Column(Text, nullable=True)
    data_evento = Column(Date, nullable=True)
    erro_ultima_tentativa = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    atleta = relationship("Atleta", backref="eventos_google_publicados")
