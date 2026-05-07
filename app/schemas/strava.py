"""Schemas Pydantic para integracao Strava."""

from typing import Optional, List, Any, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


# -----------------------------------------------------------------------------
# Status / Preferencia
# -----------------------------------------------------------------------------

class StravaStatusResponse(BaseModel):
    apelido: str
    usa_strava: Optional[bool] = Field(None, description="True/False se ja sabemos; None se ainda nao perguntamos")
    perguntar_strava: bool = True
    conectado: bool = False
    active: bool = False
    scopes: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    expires_at_ts: Optional[datetime] = None
    precisa_conectar: bool = False
    mensagem_usuario: str


class StravaPreferenceUpdate(BaseModel):
    usa_strava: bool = Field(..., description="Atleta usa Strava? true | false")


class StravaPreferenceResponse(BaseModel):
    apelido: str
    usa_strava: Optional[bool] = None
    perguntar_strava: bool
    salvo: bool
    mensagem_usuario: str


# -----------------------------------------------------------------------------
# OAuth login
# -----------------------------------------------------------------------------

class StravaLoginResponse(BaseModel):
    redirect_url: str
    scopes: str
    mensagem_usuario: str


# -----------------------------------------------------------------------------
# Atividades
# -----------------------------------------------------------------------------

class StravaActivitySummary(BaseModel):
    """Resumo de atividade Strava normalizado."""

    strava_activity_id: int
    name: Optional[str] = None
    sport_type: Optional[str] = None
    type: Optional[str] = None
    start_date_local: Optional[datetime] = None
    timezone: Optional[str] = None
    distance_km: Optional[float] = None
    moving_time_s: Optional[int] = None
    elapsed_time_s: Optional[int] = None
    duracao_min: Optional[float] = None
    total_elevation_gain_m: Optional[float] = None
    average_pace_text: Optional[str] = None
    average_pace_sec_km: Optional[int] = None
    average_speed_mps: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    has_heartrate: Optional[bool] = None
    suffer_score: Optional[int] = None
    private: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class StravaActivitiesResponse(BaseModel):
    apelido: str
    total: int
    atividades: List[StravaActivitySummary]
    mensagem_usuario: Optional[str] = None


class StravaActivityDetailResponse(BaseModel):
    apelido: str
    atividade: StravaActivitySummary
    raw_detail: Optional[Dict[str, Any]] = None


class StravaTodayResponse(BaseModel):
    apelido: str
    encontrou: bool
    multiplas: bool = False
    atividade: Optional[StravaActivitySummary] = None
    atividades: Optional[List[StravaActivitySummary]] = None
    mensagem_usuario: str


# -----------------------------------------------------------------------------
# Analise planejado vs executado
# -----------------------------------------------------------------------------

class StravaAnalyzeRequest(BaseModel):
    activity_id: int
    salvar_checkin: bool = False
    salvar_memoria: bool = False


class StravaAnalyzeWeekRequest(BaseModel):
    semana_inicio: date
    semana_fim: date
    salvar_resumo: bool = False


class StravaAnalysisResult(BaseModel):
    periodo: str
    titulo: Optional[str] = None
    planejado: Optional[Dict[str, Any]] = None
    executado: Optional[Dict[str, Any]] = None
    comparativo: Optional[Dict[str, Any]] = None
    aderencia: Optional[str] = Field(None, description="boa | parcial | baixa | risco")
    pontos_positivos: List[str] = []
    pontos_atencao: List[str] = []
    decisao_treinador: Optional[str] = None
    plano_deve_mudar: bool = False
    tipo_acao_recomendada: Optional[str] = Field(None, description="manter | ajustar | substituir | descansar")
    memoria_sugerida: Optional[Dict[str, Any]] = None
    checkin_sugerido: Optional[Dict[str, Any]] = None
    resumo_semanal_sugerido: Optional[Dict[str, Any]] = None
    salvo: Dict[str, bool] = Field(default_factory=lambda: {"memoria": False, "checkin": False, "resumo_semanal": False})
    analise_id: Optional[str] = None


# -----------------------------------------------------------------------------
# Disconnect
# -----------------------------------------------------------------------------

class StravaDisconnectResponse(BaseModel):
    desconectado: bool
    mensagem_usuario: str
