"""
Models SQLAlchemy para integracao Strava (FASE 1 do plano).

Strava e fonte de evidencia, nunca de decisao.
Tokens sao armazenados criptografados (Fernet) pelo backend.
"""

import uuid
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Numeric,
    Text,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.core.database import Base


class StravaPreference(Base):
    __tablename__ = "strava_preferences"
    __table_args__ = (
        UniqueConstraint("atleta_id", name="strava_preferences_atleta_id_key"),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usa_strava = Column(Boolean, nullable=True)
    perguntar_strava = Column(Boolean, nullable=False, default=True, server_default="true")
    oferta_conexao_exibida = Column(Boolean, nullable=False, default=False, server_default="false")
    ultima_resposta_usuario = Column(Text, nullable=True)
    origem = Column(Text, nullable=False, default="conversa", server_default="conversa")
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StravaConnection(Base):
    __tablename__ = "strava_connections"
    __table_args__ = (
        UniqueConstraint("atleta_id", name="strava_connections_atleta_id_key"),
        UniqueConstraint("strava_athlete_id", name="strava_connections_strava_athlete_id_key"),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strava_athlete_id = Column(BigInteger, nullable=False)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=False)
    expires_at = Column(BigInteger, nullable=False)
    expires_at_ts = Column(DateTime(timezone=True), nullable=True)
    token_type = Column(Text, default="Bearer", server_default="Bearer")
    scope = Column(Text, nullable=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_refresh_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=True, server_default="true")
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    raw_athlete_json = Column(JSONB, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StravaActivityCache(Base):
    __tablename__ = "strava_activity_cache"
    __table_args__ = (
        UniqueConstraint(
            "atleta_id",
            "strava_activity_id",
            name="strava_activity_cache_atleta_activity_key",
        ),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="CASCADE"),
        nullable=False,
    )
    strava_activity_id = Column(BigInteger, nullable=False)
    name = Column(Text, nullable=True)
    sport_type = Column(Text, nullable=True)
    type = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    start_date_local = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(Text, nullable=True)
    distance_m = Column(Numeric(12, 2), nullable=True)
    moving_time_s = Column(Integer, nullable=True)
    elapsed_time_s = Column(Integer, nullable=True)
    total_elevation_gain_m = Column(Numeric(10, 2), nullable=True)
    average_speed_mps = Column(Numeric(10, 4), nullable=True)
    max_speed_mps = Column(Numeric(10, 4), nullable=True)
    average_pace_sec_km = Column(Integer, nullable=True)
    average_pace_text = Column(Text, nullable=True)
    average_heartrate = Column(Numeric(8, 2), nullable=True)
    max_heartrate = Column(Numeric(8, 2), nullable=True)
    average_cadence = Column(Numeric(8, 2), nullable=True)
    average_watts = Column(Numeric(8, 2), nullable=True)
    weighted_average_watts = Column(Numeric(8, 2), nullable=True)
    kilojoules = Column(Numeric(10, 2), nullable=True)
    calories = Column(Numeric(10, 2), nullable=True)
    suffer_score = Column(Integer, nullable=True)
    has_heartrate = Column(Boolean, nullable=True)
    elev_high = Column(Numeric(10, 2), nullable=True)
    elev_low = Column(Numeric(10, 2), nullable=True)
    private = Column(Boolean, nullable=True)
    visibility = Column(Text, nullable=True)
    raw_summary_json = Column(JSONB, nullable=True)
    raw_detail_json = Column(JSONB, nullable=True)
    synced_summary_at = Column(DateTime(timezone=True), nullable=True)
    synced_detail_at = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StravaActivityStreamsCache(Base):
    __tablename__ = "strava_activity_streams_cache"
    __table_args__ = (
        UniqueConstraint(
            "atleta_id",
            "strava_activity_id",
            "stream_types",
            name="strava_streams_atleta_activity_types_key",
        ),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="CASCADE"),
        nullable=False,
    )
    strava_activity_id = Column(BigInteger, nullable=False)
    stream_types = Column(ARRAY(Text), nullable=False)
    streams_json = Column(JSONB, nullable=False)
    resolution = Column(Text, nullable=True)
    series_type = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StravaTrainingAnalysis(Base):
    __tablename__ = "strava_training_analysis"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="CASCADE"),
        nullable=False,
    )
    plano_id = Column(UUID(as_uuid=True), nullable=True)
    strava_activity_id = Column(BigInteger, nullable=True)
    periodo = Column(Text, nullable=False)
    data_inicio = Column(Date, nullable=True)
    data_fim = Column(Date, nullable=True)
    titulo = Column(Text, nullable=True)
    treino_planejado_json = Column(JSONB, nullable=True)
    treino_executado_json = Column(JSONB, nullable=True)
    comparativo_json = Column(JSONB, nullable=True)
    aderencia = Column(Text, nullable=True)
    pontos_positivos = Column(JSONB, nullable=True)
    pontos_atencao = Column(JSONB, nullable=True)
    decisao_treinador = Column(Text, nullable=True)
    plano_deve_mudar = Column(Boolean, nullable=False, default=False, server_default="false")
    tipo_acao_recomendada = Column(Text, nullable=True)
    memoria_criada = Column(Boolean, nullable=False, default=False, server_default="false")
    checkin_criado = Column(Boolean, nullable=False, default=False, server_default="false")
    resumo_semanal_criado = Column(Boolean, nullable=False, default=False, server_default="false")
    raw_input_json = Column(JSONB, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StravaSyncLog(Base):
    __tablename__ = "strava_sync_logs"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    atleta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.atletas.id", ondelete="SET NULL"),
        nullable=True,
    )
    endpoint = Column(Text, nullable=False)
    metodo = Column(Text, nullable=False, default="GET", server_default="GET")
    status_code = Column(Integer, nullable=True)
    sucesso = Column(Boolean, nullable=False, default=False, server_default="false")
    erro_texto = Column(Text, nullable=True)
    rate_limit_limit = Column(Text, nullable=True)
    rate_limit_usage = Column(Text, nullable=True)
    read_rate_limit_limit = Column(Text, nullable=True)
    read_rate_limit_usage = Column(Text, nullable=True)
    request_params_json = Column(JSONB, nullable=True)
    response_resumo_json = Column(JSONB, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
