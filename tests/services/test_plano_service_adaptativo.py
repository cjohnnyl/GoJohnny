"""
Testes de integração — lógica adaptativa de planos (novo ciclo, revisão, substituição).
Executar com: pytest tests/services/test_plano_service_adaptativo.py -v
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.atleta_memoria import AtletaMemoria
from app.models.plano_semanal import PlanoSemanal
from app.schemas.plano_semanal import (
    PlanoSemanalCreate,
    PlanoSemanalUpdate,
    SubstituirPlanoPayload,
)
from app.services.plano_service import (
    PlanoAtivoNaoEncontrado,
    SobrescritaProtegida,
    atualizar_plano_ativo,
    criar_plano,
    substituir_plano_ativo,
)


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def atleta(db_session: Session, make_apelido):
    """Atleta genérico para os testes."""
    a = Atleta(
        nome="Atleta Teste",
        apelido=make_apelido("plano"),
        objetivo="Correr 21k",
        nivel="intermediario",
        dias_treino=3,
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


def _plano_create(apelido: str, semana: date = date(2026, 5, 5), **kwargs) -> PlanoSemanalCreate:
    return PlanoSemanalCreate(
        apelido=apelido,
        semana_inicio=semana,
        objetivo_semana="Consistência",
        volume_planejado_km=20,
        status="ativo",
        plano={"treinos": [{"dia": "quarta", "tipo": "moderado"}]},
        dias_treino_json=["quarta", "domingo"],
        versao_estrutura=2,
        **kwargs,
    )


def _plano_db(db: Session, atleta: Atleta, status: str = "ativo", semana: date = date(2026, 5, 5)) -> PlanoSemanal:
    """Cria um PlanoSemanal diretamente no banco (sem passar pelo service)."""
    p = PlanoSemanal(
        atleta_id=atleta.id,
        semana_inicio=semana,
        objetivo_semana="Plano inicial",
        volume_planejado_km=18,
        status=status,
        plano={"treinos": []},
        versao_estrutura=1,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ---------------------------------------------------------------------------
# Teste 1: Criar plano quando não existe plano ativo
# ---------------------------------------------------------------------------

class TestCriarPlanoSemPlanoAtivo:
    def test_criar_plano_sem_plano_ativo(self, db_session: Session, atleta: Atleta):
        dados = _plano_create(atleta.apelido)
        plano = criar_plano(db_session, atleta, dados)

        assert plano.status == "ativo"
        assert plano.semana_inicio == date(2026, 5, 5)
        assert plano.atleta_id == atleta.id


# ---------------------------------------------------------------------------
# Teste 2 e 3: novo_ciclo=True substitui o plano anterior
# ---------------------------------------------------------------------------

class TestNovoCicloSubstituiPlano:
    def test_criar_plano_com_novo_ciclo_true(self, db_session: Session, atleta: Atleta):
        """POST com novo_ciclo=True cria o novo plano."""
        _plano_db(db_session, atleta, semana=date(2026, 4, 28))

        dados = _plano_create(atleta.apelido, semana=date(2026, 5, 5), novo_ciclo=True)
        novo = criar_plano(db_session, atleta, dados)

        assert novo.status == "ativo"
        assert novo.semana_inicio == date(2026, 5, 5)

    def test_plano_anterior_vira_substituido(self, db_session: Session, atleta: Atleta):
        """O plano anterior deve ficar com status='substituido', não apagado."""
        anterior = _plano_db(db_session, atleta, semana=date(2026, 4, 28))
        anterior_id = anterior.id

        dados = _plano_create(atleta.apelido, semana=date(2026, 5, 5), novo_ciclo=True)
        criar_plano(db_session, atleta, dados)

        db_session.expire_all()
        plano_anterior = db_session.query(PlanoSemanal).filter_by(id=anterior_id).first()
        assert plano_anterior is not None
        assert plano_anterior.status == "substituido"


# ---------------------------------------------------------------------------
# Teste 4: Só um plano ativo por atleta
# ---------------------------------------------------------------------------

class TestApenasUmPlanoAtivoPorAtleta:
    def test_apenas_um_plano_ativo_apos_novo_ciclo(self, db_session: Session, atleta: Atleta):
        _plano_db(db_session, atleta, semana=date(2026, 4, 21))
        _plano_db(db_session, atleta, semana=date(2026, 4, 28))

        # Primeiro novo_ciclo arquiva o mais recente; o mais antigo (já "ativo") fica como está
        # Mas criar_plano procura por status='ativo' e arquiva UM de cada vez
        # Se houver dois ativos (situação inconsistente), criamos um terceiro com novo_ciclo
        dados = _plano_create(atleta.apelido, semana=date(2026, 5, 5), novo_ciclo=True)
        criar_plano(db_session, atleta, dados)

        db_session.expire_all()
        ativos = (
            db_session.query(PlanoSemanal)
            .filter_by(atleta_id=atleta.id, status="ativo")
            .all()
        )
        assert len(ativos) == 1
        assert ativos[0].semana_inicio == date(2026, 5, 5)


# ---------------------------------------------------------------------------
# Teste 5: sem novo_ciclo levanta SobrescritaProtegida
# ---------------------------------------------------------------------------

class TestSobrescritaProtegida:
    def test_criar_sem_novo_ciclo_levanta_sobrescrita(self, db_session: Session, atleta: Atleta):
        _plano_db(db_session, atleta)

        dados = _plano_create(atleta.apelido, semana=date(2026, 5, 12), novo_ciclo=False)

        with pytest.raises(SobrescritaProtegida) as exc_info:
            criar_plano(db_session, atleta, dados)

        assert exc_info.value.plano_atual_id is not None


# ---------------------------------------------------------------------------
# Teste 6: PATCH atualiza campos do plano ativo
# ---------------------------------------------------------------------------

class TestAtualizarPlanoAtivoPatch:
    def test_patch_atualiza_objetivo_semana(self, db_session: Session, atleta: Atleta):
        _plano_db(db_session, atleta)

        update = PlanoSemanalUpdate(
            objetivo_semana="Reduzir impacto e preservar consistência",
            salvar_memoria=False,
        )
        plano = atualizar_plano_ativo(db_session, atleta, update)

        assert plano.objetivo_semana == "Reduzir impacto e preservar consistência"
        assert plano.status == "ativo"

    def test_patch_preserva_campos_nao_enviados(self, db_session: Session, atleta: Atleta):
        """Campos não enviados no PATCH devem permanecer inalterados."""
        original = _plano_db(db_session, atleta)
        volume_original = original.volume_planejado_km

        update = PlanoSemanalUpdate(
            objetivo_semana="Novo objetivo",
            salvar_memoria=False,
        )
        plano = atualizar_plano_ativo(db_session, atleta, update)

        assert plano.volume_planejado_km == volume_original


# ---------------------------------------------------------------------------
# Teste 7: PATCH sem plano ativo levanta PlanoAtivoNaoEncontrado
# ---------------------------------------------------------------------------

class TestAtualizarSemPlanoAtivo:
    def test_atualizar_sem_plano_ativo_levanta(self, db_session: Session, atleta: Atleta):
        update = PlanoSemanalUpdate(objetivo_semana="Algo")

        with pytest.raises(PlanoAtivoNaoEncontrado):
            atualizar_plano_ativo(db_session, atleta, update)


# ---------------------------------------------------------------------------
# Teste 8: POST /substituir-atual troca plano e salva memória
# ---------------------------------------------------------------------------

class TestSubstituirPlanoAtivo:
    def test_substituir_plano_ativo(self, db_session: Session, atleta: Atleta):
        anterior = _plano_db(db_session, atleta, semana=date(2026, 4, 28))
        anterior_id = anterior.id

        payload = SubstituirPlanoPayload(
            motivo_substituicao="Atleta relatou dor e pediu redução de carga.",
            semana_inicio=date(2026, 5, 5),
            objetivo_semana="Reduzir carga e recuperar",
            volume_planejado_km=14,
            dias_treino_json=["quarta", "domingo"],
            versao_estrutura=2,
            plano={"treinos": [{"dia": "quarta", "tipo": "leve"}]},
        )

        resultado = substituir_plano_ativo(db_session, atleta, payload)

        assert resultado["novo_plano"].status == "ativo"
        assert resultado["novo_plano"].semana_inicio == date(2026, 5, 5)

        db_session.expire_all()
        plano_anterior = db_session.query(PlanoSemanal).filter_by(id=anterior_id).first()
        assert plano_anterior.status == "substituido"

    def test_substituir_salva_memoria_automaticamente(self, db_session: Session, atleta: Atleta):
        _plano_db(db_session, atleta)

        payload = SubstituirPlanoPayload(
            motivo_substituicao="Dor no joelho. Reduzir volume.",
            semana_inicio=date(2026, 5, 5),
            plano={"treinos": []},
        )

        resultado = substituir_plano_ativo(db_session, atleta, payload)

        assert resultado["memoria_salva"] is not None
        assert resultado["memoria_salva"]["status"] in ("criado", "atualizado")

        memorias = (
            db_session.query(AtletaMemoria)
            .filter_by(atleta_id=atleta.id, tipo="decisao_treinador")
            .all()
        )
        assert len(memorias) >= 1
        assert "joelho" in memorias[0].valor_texto.lower()


# ---------------------------------------------------------------------------
# Teste 9: GET /atual retorna o plano correto após novo ciclo
# ---------------------------------------------------------------------------

class TestGetPlanoAtualRetornaCorreto:
    def test_get_plano_atual_retorna_novo_plano(self, db_session: Session, atleta: Atleta):
        """Após novo_ciclo, o plano retornado deve ser o mais recente ativo."""
        _plano_db(db_session, atleta, semana=date(2026, 4, 28))

        dados = _plano_create(
            atleta.apelido,
            semana=date(2026, 5, 5),
            novo_ciclo=True,
            objetivo_semana="Retomar consistência com controle de ritmo",
        )
        criar_plano(db_session, atleta, dados)
        db_session.commit()

        plano_ativo = (
            db_session.query(PlanoSemanal)
            .filter_by(atleta_id=atleta.id, status="ativo")
            .order_by(PlanoSemanal.semana_inicio.desc())
            .first()
        )

        assert plano_ativo is not None
        assert plano_ativo.semana_inicio == date(2026, 5, 5)
        assert plano_ativo.objetivo_semana == "Retomar consistência com controle de ritmo"
