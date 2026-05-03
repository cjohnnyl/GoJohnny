"""Testes unitarios do context_service. So funcoes puras (sem banco)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.context_service import (
    EntradaContexto,
    montar_contexto_inicial_do_onboarding,
)


pytestmark = pytest.mark.unit


class _AtletaFake:
    """Fake do Atleta com defaults None - so atributos lidos pelo service."""
    def __init__(self, **kwargs):
        self.objetivo = kwargs.get("objetivo")
        self.dias_treino = kwargs.get("dias_treino")
        self.pace_confortavel = kwargs.get("pace_confortavel")
        self.maior_distancia_recente_km = kwargs.get("maior_distancia_recente_km")
        self.historico_dores = kwargs.get("historico_dores")
        self.proxima_prova = kwargs.get("proxima_prova")
        self.data_proxima_prova = kwargs.get("data_proxima_prova")
        self.distancia_alvo_km = kwargs.get("distancia_alvo_km")


class TestMontarContextoInicial:
    def test_atleta_minimo_retorna_lista_vazia(self):
        entradas = montar_contexto_inicial_do_onboarding(_AtletaFake())
        assert entradas == []

    def test_extrai_objetivo(self):
        e = montar_contexto_inicial_do_onboarding(
            _AtletaFake(objetivo="correr 10k em 50min")
        )
        assert EntradaContexto("objetivo", "descricao", "correr 10k em 50min") in e

    def test_extrai_dias_treino_como_string(self):
        e = montar_contexto_inicial_do_onboarding(_AtletaFake(dias_treino=4))
        assert EntradaContexto("treino", "dias_por_semana", "4") in e

    def test_extrai_pace(self):
        e = montar_contexto_inicial_do_onboarding(
            _AtletaFake(pace_confortavel="6:15")
        )
        assert EntradaContexto("treino", "pace_confortavel", "6:15") in e

    def test_extrai_data_proxima_prova_iso(self):
        e = montar_contexto_inicial_do_onboarding(
            _AtletaFake(data_proxima_prova=date(2026, 9, 15))
        )
        assert EntradaContexto("prova", "data", "2026-09-15") in e

    def test_extrai_historico_dores(self):
        e = montar_contexto_inicial_do_onboarding(
            _AtletaFake(historico_dores="joelho direito 2024")
        )
        assert EntradaContexto("historico", "dores", "joelho direito 2024") in e

    def test_atleta_completo_gera_varias_entradas(self):
        e = montar_contexto_inicial_do_onboarding(_AtletaFake(
            objetivo="meia maratona",
            dias_treino=3,
            pace_confortavel="6:30",
            maior_distancia_recente_km=Decimal("12"),
            historico_dores="nada",
            proxima_prova="Meia de Sao Paulo",
            data_proxima_prova=date(2026, 10, 5),
            distancia_alvo_km=Decimal("21.1"),
        ))
        # 8 entradas esperadas
        assert len(e) == 8
        tipos = {x.tipo for x in e}
        assert tipos == {"objetivo", "treino", "historico", "prova"}

    def test_zero_em_dias_treino_e_aceito_como_valor_explicito(self):
        # dias_treino=0 e diferente de NULL e deve ser preservado
        e = montar_contexto_inicial_do_onboarding(_AtletaFake(dias_treino=0))
        assert any(
            x.chave == "dias_por_semana" and x.valor == "0" for x in e
        )
