"""
Context service - CRUD basico de contexto_atleta. Fase 1, Bloco 10.

Escopo da Fase 1: somente gravar dados relevantes do onboarding e
disponibilizar leitura. NAO faz extracao automatica continua. NAO usa
inteligencia avancada. NAO injeta massivamente no prompt.

Modelo: chave/valor por (atleta_id, tipo, chave). Upsert idempotente:
chamar salvar_contexto duas vezes com mesmo (tipo, chave) atualiza valor
em vez de duplicar - isso e o que viabiliza re-execucao segura do
onboarding sem poluir o banco.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.contexto_atleta import ContextoAtleta


@dataclass(frozen=True)
class EntradaContexto:
    """Tupla simples (tipo, chave, valor[, confianca]) para gravacao em lote."""
    tipo: str
    chave: str
    valor: Optional[str]
    confianca: float = 1.0


# Tipos canonicos suportados na Fase 1. Outros tipos sao aceitos mas
# nao tem garantia de uso pelo restante do sistema.
TIPOS_CANONICOS: tuple[str, ...] = (
    "objetivo",
    "treino",
    "historico",
    "preferencia",
    "prova",
)


def salvar_contexto(
    db: Session,
    atleta: Atleta,
    *,
    tipo: str,
    chave: str,
    valor: Optional[str],
    origem: str,
    confianca: float = 1.0,
) -> ContextoAtleta:
    """Upsert por (atleta_id, tipo, chave). Idempotente.

    Se ja existe entrada com mesma chave dentro do tipo, atualiza valor,
    confianca e origem. Senao, cria. Operacao add-only se a regra de
    unicidade for respeitada.
    """
    if not isinstance(tipo, str) or not tipo.strip():
        raise ValueError("tipo nao pode ser vazio.")
    if not isinstance(chave, str) or not chave.strip():
        raise ValueError("chave nao pode ser vazia.")
    if not isinstance(origem, str) or not origem.strip():
        raise ValueError("origem nao pode ser vazia.")
    if not (0.0 <= float(confianca) <= 1.0):
        raise ValueError("confianca deve estar entre 0 e 1.")

    existente = (
        db.query(ContextoAtleta)
        .filter(
            ContextoAtleta.atleta_id == atleta.id,
            ContextoAtleta.tipo == tipo,
            ContextoAtleta.chave == chave,
        )
        .first()
    )

    if existente is not None:
        existente.valor = valor
        existente.origem = origem
        existente.confianca = Decimal(str(confianca))
        db.add(existente)
        db.flush()
        return existente

    novo = ContextoAtleta(
        atleta_id=atleta.id,
        tipo=tipo,
        chave=chave,
        valor=valor,
        origem=origem,
        confianca=Decimal(str(confianca)),
    )
    db.add(novo)
    db.flush()
    return novo


def salvar_contexto_em_lote(
    db: Session,
    atleta: Atleta,
    entradas: Iterable[EntradaContexto],
    *,
    origem: str,
) -> list[ContextoAtleta]:
    """Variante para gravar varias entradas com mesma origem (tipico do
    onboarding). Mantem semantica de upsert por entrada."""
    resultado: list[ContextoAtleta] = []
    for e in entradas:
        if e.valor is None or (isinstance(e.valor, str) and not e.valor.strip()):
            # Pula entradas vazias para nao sujar o banco com NULLs.
            continue
        resultado.append(
            salvar_contexto(
                db, atleta,
                tipo=e.tipo, chave=e.chave, valor=e.valor,
                origem=origem, confianca=e.confianca,
            )
        )
    return resultado


def listar_contexto(
    db: Session,
    atleta_id: uuid.UUID,
    *,
    tipo: Optional[str] = None,
) -> list[ContextoAtleta]:
    """Lista todas as entradas de contexto do atleta, ordenadas por
    tipo e chave para apresentacao previsivel."""
    q = db.query(ContextoAtleta).filter(ContextoAtleta.atleta_id == atleta_id)
    if tipo is not None:
        q = q.filter(ContextoAtleta.tipo == tipo)
    return q.order_by(ContextoAtleta.tipo, ContextoAtleta.chave).all()


def resumo_contexto(
    db: Session,
    atleta_id: uuid.UUID,
) -> dict[str, dict[str, str]]:
    """Resumo no formato {tipo: {chave: valor}} para inclusao em
    POST /sessao/iniciar e demais respostas que precisam de overview."""
    entradas = listar_contexto(db, atleta_id)
    out: dict[str, dict[str, str]] = {}
    for e in entradas:
        out.setdefault(e.tipo, {})[e.chave] = e.valor or ""
    return out


def montar_contexto_inicial_do_onboarding(
    atleta: Atleta,
) -> list[EntradaContexto]:
    """Extrai entradas relevantes do proprio model de Atleta.

    Estrategia conservadora: usa SO o que ja foi coletado pelo onboarding
    e mapeia para chaves do contexto_atleta. NAO inventa, NAO infere.
    Campos NULL sao ignorados (filtrados pelo salvar_contexto_em_lote)."""
    entradas: list[EntradaContexto] = []

    if atleta.objetivo:
        entradas.append(EntradaContexto("objetivo", "descricao", atleta.objetivo))
    if atleta.dias_treino is not None:
        entradas.append(EntradaContexto("treino", "dias_por_semana", str(atleta.dias_treino)))
    if atleta.pace_confortavel:
        entradas.append(EntradaContexto("treino", "pace_confortavel", atleta.pace_confortavel))
    if atleta.maior_distancia_recente_km is not None:
        entradas.append(EntradaContexto(
            "treino", "maior_distancia_recente_km",
            str(atleta.maior_distancia_recente_km),
        ))
    if atleta.historico_dores:
        entradas.append(EntradaContexto("historico", "dores", atleta.historico_dores))
    if atleta.proxima_prova:
        entradas.append(EntradaContexto("prova", "alvo", atleta.proxima_prova))
    if atleta.data_proxima_prova is not None:
        entradas.append(EntradaContexto(
            "prova", "data", atleta.data_proxima_prova.isoformat(),
        ))
    if atleta.distancia_alvo_km is not None:
        entradas.append(EntradaContexto(
            "prova", "distancia_km", str(atleta.distancia_alvo_km),
        ))

    return entradas
