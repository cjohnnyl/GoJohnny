"""
Google OAuth Routes - ETAPA 3, BLOCO 2.

Endpoints:
- GET  /oauth/google/login/{apelido}      - Iniciar fluxo OAuth
- GET  /oauth/google/callback              - Callback do Google
- GET  /oauth/google/status/{apelido}      - Verificar status de conexão
- POST /oauth/google/disconnect/{apelido}  - Desconectar Google
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.atleta import Atleta
from app.schemas.oauth import (
    OAuthLoginResponse,
    OAuthStatusResponse,
    OAuthDisconnectResponse,
)
from app.services.google_oauth_service import (
    gerar_url_login,
    trocar_code_por_tokens,
)
from app.services.google_integration_service import (
    salvar_tokens,
    desativar_integracao,
    verificar_expiracao,
    obter_integracao_para_atleta,
)

router = APIRouter(
    prefix="/oauth/google",
    tags=["oauth"],
)


@router.get("/login/{apelido}", response_model=OAuthLoginResponse)
def oauth_login(
    apelido: str,
    db: Session = Depends(get_db),
):
    """
    Inicia fluxo de autenticação com Google.

    Gera URL para redirecionar o usuário ao Google OAuth consent screen.

    Args:
        apelido: Apelido do atleta

    Returns:
        {redirect_url: "https://accounts.google.com/..."}

    HTTP Status:
        200: OK, retorna URL
        404: Atleta não encontrado
        500: Erro ao gerar URL (config Google não definida)
    """
    # Verificar se atleta existe
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' não encontrado",
        )

    # Gerar URL de login
    try:
        url = gerar_url_login(atleta.apelido)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuração Google incompleta: {str(e)}",
        )

    return OAuthLoginResponse(redirect_url=url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code do Google"),
    state: str = Query(..., description="State parameter para CSRF protection"),
    db: Session = Depends(get_db),
):
    """
    Callback do Google OAuth.

    Google redireciona aqui após o usuário autorizar.
    Backend troca o code por tokens JWT.

    Args:
        code: Authorization code
        state: State parameter (encoda apelido do atleta)

    Returns:
        Redireciona para página de sucesso ou erro

    Processo:
        1. Validar state (extrair apelido do atleta)
        2. Chamar Google token endpoint com code
        3. Salvar tokens no banco via google_integration_service
        4. Redirecionar para página de sucesso
    """
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="code e state são obrigatórios",
        )

    # Troca code por tokens
    resultado = await trocar_code_por_tokens(code, state)

    if not resultado:
        raise HTTPException(
            status_code=400,
            detail="Falha ao trocar code por tokens. Verifique as credenciais Google.",
        )

    atleta_apelido = resultado.get("atleta_apelido")
    access_token = resultado.get("access_token")
    refresh_token = resultado.get("refresh_token")
    expires_in = resultado.get("expires_in", 3600)

    # Encontrar atleta
    atleta = (
        db.query(Atleta)
        .filter(Atleta.apelido == atleta_apelido)
        .first()
    )

    if not atleta:
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{atleta_apelido}' não encontrado",
        )

    # Salvar tokens
    try:
        salvar_tokens(
            db=db,
            atleta=atleta,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_seconds=expires_in,
            email_google=None,  # TODO: Obter do userinfo endpoint
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar tokens no banco de dados",
        )

    # Redirecionar para página de sucesso
    # TODO: Configurar URL de sucesso em variável de ambiente
    return RedirectResponse(
        url=f"http://localhost:3000/dashboard/calendário/conectado",
        status_code=302,
    )


@router.get(
    "/status/{apelido}",
    response_model=OAuthStatusResponse,
    dependencies=[Depends(verify_api_key)],
)
def oauth_status(
    apelido: str,
    db: Session = Depends(get_db),
):
    """
    Verifica status de conexão com Google.

    Args:
        apelido: Apelido do atleta

    Returns:
        {
            "conectado": true,
            "email_google": "user@gmail.com",
            "expirado": false,
            "tempo_restante_segundos": 3600
        }

    HTTP Status:
        200: OK
        404: Atleta não encontrado
    """
    # Verificar se atleta existe
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' não encontrado",
        )

    # Verificar integracao Google
    integracao = obter_integracao_para_atleta(db, atleta)

    if not integracao:
        # Não conectado
        return OAuthStatusResponse(
            conectado=False,
            email_google=None,
            expirado=False,
            tempo_restante_segundos=None,
        )

    # Verificar expiração
    status_exp = verificar_expiracao(db, atleta)

    return OAuthStatusResponse(
        conectado=True,
        email_google=integracao.email_google,
        expirado=not status_exp["valido"],
        tempo_restante_segundos=status_exp["tempo_restante_segundos"],
    )


@router.post(
    "/disconnect/{apelido}",
    response_model=OAuthDisconnectResponse,
    dependencies=[Depends(verify_api_key)],
)
def oauth_disconnect(
    apelido: str,
    db: Session = Depends(get_db),
):
    """
    Desconecta Google (remove tokens).

    Args:
        apelido: Apelido do atleta

    Returns:
        {
            "desconectado": true,
            "mensagem": "Google desconectado com sucesso"
        }

    HTTP Status:
        200: OK (desconectado ou não estava conectado)
        404: Atleta não encontrado
    """
    # Verificar se atleta existe
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' não encontrado",
        )

    # Desativar integracao
    foi_desativada = desativar_integracao(db, atleta)

    if foi_desativada:
        return OAuthDisconnectResponse(
            desconectado=True,
            mensagem="Google desconectado com sucesso",
        )
    else:
        return OAuthDisconnectResponse(
            desconectado=False,
            mensagem="Google já estava desconectado",
        )
