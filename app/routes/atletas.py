from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.atleta import Atleta
from app.schemas.atleta import AtletaRead, AtletaUpdate, AtletaCreate, AtletaFlagsUpdate, AtletaFlags

router = APIRouter(
    prefix="/atletas",
    tags=["atletas"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=List[AtletaRead])
def list_atletas(db: Session = Depends(get_db)):
    return db.query(Atleta).all()


@router.post("", response_model=AtletaRead, status_code=status.HTTP_201_CREATED)
def create_atleta(data: AtletaCreate, db: Session = Depends(get_db)):
    existing = db.query(Atleta).filter(Atleta.apelido == data.apelido).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Apelido '{data.apelido}' já existe")

    atleta = Atleta(**data.model_dump())
    db.add(atleta)
    db.commit()
    db.refresh(atleta)
    return atleta


@router.get("/{apelido}", response_model=AtletaRead)
def get_atleta(apelido: str, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")
    return atleta


@router.patch("/{apelido}", response_model=AtletaRead)
def update_atleta(apelido: str, data: AtletaUpdate, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(atleta, field, value)
    db.commit()
    db.refresh(atleta)
    return atleta


@router.patch("/{apelido}/flags", response_model=AtletaFlags)
def update_atleta_flags(apelido: str, data: AtletaFlagsUpdate, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(atleta, field, value)
    db.commit()
    db.refresh(atleta)
    return {
        "usar_datas_reais": atleta.usar_datas_reais,
        "usar_contexto_atleta": atleta.usar_contexto_atleta,
        "usar_google_calendar": atleta.usar_google_calendar,
        "usar_strava": atleta.usar_strava,
    }
