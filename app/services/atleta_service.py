from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.atleta import Atleta


def get_atleta_by_apelido(db: Session, apelido: str) -> Atleta:
    atleta = db.query(Atleta).filter(Atleta.apelido == apelido).first()
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")
    return atleta
