"""Routes de calendario e eventos - ETAPA 3, FASE 3.1, 3.2 e BLOCO 3."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.utils import normalize_apelido
from app.models.atleta import Atleta
from app.schemas.evento import CalendarioPreview, CalendarioPublicacaoResponse
from app.services.evento_service import listar_eventos_atleta
from app.services.google_calendar_service import (
    PublicacaoCalendarioConfigError,
    publicar_eventos_atleta,
)


logger = logging.getLogger("gojohnny.routes.calendario")

router = APIRouter(prefix="/calendario", tags=["calendario"])


@router.get("/{apelido}/preview", response_model=CalendarioPreview)
def preview_calendario(
    apelido: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> CalendarioPreview:
    """Preview do calendario de eventos para um atleta."""
    atleta = (
        db.query(Atleta)
        .filter(Atleta.apelido.ilike(apelido))
        .first()
    )

    if not atleta:
        logger.warning("calendario.atleta_nao_encontrado apelido=%s", apelido)
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' nao encontrado",
        )

    try:
        preview = listar_eventos_atleta(
            db=db,
            atleta=atleta,
            usar_fallback_contexto=True,
        )
        logger.info(
            "calendario.preview_gerado apelido=%s total_eventos=%d",
            apelido,
            preview.total_eventos,
        )
        return preview
    except Exception as exc:
        logger.error(
            "calendario.erro_ao_gerar_preview apelido=%s erro=%s",
            apelido,
            str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao gerar preview do calendario",
        )


@router.post("/{apelido}/publicar", response_model=CalendarioPublicacaoResponse)
async def publicar_calendario(
    apelido: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> CalendarioPublicacaoResponse:
    """Publica eventos reais do plano ativo no Google Calendar."""
    normalized_apelido = normalize_apelido(apelido)
    atleta = (
        db.query(Atleta)
        .filter(Atleta.apelido == normalized_apelido)
        .first()
    )

    if not atleta:
        logger.warning("calendario.publicar_atleta_nao_encontrado apelido=%s", normalized_apelido)
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{normalized_apelido}' nao encontrado",
        )

    try:
        resultado = await publicar_eventos_atleta(db=db, atleta=atleta)
        logger.info(
            "calendario.publicacao_concluida apelido=%s criados=%d ignorados=%d erros=%d",
            apelido,
            resultado.eventos_criados,
            resultado.eventos_ignorados,
            len(resultado.erros),
        )
        return resultado
    except PublicacaoCalendarioConfigError as exc:
        logger.error(
            "calendario.publicacao_config_invalida apelido=%s detalhe=%s",
            apelido,
            str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Configuracao Google incompleta: {str(exc)}",
        )
    except Exception as exc:
        logger.exception(
            "calendario.publicacao_erro apelido=%s erro=%s",
            apelido,
            str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao publicar eventos no Google Calendar",
        )
