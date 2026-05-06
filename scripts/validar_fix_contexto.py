#!/usr/bin/env python3
"""Validar que o fix para contexto_resumo está completo."""

import sys
sys.path.insert(0, '/c/Projetos/gojohnny')

from typing import Any
from datetime import date

print("=" * 70)
print("VALIDACAO: Fix para SessaoIniciarResponse.contexto_resumo")
print("=" * 70)

checks = []

def check(nome, condicao):
    """Registrar um check."""
    status = "PASS" if condicao else "FAIL"
    checks.append((status, nome))
    print(f"  [{status}] {nome}")

# =====================================================================
# VALIDACAO 1: Schema structure
# =====================================================================
print("\n[VALIDACAO 1] Estrutura do schema")
print("-" * 70)

try:
    from app.schemas.sessao import ContextoResumo, SessaoIniciarResponse

    check("ContextoResumo importa", True)

    # Verificar campos
    schema = ContextoResumo.__fields__
    check("memorias_relevantes existe", "memorias_relevantes" in schema)
    check("ultima_semana existe", "ultima_semana" in schema)
    check("alertas_treinador existe", "alertas_treinador" in schema)
    check("preferencias existe", "preferencias" in schema)
    check("objetivo existe", "objetivo" in schema)

except Exception as e:
    check("Schema importa", False)
    print(f"  Erro: {e}")
    sys.exit(1)

# =====================================================================
# VALIDACAO 2: Types corretos
# =====================================================================
print("\n[VALIDACAO 2] Tipos de dados corretos")
print("-" * 70)

try:
    # Teste 1: Lista vazia para memorias_relevantes (era error antes)
    ctx1 = ContextoResumo(
        memorias_relevantes=[]
    )
    check("memorias_relevantes=[] funciona", ctx1.memorias_relevantes == [])

    # Teste 2: None para ultima_semana (era error antes)
    ctx2 = ContextoResumo(
        ultima_semana=None
    )
    check("ultima_semana=None funciona", ctx2.ultima_semana is None)

    # Teste 3: Lista vazia para alertas_treinador (era error antes)
    ctx3 = ContextoResumo(
        alertas_treinador=[]
    )
    check("alertas_treinador=[] funciona", ctx3.alertas_treinador == [])

    # Teste 4: Lista de dicts para preferencias (era error antes)
    ctx4 = ContextoResumo(
        preferencias=[{"chave": "dias", "valor": "seg"}]
    )
    check("preferencias=[dict] funciona", len(ctx4.preferencias) == 1)

    # Teste 5: Todos os campos juntos (como vem do service)
    ctx_completo = ContextoResumo(
        memorias_relevantes=[
            {"id": "123", "tipo": "alert", "valor_texto": "Aviso"}
        ],
        ultima_semana={"resumo": "Semana produtiva"},
        alertas_treinador=[
            "Aumentar volume",
            "Melhorar técnica"
        ],
        preferencias=[
            {"chave": "dias_treino", "valor": "seg/qua/sex"}
        ],
        objetivo={"descricao": "Ganhar massa"}
    )
    check("Todos os campos juntos", True)

except Exception as e:
    check("Tipos de dados", False)
    print(f"  Erro: {e}")
    import traceback
    traceback.print_exc()

# =====================================================================
# VALIDACAO 3: Session Response completa
# =====================================================================
print("\n[VALIDACAO 3] SessaoIniciarResponse completa")
print("-" * 70)

try:
    resposta = SessaoIniciarResponse(
        status="existente",
        atleta=None,
        plano_atual=None,
        contexto_resumo=ContextoResumo(
            memorias_relevantes=[],
            ultima_semana=None,
            alertas_treinador=[],
            preferencias=[],
            objetivo=None
        ),
        flags={
            "usar_datas_reais": False,
            "usar_contexto_atleta": False,
            "usar_google_calendar": False,
            "usar_strava": False,
        },
        instrucao_continuacao="Bem-vindo!"
    )
    check("SessaoIniciarResponse instancia", True)

    # Teste serializacao
    dump = resposta.model_dump(mode="json")
    check("model_dump(mode='json') funciona", isinstance(dump, dict))
    check("contexto_resumo em dump é dict", isinstance(dump["contexto_resumo"], dict))
    check("contexto_resumo.memorias_relevantes é list", isinstance(dump["contexto_resumo"]["memorias_relevantes"], list))
    check("contexto_resumo.ultima_semana pode ser None", dump["contexto_resumo"]["ultima_semana"] is None)

except Exception as e:
    check("SessaoIniciarResponse", False)
    print(f"  Erro: {e}")
    import traceback
    traceback.print_exc()

# =====================================================================
# VALIDACAO 4: Session Service
# =====================================================================
print("\n[VALIDACAO 4] Session Service retorna dados corretos")
print("-" * 70)

try:
    from app.services.session_service import _resposta_novo

    resposta_novo = _resposta_novo()
    check("_resposta_novo() retorna dict", isinstance(resposta_novo, dict))
    check("contexto_resumo é dict vazio", resposta_novo["contexto_resumo"] == {})

except Exception as e:
    check("Session Service", False)
    print(f"  Erro: {e}")

# =====================================================================
# RESUMO
# =====================================================================
print("\n" + "=" * 70)
passed = sum(1 for status, _ in checks if status == "PASS")
failed = sum(1 for status, _ in checks if status == "FAIL")

print(f"TOTAL: {passed}/{len(checks)} checks passaram")

if failed == 0:
    print("\nFIX COMPLETO!")
    print("\nProblemas resolvidos:")
    print("  1. ContextoResumo schema criado com tipos corretos")
    print("  2. memorias_relevantes agora aceita list[dict]")
    print("  3. ultima_semana agora aceita None")
    print("  4. alertas_treinador agora aceita list[str]")
    print("  5. preferencias agora aceita list[dict]")
    print("  6. objetivo adicionado ao contexto")
    print("  7. SessaoIniciarResponse serializa corretamente")
    exit(0)
else:
    print(f"\n{failed} validacoes falharam!")
    exit(1)
