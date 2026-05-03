"""Testes unitarios do plano_service - parte sem banco."""

from __future__ import annotations

from datetime import date

import pytest

from app.schemas.plano_semanal import PlanoSemanalCreate
from app.services.plano_service import detectar_versao_estrutura


pytestmark = pytest.mark.unit


def _criar(**kwargs):
    return PlanoSemanalCreate(
        apelido="x",
        semana_inicio=date(2026, 5, 4),
        plano={"treinos": []},
        **kwargs,
    )


class TestDetectarVersaoEstrutura:
    def test_legado_sem_datas_e_sem_dias(self):
        assert detectar_versao_estrutura(_criar()) == 1

    def test_com_data_inicio_vira_v2(self):
        assert detectar_versao_estrutura(
            _criar(data_inicio=date(2026, 5, 4))
        ) == 2

    def test_com_data_prova_vira_v2(self):
        assert detectar_versao_estrutura(
            _criar(data_prova=date(2026, 9, 1))
        ) == 2

    def test_com_dias_treino_json_vira_v2(self):
        assert detectar_versao_estrutura(
            _criar(dias_treino_json=["segunda", "quarta"])
        ) == 2

    def test_versao_explicita_sobrepoe_heuristica(self):
        # Mesmo sem datas, se vier versao_estrutura=2 explicito, respeita
        assert detectar_versao_estrutura(_criar(versao_estrutura=2)) == 2
        # E vice-versa - mesmo com datas, se vier versao=1, respeita
        assert detectar_versao_estrutura(_criar(
            data_inicio=date(2026, 5, 4),
            versao_estrutura=1,
        )) == 1


class TestNovoCicloDefaultFalse:
    def test_default_false_se_nao_informado(self):
        p = _criar()
        assert p.novo_ciclo is False

    def test_aceita_true_explicito(self):
        p = _criar(novo_ciclo=True)
        assert p.novo_ciclo is True
