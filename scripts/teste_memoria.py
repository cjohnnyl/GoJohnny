#!/usr/bin/env python3
"""
Script de teste para validar sistema de memória.
Executar com: python scripts/teste_memoria.py
"""

import os
import sys
from datetime import date

# Adicionar app ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.atleta import Atleta
from app.models.atleta_memoria import AtletaMemoria
from app.services.memoria_service import (
    salvar_memoria,
    buscar_resumo_memorias,
    buscar_memorias_por_texto,
    salvar_resumo_semanal,
)
from app.schemas.atleta_memoria import (
    AtletaMemoriaCreate,
    ResumoSemanalCreate,
)

# Usar banco de teste
DATABASE_URL = "sqlite:///./test_memoria.db"
engine = create_engine(DATABASE_URL)

# Importar todos os modelos
import app.models.atleta_memoria

# Criar tabelas
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("=" * 60)
print("TESTE SISTEMA DE MEMÓRIA - ETAPA 4")
print("=" * 60)

try:
    # TESTE 1: Criar atleta johnny
    print("\n[TESTE 1] Criar atleta 'johnny'...")
    atleta = Atleta(
        nome="Johnny Test",
        apelido="johnny",
        objetivo="Correr 21k em agosto",
        nivel="intermediario",
        dias_treino=3,
    )
    db.add(atleta)
    db.commit()
    db.refresh(atleta)
    print(f"  ✓ Atleta criado: {atleta.apelido} (ID: {atleta.id})")

    # TESTE 2: Salvar memória de preferência
    print("\n[TESTE 2] Salvar memória de preferência...")
    mem1_data = AtletaMemoriaCreate(
        tipo="preferencia",
        chave="dias_treino_preferidos",
        valor_texto="Quarta, sexta e domingo",
        origem="conversa",
        importancia=4,
        confianca=1.0,
    )
    resultado1 = salvar_memoria(db, str(atleta.id), mem1_data)
    print(f"  ✓ Memória salva: {resultado1['status']}")
    print(f"    ID: {resultado1['id']}")

    # TESTE 3: Salvar memória de orientação
    print("\n[TESTE 3] Salvar memória de orientação do treinador...")
    mem2_data = AtletaMemoriaCreate(
        tipo="orientacao_treinador",
        chave="não_acelerar_regenerativo",
        valor_texto="Evitar acelerar em treinos regenerativos. Manter ritmo controlado.",
        origem="conversa",
        importancia=5,
        confianca=1.0,
    )
    resultado2 = salvar_memoria(db, str(atleta.id), mem2_data)
    print(f"  ✓ Orientação salva: {resultado2['status']}")

    # TESTE 4: Buscar resumo de memórias
    print("\n[TESTE 4] Buscar resumo de memórias...")
    memorias = buscar_resumo_memorias(db, str(atleta.id), limite=20)
    print(f"  ✓ Total de memórias: {len(memorias)}")
    for m in memorias:
        print(f"    - [{m['tipo']}] {m['chave']} (importância: {m['importancia']})")

    # TESTE 5: Buscar memórias por texto
    print("\n[TESTE 5] Buscar memórias por texto: 'regenerativo'...")
    resultados, total = buscar_memorias_por_texto(db, str(atleta.id), "regenerativo", 20)
    print(f"  ✓ Encontradas {total} memórias")
    for m in resultados:
        print(f"    - {m['valor_texto']}")

    # TESTE 6: Salvar resumo semanal
    print("\n[TESTE 6] Salvar resumo semanal...")
    resumo_data = ResumoSemanalCreate(
        semana_inicio=date(2026, 4, 28),
        resumo="Semana regenerativa pós-21k. Atleta completou dois treinos leves.",
        aderencia="normal",
        pontos_positivos=["Cumpriu os regenerativos", "Não forçou volume"],
        pontos_atencao=["Cansaço pós-prova", "Evitar acelerar em treino leve"],
        decisoes_treinador=["Manter próxima semana com 3 treinos: qualidade leve, regenerativo e longo controlado"],
        proximo_foco="Retomar consistência sem agressividade",
    )
    resultado6 = salvar_resumo_semanal(db, str(atleta.id), resumo_data)
    print(f"  ✓ Resumo salvo: {resultado6['status']}")
    print(f"    ID: {resultado6['id']}")

    # TESTE 7: Verificar memórias no banco
    print("\n[TESTE 7] Verificar memórias no banco...")
    total_memorias = db.query(AtletaMemoria).filter(
        AtletaMemoria.atleta_id == atleta.id
    ).count()
    print(f"  ✓ Total de memórias no banco: {total_memorias}")

    # TESTE 8: Simular busca de contexto para nova sessão
    print("\n[TESTE 8] Simular busca de contexto para nova sessão...")
    from app.services.memoria_service import buscar_memorias_para_contexto
    contexto = buscar_memorias_para_contexto(db, str(atleta.id))
    print(f"  ✓ Contexto para nova sessão:")
    print(f"    - Última semana: {'SIM' if contexto['ultima_semana'] else 'NÃO'}")
    print(f"    - Alertas do treinador: {len(contexto['alertas_treinador'])}")
    print(f"    - Preferências: {len(contexto['preferencias'])}")
    print(f"    - Objetivo: {'SIM' if contexto['objetivo'] else 'NÃO'}")

    print("\n" + "=" * 60)
    print("TODOS OS TESTES PASSARAM COM SUCESSO!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERRO] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    db.close()
