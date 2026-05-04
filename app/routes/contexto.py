"""Rotas de contexto do atleta (Fase 2, Etapa 2)."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.schemas.contexto_atleta import ContextoAtletaCreate, ContextoAtletaRead
from app.services.atleta_service import get_atleta_by_apelido
from app.services.context_service import (
    salvar_contexto,
    listar_contexto,
    contexto_com_fallback,
)


router = APIRouter(prefix="/contexto", tags=["contexto"])


@router.get("/{apelido}", response_model=Dict[str, Dict[str, str]])
def get_contexto(
    apelido: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Lista contexto de um atleta, agrupado por tipo.

    Formato: {"objetivo": {"dias_treino": "4"}, "historico": {...}}

    Se não houver contexto salvo, retorna fallback inteligente extraído do
    perfil do atleta. Fallback não é persistido automaticamente.
    """
    atleta = get_atleta_by_apelido(db, apelido)
    return contexto_com_fallback(db, atleta)


@router.post("/{apelido}/{tipo}/{chave}", response_model=ContextoAtletaRead)
def set_contexto(
    apelido: str,
    tipo: str,
    chave: str,
    data: ContextoAtletaCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Cria ou atualiza uma chave de contexto (upsert).

    Idempotente: chamar múltiplas vezes com mesmos (tipo, chave)
    atualiza o valor em vez de duplicar.
    """
    atleta = get_atleta_by_apelido(db, apelido)

    contexto = salvar_contexto(
        db,
        atleta,
        tipo=tipo,
        chave=chave,
        valor=data.valor,
        origem=data.origem,
        confianca=data.confianca or 1.0,
    )
    db.commit()
    return contexto


@router.delete("/{apelido}/{tipo}/{chave}")
def delete_contexto(
    apelido: str,
    tipo: str,
    chave: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Deleta uma chave de contexto específica."""
    atleta = get_atleta_by_apelido(db, apelido)

    from app.models.contexto_atleta import ContextoAtleta

    deleted = (
        db.query(ContextoAtleta)
        .filter(
            ContextoAtleta.atleta_id == atleta.id,
            ContextoAtleta.tipo == tipo,
            ContextoAtleta.chave == chave,
        )
        .delete()
    )
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Contexto não encontrado")

    return {"status": "deletado"}
