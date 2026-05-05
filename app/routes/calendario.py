"""Routes de calendário e eventos — ETAPA 3, FASE 3.1 e 3.2."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.atleta import Atleta
from app.schemas.evento import CalendarioPreview
from app.services.evento_service import listar_eventos_atleta

logger = logging.getLogger("gojohnny.routes.calendario")

router = APIRouter(prefix="/calendario", tags=["calendario"])


@router.get("/{apelido}/preview", response_model=CalendarioPreview)
def preview_calendario(
    apelido: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key)
) -> CalendarioPreview:
    """Preview do calendário de eventos para um atleta.

    FASE 3.2 - Simulação de calendário sem integração com Google.

    Query:
        GET /calendario/{apelido}/preview

    Response:
        CalendarioPreview com lista de eventos ordenados por data.

    Comportamento:
    - Busca plano ativo do atleta
    - Aplica contexto do usuário (horário preferido, dias)
    - Gera eventos estruturados
    - Retorna preview sem persistência
    """
    # Buscar atleta
    atleta = (
        db.query(Atleta)
        .filter(Atleta.apelido.ilike(apelido))
        .first()
    )

    if not atleta:
        logger.warning("calendario.atleta_nao_encontrado apelido=%s", apelido)
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' não encontrado"
        )

    # Gerar preview
    try:
        preview = listar_eventos_atleta(
            db=db,
            atleta=atleta,
            usar_fallback_contexto=True
        )
        logger.info(
            "calendario.preview_gerado apelido=%s total_eventos=%d",
            apelido, preview.total_eventos
        )
        return preview
    except Exception as e:
        logger.error(
            "calendario.erro_ao_gerar_preview apelido=%s erro=%s",
            apelido, str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao gerar preview do calendário"
        )
