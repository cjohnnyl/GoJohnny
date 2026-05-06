#!/usr/bin/env python3
"""Validar que o schema ContextoResumo está funcionando corretamente."""

import sys
from datetime import datetime, date
from uuid import UUID
from typing import Any

print("=" * 70)
print("VALIDACAO: Schema ContextoResumo e SessaoIniciarResponse")
print("=" * 70)

checks = []

def check(nome, condicao):
    """Registrar um check."""
    status = "PASS" if condicao else "FAIL"
    checks.append((status, nome))
    print(f"  [{status}] {nome}")

# =====================================================================
# PARTE 1: Validar import e structure do schema
# =====================================================================
print("\n[PARTE 1] Validar schemas")
print("-" * 70)

try:
    from app.schemas.sessao import ContextoResumo, SessaoIniciarResponse
    check("Import ContextoResumo", True)
except Exception as e:
    check("Import ContextoResumo", False)
    print(f"  Erro: {e}")
    sys.exit(1)

try:
    from app.schemas.sessao import SessaoIniciarResponse
    check("Import SessaoIniciarResponse", True)
except Exception as e:
    check("Import SessaoIniciarResponse", False)
    print(f"  Erro: {e}")
    sys.exit(1)

# =====================================================================
# PARTE 2: Validar ContextoResumo com dados válidos
# =====================================================================
print("\n[PARTE 2] Validar ContextoResumo com dados válidos")
print("-" * 70)

try:
    # Teste 1: ContextoResumo vazio
    contexto_vazio = ContextoResumo()
    check("ContextoResumo() com defaults", contexto_vazio.memorias_relevantes == [])

    # Teste 2: ContextoResumo com listas
    contexto_com_dados = ContextoResumo(
        memorias_relevantes=[{"id": "123", "tipo": "alert"}],
        ultima_semana={"resumo": "Semana produtiva"},
        alertas_treinador=["Aumentar volume", "Melhorar intensidade"],
        preferencias=[{"chave": "dias_treino", "valor": "Seg/Qua/Sex"}],
        objetivo={"descricao": "Ganhar massa muscular"}
    )
    check("ContextoResumo com dados completos", len(contexto_com_dados.alertas_treinador) == 2)
    check("ContextoResumo alertas_treinador é lista de strings", isinstance(contexto_com_dados.alertas_treinador[0], str))

    # Teste 3: ContextoResumo.model_dump()
    dump = contexto_com_dados.model_dump()
    check("ContextoResumo.model_dump() funciona", isinstance(dump, dict))
    check("model_dump contém 'alertas_treinador'", "alertas_treinador" in dump)

    # Teste 4: ContextoResumo com None
    contexto_none = ContextoResumo(
        ultima_semana=None,
        objetivo=None
    )
    check("ContextoResumo aceita None para ultima_semana", contexto_none.ultima_semana is None)
    check("ContextoResumo aceita None para objetivo", contexto_none.objetivo is None)

except Exception as e:
    check("ContextoResumo com dados válidos", False)
    print(f"  Erro: {e}")
    import traceback
    traceback.print_exc()

# =====================================================================
# PARTE 3: Validar SessaoIniciarResponse
# =====================================================================
print("\n[PARTE 3] Validar SessaoIniciarResponse")
print("-" * 70)

try:
    # Teste 1: SessaoIniciarResponse status 'novo'
    resposta_novo = SessaoIniciarResponse(
        status="novo",
        atleta=None,
        plano_atual=None,
        contexto_resumo=ContextoResumo(),
        flags={
            "usar_datas_reais": False,
            "usar_contexto_atleta": False,
            "usar_google_calendar": False,
            "usar_strava": False,
        },
        instrucao_continuacao="Usuario novo..."
    )
    check("SessaoIniciarResponse status=novo", resposta_novo.status == "novo")

    # Teste 2: SessaoIniciarResponse com contexto_resumo completo
    resposta_existente = SessaoIniciarResponse(
        status="existente",
        atleta=None,
        plano_atual=None,
        contexto_resumo=ContextoResumo(
            memorias_relevantes=[{"id": "456", "tipo": "pref"}],
            ultima_semana={"aderencia": "normal"},
            alertas_treinador=["Aviso 1"],
            preferencias=[],
            objetivo={"desc": "Meta"}
        ),
        flags={
            "usar_datas_reais": True,
            "usar_contexto_atleta": True,
            "usar_google_calendar": False,
            "usar_strava": False,
        },
        instrucao_continuacao="Usuario existente..."
    )
    check("SessaoIniciarResponse status=existente", resposta_existente.status == "existente")
    check("SessaoIniciarResponse contexto_resumo é ContextoResumo", isinstance(resposta_existente.contexto_resumo, ContextoResumo))

    # Teste 3: model_dump() serialização
    dump = resposta_existente.model_dump()
    check("SessaoIniciarResponse.model_dump() funciona", isinstance(dump, dict))
    check("model_dump contém contexto_resumo", "contexto_resumo" in dump)
    check("contexto_resumo em dump é dict", isinstance(dump["contexto_resumo"], dict))

    # Teste 4: mode="json"
    dump_json = resposta_existente.model_dump(mode="json")
    check("SessaoIniciarResponse.model_dump(mode='json')", isinstance(dump_json, dict))
    check("mode='json' contexto_resumo é dict", isinstance(dump_json["contexto_resumo"], dict))

except Exception as e:
    check("SessaoIniciarResponse validação", False)
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
    print("\nTODAS AS VALIDACOES PASSARAM!")
    print("\nContextoResumo e SessaoIniciarResponse estao funcionando corretamente:")
    print("  1. ContextoResumo aceita listas, dicts e None")
    print("  2. SessaoIniciarResponse serializa corretamente")
    print("  3. model_dump(mode='json') funciona")
    exit(0)
else:
    print(f"\n{failed} validacoes falharam!")
    exit(1)
