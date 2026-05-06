"""Rotas de planos semanais — criação, revisão e substituição adaptativa."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.models.plano_semanal import PlanoSemanal
from app.schemas.plano_semanal import (
    PlanoSemanalCreate,
    PlanoSemanalRead,
    PlanoSemanalUpdate,
    SubstituirPlanoPayload,
    SubstituirPlanoResponse,
)
from app.services.atleta_service import get_atleta_by_apelido
from app.services.plano_service import (
    PlanoAtivoNaoEncontrado,
    SobrescritaProtegida,
    atualizar_plano_ativo,
    criar_plano,
    substituir_plano_ativo,
)


router = APIRouter(
    prefix="/planos-semanais",
    tags=["planos_semanais"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=PlanoSemanalRead, status_code=201)
def create_plano(data: PlanoSemanalCreate = Body(...), db: Session = Depends(get_db)):
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
                    "sera marcado como 'substituido' (nao apagado)."
                ),
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Não foi possível criar plano semanal: {e}",
        )

    db.commit()
    db.refresh(plano)
    return plano


@router.patch("/{apelido}/atual", response_model=PlanoSemanalRead)
def patch_plano_atual(
    apelido: str,
    dados: PlanoSemanalUpdate = Body(...),
    db: Session = Depends(get_db),
):
    """Atualiza parcialmente o plano ativo do atleta.

    Preserva campos não enviados. Se motivo_revisao estiver presente e
    salvar_memoria=true, salva memória do tipo ajuste_plano automaticamente.
    """
    atleta = get_atleta_by_apelido(db, apelido)
    try:
        plano = atualizar_plano_ativo(db, atleta, dados)
    except PlanoAtivoNaoEncontrado:
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' não tem plano ativo para atualizar.",
        )
    return plano


@router.post("/{apelido}/substituir-atual", response_model=SubstituirPlanoResponse, status_code=201)
def post_substituir_plano_atual(
    apelido: str,
    dados: SubstituirPlanoPayload = Body(...),
    db: Session = Depends(get_db),
):
    """Substitui o plano ativo por um novo plano.

    Marca o plano atual como 'substituido' e cria novo plano ativo.
    Se motivo_substituicao estiver presente, salva memória do tipo
    decisao_treinador automaticamente.
    Retorna plano_anterior, novo_plano e memoria_salva.
    """
    atleta = get_atleta_by_apelido(db, apelido)
    try:
        resultado = substituir_plano_ativo(db, atleta, dados)
    except PlanoAtivoNaoEncontrado:
        raise HTTPException(
            status_code=404,
            detail=f"Atleta '{apelido}' não tem plano ativo para substituir.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Não foi possível substituir o plano: {e}",
        )
    return resultado


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
