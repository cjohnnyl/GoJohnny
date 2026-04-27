from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.checkin import Checkin
from app.schemas.checkin import CheckinCreate, CheckinRead
from app.services.atleta_service import get_atleta_by_apelido

router = APIRouter(
    prefix="/checkins",
    tags=["checkins"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=CheckinRead, status_code=201)
def create_checkin(data: CheckinCreate, db: Session = Depends(get_db)):
    atleta = get_atleta_by_apelido(db, data.apelido)
    checkin = Checkin(
        atleta_id=atleta.id,
        **data.model_dump(exclude={"apelido"}),
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


@router.get("/{apelido}", response_model=List[CheckinRead])
def list_checkins(apelido: str, db: Session = Depends(get_db)):
    atleta = get_atleta_by_apelido(db, apelido)
    return (
        db.query(Checkin)
        .filter(Checkin.atleta_id == atleta.id)
        .order_by(Checkin.semana_inicio.desc())
        .all()
    )
