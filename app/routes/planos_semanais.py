from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.plano_semanal import PlanoSemanal
from app.schemas.plano_semanal import PlanoSemanalCreate, PlanoSemanalRead
from app.services.atleta_service import get_atleta_by_apelido

router = APIRouter(
    prefix="/planos-semanais",
    tags=["planos_semanais"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=PlanoSemanalRead, status_code=201)
def create_plano(data: PlanoSemanalCreate, db: Session = Depends(get_db)):
    if not data.plano:
        raise HTTPException(status_code=422, detail="Campo 'plano' é obrigatório e não pode estar vazio")

    atleta = get_atleta_by_apelido(db, data.apelido)
    plano = PlanoSemanal(
        atleta_id=atleta.id,
        **data.model_dump(exclude={"apelido"}),
    )
    db.add(plano)
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
