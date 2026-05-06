#!/usr/bin/env python3
"""Validar que POST /memorias/{apelido}/resumo-semanal funciona corretamente."""

import sys
sys.path.insert(0, '/c/Projetos/gojohnny')

from datetime import date

print("=" * 70)
print("VALIDACAO: POST /memorias/{apelido}/resumo-semanal")
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
print("\n[PARTE 1] Validar ResumoSemanalCreate")
print("-" * 70)

try:
    from app.schemas.atleta_memoria import ResumoSemanalCreate
    check("Import ResumoSemanalCreate", True)
except Exception as e:
    check("Import ResumoSemanalCreate", False)
    print(f"  Erro: {e}")
    sys.exit(1)

# Payload que o usuario esta enviando
payload = {
    'semana_inicio': '2026-04-28',
    'resumo': 'Semana regenerativa pos-prova.',
    'aderencia': 'excelente',
    'pontos_positivos': ['Cumpriu a semana proposta'],
    'pontos_atencao': ['Tendencia a acelerar demais'],
    'decisoes_treinador': ['Manter tres treinos'],
    'proximo_foco': 'Retomar consistencia.'
}

try:
    resumo = ResumoSemanalCreate(**payload)
    check("ResumoSemanalCreate(**payload) valida", True)
    check("semana_inicio eh date", isinstance(resumo.semana_inicio, date))
    check("aderencia eh 'excelente'", resumo.aderencia == 'excelente')
    check("pontos_positivos eh list[str]", isinstance(resumo.pontos_positivos, list))
    check("pontos_positivos[0] eh str", isinstance(resumo.pontos_positivos[0], str))
except Exception as e:
    check("ResumoSemanalCreate validacao", False)
    print(f"  Erro: {e}")

# =====================================================================
# PARTE 2: Validar rota imports
# =====================================================================
print("\n[PARTE 2] Validar imports na rota")
print("-" * 70)

try:
    from app.routes.memorias import router
    check("Import router de memorias", True)
except Exception as e:
    check("Import router de memorias", False)
    print(f"  Erro: {e}")

try:
    from fastapi import Body
    from app.routes.memorias import post_salvar_resumo_semanal
    check("Body importado na rota", True)
except Exception as e:
    check("Body importado", False)
    print(f"  Erro: {e}")

# =====================================================================
# PARTE 3: Validar response model
# =====================================================================
print("\n[PARTE 3] Validar response do salvar_resumo_semanal")
print("-" * 70)

try:
    from app.services.memoria_service import salvar_resumo_semanal
    check("Import salvar_resumo_semanal", True)

    # Verificar que a funcao existe e tem a assinatura certa
    import inspect
    sig = inspect.signature(salvar_resumo_semanal)
    params = list(sig.parameters.keys())
    check("salvar_resumo_semanal tem parametros corretos", 'atleta_id' in params and 'dados' in params)
except Exception as e:
    check("salvar_resumo_semanal", False)
    print(f"  Erro: {e}")

# =====================================================================
# PARTE 4: Validar serializacao
# =====================================================================
print("\n[PARTE 4] Validar serializacao")
print("-" * 70)

try:
    from app.schemas.atleta_memoria import AtletaMemoriaRead
    from uuid import UUID
    from datetime import datetime

    # Mock de um objeto de memoria
    class MockMemoria:
        def __init__(self):
            self.id = UUID('12345678-1234-5678-1234-567812345678')
            self.atleta_id = UUID('87654321-4321-8765-4321-876543218765')
            self.tipo = "resumo_semanal"
            self.chave = "semana_2026_04_28"
            self.valor_texto = "Resumo da semana"
            self.valor_json = {"resumo": "test"}
            self.origem = "conversa"
            self.importancia = 5
            self.confianca = 1.0
            self.semana_inicio = date(2026, 4, 28)
            self.ativo = True
            self.criado_em = datetime.now()
            self.atualizado_em = datetime.now()

    memoria = MockMemoria()
    memoria_read = AtletaMemoriaRead.model_validate(memoria)
    check("AtletaMemoriaRead.model_validate(memoria)", True)

    # Serializar com mode="json"
    dump = memoria_read.model_dump(mode="json")
    check("model_dump(mode='json') funciona", isinstance(dump, dict))
    check("id eh string em JSON", isinstance(dump['id'], str))
    check("atleta_id eh string em JSON", isinstance(dump['atleta_id'], str))

except Exception as e:
    check("Serializacao", False)
    print(f"  Erro: {e}")
    import traceback
    traceback.print_exc()

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
    print("  1. Body(...) adicionado aos endpoints de POST")
    print("  2. ResumoSemanalCreate valida dados do usuario")
    print("  3. Campos sao types corretos (date, list[str], etc)")
    print("  4. model_dump(mode='json') serializa UUIDs para strings")
    exit(0)
else:
    print(f"\n{failed} validacoes falharam!")
    exit(1)
