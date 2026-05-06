#!/usr/bin/env python3
"""Testar endpoints de memória e sessao com dados reais."""

import sys
sys.path.insert(0, '/c/Projetos/gojohnny')

from datetime import date
from fastapi.testclient import TestClient

print("=" * 70)
print("TESTE: Endpoints de Memoria e Sessao")
print("=" * 70)

try:
    # Importar a app
    from app.main import app
    from tests.conftest import setup_database, teardown_database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import atleta, atleta_memoria, plano_semanal
    from app.models.base import Base

    # Setup test database
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from app.core.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    print("\n[TESTE 1] POST /sessao/iniciar - usuario novo")
    print("-" * 70)
    response = client.post("/sessao/iniciar", json={"apelido": "novo_atleta"})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Response contém status: {data.get('status')}")
        print(f"[OK] contexto_resumo existe: {'contexto_resumo' in data}")
        if 'contexto_resumo' in data:
            ctx = data['contexto_resumo']
            print(f"[OK] memorias_relevantes: {len(ctx.get('memorias_relevantes', []))} items")
            print(f"[OK] ultima_semana: {ctx.get('ultima_semana')}")
    else:
        print(f"[FAIL] Status {response.status_code}: {response.text}")

    print("\n[TESTE 2] POST /memorias/novo_atleta - salvar memoria")
    print("-" * 70)
    # Primeiro criar um atleta
    atleta_response = client.post("/atletas", json={
        "nome": "Novo Atleta",
        "apelido": "novo_atleta",
        "idade": 25,
        "genero": "M",
        "historia_breve": "Um novo atleta",
    }, headers={"x-api-key": "test-key"})

    print(f"Atleta criado: {atleta_response.status_code}")

    # Agora salvar uma memoria
    memoria_response = client.post("/memorias/novo_atleta",
        json={
            "tipo": "preferencia",
            "chave": "dias_treino",
            "valor_texto": "Quarta, sexta e domingo",
            "origem": "conversa",
            "importancia": 4,
            "confianca": 1.0,
        },
        headers={"x-api-key": "test-key"}
    )
    print(f"Memoria salva: {memoria_response.status_code}")
    if memoria_response.status_code in [200, 201]:
        print("[OK] Memoria salva corretamente")
    else:
        print(f"[FAIL] Status {memoria_response.status_code}: {memoria_response.text}")

    print("\n[TESTE 3] POST /sessao/iniciar - usuario com memoria salva")
    print("-" * 70)
    response = client.post("/sessao/iniciar", json={"apelido": "novo_atleta"})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Response valido com status: {data.get('status')}")
        if 'contexto_resumo' in data:
            ctx = data['contexto_resumo']
            print(f"[OK] contexto_resumo.preferencias: {len(ctx.get('preferencias', []))} items")
    else:
        print(f"[FAIL] Status {response.status_code}: {response.text}")

    print("\n[TESTE 4] POST /memorias/{apelido}/resumo-semanal")
    print("-" * 70)
    semanal_response = client.post("/memorias/novo_atleta/resumo-semanal",
        json={
            "semana_inicio": "2025-01-06",
            "resumo": "Semana muito produtiva",
            "aderencia": "excelente",
            "pontos_positivos": ["Treinou bem", "Alimentacao correta"],
            "pontos_atencao": ["Dormir pouco"],
            "decisoes_treinador": ["Aumentar volume de treino"],
            "proximo_foco": "Forca e resistencia"
        },
        headers={"x-api-key": "test-key"}
    )
    print(f"Status: {semanal_response.status_code}")
    if semanal_response.status_code in [200, 201]:
        print("[OK] Resumo semanal salvo corretamente")
        data = semanal_response.json()
        print(f"[OK] Response ID: {data.get('id')}")
    else:
        print(f"[FAIL] Status {semanal_response.status_code}: {semanal_response.text}")

    print("\n" + "=" * 70)
    print("TESTES CONCLUIDOS")
    print("=" * 70)

except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
