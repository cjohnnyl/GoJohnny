"""
QA routes - endpoints administrativos para limpeza de testes.

RESTRICOES:
- Apenas apelidos iniciados com 'qa_' podem ser removidos
- Johnny e Larissa são protegidos contra remoção
- Exige x-api-key válida
- Remove: atleta + planos + check-ins + memórias + contexto + OAuth + cache Strava

RISCO: SOMENTE QA — nunca usar em usuários reais.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.utils import normalize_apelido

logger = logging.getLogger("gojohnny.routes.qa")

router = APIRouter(
    prefix="/qa",
    tags=["qa"],
    dependencies=[Depends(verify_api_key)],
)

# Tabelas em ordem de deleção segura (filhos antes de pai).
# Migration 006 criou integracao_google e calendario_eventos_google em 2026-05-11.
_CLEANUP_SQL = [
    "DELETE FROM public.atleta_memorias WHERE atleta_id = :id",
    "DELETE FROM public.contexto_atleta WHERE atleta_id = :id",
    "DELETE FROM public.checkins WHERE atleta_id = :id",
    "DELETE FROM public.planos_semanais WHERE atleta_id = :id",
    "DELETE FROM public.strava_activity_streams_cache WHERE atleta_id = :id",
    "DELETE FROM public.strava_activity_cache WHERE atleta_id = :id",
    "DELETE FROM public.strava_training_analysis WHERE atleta_id = :id",
    "DELETE FROM public.strava_sync_logs WHERE atleta_id = :id",
    "DELETE FROM public.strava_preferences WHERE atleta_id = :id",
    "DELETE FROM public.strava_connections WHERE atleta_id = :id",
    "DELETE FROM public.integracao_google WHERE atleta_id = :id",
    "DELETE FROM public.calendario_eventos_google WHERE atleta_id = :id",
    "DELETE FROM public.atletas WHERE id = :id",
]


@router.delete(
    "/cleanup/{apelido}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[SOMENTE QA] Cleanup de usuário de teste",
    description=(
        "**Risco: SOMENTE QA** — Remove usuário de teste (prefixo qa_) e todos os dados associados. "
        "Protege usuarios reais como johnny e larissa. Nunca usar em produção real."
    ),
)
def cleanup_qa_user(apelido: str, db: Session = Depends(get_db)) -> None:
    """
    Remove completamente um usuário de teste (prefixo qa_) do banco via raw SQL.

    Regras:
    1. Apenas apelidos com prefixo 'qa_' são permitidos
    2. Johnny e Larissa nunca podem ser removidos
    3. Remove em cascata via SQL direto (evita problemas de ORM com backref)
    """
    normalized_apelido = normalize_apelido(apelido)

    if normalized_apelido in ["johnny", "larissa"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Não é permitido remover usuários reais: {normalized_apelido}",
        )

    if not normalized_apelido.startswith("qa_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas usuários com prefixo 'qa_' podem ser removidos",
        )

    # Buscar atleta via raw SQL para evitar carregar backrefs ORM
    row = db.execute(
        text("SELECT id FROM public.atletas WHERE apelido = :apelido"),
        {"apelido": normalized_apelido},
    ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta '{normalized_apelido}' não encontrado",
        )

    atleta_id = str(row[0])

    try:
        for sql in _CLEANUP_SQL:
            db.execute(text(sql), {"id": atleta_id})
        db.commit()
        logger.info("qa.cleanup_ok apelido=%s id=%s", normalized_apelido, atleta_id)
    except Exception as exc:
        db.rollback()
        logger.error("qa.cleanup_error apelido=%s erro=%s", normalized_apelido, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover atleta: {type(exc).__name__}: {exc}",
        )
