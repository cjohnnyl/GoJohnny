#!/usr/bin/env python3
"""Validar que a correção UUID foi aplicada corretamente."""

import os
import re

print("=" * 70)
print("VALIDACAO: Correcao de UUID no Schema e Service")
print("=" * 70)

checks = []

def check(nome, condicao):
    """Registrar um check."""
    status = "PASS" if condicao else "FAIL"
    checks.append((status, nome))
    print(f"  [{status}] {nome}")

# =====================================================================
# PARTE 1: Validar Schema
# =====================================================================
print("\n[PARTE 1] Validar app/schemas/atleta_memoria.py")
print("-" * 70)

schema_path = "app/schemas/atleta_memoria.py"
with open(schema_path, 'r', encoding='utf-8') as f:
    schema_content = f.read()

check("Importa UUID", "from uuid import UUID" in schema_content)
check("Importa ConfigDict", "from pydantic import" in schema_content and "ConfigDict" in schema_content)
check("AtletaMemoriaRead usa UUID para id", "class AtletaMemoriaRead" in schema_content and "id: UUID" in schema_content)
check("AtletaMemoriaRead usa UUID para atleta_id", "atleta_id: UUID" in schema_content)
check("AtletaMemoriaRead usa ConfigDict", "model_config = ConfigDict(from_attributes=True)" in schema_content)
check("ResumoSemanalRead usa UUID para id", "class ResumoSemanalRead" in schema_content and "id: UUID" in schema_content)
check("ResumoSemanalRead usa UUID para atleta_id em ResumoSemanalRead",
      schema_content.count("atleta_id: UUID") >= 2)

# =====================================================================
# PARTE 2: Validar Service
# =====================================================================
print("\n[PARTE 2] Validar app/services/memoria_service.py")
print("-" * 70)

service_path = "app/services/memoria_service.py"
with open(service_path, 'r', encoding='utf-8') as f:
    service_content = f.read()

# Contar quantas vezes model_dump(mode="json") aparece
mode_json_count = len(re.findall(r'model_dump\(mode="json"\)', service_content))
check(f"Tem {mode_json_count} chamadas de model_dump(mode='json')", mode_json_count == 10)

# Verificar se não há mais model_dump() sem mode
model_dump_sem_mode = len(re.findall(r'model_dump\(\)', service_content))
check(f"Nao ha model_dump() sem mode (encontrados: {model_dump_sem_mode})", model_dump_sem_mode == 0)

# =====================================================================
# RESUMO
# =====================================================================
print("\n" + "=" * 70)
passed = sum(1 for status, _ in checks if status == "PASS")
failed = sum(1 for status, _ in checks if status == "FAIL")

print(f"TOTAL: {passed}/{len(checks)} checks passaram")

if failed == 0:
    print("\nTODAS AS VALIDACOES PASSARAM!")
    print("\nCorrecoes aplicadas com sucesso:")
    print("  1. Schema agora usa UUID para id e atleta_id")
    print("  2. Schema usa ConfigDict(from_attributes=True)")
    print("  3. Service usa mode='json' em todas as chamadas model_dump()")
    print("  4. UUID sera convertido para string automaticamente na resposta JSON")
    exit(0)
else:
    print(f"\n{failed} validacoes falharam!")
    exit(1)
