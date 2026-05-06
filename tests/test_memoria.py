"""
Testes do sistema de memória - Etapa 4.
Executar com: pytest tests/test_memoria.py -v
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.models.atleta import Atleta
from app.models.atleta_memoria import AtletaMemoria
from app.services.memoria_service import (
    salvar_memoria,
    buscar_resumo_memorias,
    buscar_memorias_por_texto,
    salvar_resumo_semanal,
    buscar_memorias_para_contexto,
)
from app.schemas.atleta_memoria import (
    AtletaMemoriaCreate,
    ResumoSemanalCreate,
)


@pytest.fixture
def johnny(db_session: Session):
    """Criar atleta johnny para testes."""
    atleta = Atleta(
        nome="Johnny Test",
        apelido="johnny",
        objetivo="Correr 21k em agosto",
        nivel="intermediario",
        dias_treino=3,
    )
    db_session.add(atleta)
    db_session.commit()
    db_session.refresh(atleta)
    return atleta


class TestMemoria:
    """Testes do sistema de memória."""

    def test_salvar_memoria_nova(self, db_session: Session, johnny: Atleta):
        """TESTE 1: Salvar memória nova."""
        mem_data = AtletaMemoriaCreate(
            tipo="preferencia",
            chave="dias_treino_preferidos",
            valor_texto="Quarta, sexta e domingo",
            origem="conversa",
            importancia=4,
            confianca=1.0,
        )

        resultado = salvar_memoria(db_session, str(johnny.id), mem_data)

        assert resultado["status"] == "criado"
        assert "id" in resultado
        assert resultado["memoria"]["tipo"] == "preferencia"
        assert resultado["memoria"]["valor_texto"] == "Quarta, sexta e domingo"

    def test_evitar_duplicata_memoria(self, db_session: Session, johnny: Atleta):
        """TESTE 2: Evitar duplicata idêntica."""
        mem_data = AtletaMemoriaCreate(
            tipo="preferencia",
            chave="dias_treino_preferidos",
            valor_texto="Quarta, sexta e domingo",
            origem="conversa",
            importancia=4,
            confianca=1.0,
        )

        # Primeira salvação
        resultado1 = salvar_memoria(db_session, str(johnny.id), mem_data)
        assert resultado1["status"] == "criado"

        # Segunda salvação com mesma chave
        resultado2 = salvar_memoria(db_session, str(johnny.id), mem_data)
        assert resultado2["status"] == "atualizado"
        assert resultado2["id"] == resultado1["id"]

    def test_buscar_resumo_memorias(self, db_session: Session, johnny: Atleta):
        """TESTE 3: Buscar resumo de memórias."""
        # Salvar duas memórias com importâncias diferentes
        mem1 = AtletaMemoriaCreate(
            tipo="preferencia",
            chave="dias_treino",
            valor_texto="Quarta, sexta e domingo",
            origem="conversa",
            importancia=2,
        )
        mem2 = AtletaMemoriaCreate(
            tipo="orientacao_treinador",
            chave="não_acelerar_regenerativo",
            valor_texto="Evitar acelerar em treinos regenerativos",
            origem="conversa",
            importancia=5,
        )

        salvar_memoria(db_session, str(johnny.id), mem1)
        salvar_memoria(db_session, str(johnny.id), mem2)

        # Buscar resumo
        memorias = buscar_resumo_memorias(db_session, str(johnny.id), limite=20)

        assert len(memorias) == 2
        # Deve estar ordenado por importância (desc)
        assert memorias[0]["importancia"] >= memorias[1]["importancia"]

    def test_buscar_memorias_por_texto(self, db_session: Session, johnny: Atleta):
        """TESTE 4: Buscar memórias por texto."""
        mem_data = AtletaMemoriaCreate(
            tipo="orientacao_treinador",
            chave="regenerativo",
            valor_texto="Evitar acelerar em treinos regenerativos",
            origem="conversa",
            importancia=5,
        )

        salvar_memoria(db_session, str(johnny.id), mem_data)

        # Buscar por "regenerativo"
        resultados, total = buscar_memorias_por_texto(
            db_session, str(johnny.id), "regenerativo", 20
        )

        assert total == 1
        assert len(resultados) == 1
        assert "regenerativo" in resultados[0]["valor_texto"].lower()

    def test_salvar_resumo_semanal(self, db_session: Session, johnny: Atleta):
        """TESTE 5: Salvar resumo semanal."""
        resumo_data = ResumoSemanalCreate(
            semana_inicio=date(2026, 4, 28),
            resumo="Semana regenerativa pós-21k",
            aderencia="normal",
            pontos_positivos=["Cumpriu os regenerativos"],
            pontos_atencao=["Cansaço pós-prova"],
            decisoes_treinador=["Manter próxima semana com 3 treinos"],
            proximo_foco="Retomar consistência",
        )

        resultado = salvar_resumo_semanal(db_session, str(johnny.id), resumo_data)

        assert resultado["status"] == "criado"
        assert resultado["memoria"]["tipo"] == "resumo_semanal"
        assert resultado["memoria"]["valor_json"]["aderencia"] == "normal"

    def test_buscar_memorias_para_contexto(self, db_session: Session, johnny: Atleta):
        """TESTE 6: Buscar memórias para contexto de nova sessão."""
        # Salvar várias memórias
        mem1 = AtletaMemoriaCreate(
            tipo="objetivo",
            chave="prova_principal",
            valor_texto="Correr 21k em agosto",
            origem="conversa",
            importancia=5,
        )
        mem2 = AtletaMemoriaCreate(
            tipo="orientacao_treinador",
            chave="seg_ritmo",
            valor_texto="Segurar ritmo em treinos leves",
            origem="conversa",
            importancia=5,
        )
        mem3 = AtletaMemoriaCreate(
            tipo="preferencia",
            chave="dias",
            valor_texto="Quarta, sexta e domingo",
            origem="conversa",
            importancia=3,
        )

        salvar_memoria(db_session, str(johnny.id), mem1)
        salvar_memoria(db_session, str(johnny.id), mem2)
        salvar_memoria(db_session, str(johnny.id), mem3)

        # Buscar contexto
        contexto = buscar_memorias_para_contexto(db_session, str(johnny.id))

        assert "alertas_treinador" in contexto
        assert "preferencias" in contexto
        assert "objetivo" in contexto
        assert len(contexto["alertas_treinador"]) > 0
        assert len(contexto["preferencias"]) > 0
        assert contexto["objetivo"] is not None

    def test_inativacao_memoria(self, db_session: Session, johnny: Atleta):
        """TESTE 7: Memória inativa não aparece em buscas."""
        mem_data = AtletaMemoriaCreate(
            tipo="preferencia",
            chave="teste",
            valor_texto="Teste",
            origem="conversa",
        )

        resultado = salvar_memoria(db_session, str(johnny.id), mem_data)
        mem_id = resultado["id"]

        # Desativar memória
        mem = db_session.query(AtletaMemoria).filter_by(id=mem_id).first()
        mem.ativo = False
        db_session.commit()

        # Buscar - não deve aparecer
        memorias = buscar_resumo_memorias(db_session, str(johnny.id))
        assert len(memorias) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
