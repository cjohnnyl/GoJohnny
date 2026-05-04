"""
Testes QA para Etapa 2 - Contexto por usuário + Consistência.

7 cenários obrigatórios:
  1. WRITE CONTEXTO - salva corretamente
  2. UPSERT - atualiza sem duplicar
  3. READ - estrutura correta
  4. DELETE - remove corretamente
  5. SESSÃO COM CONTEXTO - contexto_resumo presente e correto
  6. SESSÃO SEM CONTEXTO - fallback funcionando
  7. CONSISTÊNCIA DE DIAS - normaliza saída
"""

from __future__ import annotations

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.atleta import Atleta
from app.models.contexto_atleta import ContextoAtleta
from app.services.context_service import (
    salvar_contexto,
    contexto_com_fallback,
)


pytestmark = pytest.mark.integration


def _no_auth():
    return None


@pytest.fixture
def client(db_session):
    """Cliente HTTP com override de get_db e auth."""
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


class TestContextoEtapa2QA:
    """Suite de testes QA para Etapa 2 - Contexto e Consistência."""

    def _criar_atleta_padrao(self, db_session, apelido: str) -> Atleta:
        """Helper para criar atleta com dados padrão."""
        atleta = Atleta(
            apelido=apelido,
            nome="Atleta Teste",
            objetivo="21km",
            dias_treino="4",
            pace_confortavel="5:00",
            maior_distancia_recente_km=15.0,
            historico_dores="joelho",
            proxima_prova="Meia Maratona ABC",
            distancia_alvo_km=21.0,
        )
        db.add(atleta)
        db.commit()
        db.refresh(atleta)
        return atleta

    # ========================================================================
    # CENÁRIO 1: WRITE CONTEXTO - Salvar contexto corretamente
    # ========================================================================

    def test_cenario_1_write_contexto_salva_corretamente(self, client, db_session, make_apelido):
        """Validar que POST /contexto/{apelido}/{tipo}/{chave} salva corretamente."""
        apelido = make_apelido("atleta_write")
        atleta = self._criar_atleta_padrao(db_session, apelido)

        # POST para salvar contexto
        response = client.post(
            f"/contexto/{apelido}/objetivo/dias_treino",
            json={
                "valor": "4",
                "origem": "teste_qa",
                "confianca": 1.0,
            },
        )

        assert response.status_code == 200, f"Erro: {response.text}"
        data = response.json()
        assert data["tipo"] == "objetivo"
        assert data["chave"] == "dias_treino"
        assert data["valor"] == "4"
        assert data["origem"] == "teste_qa"

        # Verificar que foi salvo no banco
        contexto = (
            db_session.query(ContextoAtleta)
            .filter(
                ContextoAtleta.atleta_id == atleta.id,
                ContextoAtleta.tipo == "objetivo",
                ContextoAtleta.chave == "dias_treino",
            )
            .first()
        )
        assert contexto is not None
        assert contexto.valor == "4"
        assert contexto.origem == "teste_qa"

    # ========================================================================
    # CENÁRIO 2: UPSERT - Atualiza sem duplicar
    # ========================================================================

    def test_cenario_2_upsert_atualiza_sem_duplicar(self, client, db_session, make_apelido):
        """Validar que chamar POST múltiplas vezes atualiza, não duplica."""
        apelido = make_apelido("atleta_upsert")
        atleta = self._criar_atleta_padrao(db_session, apelido)

        # Primeira escrita
        response1 = client.post(
            f"/contexto/{apelido}/objetivo/dias_treino",
            json={"valor": "4", "origem": "primeira", "confianca": 1.0},
        )
        assert response1.status_code == 200
        id1 = response1.json()["id"]

        # Segunda escrita com valor diferente
        response2 = client.post(
            f"/contexto/{apelido}/objetivo/dias_treino",
            json={"valor": "5", "origem": "segunda", "confianca": 0.9},
        )
        assert response2.status_code == 200
        id2 = response2.json()["id"]

        # Mesmos IDs = atualização, não duplicação
        assert id1 == id2, "UPSERT falhou: IDs devem ser iguais"

        # Verificar que há apenas 1 entrada no banco
        entradas = (
            db_session.query(ContextoAtleta)
            .filter(
                ContextoAtleta.atleta_id == atleta.id,
                ContextoAtleta.tipo == "objetivo",
                ContextoAtleta.chave == "dias_treino",
            )
            .all()
        )
        assert len(entradas) == 1, f"Esperado 1 entrada, encontrado {len(entradas)}"
        assert entradas[0].valor == "5"
        assert entradas[0].origem == "segunda"

    # ========================================================================
    # CENÁRIO 3: READ - Estrutura correta
    # ========================================================================

    def test_cenario_3_read_contexto_estrutura_correta(self, client, db_session, make_apelido):
        """Validar GET /contexto/{apelido} retorna estrutura correta."""
        apelido = make_apelido("atleta_read")
        atleta = self._criar_atleta_padrao(db_session, apelido)

        # Salvar vários contextos
        client.post(
            f"/contexto/{apelido}/objetivo/dias_treino",
            json={"valor": "4", "origem": "teste", "confianca": 1.0},
        )
        client.post(
            f"/contexto/{apelido}/objetivo/distancia",
            json={"valor": "21", "origem": "teste", "confianca": 1.0},
        )
        client.post(
            f"/contexto/{apelido}/historico/lesao",
            json={"valor": "joelho", "origem": "teste", "confianca": 0.8},
        )

        # GET para ler contexto
        response = client.get(f"/contexto/{apelido}")
        assert response.status_code == 200

        data = response.json()
        # Estrutura esperada: {tipo: {chave: valor}}
        assert "objetivo" in data
        assert data["objetivo"]["dias_treino"] == "4"
        assert data["objetivo"]["distancia"] == "21"
        assert "historico" in data
        assert data["historico"]["lesao"] == "joelho"

    # ========================================================================
    # CENÁRIO 4: DELETE - Remove corretamente
    # ========================================================================

    def test_cenario_4_delete_contexto_remove_corretamente(self, client, db_session, make_apelido):
        """Validar DELETE /contexto/{apelido}/{tipo}/{chave} remove."""
        apelido = make_apelido("atleta_delete")
        atleta = self._criar_atleta_padrao(db_session, apelido)

        # Salvar contexto
        client.post(
            f"/contexto/{apelido}/objetivo/dias_treino",
            json={"valor": "4", "origem": "teste", "confianca": 1.0},
        )

        # Verificar que existe
        get_resp = client.get(f"/contexto/{apelido}")
        assert "objetivo" in get_resp.json()

        # DELETE
        del_resp = client.delete(f"/contexto/{apelido}/objetivo/dias_treino")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deletado"

        # Verificar que foi removido
        get_resp2 = client.get(f"/contexto/{apelido}")
        assert "objetivo" not in get_resp2.json()

    # ========================================================================
    # CENÁRIO 5: SESSÃO COM CONTEXTO - contexto_resumo presente e correto
    # ========================================================================

    def test_cenario_5_sessao_com_contexto_resumo_correto(self, client, db_session, make_apelido):
        """Validar POST /sessao/iniciar com contexto retorna contexto_resumo."""
        apelido = make_apelido("atleta_sessao_com")
        atleta = self._criar_atleta_padrao(db_session, apelido)

        # Salvar contexto
        client.post(
            f"/contexto/{apelido}/objetivo/dias_treino",
            json={"valor": "4", "origem": "teste", "confianca": 1.0},
        )
        client.post(
            f"/contexto/{apelido}/historico/lesao",
            json={"valor": "joelho", "origem": "teste", "confianca": 0.8},
        )

        # Iniciar sessão
        response = client.post(
            "/sessao/iniciar",
            json={"apelido": apelido},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "existente"

        # Validar contexto_resumo
        contexto_resumo = data.get("contexto_resumo", {})
        assert "objetivo" in contexto_resumo
        assert contexto_resumo["objetivo"]["dias_treino"] == "4"
        assert "historico" in contexto_resumo
        assert contexto_resumo["historico"]["lesao"] == "joelho"

    # ========================================================================
    # CENÁRIO 6: SESSÃO SEM CONTEXTO - Fallback funcionando
    # ========================================================================

    def test_cenario_6_sessao_sem_contexto_fallback_ativado(self, client, db_session, make_apelido):
        """Validar POST /sessao/iniciar sem contexto retorna fallback (nunca vazio)."""
        apelido = make_apelido("atleta_sessao_fallback")
        # Criar atleta COM dados no modelo (para fallback)
        atleta = Atleta(
            apelido=apelido,
            nome="Atleta Fallback",
            objetivo="Meia Maratona",
            dias_treino="3",
            pace_confortavel="5:30",
            historico_dores="tornozelo",
            proxima_prova="Meia ABC",
            distancia_alvo_km=21.0,
        )
        db_session.add(atleta)
        db_session.commit()

        # NÃO salvar contexto explicitamente

        # Iniciar sessão
        response = client.post(
            "/sessao/iniciar",
            json={"apelido": apelido},
        )

        assert response.status_code == 200
        data = response.json()

        # Validar contexto_resumo (não deve estar vazio)
        contexto_resumo = data.get("contexto_resumo", {})
        assert contexto_resumo != {}, "contexto_resumo não deve ser vazio (fallback deveria ativar)"

        # Validar que fallback mapeou corretamente
        # O fallback deve ter extraído os dados do atleta
        assert len(contexto_resumo) > 0, "Fallback não gerou contexto"

    # ========================================================================
    # CENÁRIO 7: CONSISTÊNCIA DE DIAS - Normaliza saída
    # ========================================================================

    def test_cenario_7_consistencia_dias_entrada_variada(self, client, db_session, make_apelido):
        """Validar que dias com variações (inglês, acentos) normalizam na saída."""
        apelido = make_apelido("atleta_dias_variados")
        atleta = self._criar_atleta_padrao(db_session, apelido)

        # Entrada com variações: inglês, acento, minúscula
        dias_entrada = ["Tuesday", "terça", "quinta"]

        # POST plano com dias variados
        response = client.post(
            "/planos-semanais",
            json={
                "apelido": apelido,
                "semana_inicio": "2026-05-04",
                "objetivo_semana": "Teste",
                "volume_planejado_km": 30.0,
                "plano": {"treinos": []},
                "dias_treino_json": dias_entrada,
            },
        )

        assert response.status_code == 201, f"Erro ao criar plano: {response.text}"
        data = response.json()

        # Validar que dias foram normalizados na saída
        dias_saida = data.get("dias_treino_json", [])
        # "Tuesday" deve virar "terca", "terça" deve virar "terca", "quinta" fica "quinta"
        assert "terca" in dias_saida, f"Esperado 'terca' em saída, recebido: {dias_saida}"
        assert "quinta" in dias_saida
        assert "Tuesday" not in dias_saida, "Saída não foi normalizada"
        assert "terça" not in dias_saida, "Saída não foi normalizada"

    # ========================================================================
    # TESTES ADICIONAIS - Integração
    # ========================================================================

    def test_contexto_com_fallback_prioriza_persistido(self, db_session, make_apelido):
        """Validar que contexto_com_fallback prioriza persistido sobre fallback."""
        apelido = make_apelido("atleta_prioridade")
        atleta = Atleta(
            apelido=apelido,
            nome="Teste",
            objetivo="21km",
            historico_dores="joelho",
        )
        db_session.add(atleta)
        db_session.commit()

        # Salvár contexto diferente do modelo
        salvar_contexto(
            db_session,
            atleta,
            tipo="objetivo",
            chave="descricao",
            valor="Contexto Persistido",
            origem="teste",
            confianca=1.0,
        )
        db_session.commit()

        # Chamar contexto_com_fallback
        resultado = contexto_com_fallback(db_session, atleta)

        # Deve retornar o contexto persistido, não o fallback
        assert "objetivo" in resultado
        assert resultado["objetivo"]["descricao"] == "Contexto Persistido"

    def test_404_contexto_atleta_inexistente(self, client):
        """Validar que GET /contexto/{apelido_inexistente} retorna 404."""
        response = client.get("/contexto/apelido_inexistente_1234567890")
        assert response.status_code == 404
