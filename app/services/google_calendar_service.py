"""
Google Calendar Service - ETAPA 3, BLOCO 3.

Publica eventos reais no Google Calendar a partir do preview interno,
com idempotencia por hash_evento, retry seguro e falha parcial.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.evento_google_publicado import EventoGooglePublicado
from app.schemas.evento import CalendarioPublicacaoResponse, EventoTreinoRead
from app.services.evento_service import listar_eventos_atleta
from app.services.feature_flag_service import capabilities_para
from app.services.google_integration_service import (
    obter_access_token_valido,
    obter_integracao_para_atleta,
)
from app.services.google_oauth_service import renovar_access_token


logger = logging.getLogger("gojohnny.google_calendar_service")

GOOGLE_CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
TIMEZONE_PADRAO = "America/Sao_Paulo"
STATUS_PUBLICADO = "publicado"
STATUS_ERRO = "erro"


class PublicacaoCalendarioPrecondicaoError(Exception):
    """Falha controlada de precondicao para publicar no Google Calendar."""

    def __init__(self, motivo: str, mensagem: str):
        self.motivo = motivo
        super().__init__(mensagem)


class PublicacaoCalendarioConfigError(Exception):
    """Falha de configuracao do backend para publicar no Google Calendar."""


class PublicacaoEventoGoogleError(Exception):
    """Falha ao criar um evento especifico no Google Calendar."""


def _resposta_controlada(
    *,
    publicado: bool,
    motivo: str | None = None,
    eventos_criados: int = 0,
    eventos_ignorados: int = 0,
    erros: list[str] | None = None,
) -> CalendarioPublicacaoResponse:
    return CalendarioPublicacaoResponse(
        publicado=publicado,
        motivo=motivo,
        eventos_criados=eventos_criados,
        eventos_ignorados=eventos_ignorados,
        erros=erros or [],
    )


def _hash_evento(atleta: Atleta, evento: EventoTreinoRead) -> str:
    """Gera hash deterministico do evento para evitar duplicacao."""
    identidade = "|".join(
        [
            str(atleta.id),
            evento.data.isoformat(),
            evento.hora.isoformat(timespec="minutes"),
            evento.titulo.strip(),
            evento.descricao.strip(),
            str(int(evento.duracao_min)),
        ]
    )
    return hashlib.sha256(identidade.encode("utf-8")).hexdigest()


def _montar_payload_google(evento: EventoTreinoRead, hash_evento: str) -> dict:
    """Converte evento interno no payload aceito pelo Google Calendar."""
    inicio = datetime.combine(evento.data, evento.hora)
    fim = inicio + timedelta(minutes=evento.duracao_min)

    return {
        "summary": evento.titulo,
        "description": evento.descricao,
        "start": {
            "dateTime": inicio.isoformat(timespec="seconds"),
            "timeZone": TIMEZONE_PADRAO,
        },
        "end": {
            "dateTime": fim.isoformat(timespec="seconds"),
            "timeZone": TIMEZONE_PADRAO,
        },
        "extendedProperties": {
            "private": {
                "gojohnny_hash_evento": hash_evento,
            }
        },
    }


def _buscar_registro_evento(
    db: Session,
    atleta: Atleta,
    hash_evento: str,
) -> EventoGooglePublicado | None:
    return (
        db.query(EventoGooglePublicado)
        .filter(
            EventoGooglePublicado.atleta_id == atleta.id,
            EventoGooglePublicado.hash_evento == hash_evento,
        )
        .first()
    )


def _salvar_registro_evento(
    db: Session,
    registro: EventoGooglePublicado,
) -> EventoGooglePublicado:
    db.add(registro)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(registro)
    return registro


def _registrar_publicacao_sucesso(
    db: Session,
    atleta: Atleta,
    evento: EventoTreinoRead,
    hash_evento: str,
    google_event_id: str,
) -> EventoGooglePublicado:
    registro = _buscar_registro_evento(db, atleta, hash_evento)

    if registro is None:
        registro = EventoGooglePublicado(
            atleta_id=atleta.id,
            hash_evento=hash_evento,
        )

    registro.status = STATUS_PUBLICADO
    registro.google_event_id = google_event_id
    registro.titulo = evento.titulo
    registro.data_evento = evento.data
    registro.erro_ultima_tentativa = None

    try:
        return _salvar_registro_evento(db, registro)
    except IntegrityError:
        existente = _buscar_registro_evento(db, atleta, hash_evento)
        if existente is not None:
            return existente
        raise


def _registrar_publicacao_erro(
    db: Session,
    atleta: Atleta,
    evento: EventoTreinoRead,
    hash_evento: str,
    mensagem: str,
) -> EventoGooglePublicado:
    registro = _buscar_registro_evento(db, atleta, hash_evento)

    if registro is None:
        registro = EventoGooglePublicado(
            atleta_id=atleta.id,
            hash_evento=hash_evento,
        )

    registro.status = STATUS_ERRO
    registro.google_event_id = None
    registro.titulo = evento.titulo
    registro.data_evento = evento.data
    registro.erro_ultima_tentativa = mensagem

    return _salvar_registro_evento(db, registro)


async def _obter_access_token_para_publicacao(
    db: Session,
    atleta: Atleta,
    *,
    forcar_renovacao: bool = False,
) -> str:
    integracao = obter_integracao_para_atleta(db, atleta)
    if integracao is None:
        raise PublicacaoCalendarioPrecondicaoError(
            "google_nao_conectado",
            "Google Calendar nao conectado para este atleta.",
        )

    access_token = obter_access_token_valido(db, atleta)
    if access_token and not forcar_renovacao:
        return access_token

    try:
        renovado = await renovar_access_token(db, atleta)
    except ValueError as exc:
        raise PublicacaoCalendarioConfigError(str(exc)) from exc

    if not renovado:
        raise PublicacaoCalendarioPrecondicaoError(
            "token_google_expirado",
            "Integracao Google expirada e nao foi possivel renovar o token.",
        )

    access_token = obter_access_token_valido(db, atleta)
    if not access_token:
        raise PublicacaoCalendarioPrecondicaoError(
            "token_google_expirado",
            "Integracao Google indisponivel para publicacao.",
        )

    return access_token


async def _post_evento_google(
    access_token: str,
    payload: dict,
) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.post(
            GOOGLE_CALENDAR_EVENTS_URL,
            headers=headers,
            json=payload,
        )


def _detalhe_erro_resposta(resp: httpx.Response) -> str:
    try:
        corpo = resp.json()
    except ValueError:
        return f"Google retornou status {resp.status_code}."

    erro = corpo.get("error") if isinstance(corpo, dict) else None
    if isinstance(erro, dict):
        mensagem = erro.get("message")
        if mensagem:
            return f"Google retornou status {resp.status_code}: {mensagem}"

    return f"Google retornou status {resp.status_code}."


async def _criar_evento_google(
    db: Session,
    atleta: Atleta,
    evento: EventoTreinoRead,
    hash_evento: str,
    access_token: str,
) -> tuple[str, str]:
    payload = _montar_payload_google(evento, hash_evento)
    resposta = await _post_evento_google(access_token, payload)

    if resposta.status_code == 401:
        access_token = await _obter_access_token_para_publicacao(
            db,
            atleta,
            forcar_renovacao=True,
        )
        resposta = await _post_evento_google(access_token, payload)

    if resposta.status_code not in (200, 201):
        raise PublicacaoEventoGoogleError(_detalhe_erro_resposta(resposta))

    try:
        google_event_id = resposta.json().get("id")
    except ValueError as exc:
        raise PublicacaoEventoGoogleError(
            "Google retornou uma resposta invalida ao criar evento."
        ) from exc

    if not google_event_id:
        raise PublicacaoEventoGoogleError(
            "Google nao retornou id do evento criado."
        )

    return google_event_id, access_token


async def publicar_eventos_atleta(
    db: Session,
    atleta: Atleta,
) -> CalendarioPublicacaoResponse:
    """Publica os eventos do plano ativo no Google Calendar."""
    caps = capabilities_para(atleta)
    if not caps.usar_google_calendar:
        return _resposta_controlada(
            publicado=False,
            motivo="usar_google_calendar_desativado",
        )

    if obter_integracao_para_atleta(db, atleta) is None:
        return _resposta_controlada(
            publicado=False,
            motivo="google_nao_conectado",
        )

    preview = listar_eventos_atleta(
        db=db,
        atleta=atleta,
        usar_fallback_contexto=True,
    )

    if not preview.eventos:
        return _resposta_controlada(publicado=True)

    try:
        access_token = await _obter_access_token_para_publicacao(db, atleta)
    except PublicacaoCalendarioPrecondicaoError as exc:
        return _resposta_controlada(publicado=False, motivo=exc.motivo)

    eventos_criados = 0
    eventos_ignorados = 0
    erros: list[str] = []

    for evento in preview.eventos:
        hash_evento = _hash_evento(atleta, evento)
        registro_existente = _buscar_registro_evento(db, atleta, hash_evento)

        if (
            registro_existente is not None
            and registro_existente.status == STATUS_PUBLICADO
            and registro_existente.google_event_id
        ):
            eventos_ignorados += 1
            logger.info(
                "google_calendar.evento_ignorado atleta_id=%s data=%s titulo=%s",
                atleta.id,
                evento.data,
                evento.titulo,
            )
            continue

        try:
            google_event_id, access_token = await _criar_evento_google(
                db=db,
                atleta=atleta,
                evento=evento,
                hash_evento=hash_evento,
                access_token=access_token,
            )
            _registrar_publicacao_sucesso(
                db=db,
                atleta=atleta,
                evento=evento,
                hash_evento=hash_evento,
                google_event_id=google_event_id,
            )
            eventos_criados += 1
            logger.info(
                "google_calendar.evento_criado atleta_id=%s data=%s titulo=%s",
                atleta.id,
                evento.data,
                evento.titulo,
            )
        except PublicacaoCalendarioConfigError as exc:
            mensagem = str(exc)
            _registrar_publicacao_erro(
                db=db,
                atleta=atleta,
                evento=evento,
                hash_evento=hash_evento,
                mensagem=mensagem,
            )
            erros.append(f"{evento.data.isoformat()} {evento.titulo}: {mensagem}")
            logger.error(
                "google_calendar.falha_config_evento atleta_id=%s data=%s titulo=%s",
                atleta.id,
                evento.data,
                evento.titulo,
            )
        except PublicacaoCalendarioPrecondicaoError as exc:
            mensagem = str(exc)
            _registrar_publicacao_erro(
                db=db,
                atleta=atleta,
                evento=evento,
                hash_evento=hash_evento,
                mensagem=mensagem,
            )
            erros.append(f"{evento.data.isoformat()} {evento.titulo}: {mensagem}")
            logger.warning(
                "google_calendar.falha_precondicao_evento atleta_id=%s data=%s titulo=%s motivo=%s",
                atleta.id,
                evento.data,
                evento.titulo,
                exc.motivo,
            )
        except PublicacaoEventoGoogleError as exc:
            mensagem = str(exc)
            _registrar_publicacao_erro(
                db=db,
                atleta=atleta,
                evento=evento,
                hash_evento=hash_evento,
                mensagem=mensagem,
            )
            erros.append(f"{evento.data.isoformat()} {evento.titulo}: {mensagem}")
            logger.warning(
                "google_calendar.falha_evento atleta_id=%s data=%s titulo=%s",
                atleta.id,
                evento.data,
                evento.titulo,
            )
        except Exception as exc:
            mensagem = "falha inesperada ao publicar."
            _registrar_publicacao_erro(
                db=db,
                atleta=atleta,
                evento=evento,
                hash_evento=hash_evento,
                mensagem=mensagem,
            )
            erros.append(f"{evento.data.isoformat()} {evento.titulo}: {mensagem}")
            logger.exception(
                "google_calendar.erro_inesperado atleta_id=%s data=%s titulo=%s erro=%s",
                atleta.id,
                evento.data,
                evento.titulo,
                str(exc),
            )

    publicado = (eventos_criados + eventos_ignorados) > 0 or not preview.eventos
    return _resposta_controlada(
        publicado=publicado,
        eventos_criados=eventos_criados,
        eventos_ignorados=eventos_ignorados,
        erros=erros,
    )
