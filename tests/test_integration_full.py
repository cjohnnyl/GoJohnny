"""
Suite de testes de integração GoJohnny — 20 testes obrigatórios.

Testa contra a API real (produção ou staging).

Variáveis de ambiente:
  GJ_TEST_BASE_URL  — URL base. Default: https://gojohnny.onrender.com
  GJ_TEST_KEY       — API key de teste. Obrigatória.

Uso:
  GJ_TEST_KEY=sua_chave pytest tests/test_integration_full.py -v

REGRAS DE SEGURANÇA:
  - Todos os writes são feitos em usuários com prefixo qa_
  - Johnny e Larissa: apenas leitura
  - Cleanup de qa_ ao final de cada teste que cria dados
"""

from __future__ import annotations

import os
import time
import uuid

import httpx
import pytest

BASE_URL = os.getenv("GJ_TEST_BASE_URL", "https://gojohnny.onrender.com").rstrip("/")
API_KEY = os.getenv("GJ_TEST_KEY", os.getenv("API_KEY", ""))

AUTH_HEADERS = {"x-api-key": API_KEY}
JSON_HEADERS = {**AUTH_HEADERS, "Content-Type": "application/json"}


def _ts_apelido(prefix: str = "qa_test") -> str:
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:4]}"


def _cleanup(apelido: str) -> None:
    """Remove usuário qa_ criado durante teste. Falha silenciosa."""
    with httpx.Client(timeout=15) as client:
        client.delete(f"{BASE_URL}/qa/cleanup/{apelido}", headers=AUTH_HEADERS)


@pytest.fixture(scope="session", autouse=True)
def require_api_key():
    if not API_KEY:
        pytest.skip("GJ_TEST_KEY ou API_KEY não configurado. Exporte antes de rodar.")


# ---------------------------------------------------------------------------
# T01 — Healthcheck
# ---------------------------------------------------------------------------

def test_01_healthcheck_root():
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{BASE_URL}/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "online"


def test_02_healthcheck_health():
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ---------------------------------------------------------------------------
# T03 — OpenAPI válido e contém /qa/cleanup
# ---------------------------------------------------------------------------

def test_03_openapi_valido_com_qa_cleanup():
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{BASE_URL}/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec.get("paths", {})
    assert "/qa/cleanup/{apelido}" in paths, (
        f"Endpoint /qa/cleanup/{{apelido}} ausente no OpenAPI. Paths: {list(paths.keys())}"
    )


# ---------------------------------------------------------------------------
# T04 — Autenticação sem API key → 401 ou 422
# ---------------------------------------------------------------------------

def test_04_auth_sem_api_key():
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas")
    assert r.status_code in (401, 422), f"Esperado 401 ou 422 sem key, obteve {r.status_code}"
    body = r.json()
    # Stack trace não deve vazar
    assert "traceback" not in str(body).lower()
    assert "sqlalchemy" not in str(body).lower()


def test_05_auth_api_key_invalida():
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas", headers={"x-api-key": "chave_invalida_xyz"})
    assert r.status_code == 401
    body = r.json()
    assert "traceback" not in str(body).lower()


def test_06_auth_api_key_valida():
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas", headers=AUTH_HEADERS)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# T07 — Sessão Johnny somente leitura
# ---------------------------------------------------------------------------

