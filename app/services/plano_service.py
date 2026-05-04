"""
Servico de plano semanal - Fase 1, Blocos 6, 8 e 9.

Concentra:
  - regra de protecao contra sobrescrita (Bloco 9)
  - aplicacao de defaults aditivos do Fase 1
  - logging estruturado de toda criacao/atualizacao
  - validacao basica antes de gravar

Regra de protecao (decidida com Johnny):
  Se ja existe plano com status='ativo' para o atleta, a criacao de um
  NOVO plano so e permitida com novo_ciclo=True. Sem essa flag, o
  servico levanta SobrescritaProtegida (a route mapeia para HTTP 409).
  Quando novo_ciclo=True, o plano anterior e marcado como 'arquivado'
  na MESMA transacao do novo plano. Nada e apagado.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.plano_semanal import PlanoSemanal
from app.schemas.plano_semanal import PlanoSemanalCreate


logger = logging.getLogger("gojohnny.plano_service")


STATUS_ATIVO = "ativo"
STATUS_ARQUIVADO = "arquivado"


class SobrescritaProtegida(Exception):
    """Levantada quando ha tentativa de criar plano sem novo_ciclo
    enquanto o atleta ainda tem plano ativo."""

    def __init__(self, plano_atual_id: str, semana_inicio: str):
        self.plano_atual_id = plano_atual_id
        self.semana_inicio = semana_inicio
        super().__init__(
            f"Atleta ja tem plano ativo (id={plano_atual_id}, "
            f"semana_inicio={semana_inicio}). Para criar um novo, "
            f"envie novo_ciclo=true. Sem isso, o backend protege o "
            f"plano existente contra sobrescrita."
        )


def _plano_ativo_de(db: Session, atleta_id) -> Optional[PlanoSemanal]:
    return (
        db.query(PlanoSemanal)
        .filter(
            PlanoSemanal.atleta_id == atleta_id,
            PlanoSemanal.status == STATUS_ATIVO,
        )
        .order_by(PlanoSemanal.semana_inicio.desc())
        .first()
    )


def _detectar_versao_estrutura(data: PlanoSemanalCreate) -> int:
    """Decide versao_estrutura quando o caller nao informa.
    Versao 2 se o plano traz datas reais; senao versao 1 (legado)."""
    if data.versao_estrutura is not None:
        return int(data.versao_estrutura)
    if data.data_inicio is not None or data.data_prova is not None:
        return 2
    if data.dias_treino_json:
        return 2
    return 1


def criar_plano(
    db: Session,
    atleta: Atleta,
    data: PlanoSemanalCreate,
) -> PlanoSemanal:
    """Cria plano semanal aplicando todas as regras da Fase 1.

    Levanta:
      SobrescritaProtegida: se ja existe plano ativo e novo_ciclo=False.
      ValueError: se o JSONB 'plano' estiver ausente/vazio.
    """
    if data.plano is None or data.plano == {} or data.plano == []:
        raise ValueError("Campo 'plano' e obrigatorio e nao pode estar vazio.")

    plano_ativo_existente = _plano_ativo_de(db, atleta.id)

    if plano_ativo_existente is not None:
        if not data.novo_ciclo:
            logger.warning(
                "plano.criacao_bloqueada apelido=%s atleta_id=%s "
                "plano_ativo_id=%s motivo=novo_ciclo_falso",
                atleta.apelido, atleta.id, plano_ativo_existente.id,
            )
            raise SobrescritaProtegida(
                plano_atual_id=str(plano_ativo_existente.id),
                semana_inicio=str(plano_ativo_existente.semana_inicio),
            )
        # Arquiva o anterior na MESMA transacao - sem deletar dados.
        plano_ativo_existente.status = STATUS_ARQUIVADO
        db.add(plano_ativo_existente)
        logger.info(
            "plano.arquivado_para_novo_ciclo apelido=%s atleta_id=%s "
            "plano_arquivado_id=%s",
            atleta.apelido, atleta.id, plano_ativo_existente.id,
        )

    # Constroi novo plano (excluindo campos que NAO sao colunas)
    payload = data.model_dump(exclude={"apelido", "novo_ciclo"})
    payload["status"] = data.status or STATUS_ATIVO
    payload["versao_estrutura"] = _detectar_versao_estrutura(data)

    plano = PlanoSemanal(atleta_id=atleta.id, **payload)
    db.add(plano)
    db.flush()  # garante id sem fazer commit

    logger.info(
        "plano.criado apelido=%s atleta_id=%s plano_id=%s "
        "versao_estrutura=%s status=%s novo_ciclo=%s",
        atleta.apelido, atleta.id, plano.id,
        plano.versao_estrutura, plano.status, data.novo_ciclo,
    )

    return plano


def detectar_versao_estrutura(data: PlanoSemanalCreate) -> int:
    """Wrapper publico para teste unitario do detector."""
    return _detectar_versao_estrutura(data)
