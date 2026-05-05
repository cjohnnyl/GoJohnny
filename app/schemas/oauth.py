from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OAuthLoginResponse(BaseModel):
    """Resposta do endpoint GET /oauth/google/login."""
    redirect_url: str


class OAuthCallbackRequest(BaseModel):
    """Parametros do callback OAuth."""
    code: str
    state: str
    scope: Optional[str] = None


class OAuthStatusResponse(BaseModel):
    """Resposta do endpoint GET /oauth/google/status/{apelido}."""
    conectado: bool
    email_google: Optional[str] = None
    expirado: bool
    tempo_restante_segundos: Optional[int] = None


class OAuthDisconnectResponse(BaseModel):
    """Resposta do endpoint POST /oauth/google/disconnect/{apelido}."""
    desconectado: bool
    mensagem: str
