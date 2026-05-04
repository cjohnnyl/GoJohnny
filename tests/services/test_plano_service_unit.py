"""Testes unitarios do plano_service - parte sem banco."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.schemas.plano_semanal import PlanoSemanalCreate
from app.services.plano_service import (
    detectar_versao_estrutura,
    enriquecer_plano_com_datas,
    _normalizar_dia,
)


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


class TestEnriquecerPlanoComDatas:
    """Testes do enriquecimento de plano com datas reais (Fase 2, Etapa 1)."""

    def _mock_atleta(self, usar_datas_reais=False):
        """Helper para criar um mock de Atleta."""
        atleta = MagicMock()
        atleta.apelido = "johnny"
        atleta.usar_datas_reais = usar_datas_reais
        return atleta

    def test_sem_flag_retorna_plano_intocado(self):
        """Se usar_datas_reais=False no atleta, retorna plano original."""
        plano = {"treinos": [{"dia_semana": "terça"}]}
        atleta = self._mock_atleta(usar_datas_reais=False)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),
            data_prova=date(2026, 6, 1),
            dias_treino_json=["terça"],
        )

        assert resultado is plano
        assert "data" not in resultado["treinos"][0]

    def test_com_flag_e_dados_enriquece(self):
        """Se flag=True e dados presentes, enriquece treinos com datas."""
        plano = {"treinos": [{"dia_semana": "terça", "tipo": "leve"}]}
        atleta = self._mock_atleta(usar_datas_reais=True)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),  # sexta-feira
            data_prova=date(2026, 5, 31),
            dias_treino_json=["terça"],
        )

        # Primeira terça a partir de 2026-05-01 (sexta) é 2026-05-05
        assert resultado["treinos"][0]["data"] == "2026-05-05"
        assert resultado["treinos"][0]["tipo"] == "leve"

    def test_sem_data_inicio_retorna_intocado(self):
        """Se data_inicio falta, retorna plano original."""
        plano = {"treinos": [{"dia_semana": "terça"}]}
        atleta = self._mock_atleta(usar_datas_reais=True)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=None,
            data_prova=date(2026, 6, 1),
            dias_treino_json=["terça"],
        )

        assert resultado is plano

    def test_sem_dias_treino_retorna_intocado(self):
        """Se dias_treino_json falta, retorna plano original."""
        plano = {"treinos": [{"dia_semana": "terça"}]}
        atleta = self._mock_atleta(usar_datas_reais=True)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),
            data_prova=date(2026, 6, 1),
            dias_treino_json=None,
        )

        assert resultado is plano

    def test_multiplos_treinos_mesmo_dia(self):
        """Se há múltiplos treinos no mesmo dia, mapeia em ordem."""
        plano = {
            "treinos": [
                {"dia_semana": "terça", "tipo": "leve"},
                {"dia_semana": "terça", "tipo": "moderado"},
            ]
        }
        atleta = self._mock_atleta(usar_datas_reais=True)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),  # sexta-feira
            data_prova=date(2026, 5, 31),
            dias_treino_json=["terça"],
        )

        # 1ª terça a partir de 2026-05-01 = 2026-05-05, 2ª terça = 2026-05-12
        assert resultado["treinos"][0]["data"] == "2026-05-05"
        assert resultado["treinos"][1]["data"] == "2026-05-12"

    def test_treino_sem_dia_semana_nao_recebe_data(self):
        """Treino sem dia_semana não recebe data enriquecida."""
        plano = {
            "treinos": [
                {"tipo": "leve"},  # sem dia_semana
            ]
        }
        atleta = self._mock_atleta(usar_datas_reais=True)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),
            data_prova=date(2026, 6, 1),
            dias_treino_json=["terça"],
        )

        assert "data" not in resultado["treinos"][0]
        assert resultado["treinos"][0]["tipo"] == "leve"

    def test_plano_sem_treinos_retorna_intocado(self):
        """Plano sem campo 'treinos' retorna intocado."""
        plano = {"objetivo": "meia maratona"}
        atleta = self._mock_atleta(usar_datas_reais=True)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),
            data_prova=date(2026, 6, 1),
            dias_treino_json=["terça"],
        )

        assert resultado is plano

    def test_param_usar_datas_reais_sobrepoe_atleta(self):
        """Se usar_datas_reais=True (param), sobrepõe flag do atleta."""
        plano = {"treinos": [{"dia_semana": "terça"}]}
        atleta = self._mock_atleta(usar_datas_reais=False)

        resultado = enriquecer_plano_com_datas(
            plano_jsonb=plano,
            atleta=atleta,
            data_inicio=date(2026, 5, 1),
            data_prova=date(2026, 6, 1),
            dias_treino_json=["terça"],
            usar_datas_reais=True,  # param sobrepõe False do atleta
        )

        # Deve enriquecer mesmo com atleta.usar_datas_reais=False
        assert "data" in resultado["treinos"][0]


class TestNormalizarDia:
    """Testes de normalização de dias da semana (Fase 2, Etapa 1 - Hardening)."""

    def test_portugues_sem_acento(self):
        """Dias em português sem acento devem ser normalizados."""
        assert _normalizar_dia("segunda") == "segunda"
        assert _normalizar_dia("terca") == "terca"
        assert _normalizar_dia("quarta") == "quarta"
        assert _normalizar_dia("quinta") == "quinta"
        assert _normalizar_dia("sexta") == "sexta"
        assert _normalizar_dia("sabado") == "sabado"
        assert _normalizar_dia("domingo") == "domingo"

    def test_portugues_com_acento(self):
        """Dias em português com acento devem ser normalizados."""
        assert _normalizar_dia("terça") == "terca"
        assert _normalizar_dia("sábado") == "sabado"

    def test_inglês_lowercase(self):
        """Dias em inglês minúsculo devem ser normalizados."""
        assert _normalizar_dia("monday") == "segunda"
        assert _normalizar_dia("tuesday") == "terca"
        assert _normalizar_dia("wednesday") == "quarta"
        assert _normalizar_dia("thursday") == "quinta"
        assert _normalizar_dia("friday") == "sexta"
        assert _normalizar_dia("saturday") == "sabado"
        assert _normalizar_dia("sunday") == "domingo"

    def test_inglês_uppercase(self):
        """Dias em inglês maiúsculo devem ser normalizados."""
        assert _normalizar_dia("Tuesday") == "terca"
        assert _normalizar_dia("THURSDAY") == "quinta"
        assert _normalizar_dia("Friday") == "sexta"

    def test_abreviacoes_portugues(self):
        """Abreviações em português devem ser normalizadas."""
        assert _normalizar_dia("seg") == "segunda"
        assert _normalizar_dia("ter") == "terca"
        assert _normalizar_dia("qua") == "quarta"
        assert _normalizar_dia("qui") == "quinta"
        assert _normalizar_dia("sex") == "sexta"
        assert _normalizar_dia("sab") == "sabado"
        assert _normalizar_dia("dom") == "domingo"

    def test_abreviacoes_ingles(self):
        """Abreviações em inglês devem ser normalizadas."""
        assert _normalizar_dia("mon") == "segunda"
        assert _normalizar_dia("tue") == "terca"
        assert _normalizar_dia("wed") == "quarta"
        assert _normalizar_dia("thu") == "quinta"
        assert _normalizar_dia("fri") == "sexta"
        assert _normalizar_dia("sat") == "sabado"
        assert _normalizar_dia("sun") == "domingo"

    def test_com_espacos(self):
        """Espaços em branco devem ser ignorados."""
        assert _normalizar_dia("  terca  ") == "terca"
        assert _normalizar_dia(" Tuesday ") == "terca"

    def test_dia_invalido(self):
        """Dias inválidos devem retornar None."""
        assert _normalizar_dia("xyz") is None
        assert _normalizar_dia("foo") is None
        assert _normalizar_dia("") is None

    def test_tipo_invalido(self):
        """Entrada que não é string deve retornar None."""
        assert _normalizar_dia(123) is None
        assert _normalizar_dia(None) is None
