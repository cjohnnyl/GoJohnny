"""Testes unitários do plan_parser (Fase 1, Bloco 8).

Cobertura: planos antigos (formato atual em produção) e enriquecidos
(formato Fase 1) precisam coexistir sem quebrar.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.services.plan_parser import (
    EstruturaPlanoNormalizada,
    TreinoNormalizado,
    normalizar_plano,
)


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Plano vazio / inválido                                                       #
# --------------------------------------------------------------------------- #

class TestPlanoVazioOuInvalido:
    def test_plano_none(self):
        r = normalizar_plano(None)
        assert isinstance(r, EstruturaPlanoNormalizada)
        assert r.versao == 1
        assert r.treinos == tuple()
        assert r.tem_datas is False
        assert r.tem_semanas is False

    def test_plano_dict_vazio(self):
        r = normalizar_plano({})
        assert r.versao == 1
        assert r.treinos == tuple()

    def test_plano_lista_em_vez_de_dict(self):
        # Defesa contra entrada malformada.
        r = normalizar_plano([1, 2, 3])  # type: ignore[arg-type]
        assert r.treinos == tuple()
        assert r.bruto == {"_raw": [1, 2, 3]}

    def test_plano_string(self):
        r = normalizar_plano("texto livre")  # type: ignore[arg-type]
        assert r.treinos == tuple()


# --------------------------------------------------------------------------- #
# Plano antigo (formato em produção hoje)                                      #
# --------------------------------------------------------------------------- #

class TestPlanoLegado:
    """Réplica do exemplo do README:
       {"treinos": [{"dia": "terça", "tipo": "leve",
                     "distancia_km": 6, "intensidade": "confortável",
                     "objetivo": "manter base aeróbica"}]}
    """
    def setup_method(self):
        self.plano_legado = {
            "treinos": [
                {
                    "dia": "terça",
                    "tipo": "leve",
                    "distancia_km": 6,
                    "intensidade": "confortável",
                    "objetivo": "manter base aeróbica",
                },
                {
                    "dia": "quinta",
                    "tipo": "intervalado",
                    "distancia_km": 8,
                    "intensidade": "forte",
                    "objetivo": "vo2max",
                    "duracao_min": 50,
                },
            ]
        }

    def test_versao_detectada_como_legada(self):
        r = normalizar_plano(self.plano_legado)
        assert r.versao == 1
        assert r.tem_datas is False
        assert r.tem_semanas is False

    def test_treinos_extraidos(self):
        r = normalizar_plano(self.plano_legado)
        assert len(r.treinos) == 2

    def test_dia_legado_mapeado_para_dia_semana(self):
        r = normalizar_plano(self.plano_legado)
        assert r.treinos[0].dia_semana == "terça"
        assert r.treinos[1].dia_semana == "quinta"

    def test_distancia_convertida_para_float(self):
        r = normalizar_plano(self.plano_legado)
        assert r.treinos[0].distancia_km == 6.0
        assert isinstance(r.treinos[0].distancia_km, float)

    def test_data_ausente_e_none(self):
        r = normalizar_plano(self.plano_legado)
        assert all(t.data is None for t in r.treinos)

    def test_duracao_min_quando_presente(self):
        r = normalizar_plano(self.plano_legado)
        assert r.treinos[1].duracao_min == 50


# --------------------------------------------------------------------------- #
# Plano enriquecido (Fase 1)                                                   #
# --------------------------------------------------------------------------- #

class TestPlanoEnriquecido:
    def test_treino_com_data_iso(self):
        r = normalizar_plano({
            "treinos": [
                {
                    "data": "2026-05-05",
                    "dia_semana": "terça",
                    "tipo": "leve",
                    "distancia_km": 5.5,
                    "duracao_min": 35,
                }
            ],
        })
        assert r.versao == 2
        assert r.tem_datas is True
        assert r.treinos[0].data == date(2026, 5, 5)
        assert r.treinos[0].dia_semana == "terça"

    def test_data_com_timestamp_completo(self):
        r = normalizar_plano({
            "treinos": [{"data": "2026-05-05T07:00:00Z"}],
        })
        assert r.treinos[0].data == date(2026, 5, 5)

    def test_data_invalida_vira_none(self):
        r = normalizar_plano({"treinos": [{"data": "amanhã"}]})
        assert r.treinos[0].data is None
        # Ainda assim a versão é 1 (não há data válida nem semanas).
        assert r.versao == 1

    def test_presenca_de_semanas_aciona_v2(self):
        r = normalizar_plano({
            "semanas": [{"numero": 1}],
            "treinos": [],
        })
        assert r.versao == 2
        assert r.tem_semanas is True

    def test_versao_hint_explicita_sobrepoe_heuristica(self):
        r = normalizar_plano({"treinos": []}, versao_hint=2)
        assert r.versao == 2


# --------------------------------------------------------------------------- #
# Tolerância em campos individuais                                             #
# --------------------------------------------------------------------------- #

class TestTolerancia:
    def test_campos_extras_preservados(self):
        r = normalizar_plano({
            "treinos": [{
                "dia": "terça",
                "tipo": "leve",
                "campo_estranho": "valor_qualquer",
                "outro": 42,
            }],
        })
        assert r.treinos[0].extras == {
            "campo_estranho": "valor_qualquer",
            "outro": 42,
        }

    def test_distancia_string_convertida(self):
        r = normalizar_plano({
            "treinos": [{"dia": "terça", "distancia_km": "7.5"}],
        })
        assert r.treinos[0].distancia_km == 7.5

    def test_distancia_invalida_vira_none(self):
        r = normalizar_plano({
            "treinos": [{"dia": "terça", "distancia_km": "bla"}],
        })
        assert r.treinos[0].distancia_km is None

    def test_duracao_string_decimal(self):
        r = normalizar_plano({
            "treinos": [{"dia": "terça", "duracao_min": "30.0"}],
        })
        assert r.treinos[0].duracao_min == 30

    def test_strings_vazias_viram_none(self):
        r = normalizar_plano({
            "treinos": [{"dia": "  ", "tipo": "", "objetivo": ""}],
        })
        assert r.treinos[0].dia_semana is None
        assert r.treinos[0].tipo is None
        assert r.treinos[0].objetivo is None

    def test_treino_nao_dict_nao_quebra(self):
        r = normalizar_plano({"treinos": ["string solta", 42, None]})
        assert len(r.treinos) == 3
        for t in r.treinos:
            assert t.dia_semana is None
            assert t.data is None

    def test_treinos_nao_lista_e_ignorado(self):
        r = normalizar_plano({"treinos": "isso devia ser lista"})
        assert r.treinos == tuple()

    def test_chave_treinos_ausente(self):
        r = normalizar_plano({"semanas": []})
        assert r.treinos == tuple()


# --------------------------------------------------------------------------- #
# Bruto preservado                                                              #
# --------------------------------------------------------------------------- #

class TestBrutoPreservado:
    def test_dict_original_acessivel(self):
        original = {"treinos": [{"dia": "terça"}], "extra": "x"}
        r = normalizar_plano(original)
        assert r.bruto == original

    def test_imutabilidade_do_resultado(self):
        r = normalizar_plano({"treinos": [{"dia": "terça"}]})
        with pytest.raises(Exception):
            r.versao = 99  # type: ignore[misc]
