"""POST /planos-semanais com protecao contra sobrescrita - Fase 1, Bloco 9."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.models.plano_semanal import PlanoSemanal
from app.schemas.plano_semanal import PlanoSemanalCreate, PlanoSemanalRead
from app.services.atleta_service import get_atleta_by_apelido
from app.services.plano_service import (
    SobrescritaProtegida,
    criar_plano,
)


router = APIRouter(
    prefix="/planos-semanais",
    tags=["planos_semanais"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=PlanoSemanalRead, status_code=201)
def create_plano(data: PlanoSemanalCreate, db: Session = Depends(get_db)):
    atleta = get_atleta_by_apelido(db, data.apelido)
    try:
        plano = criar_plano(db, atleta, data)
    except SobrescritaProtegida as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "erro": "plano_ativo_ja_existe",
                "mensagem": str(e),
                "plano_atual_id": e.plano_atual_id,
                "semana_inicio": e.semana_inicio,
                "como_proceder": (
                    "Se a intencao e iniciar um novo ciclo, refaca a "
                    "chamada com 'novo_ciclo': true. O plano anterior "
                    "sera marcado como 'arquivado' (nao apagado)."
                ),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    db.commit()
    db.refresh(plano)
    return plano


@router.get("/{apelido}/atual", response_model=PlanoSemanalRead)
def get_plano_atual(apelido: str, db: Session = Depends(get_db)):
    atleta = get_atleta_by_apelido(db, apelido)
    plano = (
        db.query(PlanoSemanal)
        .filter(
            PlanoSemanal.atleta_id == atleta.id,
            PlanoSemanal.status == "ativo",
        )
        .order_by(PlanoSemanal.semana_inicio.desc())
        .first()
    )
    if not plano:
        raise HTTPException(status_code=404, detail="Nenhum plano ativo encontrado")
    return plano


@router.get("/{apelido}", response_model=List[PlanoSemanalRead])
def list_planos(apelido: str, db: Session = Depends(get_db)):
    atleta = get_atleta_by_apelido(db, apelido)
    return (
        db.query(PlanoSemanal)
        .filter(PlanoSemanal.atleta_id == atleta.id)
        .order_by(PlanoSemanal.semana_inicio.desc())
        .all()
    )
