"""
POST /sessao/iniciar - Fase 1, Bloco 2.

Endpoint UNICO chamado pelo Custom GPT no inicio do chat para
identificar usuario e receber instrucao de continuacao.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.schemas.sessao import SessaoIniciarRequest, SessaoIniciarResponse
from app.services.session_service import iniciar_sessao


router = APIRouter(
    prefix="/sessao",
    tags=["sessao"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/iniciar",
    response_model=SessaoIniciarResponse,
    summary="Iniciar sessao do atleta",
    description=(
        "Identifica usuario por apelido e devolve plano atual, contexto "
        "e instrucao de continuacao para o GPT. Idempotente. Status "
        "'novo' quando o apelido nao corresponde a nenhum atleta."
    ),
)
def post_iniciar_sessao(
    payload: SessaoIniciarRequest,
    db: Session = Depends(get_db),
) -> SessaoIniciarResponse:
    resultado = iniciar_sessao(db, apelido=payload.apelido)
    return SessaoIniciarResponse.model_validate(resultado)
