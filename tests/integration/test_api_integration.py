"""
Testes de integracao Fase 1 - cobre os 5 cenarios A-E do briefing
+ regressao dos endpoints existentes.

Estrategia:
  - Postgres real via TEST_DATABASE_URL.
  - TestClient da FastAPI com override do get_db por teste.
  - Cada teste e isolado: cria atleta com apelido unico e nao vaza
    estado para outros testes.
"""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.auth import verify_api_key


pytestmark = pytest.mark.integration


# Bypass auth nos testes - a auth e exercitada em test separado.
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


def _criar_atleta(client: TestClient, apelido: str, **extra) -> dict:
    payload = {"nome": "Teste", "apelido": apelido}
    payload.update(extra)
    r = client.post("/atletas", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# =========================================================================
# CENARIO A - Usuario novo em chat novo
# =========================================================================

class TestCenarioA_UsuarioNovo:
    def test_sessao_iniciar_apelido_inexistente_retorna_novo(self, client, make_apelido):
        apelido = make_apelido("a_novo")
        r = client.post("/sessao/iniciar", json={"apelido": apelido})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "novo"
        assert body["atleta"] is None
        assert body["plano_atual"] is None
        assert body["contexto_resumo"] == {}
        # Default das flags = false
        assert body["flags"]["usar_datas_reais"] is False
        assert "onboarding" in body["instrucao_continuacao"].lower()

    def test_apos_criacao_sessao_iniciar_passa_a_retornar_existente(
        self, client, make_apelido
    ):
        apelido = make_apelido("a_apos")
        # Sessao 1: novo
        r1 = client.post("/sessao/iniciar", json={"apelido": apelido})
        assert r1.json()["status"] == "novo"
        # Cria
        _criar_atleta(client, apelido, objetivo="correr 10k")
        # Sessao 2: existente
        r2 = client.post("/sessao/iniciar", json={"apelido": apelido})
        assert r2.status_code == 200
        body = r2.json()
        assert body["status"] == "existente"
        assert body["atleta"]["apelido"] == apelido
        assert body["atleta"]["objetivo"] == "correr 10k"


# =========================================================================
# CENARIO B - Usuario existente em chat novo
# =========================================================================

class TestCenarioB_UsuarioExistenteSemPlano:
    def test_existente_sem_plano_retorna_instrucao_correta(self, client, make_apelido):
        apelido = make_apelido("b")
        _criar_atleta(client, apelido)
        r = client.post("/sessao/iniciar", json={"apelido": apelido})
        body = r.json()
        assert body["status"] == "existente"
        assert body["plano_atual"] is None
        assert "sem plano" in body["instrucao_continuacao"].lower() or \
               "objetivo atual" in body["instrucao_continuacao"].lower()


class TestCenarioB_UsuarioExistenteComPlano:
    def test_existente_com_plano_recupera_plano_atual(self, client, make_apelido):
        apelido = make_apelido("b_plan")
        _criar_atleta(client, apelido)
        # Cria plano legado (sem datas)
        plano_payload = {
            "apelido": apelido,
            "semana_inicio": "2026-04-27",
            "objetivo_semana": "manter base",
            "status": "ativo",
            "plano": {"treinos": [{"dia": "terça", "tipo": "leve"}]},
        }
        r = client.post("/planos-semanais", json=plano_payload)
        assert r.status_code == 201, r.text

        sess = client.post("/sessao/iniciar", json={"apelido": apelido}).json()
        assert sess["status"] == "existente"
        assert sess["plano_atual"] is not None
        assert sess["plano_atual"]["objetivo_semana"] == "manter base"
        assert sess["plano_atual"]["versao_estrutura"] == 1  # legado


# =========================================================================
# CENARIO C - Usuario com plano antigo (legado)
# =========================================================================

class TestCenarioC_PlanoLegadoLegivel:
    def test_plano_sem_datas_continua_legivel(self, client, make_apelido):
        apelido = make_apelido("c")
        _criar_atleta(client, apelido)
        client.post("/planos-semanais", json={
            "apelido": apelido,
            "semana_inicio": "2026-04-27",
            "status": "ativo",
            "plano": {"treinos": [{"dia": "terça", "distancia_km": 6}]},
        })
        r = client.get(f"/planos-semanais/{apelido}/atual")
        assert r.status_code == 200
        body = r.json()
        assert body["data_inicio"] is None
        assert body["data_prova"] is None
        assert body["dias_treino_json"] is None
        assert body["versao_estrutura"] == 1
        assert body["plano"]["treinos"][0]["dia"] == "terça"


# =========================================================================
# CENARIO D - Feature flag nova desligada
# =========================================================================

class TestCenarioD_FlagDesligadaPorPadrao:
    def test_atleta_novo_tem_flags_em_false(self, client, make_apelido):
        apelido = make_apelido("d")
        _criar_atleta(client, apelido)
        r = client.get(f"/atletas/{apelido}")
        assert r.status_code == 200
        body = r.json()
        assert body["usar_datas_reais"] is False
        assert body["usar_contexto_atleta"] is False
        assert body["usar_google_calendar"] is False
        assert body["usar_strava"] is False


# =========================================================================
# CENARIO E - Plano enriquecido com datas reais
# =========================================================================

class TestCenarioE_PlanoEnriquecido:
    def test_cria_e_le_plano_com_datas(self, client, make_apelido):
        apelido = make_apelido("e")
        _criar_atleta(client, apelido)
        r = client.post("/planos-semanais", json={
            "apelido": apelido,
            "semana_inicio": "2026-05-04",
            "status": "ativo",
            "data_inicio": "2026-05-04",
            "data_prova": "2026-09-15",
            "dias_treino_json": ["terça", "quinta", "sábado"],
            "plano": {
                "treinos": [
                    {"data": "2026-05-05", "dia_semana": "terça",
                     "tipo": "leve", "distancia_km": 5},
                ],
            },
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["data_inicio"] == "2026-05-04"
        assert body["data_prova"] == "2026-09-15"
        assert body["dias_treino_json"] == ["terça", "quinta", "sábado"]
        assert body["versao_estrutura"] == 2  # heuristica detectou


# =========================================================================
# Protecao contra sobrescrita - Bloco 9
# =========================================================================

class TestProtecaoSobrescrita:
    def test_segundo_post_sem_novo_ciclo_retorna_409(self, client, make_apelido):
        apelido = make_apelido("ovr1")
        _criar_atleta(client, apelido)
        # plano 1
        r1 = client.post("/planos-semanais", json={
            "apelido": apelido,
            "semana_inicio": "2026-05-04",
            "status": "ativo",
            "plano": {"treinos": []},
        })
        assert r1.status_code == 201
        # plano 2 sem novo_ciclo -> 409
        r2 = client.post("/planos-semanais", json={
            "apelido": apelido,
            "semana_inicio": "2026-05-11",
            "status": "ativo",
            "plano": {"treinos": []},
        })
        assert r2.status_code == 409
        detail = r2.json()["detail"]
        assert detail["erro"] == "plano_ativo_ja_existe"
        assert "novo_ciclo" in detail["como_proceder"]

    def test_novo_ciclo_true_arquiva_anterior(self, client, make_apelido):
        apelido = make_apelido("ovr2")
        _criar_atleta(client, apelido)
        r1 = client.post("/planos-semanais", json={
            "apelido": apelido,
            "semana_inicio": "2026-05-04",
            "status": "ativo",
            "plano": {"treinos": [{"dia": "terça"}]},
        }).json()
        plano1_id = r1["id"]

        r2 = client.post("/planos-semanais", json={
            "apelido": apelido,
            "semana_inicio": "2026-05-11",
            "status": "ativo",
            "novo_ciclo": True,
            "plano": {"treinos": [{"dia": "quarta"}]},
        })
        assert r2.status_code == 201, r2.text

        # Lista os 2 e confere status
        lista = client.get(f"/planos-semanais/{apelido}").json()
        ids_para_status = {p["id"]: p["status"] for p in lista}
        assert ids_para_status[plano1_id] == "arquivado"
        assert ids_para_status[r2.json()["id"]] == "ativo"

        # GET /atual retorna o NOVO
        atual = client.get(f"/planos-semanais/{apelido}/atual").json()
        assert atual["id"] == r2.json()["id"]


# =========================================================================
# Regressao - endpoints existentes continuam funcionando
# =========================================================================

class TestRegressao:
    def test_post_atleta_apelido_duplicado_continua_dando_409(
        self, client, make_apelido
    ):
        apelido = make_apelido("reg_dup")
        _criar_atleta(client, apelido)
        r = client.post("/atletas", json={"nome": "outro", "apelido": apelido})
        assert r.status_code == 409

    def test_patch_atleta_atualiza_campo_existente(self, client, make_apelido):
        apelido = make_apelido("reg_patch")
        _criar_atleta(client, apelido, peso_kg=70)
        r = client.patch(f"/atletas/{apelido}", json={"peso_kg": 71.5})
        assert r.status_code == 200
        assert float(r.json()["peso_kg"]) == 71.5

    def test_post_checkin_continua_funcionando(self, client, make_apelido):
        apelido = make_apelido("reg_chk")
        _criar_atleta(client, apelido)
        r = client.post("/checkins", json={
            "apelido": apelido,
            "semana_inicio": "2026-04-27",
            "treinos_planejados": 3,
            "treinos_realizados": 3,
        })
        assert r.status_code == 201

    def test_get_checkins_lista_em_ordem_decrescente(self, client, make_apelido):
        apelido = make_apelido("reg_lst")
        _criar_atleta(client, apelido)
        for sem in ("2026-04-13", "2026-04-20", "2026-04-27"):
            client.post("/checkins", json={
                "apelido": apelido, "semana_inicio": sem,
            })
        r = client.get(f"/checkins/{apelido}")
        assert r.status_code == 200
        datas = [c["semana_inicio"] for c in r.json()]
        assert datas == sorted(datas, reverse=True)

    def test_health_endpoint_continua_publico(self, client):
        # Health nao tem auth - devemos conseguir bater sem nada
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# =========================================================================
# Idempotencia - sessao
# =========================================================================

class TestIdempotenciaSessao:
    def test_chamar_sessao_iniciar_3_vezes_nao_cria_lixo(
        self, client, make_apelido, db_session
    ):
        from app.models.atleta import Atleta
        from app.models.contexto_atleta import ContextoAtleta

        apelido = make_apelido("idem")
        _criar_atleta(client, apelido)

        for _ in range(3):
            r = client.post("/sessao/iniciar", json={"apelido": apelido})
            assert r.status_code == 200

        n_atletas = db_session.query(Atleta).filter(
            Atleta.apelido == apelido
        ).count()
        assert n_atletas == 1


# =========================================================================
# Context service - upsert real contra DB
# =========================================================================

class TestContextServiceIntegration:
    def test_upsert_atualiza_em_vez_de_duplicar(self, db_session, make_apelido):
        from app.models.atleta import Atleta
        from app.models.contexto_atleta import ContextoAtleta
        from app.services.context_service import salvar_contexto

        atleta = Atleta(nome="Teste", apelido=make_apelido("ctx"))
        db_session.add(atleta)
        db_session.flush()

        salvar_contexto(
            db_session, atleta,
            tipo="objetivo", chave="descricao", valor="v1", origem="test",
        )
        salvar_contexto(
            db_session, atleta,
            tipo="objetivo", chave="descricao", valor="v2", origem="test",
        )

        items = db_session.query(ContextoAtleta).filter(
            ContextoAtleta.atleta_id == atleta.id
        ).all()
        assert len(items) == 1
        assert items[0].valor == "v2"
