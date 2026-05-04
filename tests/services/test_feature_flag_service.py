"""Testes unitarios do feature_flag_service - sem dependencia de banco."""

from __future__ import annotations

import pytest

from app.services.feature_flag_service import (
    CapabilitiesAtleta,
    FLAGS_CONHECIDAS,
    capabilities_para,
    defaults_para_novo_usuario,
)


pytestmark = pytest.mark.unit


class _AtletaFake:
    """Fake minimo do model Atleta - so tem os atributos que o service le."""
    def __init__(self, **flags):
        for f in FLAGS_CONHECIDAS:
            setattr(self, f, flags.get(f, False))


class TestCapabilitiesPara:
    def test_atleta_sem_flags_setadas_retorna_tudo_false(self):
        atleta = _AtletaFake()
        caps = capabilities_para(atleta)
        assert caps.usar_datas_reais is False
        assert caps.usar_contexto_atleta is False
        assert caps.usar_google_calendar is False
        assert caps.usar_strava is False

    def test_atleta_com_uma_flag_true(self):
        atleta = _AtletaFake(usar_datas_reais=True)
        caps = capabilities_para(atleta)
        assert caps.usar_datas_reais is True
        assert caps.usar_contexto_atleta is False

    def test_to_dict_tem_todas_as_chaves(self):
        caps = capabilities_para(_AtletaFake(usar_strava=True))
        d = caps.to_dict()
        assert set(d.keys()) == set(FLAGS_CONHECIDAS)
        assert d["usar_strava"] is True

    def test_is_enabled(self):
        caps = capabilities_para(_AtletaFake(usar_google_calendar=True))
        assert caps.is_enabled("usar_google_calendar") is True
        assert caps.is_enabled("usar_strava") is False

    def test_is_enabled_recusa_flag_desconhecida(self):
        caps = capabilities_para(_AtletaFake())
        with pytest.raises(ValueError, match="desconhecida"):
            caps.is_enabled("inventada")

    def test_capabilities_e_imutavel(self):
        caps = capabilities_para(_AtletaFake())
        with pytest.raises(Exception):
            caps.usar_datas_reais = True  # type: ignore[misc]


class TestDefaultsParaNovoUsuario:
    def test_todas_as_flags_em_false(self):
        d = defaults_para_novo_usuario()
        assert set(d.keys()) == set(FLAGS_CONHECIDAS)
        assert all(v is False for v in d.values())


class TestFlagsConhecidas:
    def test_lista_imutavel(self):
        # FLAGS_CONHECIDAS e tupla, nao pode ser modificada por engano
        with pytest.raises((TypeError, AttributeError)):
            FLAGS_CONHECIDAS.append("xpto")  # type: ignore[attr-defined]

    def test_lista_contem_todas_da_decisao(self):
        # Lista do briefing
        esperadas = {
            "usar_datas_reais", "usar_contexto_atleta",
            "usar_google_calendar", "usar_strava",
        }
        assert set(FLAGS_CONHECIDAS) == esperadas
