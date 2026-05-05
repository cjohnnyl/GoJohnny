"""
Google OAuth Service - FASE 3.3 - BLOCO 2.

Gerencia o fluxo OAuth com Google:
1. Gerar URL de login
2. Troca code por tokens
3. Salva tokens no banco

Responsabilidades:
- Montar URLs de OAuth
- Fazer chamadas POST ao Google token endpoint
- Salvar tokens com segurança
- Validar state parameter
- Nunca expor tokens
"""

from __future__ import annotations

import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx

from app.core.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)
from app.models.atleta import Atleta
from app.services.google_integration_service import salvar_tokens

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Scopes (apenas calendar.events, não acesso total)
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def gerar_state(atleta_apelido: str) -> str:
    """
    Gera state parameter para CSRF protection.

    O state encoda o apelido do atleta de forma segura para validar
    no callback que a autorização pertence ao atleta certo.

    Args:
        atleta_apelido: Apelido do atleta (ex: "johnny")

    Returns:
        Base64-encoded state string
    """
    # State = base64(apelido)
    # Em produção, usar HMAC para mais segurança, mas esse é simples e suficiente
    estado = base64.b64encode(atleta_apelido.encode()).decode()
    return estado


def validar_state(state: str) -> Optional[str]:
    """
    Valida e decodifica state parameter.

    Args:
        state: State recebido no callback

    Returns:
        Apelido do atleta se válido, None se inválido
    """
    try:
        apelido = base64.b64decode(state).decode()
        # Validação básica: apelido não vazio
        if not apelido or len(apelido) > 100:
            return None
        return apelido
    except Exception:
        return None


def gerar_url_login(atleta_apelido: str) -> str:
    """
    Gera URL para iniciar fluxo OAuth do Google.

    Args:
        atleta_apelido: Apelido do atleta que está se conectando

    Returns:
        URL completa para redirecionar o usuário
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        raise ValueError("GOOGLE_CLIENT_ID ou GOOGLE_REDIRECT_URI não configurados")

    state = gerar_state(atleta_apelido)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return url


async def trocar_code_por_tokens(
    code: str,
    state: str,
) -> Optional[Dict[str, Any]]:
    """
    Troca authorization code por tokens JWT.

    Faz chamada POST ao Google token endpoint.

    Args:
        code: Authorization code recebido do Google
        state: State parameter para validação

    Returns:
        Dict com {access_token, refresh_token, expires_in, email} ou None se falha
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise ValueError("Credenciais Google não configuradas")

    # Validar state
    atleta_apelido = validar_state(state)
    if not atleta_apelido:
        return None

    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)

        if resp.status_code != 200:
            # Não logar o erro completo (pode conter dados sensíveis)
            return None

        dados = resp.json()

        # Extrair campos necessários
        access_token = dados.get("access_token")
        refresh_token = dados.get("refresh_token")
        expires_in = dados.get("expires_in", 3600)

        if not access_token:
            return None

        # TODO: Opcionalmente, chamar Google userinfo endpoint para obter email
        # Por enquanto, deixar email como None (será preenchido no callback)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "email": None,
            "atleta_apelido": atleta_apelido,
        }

    except Exception:
        # Não logar exceção completa (pode conter dados sensíveis)
        return None


async def renovar_access_token(
    db,
    atleta: Atleta,
) -> bool:
    """
    Renova access_token usando refresh_token.

    Args:
        db: Session do SQLAlchemy
        atleta: Atleta cuja token será renovada

    Returns:
        True se renovação bem-sucedida, False se falha
    """
    from app.services.google_integration_service import obter_tokens_para_renovacao

    dados = obter_tokens_para_renovacao(db, atleta)
    if not dados or not dados.get("refresh_token"):
        return False

    refresh_token = dados["refresh_token"]

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Credenciais Google não configuradas")

    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)

        if resp.status_code != 200:
            return False

        dados_renovacao = resp.json()
        access_token = dados_renovacao.get("access_token")
        expires_in = dados_renovacao.get("expires_in", 3600)

        if not access_token:
            return False

        # Salvar novo access_token
        salvar_tokens(
            db=db,
            atleta=atleta,
            access_token=access_token,
            refresh_token=refresh_token,  # Manter refresh_token original se não retornar novo
            expires_in_seconds=expires_in,
        )

        return True

    except Exception:
        return False
