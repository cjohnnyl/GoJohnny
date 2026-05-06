"""
Serviço de memória por atleta - Etapa 4: Knowledge Base.

Centraliza CRUD de memórias, buscas e resumos semanais.
Garante que memórias são vinculadas a atleta_id, nunca apenas a apelido.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.atleta import Atleta
from app.models.atleta_memoria import AtletaMemoria
from app.schemas.atleta_memoria import (
    AtletaMemoriaCreate,
    AtletaMemoriaRead,
    ResumoSemanalCreate,
)


def get_atleta_by_apelido(db: Session, apelido: str) -> Optional[Atleta]:
    """Busca atleta por apelido (normalizado)."""
    apelido_norm = (apelido or "").strip().lower()
    if not apelido_norm:
        return None
    return db.query(Atleta).filter(Atleta.apelido.ilike(apelido_norm)).first()


def salvar_memoria(
    db: Session,
    atleta_id: str,
    dados: AtletaMemoriaCreate,
) -> dict:
    """Salva memória do atleta. Evita duplicatas idênticas."""
    # Buscar se já existe memória idêntica
    existente = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo == dados.tipo,
                AtletaMemoria.chave == dados.chave,
                AtletaMemoria.ativo == True,
            )
        )
        .first()
    )

    if existente:
        # Atualizar memória existente
        existente.valor_texto = dados.valor_texto
        existente.valor_json = dados.valor_json
        existente.importancia = dados.importancia
        existente.confianca = dados.confianca
        existente.semana_inicio = dados.semana_inicio
        existente.atualizado_em = func.now()
        db.commit()
        db.refresh(existente)
        return {
            "id": str(existente.id),
            "status": "atualizado",
            "memoria": AtletaMemoriaRead.model_validate(existente).model_dump(mode="json"),
        }

    # Criar nova memória
    memoria = AtletaMemoria(
        atleta_id=atleta_id,
        tipo=dados.tipo,
        chave=dados.chave,
        valor_texto=dados.valor_texto,
        valor_json=dados.valor_json,
        origem=dados.origem,
        importancia=dados.importancia,
        confianca=dados.confianca,
        semana_inicio=dados.semana_inicio,
    )
    db.add(memoria)
    db.commit()
    db.refresh(memoria)

    return {
        "id": str(memoria.id),
        "status": "criado",
        "memoria": AtletaMemoriaRead.model_validate(memoria).model_dump(mode="json"),
    }


def buscar_resumo_memorias(
    db: Session,
    atleta_id: str,
    limite: int = 20,
    tipo_filtro: Optional[str] = None,
) -> List[dict]:
    """Retorna memórias mais importantes e recentes."""
    query = db.query(AtletaMemoria).filter(
        and_(
            AtletaMemoria.atleta_id == atleta_id,
            AtletaMemoria.ativo == True,
        )
    )

    if tipo_filtro:
        query = query.filter(AtletaMemoria.tipo == tipo_filtro)

    # Ordenar por importância (desc) e depois por data (desc)
    memorias = (
        query.order_by(
            AtletaMemoria.importancia.desc(),
            AtletaMemoria.atualizado_em.desc(),
        )
        .limit(limite)
        .all()
    )

    return [AtletaMemoriaRead.model_validate(m).model_dump(mode="json") for m in memorias]


def buscar_memorias_por_texto(
    db: Session,
    atleta_id: str,
    q: str,
    limite: int = 20,
) -> tuple[List[dict], int]:
    """Busca memórias por texto em chave e valor_texto."""
    q_lower = q.lower()

    query = db.query(AtletaMemoria).filter(
        and_(
            AtletaMemoria.atleta_id == atleta_id,
            AtletaMemoria.ativo == True,
            or_(
                func.lower(AtletaMemoria.chave).contains(q_lower),
                func.lower(AtletaMemoria.valor_texto).contains(q_lower),
            ),
        )
    )

    total = query.count()
    memorias = query.order_by(AtletaMemoria.atualizado_em.desc()).limit(limite).all()

    return [AtletaMemoriaRead.model_validate(m).model_dump(mode="json") for m in memorias], total


def buscar_resumo_semanal(
    db: Session,
    atleta_id: str,
    semana_inicio: date,
) -> Optional[dict]:
    """Busca resumo semanal se existir."""
    memoria = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo == "resumo_semanal",
                AtletaMemoria.semana_inicio == semana_inicio,
                AtletaMemoria.ativo == True,
            )
        )
        .first()
    )

    if memoria:
        return AtletaMemoriaRead.model_validate(memoria).model_dump(mode="json")
    return None


def buscar_ultima_semana(
    db: Session,
    atleta_id: str,
) -> Optional[dict]:
    """Busca resumo semanal mais recente."""
    memoria = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo == "resumo_semanal",
                AtletaMemoria.ativo == True,
            )
        )
        .order_by(AtletaMemoria.semana_inicio.desc())
        .first()
    )

    if memoria:
        return AtletaMemoriaRead.model_validate(memoria).model_dump(mode="json")
    return None


def salvar_resumo_semanal(
    db: Session,
    atleta_id: str,
    dados: ResumoSemanalCreate,
) -> dict:
    """Salva resumo semanal como memória estruturada."""
    valor_json = {
        "resumo": dados.resumo,
        "aderencia": dados.aderencia,
        "pontos_positivos": dados.pontos_positivos,
        "pontos_atencao": dados.pontos_atencao,
        "decisoes_treinador": dados.decisoes_treinador,
        "proximo_foco": dados.proximo_foco,
    }

    # Criar ou atualizar memória de resumo semanal
    memoria = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo == "resumo_semanal",
                AtletaMemoria.semana_inicio == dados.semana_inicio,
            )
        )
        .first()
    )

    if memoria:
        memoria.valor_texto = dados.resumo
        memoria.valor_json = valor_json
        memoria.importancia = 5
        memoria.atualizado_em = func.now()
        db.commit()
        db.refresh(memoria)
        status = "atualizado"
    else:
        memoria = AtletaMemoria(
            atleta_id=atleta_id,
            tipo="resumo_semanal",
            chave=f"semana_{dados.semana_inicio.isoformat()}",
            valor_texto=dados.resumo,
            valor_json=valor_json,
            origem="conversa",
            importancia=5,
            confianca=1.0,
            semana_inicio=dados.semana_inicio,
        )
        db.add(memoria)
        db.commit()
        db.refresh(memoria)
        status = "criado"

    return {
        "id": str(memoria.id),
        "status": status,
        "memoria": AtletaMemoriaRead.model_validate(memoria).model_dump(mode="json"),
    }


def buscar_memorias_para_contexto(
    db: Session,
    atleta_id: str,
    limite: int = 30,
) -> dict:
    """
    Busca memórias relevantes para contexto inicial de chat.
    Prioriza: importância alta, últimas semanas, orientações, erros.
    """
    # Buscar último resumo semanal
    ultima_semana = buscar_ultima_semana(db, atleta_id)

    # Buscar alertas/orientações do treinador (alta importância)
    alertas = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo.in_(["orientacao_treinador", "erro_recorrente"]),
                AtletaMemoria.ativo == True,
                AtletaMemoria.importancia >= 4,
            )
        )
        .order_by(AtletaMemoria.atualizado_em.desc())
        .limit(5)
        .all()
    )

    # Buscar preferências
    preferencias = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo == "preferencia",
                AtletaMemoria.ativo == True,
            )
        )
        .all()
    )

    # Buscar objetivo
    objetivo = (
        db.query(AtletaMemoria)
        .filter(
            and_(
                AtletaMemoria.atleta_id == atleta_id,
                AtletaMemoria.tipo == "objetivo",
                AtletaMemoria.ativo == True,
            )
        )
        .first()
    )

    return {
        "ultima_semana": ultima_semana,
        "alertas_treinador": [AtletaMemoriaRead.model_validate(a).model_dump(mode="json") for a in alertas],
        "preferencias": [AtletaMemoriaRead.model_validate(p).model_dump(mode="json") for p in preferencias],
        "objetivo": AtletaMemoriaRead.model_validate(objetivo).model_dump(mode="json") if objetivo else None,
    }
