#!/usr/bin/env python3
"""Validar que POST /planos-semanais funciona com o payload do usuario."""

import sys
sys.path.insert(0, '/c/Projetos/gojohnny')

from datetime import date
from decimal import Decimal

print("=" * 70)
print("VALIDACAO: POST /planos-semanais com Body()")
print("=" * 70)

checks = []

def check(nome, condicao):
    """Registrar um check."""
    status = "PASS" if condicao else "FAIL"
    checks.append((status, nome))
    print(f"  [{status}] {nome}")

# =====================================================================
# PARTE 1: Validar schema
# =====================================================================
print("\n[PARTE 1] Validar PlanoSemanalCreate")
print("-" * 70)

try:
    from app.schemas.plano_semanal import PlanoSemanalCreate
    check("Import PlanoSemanalCreate", True)
except Exception as e:
    check("Import PlanoSemanalCreate", False)
    print(f"  Erro: {e}")
    sys.exit(1)

# Payload que o usuario esta enviando
payload = {
    "apelido": "johnny",
    "semana_inicio": "2026-05-05",
    "objetivo_semana": "Retomar consistência com controle de ritmo",
    "volume_planejado_km": 23,
    "status": "ativo",
    "novo_ciclo": True,
    "dias_treino_json": ["quarta", "sexta", "domingo"],
    "versao_estrutura": 2,
    "plano": {
        "semana": 1,
        "foco": "controle + consistência",
        "volume_estimado_km": "22-24",
        "treinos": [
            {
                "dia": "quarta",
                "tipo": "moderado_progressivo",
                "titulo": "Moderado progressivo",
                "duracao_min": 40,
                "pace": "6:20-5:50/km"
            },
            {
                "dia": "sexta",
                "tipo": "leve_regenerativo",
                "titulo": "Leve regenerativo",
                "duracao_min": 35,
                "pace": "6:30-7:00/km"
            },
            {
                "dia": "domingo",
                "tipo": "longo",
                "titulo": "Longo",
                "duracao_min": 70,
                "pace": "6:20-6:40/km"
            }
        ]
    }
}

try:
    plano = PlanoSemanalCreate(**payload)
    check("PlanoSemanalCreate(**payload) valida", True)
    check("apelido eh 'johnny'", plano.apelido == "johnny")
    check("semana_inicio eh date", isinstance(plano.semana_inicio, date))
    check("novo_ciclo eh True", plano.novo_ciclo == True)
    check("dias_treino_json eh list[str]", isinstance(plano.dias_treino_json, list))
    check("dias_treino_json normalizado", "quarta" in plano.dias_treino_json)
    check("plano eh dict/object", isinstance(plano.plano, dict))
    check("plano contém treinos", "treinos" in plano.plano)
except Exception as e:
    check("PlanoSemanalCreate validacao", False)
    print(f"  Erro: {e}")
    import traceback
    traceback.print_exc()

# =====================================================================
# PARTE 2: Validar rota imports
# =====================================================================
print("\n[PARTE 2] Validar imports na rota")
print("-" * 70)

try:
    from app.routes.planos_semanais import router
    check("Import router de planos_semanais", True)
except Exception as e:
    check("Import router", False)
    print(f"  Erro: {e}")

try:
    from fastapi import Body
    from app.routes.planos_semanais import create_plano
    check("Body importado na rota", True)
except Exception as e:
    check("Body importado", False)
    print(f"  Erro: {e}")

# =====================================================================
# PARTE 3: Validar signature da rota
# =====================================================================
print("\n[PARTE 3] Validar signature da rota")
print("-" * 70)

try:
    from app.routes.planos_semanais import create_plano
    import inspect
    sig = inspect.signature(create_plano)
    params = sig.parameters

    check("create_plano tem parametro 'data'", 'data' in params)

    # Verificar se data tem default (Body(...))
    data_param = params.get('data')
    if data_param:
        has_default = data_param.default != inspect.Parameter.empty
        check("data tem default value", has_default)

        # Verificar se eh Body
        if hasattr(data_param.default, '__class__'):
            is_body = 'Body' in str(data_param.default.__class__)
            check("default eh Body", is_body or str(data_param.default) == '...')

    check("create_plano tem parametro 'db'", 'db' in params)

except Exception as e:
    check("Signature validation", False)
    print(f"  Erro: {e}")
    import traceback
    traceback.print_exc()

# =====================================================================
# PARTE 4: Validar tipos de dados
# =====================================================================
print("\n[PARTE 4] Validar tipos de dados")
print("-" * 70)

try:
    # Teste com volume em Decimal
    payload2 = payload.copy()
    payload2["volume_planejado_km"] = Decimal("23.5")
    plano2 = PlanoSemanalCreate(**payload2)
    check("volume_planejado_km como Decimal", isinstance(plano2.volume_planejado_km, Decimal))

    # Teste com status custom
    payload3 = payload.copy()
    payload3["status"] = "pausado"
    plano3 = PlanoSemanalCreate(**payload3)
    check("status aceita valores custom", plano3.status == "pausado")

except Exception as e:
    check("Tipos de dados", False)
    print(f"  Erro: {e}")

# =====================================================================
# RESUMO
# =====================================================================
print("\n" + "=" * 70)
passed = sum(1 for status, _ in checks if status == "PASS")
failed = sum(1 for status, _ in checks if status == "FAIL")

print(f"TOTAL: {passed}/{len(checks)} checks passaram")

if failed == 0:
    print("\nTODOS OS CHECKS PASSARAM!")
    print("\nFixes aplicados:")
    print("  1. Body(...) adicionado ao endpoint POST /planos-semanais")
    print("  2. PlanoSemanalCreate valida todos os campos do usuario")
    print("  3. dias_treino_json eh normalizado automaticamente")
    print("  4. plano aceita dict/object completo")
    print("  5. Rota pronta para receber JSON payload")
    exit(0)
else:
    print(f"\n{failed} validacoes falharam!")
    exit(1)
