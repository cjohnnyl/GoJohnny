import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class IntegracaoGoogle(Base):
    __tablename__ = "integracao_google"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(UUID(as_uuid=True), ForeignKey("public.atletas.id"), nullable=False, index=True)

    # Tokens OAuth
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)

    # Metadados
    expires_at = Column(DateTime(timezone=True), nullable=True)
    email_google = Column(String(255), nullable=True)

    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamento
    atleta = relationship("Atleta", backref="integracao_google")
