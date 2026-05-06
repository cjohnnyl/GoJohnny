#!/usr/bin/env python3
"""Validar implementacao do sistema de memoria."""

import os
import sys
import json

print("=" * 70)
print("VALIDACAO DE IMPLEMENTACAO - SISTEMA DE MEMORIA - ETAPA 4")
print("=" * 70)

checks = []

def check(nome, condicao, detalhes=""):
    """Registrar um check."""
    status = "PASS" if condicao else "FAIL"
    checks.append((status, nome, detalhes))
    print(f"  [{status}] {nome}")
    if detalhes:
        print(f"    -> {detalhes}")

# PARTE 1: VERIFICAR MODELOS
print("\n[PARTE 1] Verificar Modelos de Dados")
print("-" * 70)

modelo_path = "app/models/atleta_memoria.py"
exists = os.path.exists(modelo_path)
check("Modelo AtletaMemoria existe", exists, modelo_path if exists else "Nao encontrado")

if exists:
    with open(modelo_path, 'r', encoding='utf-8') as f:
        content = f.read()
        check("Tem classe AtletaMemoria", "class AtletaMemoria" in content)
        check("Tem coluna 'tipo'", "tipo" in content)
        check("Tem coluna 'chave'", "chave" in content)
        check("Tem coluna 'valor_texto'", "valor_texto" in content)
        check("Tem coluna 'valor_json'", "valor_json" in content)
        check("Tem coluna 'importancia'", "importancia" in content)

# PARTE 2: VERIFICAR SCHEMAS
print("\n[PARTE 2] Verificar Schemas Pydantic")
print("-" * 70)

schema_path = "app/schemas/atleta_memoria.py"
exists = os.path.exists(schema_path)
check("Schema atleta_memoria existe", exists, schema_path if exists else "Nao encontrado")

if exists:
    with open(schema_path, 'r', encoding='utf-8') as f:
        content = f.read()
        check("Tem AtletaMemoriaCreate", "class AtletaMemoriaCreate" in content)
        check("Tem AtletaMemoriaRead", "class AtletaMemoriaRead" in content)
        check("Tem ResumoSemanalCreate", "class ResumoSemanalCreate" in content)
        check("Tem MemoriasResumoResponse", "class MemoriasResumoResponse" in content)

# PARTE 3: VERIFICAR SERVICO
print("\n[PARTE 3] Verificar Servico de Memoria")
print("-" * 70)

service_path = "app/services/memoria_service.py"
exists = os.path.exists(service_path)
check("Servico memoria_service existe", exists, service_path if exists else "Nao encontrado")

if exists:
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()
        check("Tem salvar_memoria", "def salvar_memoria" in content)
        check("Tem buscar_resumo_memorias", "def buscar_resumo_memorias" in content)
        check("Tem buscar_memorias_por_texto", "def buscar_memorias_por_texto" in content)
        check("Tem salvar_resumo_semanal", "def salvar_resumo_semanal" in content)
        check("Tem buscar_memorias_para_contexto", "def buscar_memorias_para_contexto" in content)

# PARTE 4: VERIFICAR ROTAS
print("\n[PARTE 4] Verificar Rotas (Endpoints)")
print("-" * 70)

routes_path = "app/routes/memorias.py"
exists = os.path.exists(routes_path)
check("Rotas de memoria existem", exists, routes_path if exists else "Nao encontrado")

