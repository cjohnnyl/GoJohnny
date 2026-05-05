from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.main import app
from app.models.atleta import Atleta
from app.models.evento_google_publicado import EventoGooglePublicado
from app.models.integracao_google import IntegracaoGoogle
from app.models.plano_semanal import PlanoSemanal
from app.services.google_calendar_service import STATUS_ERRO, STATUS_PUBLICADO


pytestmark = pytest.mark.integration


def _no_auth():
    return None


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = _no_auth
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _criar_atleta(
    db_session,
    apelido: str,
    *,
    usar_google_calendar: bool,
) -> Atleta:
    atleta = Atleta(
        nome="Teste",
        apelido=apelido,
        usar_google_calendar=usar_google_calendar,
    )
    db_session.add(atleta)
    db_session.commit()
    db_session.refresh(atleta)
    return atleta


def _criar_plano_ativo(db_session, atleta: Atleta) -> PlanoSemanal:
    plano = PlanoSemanal(
        atleta_id=atleta.id,
        semana_inicio=datetime(2026, 5, 4, tzinfo=UTC).date(),
        status="ativo",
        plano={
            "treinos": [
                {
                    "data": "2026-05-05",
                    "dia_semana": "terca",
                    "tipo": "leve",
                    "distancia_km": 8,
                },
                {
                    "data": "2026-05-07",
                    "dia_semana": "quinta",
                    "tipo": "moderado",
                    "distancia_km": 10,
                },
            ]
        },
    )
    db_session.add(plano)
    db_session.commit()
    db_session.refresh(plano)
    return plano


def _criar_integracao_google(
    db_session,
    atleta: Atleta,
    *,
    access_token: str = "token-valido",
    refresh_token: str | None = "refresh-token",
    expires_at: datetime | None = None,
) -> IntegracaoGoogle:
    integracao = IntegracaoGoogle(
        atleta_id=atleta.id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at or (datetime.now(UTC) + timedelta(hours=1)),
        email_google="teste@example.com",
    )
    db_session.add(integracao)
    db_session.commit()
    db_session.refresh(integracao)
    return integracao


def _listar_registros(db_session, atleta: Atleta) -> list[EventoGooglePublicado]:
    return (
        db_session.query(EventoGooglePublicado)
        .filter(EventoGooglePublicado.atleta_id == atleta.id)
        .order_by(EventoGooglePublicado.data_evento.asc(), EventoGooglePublicado.criado_em.asc())
        .all()
    )


