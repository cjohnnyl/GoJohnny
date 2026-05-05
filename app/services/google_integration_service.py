"""
Google Integration Service - FASE 3.3 - Bloco 1.

Gerencia tokens OAuth do Google, persistencia e validacao de expiracao.

Responsabilidades:
- Salvar access_token e refresh_token de forma segura
- Recuperar tokens validos por atleta
- Verificar expiração e gerenciar renovacao
- Never expose tokens em logs ou respostas publicas
- Tudo via backend (nunca enviar tokens ao frontend)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.integracao_google import IntegracaoGoogle


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalizar_datetime_utc(valor: Optional[datetime]) -> Optional[datetime]:
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def salvar_tokens(
    db: Session,
    atleta: Atleta,
    *,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in_seconds: int = 3600,
    email_google: Optional[str] = None,
) -> IntegracaoGoogle:
    """
    Salva ou atualiza tokens OAuth do Google para um atleta.

    Args:
        db: Session do SQLAlchemy
        atleta: Atleta que esta autorizando
        access_token: JWT access token do Google
        refresh_token: Token de refresh (opcional)
        expires_in_seconds: Segundos ate expiracao (padrao 3600 = 1 hora)
        email_google: Email da conta Google (opcional)

    Returns:
        IntegracaoGoogle atualizada
    """
    if not isinstance(access_token, str) or not access_token.strip():
        raise ValueError("access_token nao pode ser vazio")

    # Calcular expires_at
    expires_at = _agora_utc() + timedelta(seconds=expires_in_seconds)

    # Verificar se ja existe integracao para este atleta
    existente = (
        db.query(IntegracaoGoogle)
        .filter(IntegracaoGoogle.atleta_id == atleta.id)
        .first()
    )

    if existente:
        # Atualizar tokens existentes
        existente.access_token = access_token
        existente.refresh_token = refresh_token
        existente.expires_at = expires_at
        existente.email_google = email_google or existente.email_google
        existente.atualizado_em = _agora_utc()
        db.add(existente)
    else:
        # Criar nova integracao
        nova_integracao = IntegracaoGoogle(
            id=uuid.uuid4(),
            atleta_id=atleta.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            email_google=email_google,
        )
        db.add(nova_integracao)

    db.commit()

    # Re-fetch para garantir que temos dados atualizados (sem tokens expostos)
    return obter_integracao_para_atleta(db, atleta)


def obter_integracao_para_atleta(
    db: Session,
    atleta: Atleta,
) -> Optional[IntegracaoGoogle]:
    """
    Retorna a integracao Google para um atleta, ou None se nao existe.

    SEGURANCA: Nunca retorna tokens em logs. Use apenas internamente.
    """
    return (
        db.query(IntegracaoGoogle)
        .filter(IntegracaoGoogle.atleta_id == atleta.id)
        .first()
    )


def obter_access_token_valido(
    db: Session,
    atleta: Atleta,
) -> Optional[str]:
    """
    Retorna access_token valido se existe e nao expirou.

    SEGURANCA: Nunca logar o token. Usar apenas internamente.
    Returns:
        access_token se valido, None se nao existe ou expirou
    """
    integracao = obter_integracao_para_atleta(db, atleta)

    if not integracao:
        return None

    # Verificar expiracao (com margem de 60 segundos de segurança)
    expires_at = _normalizar_datetime_utc(integracao.expires_at)
    if expires_at:
        margem = _agora_utc() + timedelta(seconds=60)
        if expires_at <= margem:
            return None

    return integracao.access_token


def obter_tokens_para_renovacao(
    db: Session,
    atleta: Atleta,
) -> Optional[dict]:
    """
    Retorna tokens necessarios para renovar access_token.

    Usado apenas internamente para renovacao de tokens expirados.

    Returns:
        dict com refresh_token e email, ou None
    """
    integracao = obter_integracao_para_atleta(db, atleta)

    if not integracao or not integracao.refresh_token:
        return None

    return {
        "refresh_token": integracao.refresh_token,
        "email": integracao.email_google,
    }


def verificar_expiracao(
    db: Session,
    atleta: Atleta,
) -> dict:
    """
    Verifica status de expiracao dos tokens.

    Returns:
        {
            "valido": bool,
            "expira_em": datetime ou None,
            "tempo_restante_segundos": int ou None,
        }
    """
    integracao = obter_integracao_para_atleta(db, atleta)

    if not integracao:
        return {
            "valido": False,
            "expira_em": None,
            "tempo_restante_segundos": None,
        }

    agora = _agora_utc()
    margem = agora + timedelta(seconds=60)
    expires_at = _normalizar_datetime_utc(integracao.expires_at)

    if expires_at and expires_at <= margem:
        return {
            "valido": False,
            "expira_em": expires_at,
            "tempo_restante_segundos": int(
                (expires_at - agora).total_seconds()
            ),
        }

    tempo_restante = None
    if expires_at:
        tempo_restante = int((expires_at - agora).total_seconds())

    return {
        "valido": True,
        "expira_em": expires_at,
        "tempo_restante_segundos": tempo_restante,
    }


def desativar_integracao(
    db: Session,
    atleta: Atleta,
) -> bool:
    """
    Remove tokens da integracao (desconecta Google).

    Returns:
        True se foi removida, False se nao existia
    """
    integracao = obter_integracao_para_atleta(db, atleta)

    if not integracao:
        return False

    db.delete(integracao)
    db.commit()

    return True
