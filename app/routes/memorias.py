"""
Endpoints de memória e knowledge base por atleta - Etapa 4.

POST /memorias/{apelido} - Salvar memória
GET /memorias/{apelido}/resumo - Resumo de memórias
GET /memorias/{apelido}/buscar - Buscar por texto
POST /memorias/{apelido}/resumo-semanal - Salvar resumo semanal
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.services.memoria_service import (
    get_atleta_by_apelido,
    salvar_memoria,
    buscar_resumo_memorias,
    buscar_memorias_por_texto,
    salvar_resumo_semanal,
)
from app.schemas.atleta_memoria import (
    AtletaMemoriaCreate,
    ResumoSemanalCreate,
    MemoriasResumoResponse,
    BuscaMemorias,
)

router = APIRouter(
    prefix="/memorias",
    tags=["memorias"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/{apelido}",
    summary="Salvar memória do atleta",
    description="Salva uma memória útil do atleta (feedback, objetivo, preferência, etc.)",
    tags=["memorias"],
)
def post_salvar_memoria(
    apelido: str,
    dados: AtletaMemoriaCreate = Body(...),
    db: Session = Depends(get_db),
):
    """Salva memória do atleta, evitando duplicatas idênticas."""
    atleta = get_atleta_by_apelido(db, apelido)
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")

    resultado = salvar_memoria(db, str(atleta.id), dados)
    return resultado


@router.get(
    "/{apelido}/resumo",
    response_model=MemoriasResumoResponse,
    summary="Buscar resumo de memórias",
    description="Retorna memórias mais importantes e recentes do atleta",
    tags=["memorias"],
)
def get_resumo_memorias(
    apelido: str,
    limite: int = Query(20, ge=1, le=100),
    tipo: str = Query(None),
    db: Session = Depends(get_db),
):
    """Retorna resumo compacto das memórias mais importantes e recentes."""
    atleta = get_atleta_by_apelido(db, apelido)
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")

    memorias = buscar_resumo_memorias(db, str(atleta.id), limite, tipo)
    return MemoriasResumoResponse(apelido=apelido, memorias=memorias)


@router.get(
    "/{apelido}/buscar",
    response_model=BuscaMemorias,
    summary="Buscar memórias por texto",
    description="Busca memórias relevantes por texto",
    tags=["memorias"],
)
def get_buscar_memorias(
    apelido: str,
    q: str = Query(..., min_length=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Busca memórias por texto em chave e valor."""
    atleta = get_atleta_by_apelido(db, apelido)
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")

    resultados, total = buscar_memorias_por_texto(db, str(atleta.id), q, limite)
    return BuscaMemorias(resultados=resultados, total=total)


@router.post(
    "/{apelido}/resumo-semanal",
    summary="Salvar resumo semanal",
    description="Registra um resumo fechado da semana do atleta",
    tags=["memorias"],
)
def post_salvar_resumo_semanal(
    apelido: str,
    dados: ResumoSemanalCreate = Body(...),
    db: Session = Depends(get_db),
):
    """Registra resumo fechado da semana."""
    atleta = get_atleta_by_apelido(db, apelido)
    if not atleta:
        raise HTTPException(status_code=404, detail=f"Atleta '{apelido}' não encontrado")

    resultado = salvar_resumo_semanal(db, str(atleta.id), dados)
    return resultado
