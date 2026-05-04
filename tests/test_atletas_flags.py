import pytest
from fastapi.testclient import TestClient


def test_patch_flags_atleta_nao_existe(client, headers):
    """Deve retornar 404 se atleta não existe."""
    response = client.patch(
        "/atletas/nao-existe/flags",
        json={"usar_datas_reais": True},
        headers=headers
    )
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]


def test_patch_flags_sem_api_key(client):
    """Deve retornar 401 sem API key."""
    response = client.patch(
        "/atletas/teste/flags",
        json={"usar_datas_reais": True}
    )
    assert response.status_code == 401


def test_patch_flags_api_key_invalida(client):
    """Deve retornar 401 com API key inválida."""
    response = client.patch(
        "/atletas/teste/flags",
        json={"usar_datas_reais": True},
        headers={"x-api-key": "invalida"}
    )
    assert response.status_code == 401


def test_patch_flags_single_flag(client, headers, test_db):
    """Deve atualizar apenas a flag enviada."""
    from app.models.atleta import Atleta

    atleta = Atleta(nome="Teste", apelido="teste")
    test_db.add(atleta)
    test_db.commit()
    test_db.refresh(atleta)

    response = client.patch(
        "/atletas/teste/flags",
        json={"usar_datas_reais": True},
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["usar_datas_reais"] is True
    assert data["usar_contexto_atleta"] is False
    assert data["usar_google_calendar"] is False
    assert data["usar_strava"] is False


def test_patch_flags_multiple_flags(client, headers, test_db):
    """Deve atualizar múltiplas flags."""
    from app.models.atleta import Atleta

    atleta = Atleta(nome="Teste", apelido="teste")
    test_db.add(atleta)
    test_db.commit()

    response = client.patch(
        "/atletas/teste/flags",
        json={
            "usar_datas_reais": True,
            "usar_contexto_atleta": True,
            "usar_strava": False
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["usar_datas_reais"] is True
    assert data["usar_contexto_atleta"] is True
    assert data["usar_google_calendar"] is False
    assert data["usar_strava"] is False


def test_patch_flags_all_flags(client, headers, test_db):
    """Deve atualizar todas as flags."""
    from app.models.atleta import Atleta

    atleta = Atleta(nome="Teste", apelido="teste")
    test_db.add(atleta)
    test_db.commit()

    response = client.patch(
        "/atletas/teste/flags",
        json={
            "usar_datas_reais": True,
            "usar_contexto_atleta": True,
            "usar_google_calendar": True,
            "usar_strava": True
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["usar_datas_reais"] is True
    assert data["usar_contexto_atleta"] is True
    assert data["usar_google_calendar"] is True
    assert data["usar_strava"] is True


def test_patch_flags_idempotent(client, headers, test_db):
    """Deve ser idempotente - múltiplas chamadas devem retornar o mesmo resultado."""
    from app.models.atleta import Atleta

    atleta = Atleta(nome="Teste", apelido="teste")
    test_db.add(atleta)
    test_db.commit()

    payload = {"usar_datas_reais": True, "usar_contexto_atleta": True}

    response1 = client.patch(
        "/atletas/teste/flags",
        json=payload,
        headers=headers
    )
    assert response1.status_code == 200
    data1 = response1.json()

    response2 = client.patch(
        "/atletas/teste/flags",
        json=payload,
        headers=headers
    )
    assert response2.status_code == 200
    data2 = response2.json()

    assert data1 == data2


def test_patch_flags_partial_update_preserves_other_flags(client, headers, test_db):
    """Deve preservar flags não enviadas na atualização."""
    from app.models.atleta import Atleta

    atleta = Atleta(
        nome="Teste",
        apelido="teste",
        usar_datas_reais=True,
        usar_contexto_atleta=True,
        usar_google_calendar=False,
        usar_strava=False
    )
    test_db.add(atleta)
    test_db.commit()

    response = client.patch(
        "/atletas/teste/flags",
        json={"usar_strava": True},
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["usar_datas_reais"] is True
    assert data["usar_contexto_atleta"] is True
    assert data["usar_google_calendar"] is False
    assert data["usar_strava"] is True


def test_patch_flags_empty_payload(client, headers, test_db):
    """Deve aceitar payload vazio e retornar flags atuais."""
    from app.models.atleta import Atleta

    atleta = Atleta(
        nome="Teste",
        apelido="teste",
        usar_datas_reais=True
    )
    test_db.add(atleta)
    test_db.commit()

    response = client.patch(
        "/atletas/teste/flags",
        json={},
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["usar_datas_reais"] is True
    assert data["usar_contexto_atleta"] is False


def test_patch_flags_case_sensitive_apelido(client, headers, test_db):
    """Deve ser case-sensitive na busca por apelido."""
    from app.models.atleta import Atleta

    atleta = Atleta(nome="Teste", apelido="teste")
    test_db.add(atleta)
    test_db.commit()

    response = client.patch(
        "/atletas/Teste/flags",
        json={"usar_datas_reais": True},
        headers=headers
    )

    assert response.status_code == 404


def test_get_atleta_returns_flags(client, headers, test_db):
    """GET /atletas/{apelido} deve retornar as flags."""
    from app.models.atleta import Atleta

    atleta = Atleta(
        nome="Teste",
        apelido="teste",
        usar_datas_reais=True,
        usar_contexto_atleta=True
    )
    test_db.add(atleta)
    test_db.commit()

    response = client.get("/atletas/teste", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["usar_datas_reais"] is True
    assert data["usar_contexto_atleta"] is True
    assert data["usar_google_calendar"] is False
    assert data["usar_strava"] is False