def test_07_sessao_johnny_leitura():
    with httpx.Client(timeout=15) as c:
        r = c.post(
            f"{BASE_URL}/sessao/iniciar",
            headers=JSON_HEADERS,
            json={"apelido": "johnny"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") in ("existente", "novo")
    # Não deve retornar dados de outro usuário
    atleta = data.get("atleta") or {}
    if atleta:
        assert atleta.get("apelido", "").lower() == "johnny"


# ---------------------------------------------------------------------------
# T08 — Plano Johnny somente leitura
# ---------------------------------------------------------------------------

def test_08_plano_johnny_leitura():
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/planos-semanais/johnny/atual", headers=AUTH_HEADERS)
    # 200 com plano ou 404 se não tiver. Nunca 500.
    assert r.status_code in (200, 404), f"Esperado 200 ou 404, obteve {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "plano" in data or "plano" in str(data)


# ---------------------------------------------------------------------------
# T09 — Case-sensitivity: johnny, Johnny, JOHNNY
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("variante", ["johnny", "Johnny", "JOHNNY"])
def test_09_case_sensitivity_johnny(variante):
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas/{variante}", headers=AUTH_HEADERS)
    assert r.status_code == 200, f"GET /atletas/{variante} retornou {r.status_code}"
    data = r.json()
    assert data.get("apelido") == "johnny", (
        f"Apelido retornado '{data.get('apelido')}' ≠ 'johnny' para variante '{variante}'"
    )


# ---------------------------------------------------------------------------
# T10 — Usuário inexistente → 404 controlado
# ---------------------------------------------------------------------------

def test_10_usuario_inexistente():
    apelido = f"usuario_inexistente_{uuid.uuid4().hex[:8]}"
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas/{apelido}", headers=AUTH_HEADERS)
    assert r.status_code == 404
    body = r.json()
    assert "traceback" not in str(body).lower()
    assert "sqlalchemy" not in str(body).lower()


# ---------------------------------------------------------------------------
# T11 — Criar usuário qa_
# ---------------------------------------------------------------------------

def test_11_criar_usuario_qa():
    apelido = _ts_apelido("qa_test_criar")
    try:
        with httpx.Client(timeout=15) as c:
            r = c.post(
                f"{BASE_URL}/atletas",
                headers=JSON_HEADERS,
                json={"nome": "QA Auto Test", "apelido": apelido},
            )
        assert r.status_code in (200, 201), f"Criar qa_ falhou: {r.status_code} {r.text}"
        data = r.json()
        assert data.get("apelido") == apelido
    finally:
        _cleanup(apelido)


# ---------------------------------------------------------------------------
# T12 — Criar plano para usuário qa_
# ---------------------------------------------------------------------------

def test_12_criar_plano_qa():
    apelido = _ts_apelido("qa_plano")
    try:
        with httpx.Client(timeout=15) as c:
            # Criar usuário
            r = c.post(
                f"{BASE_URL}/atletas",
                headers=JSON_HEADERS,
                json={"nome": "QA Plano Test", "apelido": apelido},
            )
            assert r.status_code in (200, 201)

            # Criar plano
            r = c.post(
                f"{BASE_URL}/planos-semanais",
                headers=JSON_HEADERS,
                json={
                    "apelido": apelido,
                    "semana_inicio": "2026-05-11",
                    "objetivo_semana": "Teste QA",
                    "volume_planejado_km": 20,
                    "status": "ativo",
                    "plano": {
                        "treinos": [
                            {"dia": "segunda", "tipo": "fácil", "duracao_min": 30, "km": 5, "pace": "6:00", "objetivo": "base aeróbica"},
                        ]
                    },
                },
            )
            assert r.status_code in (200, 201), f"Criar plano falhou: {r.status_code} {r.text}"

            # Verificar plano existe
            r = c.get(f"{BASE_URL}/planos-semanais/{apelido}/atual", headers=AUTH_HEADERS)
            assert r.status_code == 200
    finally:
        _cleanup(apelido)


# ---------------------------------------------------------------------------
# T13 — Strava sem conexão → 409 controlado (não 500)
# ---------------------------------------------------------------------------

def test_13_strava_sem_conexao_nao_500():
    apelido = _ts_apelido("qa_strava")
    try:
        with httpx.Client(timeout=15) as c:
            # Criar usuário sem Strava
            r = c.post(
                f"{BASE_URL}/atletas",
                headers=JSON_HEADERS,
                json={"nome": "QA Strava Test", "apelido": apelido},
            )
            assert r.status_code in (200, 201)

            # Tentar buscar treinos sem Strava conectado
            r = c.get(f"{BASE_URL}/strava/treinos-recentes/{apelido}", headers=AUTH_HEADERS)

        assert r.status_code != 500, "Strava sem conexão não deve retornar 500"
        assert r.status_code in (409, 424, 404), (
            f"Esperado 409/424 para Strava sem conexão, obteve {r.status_code}"
        )
    finally:
        _cleanup(apelido)


def test_14_strava_sem_conexao_formato_resposta():
    apelido = _ts_apelido("qa_strava_fmt")
    try:
        with httpx.Client(timeout=15) as c:
            r = c.post(
                f"{BASE_URL}/atletas",
                headers=JSON_HEADERS,
                json={"nome": "QA Strava Fmt", "apelido": apelido},
            )
            assert r.status_code in (200, 201)

            r = c.get(f"{BASE_URL}/strava/treinos-recentes/{apelido}", headers=AUTH_HEADERS)

        assert r.status_code == 409
        data = r.json()
        assert data.get("connected") is False, f"Esperado connected=false: {data}"
        assert data.get("action_required") == "connect_strava", f"Esperado action_required: {data}"
        assert "request_id" in data, f"Esperado request_id no body: {data}"
    finally:
        _cleanup(apelido)


# ---------------------------------------------------------------------------
# T15 — Payload inválido → 422 controlado
# ---------------------------------------------------------------------------

def test_15_payload_invalido_422():
    with httpx.Client(timeout=15) as c:
        # POST sessao sem apelido
        r = c.post(f"{BASE_URL}/sessao/iniciar", headers=JSON_HEADERS, json={})
    assert r.status_code == 422
    body = r.json()
    assert "traceback" not in str(body).lower()
    # FastAPI retorna "detail" com lista de erros de validação
    assert "detail" in body


# ---------------------------------------------------------------------------
# T16 — Cleanup qa_
# ---------------------------------------------------------------------------

def test_16_cleanup_qa_funciona():
    apelido = _ts_apelido("qa_cleanup_test")
    with httpx.Client(timeout=15) as c:
        # Criar
        r = c.post(
            f"{BASE_URL}/atletas",
            headers=JSON_HEADERS,
            json={"nome": "QA Cleanup Test", "apelido": apelido},
        )
        assert r.status_code in (200, 201)

        # Confirmar existência
        r = c.get(f"{BASE_URL}/atletas/{apelido}", headers=AUTH_HEADERS)
        assert r.status_code == 200

        # Deletar
        r = c.delete(f"{BASE_URL}/qa/cleanup/{apelido}", headers=AUTH_HEADERS)
        assert r.status_code == 204, f"Cleanup retornou {r.status_code}: {r.text}"

        # Confirmar remoção
        r = c.get(f"{BASE_URL}/atletas/{apelido}", headers=AUTH_HEADERS)
        assert r.status_code == 404, "Usuário deveria estar removido após cleanup"


# ---------------------------------------------------------------------------
# T17 — Cleanup bloqueia johnny
# ---------------------------------------------------------------------------

def test_17_cleanup_bloqueia_johnny():
    with httpx.Client(timeout=15) as c:
        r = c.delete(f"{BASE_URL}/qa/cleanup/johnny", headers=AUTH_HEADERS)
    assert r.status_code == 403, f"Johnny deve ser bloqueado pelo cleanup (obteve {r.status_code})"
    # Verificar johnny ainda existe
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas/johnny", headers=AUTH_HEADERS)
    assert r.status_code == 200, "Johnny deve existir após tentativa de cleanup"


# ---------------------------------------------------------------------------
# T18 — Cleanup bloqueia larissa
# ---------------------------------------------------------------------------

def test_18_cleanup_bloqueia_larissa():
    with httpx.Client(timeout=15) as c:
        r = c.delete(f"{BASE_URL}/qa/cleanup/larissa", headers=AUTH_HEADERS)
    assert r.status_code == 403, f"Larissa deve ser bloqueada pelo cleanup (obteve {r.status_code})"


# ---------------------------------------------------------------------------
# T19 — request_id no header e/ou body
# ---------------------------------------------------------------------------

def test_19_request_id_em_erro():
    apelido = f"usuario_inexistente_{uuid.uuid4().hex[:8]}"
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{BASE_URL}/atletas/{apelido}", headers=AUTH_HEADERS)

    assert r.status_code == 404
    has_rid_header = "x-request-id" in {k.lower() for k in r.headers}
    rid_in_body = "request_id" in r.text

    assert has_rid_header or rid_in_body, (
        f"request_id ausente em header ({dict(r.headers)}) e body ({r.text})"
    )


# ---------------------------------------------------------------------------
# T20 — Isolamento: qa_ não recebe dados de johnny
# ---------------------------------------------------------------------------

def test_20_isolamento_qa_nao_recebe_dados_johnny():
    apelido = _ts_apelido("qa_isolamento")
    try:
        with httpx.Client(timeout=15) as c:
            # Criar qa_
            r = c.post(
                f"{BASE_URL}/atletas",
                headers=JSON_HEADERS,
                json={"nome": "QA Isolamento Test", "apelido": apelido},
            )
            assert r.status_code in (200, 201)
            qa_id = r.json().get("id")

            # Buscar contexto do qa_
            r_ctx = c.get(f"{BASE_URL}/contexto/{apelido}", headers=AUTH_HEADERS)
            # Buscar contexto do johnny
            r_ctx_j = c.get(f"{BASE_URL}/contexto/johnny", headers=AUTH_HEADERS)

        # IDs devem ser diferentes
        if r_ctx.status_code == 200 and r_ctx_j.status_code == 200:
            ctx_qa = r_ctx.json()
            ctx_j = r_ctx_j.json()
            # Verificar que IDs de contexto não se cruzam
            qa_ids = {str(item.get("id", "")) for item in (ctx_qa if isinstance(ctx_qa, list) else [])}
            j_ids = {str(item.get("id", "")) for item in (ctx_j if isinstance(ctx_j, list) else [])}
            overlap = qa_ids & j_ids
            assert not overlap, f"Contexto qa_ e johnny compartilham IDs: {overlap}"

        # Buscar plano do qa_ — deve ser 404 (não tem plano) ou plano vazio
        with httpx.Client(timeout=15) as c:
            r_plano = c.get(f"{BASE_URL}/planos-semanais/{apelido}/atual", headers=AUTH_HEADERS)
        assert r_plano.status_code in (200, 404)
        if r_plano.status_code == 200:
            plano_data = r_plano.json()
            # O ID do atleta no plano deve ser o qa_, não o johnny
            assert plano_data.get("atleta_id") != "johnny"

    finally:
        _cleanup(apelido)
