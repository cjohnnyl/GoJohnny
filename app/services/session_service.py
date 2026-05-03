"""
Servico de inicio de sessao - Fase 1, Bloco 2 e 3.

Identifica usuario novo vs existente, recupera plano atual e contexto,
e devolve uma instrucao de continuacao para o GPT.

Decisoes (com Johnny):
  - Identificador: apelido direto (UNIQUE INDEX em atletas).
  - Sem fuzzy match. Se nao bate, status='novo'.
  - Idempotente: chamar duas vezes para o mesmo apelido nao tem efeito
    colateral.
  - Nao cria atleta (criacao continua via POST /atletas).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.plano_semanal import PlanoSemanal
from app.services.context_service import resumo_contexto
from app.services.feature_flag_service import capabilities_para


# ---------------------------------------------------------------------------
# Mensagens de continuacao - centralizadas para auditabilidade.
# ---------------------------------------------------------------------------

INSTRUCAO_NOVO = (
    "Usuario nao encontrado. Trate como NOVO atleta: faca o onboarding "
    "completo SEM chamar APIs durante a coleta. Apos resumir o entendimento "
    "e obter confirmacao explicita do usuario, chame POST /atletas para "
    "persistir o perfil. Nao mencione termos tecnicos."
)

INSTRUCAO_EXISTENTE_COM_PLANO = (
    "Usuario JA EXISTE e tem plano ativo. Trate como continuacao: "
    "cumprimente pelo nome, retome o plano atual de onde parou e nao "
    "reinicie onboarding. Se houver novidades opt-in, mencione brevemente "
    "que estao disponiveis - nunca ative sem consentimento explicito."
)

INSTRUCAO_EXISTENTE_SEM_PLANO = (
    "Usuario JA EXISTE mas nao tem plano ativo. Cumprimente, confirme o "
    "objetivo atual e proponha montar um plano novo. Nao reinicie o "
    "onboarding completo - pergunte apenas o necessario."
)


def iniciar_sessao(db: Session, *, apelido: str) -> dict:
    """Retorna um dict serializavel pelo schema SessaoIniciarResponse.

    Nunca levanta para apelido nao encontrado - status='novo'.
    Apenas erros tecnicos (banco fora) levantam.
    """
    apelido_norm = (apelido or "").strip()
    if not apelido_norm:
        # Defesa: vem do schema validado, mas garantia extra.
        return _resposta_novo()

    atleta: Atleta | None = (
        db.query(Atleta).filter(Atleta.apelido == apelido_norm).first()
    )

    if atleta is None:
        return _resposta_novo()

    plano = (
        db.query(PlanoSemanal)
        .filter(
            PlanoSemanal.atleta_id == atleta.id,
            PlanoSemanal.status == "ativo",
        )
        .order_by(PlanoSemanal.semana_inicio.desc())
        .first()
    )

    caps = capabilities_para(atleta)
    contexto = resumo_contexto(db, atleta.id)

    instrucao = (
        INSTRUCAO_EXISTENTE_COM_PLANO if plano is not None
        else INSTRUCAO_EXISTENTE_SEM_PLANO
    )

    return {
        "status": "existente",
        "atleta": atleta,
        "plano_atual": plano,
        "contexto_resumo": contexto,
        "flags": caps.to_dict(),
        "instrucao_continuacao": instrucao,
    }


def _resposta_novo() -> dict:
    return {
        "status": "novo",
        "atleta": None,
        "plano_atual": None,
        "contexto_resumo": {},
        "flags": {
            "usar_datas_reais": False,
            "usar_contexto_atleta": False,
            "usar_google_calendar": False,
            "usar_strava": False,
        },
        "instrucao_continuacao": INSTRUCAO_NOVO,
    }