class TestCalendarioPublicacaoGoogle:
    def test_publicar_flag_desligada_retorna_resposta_controlada_sem_chamar_google(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        from app.services import google_calendar_service as service

        atleta = _criar_atleta(
            db_session,
            "calendar_flag_false",
            usar_google_calendar=False,
        )
        _criar_plano_ativo(db_session, atleta)
        _criar_integracao_google(db_session, atleta)

        chamadas: list[dict] = []

        async def fake_post_evento_google(access_token: str, payload: dict):
            chamadas.append(payload)
            return httpx.Response(201, json={"id": "nao-deveria"})

        monkeypatch.setattr(service, "_post_evento_google", fake_post_evento_google)

        resp = client.post(f"/calendario/{atleta.apelido}/publicar")

        assert resp.status_code == 200, resp.text
        assert resp.json() == {
            "publicado": False,
            "motivo": "usar_google_calendar_desativado",
            "eventos_criados": 0,
            "eventos_ignorados": 0,
            "erros": [],
        }
        assert chamadas == []
        assert _listar_registros(db_session, atleta) == []

    def test_publicar_google_desconectado_retorna_resposta_controlada_sem_chamar_google(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        from app.services import google_calendar_service as service

        atleta = _criar_atleta(
            db_session,
            "calendar_sem_google",
            usar_google_calendar=True,
        )
        _criar_plano_ativo(db_session, atleta)

        chamadas: list[dict] = []

        async def fake_post_evento_google(access_token: str, payload: dict):
            chamadas.append(payload)
            return httpx.Response(201, json={"id": "nao-deveria"})

        monkeypatch.setattr(service, "_post_evento_google", fake_post_evento_google)

        resp = client.post(f"/calendario/{atleta.apelido}/publicar")

        assert resp.status_code == 200, resp.text
        assert resp.json() == {
            "publicado": False,
            "motivo": "google_nao_conectado",
            "eventos_criados": 0,
            "eventos_ignorados": 0,
            "erros": [],
        }
        assert chamadas == []
        assert _listar_registros(db_session, atleta) == []

    def test_publicar_cria_eventos_e_ignora_na_republicacao(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        from app.services import google_calendar_service as service

        atleta = _criar_atleta(
            db_session,
            "calendar_idempotente",
            usar_google_calendar=True,
        )
        _criar_plano_ativo(db_session, atleta)
        _criar_integracao_google(db_session, atleta)

        chamadas: list[tuple[str, dict]] = []

        async def fake_post_evento_google(access_token: str, payload: dict):
            chamadas.append((access_token, payload))
            return httpx.Response(
                201,
                json={"id": f"google-{len(chamadas)}"},
            )

        monkeypatch.setattr(service, "_post_evento_google", fake_post_evento_google)

        primeira = client.post(f"/calendario/{atleta.apelido}/publicar")
        assert primeira.status_code == 200, primeira.text
        assert primeira.json() == {
            "publicado": True,
            "motivo": None,
            "eventos_criados": 2,
            "eventos_ignorados": 0,
            "erros": [],
        }

        registros = _listar_registros(db_session, atleta)
        assert len(registros) == 2
        assert all(r.status == STATUS_PUBLICADO for r in registros)
        assert all(r.google_event_id for r in registros)
        assert all(r.hash_evento for r in registros)
        assert len(chamadas) == 2

        segunda = client.post(f"/calendario/{atleta.apelido}/publicar")
        assert segunda.status_code == 200, segunda.text
        assert segunda.json() == {
            "publicado": True,
            "motivo": None,
            "eventos_criados": 0,
            "eventos_ignorados": 2,
            "erros": [],
        }
        assert len(chamadas) == 2

        registros_apos = _listar_registros(db_session, atleta)
        assert len(registros_apos) == 2

    def test_publicar_retry_reaproveita_registro_com_status_erro(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        from app.services import google_calendar_service as service

        atleta = _criar_atleta(
            db_session,
            "calendar_retry_erro",
            usar_google_calendar=True,
        )
        _criar_plano_ativo(db_session, atleta)
        _criar_integracao_google(db_session, atleta)

        primeira_rodada = [
            httpx.Response(500, json={"error": {"message": "backendError"}}),
            httpx.Response(201, json={"id": "google-ok-2"}),
        ]

        async def fake_post_primeira(access_token: str, payload: dict):
            return primeira_rodada.pop(0)

        monkeypatch.setattr(service, "_post_evento_google", fake_post_primeira)

        primeira = client.post(f"/calendario/{atleta.apelido}/publicar")
        assert primeira.status_code == 200, primeira.text
        assert primeira.json() == {
            "publicado": True,
            "motivo": None,
            "eventos_criados": 1,
            "eventos_ignorados": 0,
            "erros": ["2026-05-05 Treino Leve: Google retornou status 500: backendError"],
        }

        registros = _listar_registros(db_session, atleta)
        assert len(registros) == 2
        erro = next(r for r in registros if r.status == STATUS_ERRO)
        publicado = next(r for r in registros if r.status == STATUS_PUBLICADO)
        assert erro.google_event_id is None
        assert "backendError" in (erro.erro_ultima_tentativa or "")
        assert publicado.google_event_id == "google-ok-2"

        chamadas_retry: list[dict] = []

        async def fake_post_segunda(access_token: str, payload: dict):
            chamadas_retry.append(payload)
            return httpx.Response(201, json={"id": "google-retry-1"})

        monkeypatch.setattr(service, "_post_evento_google", fake_post_segunda)

        segunda = client.post(f"/calendario/{atleta.apelido}/publicar")
        assert segunda.status_code == 200, segunda.text
        assert segunda.json() == {
            "publicado": True,
            "motivo": None,
            "eventos_criados": 1,
            "eventos_ignorados": 1,
            "erros": [],
        }

        assert len(chamadas_retry) == 1
        registros_apos = _listar_registros(db_session, atleta)
        assert len(registros_apos) == 2
        erro_atualizado = next(r for r in registros_apos if r.hash_evento == erro.hash_evento)
        assert erro_atualizado.status == STATUS_PUBLICADO
        assert erro_atualizado.google_event_id == "google-retry-1"
        assert erro_atualizado.erro_ultima_tentativa is None

    def test_publicar_continua_quando_um_evento_falha(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        from app.services import google_calendar_service as service

        atleta = _criar_atleta(
            db_session,
            "calendar_falha_parcial",
            usar_google_calendar=True,
        )
        _criar_plano_ativo(db_session, atleta)
        _criar_integracao_google(db_session, atleta)

        respostas = [
            httpx.Response(201, json={"id": "google-ok-1"}),
            httpx.Response(500, json={"error": {"message": "backendError"}}),
        ]

        async def fake_post_evento_google(access_token: str, payload: dict):
            return respostas.pop(0)

        monkeypatch.setattr(service, "_post_evento_google", fake_post_evento_google)

        resp = client.post(f"/calendario/{atleta.apelido}/publicar")

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body == {
            "publicado": True,
            "motivo": None,
            "eventos_criados": 1,
            "eventos_ignorados": 0,
            "erros": ["2026-05-07 Treino Moderado: Google retornou status 500: backendError"],
        }

        registros = _listar_registros(db_session, atleta)
        assert len(registros) == 2
        assert sum(1 for r in registros if r.status == STATUS_PUBLICADO) == 1
        assert sum(1 for r in registros if r.status == STATUS_ERRO) == 1

    def test_publicar_renova_token_expirado_antes_de_criar_eventos(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        from app.services import google_calendar_service as service

        atleta = _criar_atleta(
            db_session,
            "calendar_token_expirado",
            usar_google_calendar=True,
        )
        _criar_plano_ativo(db_session, atleta)
        _criar_integracao_google(
            db_session,
            atleta,
            access_token="token-expirado",
            refresh_token="refresh-ok",
            expires_at=datetime.now(UTC) - timedelta(minutes=5),
        )

        async def fake_renovar_access_token(db, atleta_param):
            assert atleta_param.id == atleta.id
            integracao_db = db.query(IntegracaoGoogle).filter(
                IntegracaoGoogle.atleta_id == atleta.id
            ).first()
            integracao_db.access_token = "token-renovado"
            integracao_db.expires_at = datetime.now(UTC) + timedelta(hours=1)
            db.add(integracao_db)
            db.commit()
            return True

        tokens_usados: list[str] = []

        async def fake_post_evento_google(access_token: str, payload: dict):
            tokens_usados.append(access_token)
            return httpx.Response(
                201,
                json={"id": f"google-renovado-{len(tokens_usados)}"},
            )

        monkeypatch.setattr(service, "renovar_access_token", fake_renovar_access_token)
        monkeypatch.setattr(service, "_post_evento_google", fake_post_evento_google)

        resp = client.post(f"/calendario/{atleta.apelido}/publicar")

        assert resp.status_code == 200, resp.text
        assert resp.json() == {
            "publicado": True,
            "motivo": None,
            "eventos_criados": 2,
            "eventos_ignorados": 0,
            "erros": [],
        }
        assert tokens_usados == ["token-renovado", "token-renovado"]
