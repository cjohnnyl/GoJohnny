"""
Quick test para validar que case-sensitivity foi corrigido.
Testa GET /atletas/{apelido} com Larissa (capitalizado vs lowercase).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Usar um header fake para testes
FAKE_API_KEY = "apikdnvusdnmd58625@#*lsdj"
HEADERS = {"x-api-key": FAKE_API_KEY}


def test_get_atleta_lowercase():
    """GET /atletas/larissa deve retornar 200 (antes dava 404)."""
    response = client.get("/atletas/larissa", headers=HEADERS)
    assert response.status_code == 200, f"esperado 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["apelido"] == "larissa" or data["apelido"].lower() == "larissa"


def test_get_atleta_uppercase():
    """GET /atletas/LARISSA também deve retornar 200."""
    response = client.get("/atletas/LARISSA", headers=HEADERS)
    assert response.status_code == 200, f"esperado 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["apelido"] == "larissa" or data["apelido"].lower() == "larissa"


def test_get_atleta_mixed_case():
    """GET /atletas/Larissa também deve retornar 200."""
    response = client.get("/atletas/Larissa", headers=HEADERS)
    assert response.status_code == 200, f"esperado 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["apelido"] == "larissa" or data["apelido"].lower() == "larissa"


def test_sessao_already_worked():
    """POST /sessao/iniciar com larissa já funcionava, confirmar que continua."""
    response = client.post("/sessao/iniciar", json={"apelido": "larissa"}, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["novo", "existente"]
