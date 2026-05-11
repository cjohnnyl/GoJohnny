"""
QA routes - endpoints administrativos para limpeza de testes.

RESTRICOES:
- Apenas apelidos iniciados com 'qa_' podem ser removidos
- Johnny e Larissa são protegidos contra remoção
- Exige x-api-key válida
- Remove: atleta + planos + check-ins + memórias + contexto + OAuth + cache Strava
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.utils import normalize_apelido
from app.models.atleta import Atleta
from app.models.plano_semanal import PlanoSemanal
from app.models.checkin import Checkin
from app.models.atleta_memoria import AtletaMemoria
from app.models.contexto_atleta import ContextoAtleta
from app.models.evento_google_publicado import EventoGooglePublicado
from app.models.strava import (
    StravaPreference,
    StravaConnection,
    StravaActivityCache,
    StravaActivityStreamsCache,
    StravaTrainingAnalysis,
    StravaSyncLog,
)
from app.models.integracao_google import IntegracaoGoogle

router = APIRouter(
    prefix="/qa",
    tags=["qa"],
    dependencies=[Depends(verify_api_key)],
)


@router.delete(
    "/cleanup/{apelido}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cleanup de usuário QA",
    description=(
        "Remove um usuário de teste (prefixo qa_) e todos os dados associados. "
        "Protege usuarios reais como johnny e larissa."
    ),
)
def cleanup_qa_user(apelido: str, db: Session = Depends(get_db)) -> None:
    """
    Remove completamente um usuário de teste (prefixo qa_) do banco.

    Regras:
    1. Apenas apelidos com prefixo 'qa_' são permitidos
    2. Johnny e Larissa nunca podem ser removidos
    3. Remove: atleta, planos, check-ins, memórias, contexto, conexões OAuth, cache Strava

    Args:
        apelido: Apelido do usuário QA a remover

    Raises:
        HTTPException 403: Se apelido não tem prefixo qa_ ou é usuario real
        HTTPException 404: Se apelido não existe
    """
    normalized_apelido = normalize_apelido(apelido)

    # Proteger usuarios reais
    if normalized_apelido in ["johnny", "larissa"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Não é permitido remover usuários reais: {normalized_apelido}",
        )

    # Verificar prefixo qa_
    if not normalized_apelido.startswith("qa_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários com prefixo 'qa_' podem ser removidos",
        )

    # Encontrar atleta
    atleta = db.query(Atleta).filter(Atleta.apelido == normalized_apelido).first()
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta '{normalized_apelido}' não encontrado",
        )

    atleta_id = atleta.id

    # Remover em cascata (synchronize_session=False evita conflitos no identity map do ORM)
    # 1. Memórias
    db.query(AtletaMemoria).filter(AtletaMemoria.atleta_id == atleta_id).delete(synchronize_session=False)

    # 2. Contexto
    db.query(ContextoAtleta).filter(ContextoAtleta.atleta_id == atleta_id).delete(synchronize_session=False)

    # 3. Check-ins
    db.query(Checkin).filter(Checkin.atleta_id == atleta_id).delete(synchronize_session=False)

    # 4. Planos Semanais
    db.query(PlanoSemanal).filter(PlanoSemanal.atleta_id == atleta_id).delete(synchronize_session=False)

    # 5. Strava (streams antes de activity cache, por dependência de dados)
    db.query(StravaActivityStreamsCache).filter(StravaActivityStreamsCache.atleta_id == atleta_id).delete(synchronize_session=False)
    db.query(StravaActivityCache).filter(StravaActivityCache.atleta_id == atleta_id).delete(synchronize_session=False)
    db.query(StravaTrainingAnalysis).filter(StravaTrainingAnalysis.atleta_id == atleta_id).delete(synchronize_session=False)
    db.query(StravaSyncLog).filter(StravaSyncLog.atleta_id == atleta_id).delete(synchronize_session=False)
    db.query(StravaPreference).filter(StravaPreference.atleta_id == atleta_id).delete(synchronize_session=False)
    db.query(StravaConnection).filter(StravaConnection.atleta_id == atleta_id).delete(synchronize_session=False)

    # 6. Google OAuth + Calendário
    db.query(IntegracaoGoogle).filter(IntegracaoGoogle.atleta_id == atleta_id).delete(synchronize_session=False)
    db.query(EventoGooglePublicado).filter(EventoGooglePublicado.atleta_id == atleta_id).delete(synchronize_session=False)

    # 7. Atleta — raw SQL para evitar processamento de backref do ORM
    db.execute(text("DELETE FROM public.atletas WHERE id = :id"), {"id": str(atleta_id)})

    # Confirmar
    db.commit()
