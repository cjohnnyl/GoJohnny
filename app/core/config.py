import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
API_KEY: str = os.getenv("API_KEY", "")

# Google OAuth (ETAPA 3, BLOCO 2)
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI: str = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:8000/oauth/google/callback"
)

# Strava OAuth (FASE 1 do plano de integracao)
STRAVA_CLIENT_ID: str = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET: str = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_REDIRECT_URI: str = os.getenv(
    "STRAVA_REDIRECT_URI",
    "http://localhost:8000/strava/callback",
)
STRAVA_SCOPES: str = os.getenv("STRAVA_SCOPES", "read,activity:read")
STRAVA_TOKEN_ENCRYPTION_KEY: str = os.getenv("STRAVA_TOKEN_ENCRYPTION_KEY", "")
STRAVA_SUCCESS_REDIRECT_URL: str = os.getenv(
    "STRAVA_SUCCESS_REDIRECT_URL",
    "",
)