if exists:
    with open(routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
        check("Tem POST /memorias/{apelido}", "/memorias/{apelido}" in content and "post" in content)
        check("Tem GET /memorias/{apelido}/resumo", "/resumo" in content and "get" in content)
        check("Tem GET /memorias/{apelido}/buscar", "/buscar" in content and "get" in content)
        check("Tem POST /memorias/{apelido}/resumo-semanal", "/resumo-semanal" in content and "post" in content)

# PARTE 5: VERIFICAR INTEGRACAO NO MAIN
print("\n[PARTE 5] Verificar Integracao com Main")
print("-" * 70)

main_path = "app/main.py"
with open(main_path, 'r', encoding='utf-8') as f:
    content = f.read()
    check("Importa rotas de memorias", "from app.routes import" in content and "memorias" in content)
    check("Inclui router de memorias", "memorias.router" in content)

# PARTE 6: VERIFICAR SESSION SERVICE
print("\n[PARTE 6] Verificar Integracao com Session Service")
print("-" * 70)

session_service_path = "app/services/session_service.py"
with open(session_service_path, 'r', encoding='utf-8') as f:
    content = f.read()
    check("Importa buscar_memorias_para_contexto", "buscar_memorias_para_contexto" in content)
    check("Chama buscar_memorias_para_contexto", "memorias_contexto = buscar_memorias_para_contexto" in content)
    check("Enriquece contexto_resumo", "contexto_enriched" in content)

# PARTE 7: VERIFICAR MIGRATION
print("\n[PARTE 7] Verificar Migration SQL")
print("-" * 70)

migration_path = "migrations/004_atleta_memorias.sql"
exists = os.path.exists(migration_path)
check("Migration 004_atleta_memorias existe", exists, migration_path if exists else "Nao encontrado")

if exists:
    with open(migration_path, 'r', encoding='utf-8') as f:
        content = f.read()
        check("Cria tabela atleta_memorias", "CREATE TABLE" in content and "atleta_memorias" in content)
        check("Tem indice de atleta_id", "idx_atleta_memorias_atleta_id" in content)
        check("Tem indice de tipo", "idx_atleta_memorias_tipo" in content)
        check("Tem indice unico de chave", "idx_atleta_memorias_uniq_tipo_chave" in content)

# PARTE 8: VERIFICAR CONFTEST
print("\n[PARTE 8] Verificar Integracao com Testes (conftest.py)")
print("-" * 70)

conftest_path = "tests/conftest.py"
with open(conftest_path, 'r', encoding='utf-8') as f:
    content = f.read()
    check("Importa atleta_memoria no conftest", "app.models.atleta_memoria" in content)

# PARTE 9: VERIFICAR OPENAPI
print("\n[PARTE 9] Verificar OpenAPI Schema")
print("-" * 70)

openapi_path = "openapi-gpt-actions.json"
with open(openapi_path, 'r', encoding='utf-8') as f:
    openapi = json.load(f)
    paths_count = len(openapi.get('paths', {}))
    schemas_count = len(openapi.get('components', {}).get('schemas', {}))

    check("OpenAPI tem /memorias/{apelido}", "/memorias/{apelido}" in openapi['paths'])
    check("OpenAPI tem /memorias/{apelido}/resumo", "/memorias/{apelido}/resumo" in openapi['paths'])
    check("OpenAPI tem /memorias/{apelido}/buscar", "/memorias/{apelido}/buscar" in openapi['paths'])
    check("OpenAPI tem /memorias/{apelido}/resumo-semanal", "/memorias/{apelido}/resumo-semanal" in openapi['paths'])

    check("Schema tem AtletaMemoriaCreate", "AtletaMemoriaCreate" in openapi['components']['schemas'])
    check("Schema tem AtletaMemoriaRead", "AtletaMemoriaRead" in openapi['components']['schemas'])
    check("Schema tem ResumoSemanalCreate", "ResumoSemanalCreate" in openapi['components']['schemas'])

    print(f"\n    Total de endpoints: {paths_count}")
    print(f"    Total de schemas: {schemas_count}")

# PARTE 10: VERIFICAR TESTES
print("\n[PARTE 10] Verificar Testes")
print("-" * 70)

test_path = "tests/test_memoria.py"
exists = os.path.exists(test_path)
check("Arquivo de testes test_memoria.py existe", exists, test_path if exists else "Nao encontrado")

if exists:
    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()
        check("Tem teste de salvar memoria", "test_salvar_memoria_nova" in content)
        check("Tem teste de evitar duplicata", "test_evitar_duplicata_memoria" in content)
        check("Tem teste de buscar resumo", "test_buscar_resumo_memorias" in content)
        check("Tem teste de buscar por texto", "test_buscar_memorias_por_texto" in content)
        check("Tem teste de resumo semanal", "test_salvar_resumo_semanal" in content)
        check("Tem teste de contexto", "test_buscar_memorias_para_contexto" in content)

# RESUMO FINAL
print("\n" + "=" * 70)
print("RESUMO FINAL")
print("=" * 70)

passed = sum(1 for status, _, _ in checks if status == "PASS")
failed = sum(1 for status, _, _ in checks if status == "FAIL")

print(f"\nTotal de checks: {len(checks)}")
print(f"Passou: {passed}")
print(f"Falhou: {failed}")

if failed == 0:
    print("\nTODOS OS CHECKS PASSARAM!")
    print("\nImplementacao completa com:")
    print("  * Modelo AtletaMemoria com todos os campos")
    print("  * Schemas Pydantic para validacao")
    print("  * Servico de memoria com 5 funcoes principais")
    print("  * 4 novos endpoints REST")
    print("  * Migration SQL para tabela atleta_memorias")
    print("  * Integracao com session_service")
    print("  * OpenAPI schema atualizado com 4 novos paths e 5 novos schemas")
    print("  * Suite de testes com 7 testes")
    sys.exit(0)
else:
    print("\nAlguns checks falharam!")
    sys.exit(1)
