"""Testes unitários da engine de calendário (Fase 1, Bloco 7)."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.calendar_engine import (
    CalendarioPlano,
    TreinoCalendario,
    gerar_calendario,
    nome_canonico_do_weekday,
    normalizar_dia_da_semana,
)


pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Normalização de dias da semana                                               #
# --------------------------------------------------------------------------- #

class TestNormalizacaoDias:
    def test_aceita_nome_completo_sem_acento(self):
        assert normalizar_dia_da_semana("segunda") == 0
        assert normalizar_dia_da_semana("terca") == 1
        assert normalizar_dia_da_semana("quarta") == 2
        assert normalizar_dia_da_semana("quinta") == 3
        assert normalizar_dia_da_semana("sexta") == 4
        assert normalizar_dia_da_semana("sabado") == 5
        assert normalizar_dia_da_semana("domingo") == 6

    def test_aceita_acentos(self):
        assert normalizar_dia_da_semana("terça") == 1
        assert normalizar_dia_da_semana("sábado") == 5

    def test_aceita_capitalizacao_variada(self):
        assert normalizar_dia_da_semana("Segunda") == 0
        assert normalizar_dia_da_semana("TERÇA") == 1
        assert normalizar_dia_da_semana("Sábado") == 5

    def test_aceita_espacos_em_volta(self):
        assert normalizar_dia_da_semana("  segunda  ") == 0
        assert normalizar_dia_da_semana("\tquarta\n") == 2

    def test_aceita_abreviacoes_3_letras(self):
        assert normalizar_dia_da_semana("seg") == 0
        assert normalizar_dia_da_semana("ter") == 1
        assert normalizar_dia_da_semana("qua") == 2
        assert normalizar_dia_da_semana("qui") == 3
        assert normalizar_dia_da_semana("sex") == 4
        assert normalizar_dia_da_semana("sab") == 5
        assert normalizar_dia_da_semana("dom") == 6

    def test_aceita_forma_com_feira(self):
        assert normalizar_dia_da_semana("segunda-feira") == 0
        assert normalizar_dia_da_semana("Quinta-Feira") == 3
        assert normalizar_dia_da_semana("sexta feira") == 4

    def test_recusa_string_invalida(self):
        with pytest.raises(ValueError, match="não reconhecido"):
            normalizar_dia_da_semana("bla")

    def test_recusa_string_vazia(self):
        with pytest.raises(ValueError, match="não reconhecido"):
            normalizar_dia_da_semana("")

    def test_recusa_tipo_invalido(self):
        with pytest.raises(TypeError):
            normalizar_dia_da_semana(0)  # type: ignore[arg-type]


class TestNomeCanonico:
    def test_retorna_com_acento_quando_aplicavel(self):
        assert nome_canonico_do_weekday(0) == "segunda"
        assert nome_canonico_do_weekday(1) == "terça"
        assert nome_canonico_do_weekday(5) == "sábado"
        assert nome_canonico_do_weekday(6) == "domingo"

    def test_recusa_fora_de_intervalo(self):
        with pytest.raises(ValueError):
            nome_canonico_do_weekday(-1)
        with pytest.raises(ValueError):
            nome_canonico_do_weekday(7)


# --------------------------------------------------------------------------- #
# Geração de calendário — casos básicos                                        #
# --------------------------------------------------------------------------- #

class TestGerarCalendarioBasico:
    """Cenário-guia: plano de 4 semanas, 3 treinos por semana (2/4/6)."""

    def setup_method(self):
        # 2026-05-04 é uma SEGUNDA-feira (verificado via date.weekday()==0).
        self.data_inicio = date(2026, 5, 4)
        # +27 dias = 2026-05-31, um domingo. Plano de 4 semanas cheias.
        self.data_prova = date(2026, 5, 31)
        self.cal = gerar_calendario(
            data_inicio=self.data_inicio,
            data_prova=self.data_prova,
            dias_treino=["terça", "quinta", "sábado"],
        )

    def test_data_inicio_e_segunda(self):
        assert self.data_inicio.weekday() == 0

    def test_total_treinos_correto(self):
        # 4 semanas x 3 treinos = 12
        assert self.cal.total_treinos == 12

    def test_total_semanas_correto(self):
        assert self.cal.total_semanas == 4

    def test_apenas_dias_pedidos(self):
        weekdays_obtidos = {t.data.weekday() for t in self.cal.treinos}
        assert weekdays_obtidos == {1, 3, 5}  # terça, quinta, sábado

    def test_treinos_em_ordem_cronologica(self):
        datas = [t.data for t in self.cal.treinos]
        assert datas == sorted(datas)

    def test_nenhum_treino_antes_de_data_inicio(self):
        for t in self.cal.treinos:
            assert t.data >= self.data_inicio

    def test_nenhum_treino_depois_de_data_prova(self):
        for t in self.cal.treinos:
            assert t.data <= self.data_prova

    def test_dias_canonicos_ordenados(self):
        assert self.cal.dias_treino_canonicos == ("terça", "quinta", "sábado")

    def test_nomes_dos_dias_estao_corretos(self):
        nome_por_weekday = {1: "terça", 3: "quinta", 5: "sábado"}
        for t in self.cal.treinos:
            assert t.dia_semana == nome_por_weekday[t.data.weekday()]

    def test_numero_semana_comeca_em_1(self):
        assert self.cal.treinos[0].numero_semana == 1

    def test_numero_semana_incrementa_corretamente(self):
        # Cada semana deve ter numero_semana único e contíguo de 1..N.
        numeros = sorted({t.numero_semana for t in self.cal.treinos})
        assert numeros == [1, 2, 3, 4]


# --------------------------------------------------------------------------- #
# Casos de borda                                                                #
# --------------------------------------------------------------------------- #

class TestCasosDeBorda:
    def test_data_inicio_no_meio_da_semana(self):
        # Quarta-feira como data_inicio. Treino só na sexta.
        # Semana 1 contém só a sexta dessa primeira semana.
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 6),   # quarta
            data_prova=date(2026, 5, 22),   # sexta, +16 dias
            dias_treino=["sexta"],
        )
        # Sextas: 8/5, 15/5, 22/5 -> 3 treinos
        assert [t.data for t in cal.treinos] == [
            date(2026, 5, 8),
            date(2026, 5, 15),
            date(2026, 5, 22),
        ]
        # Numero da semana: 8/5 e a quarta caem na MESMA semana ISO
        # (segunda 4/5 a domingo 10/5). Logo semana 1.
        assert cal.treinos[0].numero_semana == 1
        assert cal.treinos[1].numero_semana == 2
        assert cal.treinos[2].numero_semana == 3

    def test_data_inicio_igual_data_prova_em_dia_de_treino(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 6),  # quarta
            data_prova=date(2026, 5, 6),
            dias_treino=["quarta"],
        )
        assert cal.total_treinos == 1
        assert cal.treinos[0].eh_dia_da_prova is True

    def test_data_inicio_igual_data_prova_em_dia_sem_treino(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 6),  # quarta
            data_prova=date(2026, 5, 6),
            dias_treino=["sábado"],
        )
        assert cal.total_treinos == 0
        assert cal.total_semanas == 0

    def test_data_prova_em_dia_de_treino_marca_flag(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),
            data_prova=date(2026, 5, 17),  # domingo
            dias_treino=["domingo"],
        )
        assert cal.treinos[-1].data == date(2026, 5, 17)
        assert cal.treinos[-1].eh_dia_da_prova is True

    def test_treino_apos_data_prova_nunca_aparece(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),
            data_prova=date(2026, 5, 7),  # quinta
            dias_treino=["sexta"],  # primeira sexta seria 8/5
        )
        assert cal.total_treinos == 0

    def test_dias_duplicados_sao_deduplicados(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),
            data_prova=date(2026, 5, 10),
            dias_treino=["terça", "Terça", "TER", "terca-feira"],
        )
        assert cal.dias_treino_canonicos == ("terça",)
        assert cal.total_treinos == 1

    def test_virada_de_ano(self):
        # 2026-12-28 é segunda. 2027-01-10 é domingo.
        cal = gerar_calendario(
            data_inicio=date(2026, 12, 28),
            data_prova=date(2027, 1, 10),
            dias_treino=["segunda"],
        )
        assert [t.data for t in cal.treinos] == [
            date(2026, 12, 28),
            date(2027, 1, 4),
        ]
        assert cal.treinos[0].numero_semana == 1
        assert cal.treinos[1].numero_semana == 2

    def test_todos_os_dias_da_semana(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),  # segunda
            data_prova=date(2026, 5, 10),  # domingo
            dias_treino=[
                "segunda", "terça", "quarta", "quinta",
                "sexta", "sábado", "domingo",
            ],
        )
        assert cal.total_treinos == 7
        assert cal.total_semanas == 1


# --------------------------------------------------------------------------- #
# Validações de input                                                          #
# --------------------------------------------------------------------------- #

class TestValidacoes:
    def test_data_inicio_apos_data_prova(self):
        with pytest.raises(ValueError, match="posterior"):
            gerar_calendario(
                data_inicio=date(2026, 5, 10),
                data_prova=date(2026, 5, 4),
                dias_treino=["segunda"],
            )

    def test_dias_treino_vazio(self):
        with pytest.raises(ValueError, match="vazio"):
            gerar_calendario(
                data_inicio=date(2026, 5, 4),
                data_prova=date(2026, 5, 10),
                dias_treino=[],
            )

    def test_dia_invalido_propaga(self):
        with pytest.raises(ValueError, match="não reconhecido"):
            gerar_calendario(
                data_inicio=date(2026, 5, 4),
                data_prova=date(2026, 5, 10),
                dias_treino=["segunda", "blargh"],
            )

    def test_recusa_datetime_em_data_inicio(self):
        from datetime import datetime as _dt
        with pytest.raises(TypeError, match="date"):
            gerar_calendario(
                data_inicio=_dt(2026, 5, 4, 10, 0),  # type: ignore[arg-type]
                data_prova=date(2026, 5, 10),
                dias_treino=["segunda"],
            )


# --------------------------------------------------------------------------- #
# Estrutura das semanas                                                        #
# --------------------------------------------------------------------------- #

class TestEstruturaSemanas:
    def test_segunda_e_domingo_da_semana(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),
            data_prova=date(2026, 5, 17),
            dias_treino=["quarta"],
        )
        assert cal.semanas[0].segunda == date(2026, 5, 4)
        assert cal.semanas[0].domingo == date(2026, 5, 10)
        assert cal.semanas[1].segunda == date(2026, 5, 11)
        assert cal.semanas[1].domingo == date(2026, 5, 17)

    def test_treinos_da_semana_estao_dentro_do_intervalo(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),
            data_prova=date(2026, 6, 7),
            dias_treino=["segunda", "quarta", "sexta"],
        )
        for sem in cal.semanas:
            for t in sem.treinos:
                assert sem.segunda <= t.data <= sem.domingo
                assert t.numero_semana == sem.numero

    def test_imutabilidade_das_estruturas(self):
        cal = gerar_calendario(
            data_inicio=date(2026, 5, 4),
            data_prova=date(2026, 5, 10),
            dias_treino=["quarta"],
        )
        # frozen dataclass não permite atribuição
        with pytest.raises(Exception):
            cal.treinos[0].data = date(2099, 1, 1)  # type: ignore[misc]
