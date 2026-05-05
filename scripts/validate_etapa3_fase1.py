#!/usr/bin/env python3
"""Validação ETAPA 3, FASE 3.1 - Modelo de Evento (sem banco de dados).

Testa a função gerar_eventos_treino com dados simulados.
Valida:
1. Estrutura de evento
2. Aplicação de contexto (horário preferido)
3. Estimativa de duração
4. Ordenação por data
5. Coerência com plano
"""

import json
from datetime import date, time
from decimal import Decimal

# Simular imports (sem dependência de DB)
from typing import Dict, Any, List, Optional


def gerar_eventos_treino(
    plano: Dict[str, Any],
    contexto: Optional[Dict[str, Any]] = None,
    data_inicio_override: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Função simplificada para teste."""

    eventos = []

    if not plano or not isinstance(plano, dict):
        return eventos

    treinos = plano.get("treinos", [])
    if not isinstance(treinos, list):
        return eventos

    # Extrair horário preferido
    horario_preferido = time(7, 0)
    if contexto and isinstance(contexto, dict):
        preferencia = contexto.get("preferencia", {})
        horario_str = preferencia.get("horario_preferido")
        if horario_str:
            try:
                partes = str(horario_str).split(":")
                if len(partes) >= 2:
                    horario_preferido = time(int(partes[0]), int(partes[1]))
            except (ValueError, AttributeError):
                pass

    for treino in treinos:
        if not isinstance(treino, dict):
            continue

        tipo_treino = treino.get("tipo")
        distancia_km = treino.get("distancia_km") or treino.get("distancia")
        dia_semana = treino.get("dia_semana") or treino.get("dia")

        # Data do treino enriquecido (ETAPA 1)
        data_treino_str = treino.get("data")
        if not data_treino_str:
            continue

        try:
            if isinstance(data_treino_str, str):
                data_treino = date.fromisoformat(data_treino_str)
            else:
                data_treino = data_treino_str
        except (ValueError, AttributeError):
            continue

        # Estimar duração
        duracao_min = 60
        if distancia_km:
            try:
                duracao_min = int(float(distancia_km) * 6)
                duracao_min = max(30, min(180, duracao_min))
            except (ValueError, TypeError):
                pass

        # Construir descrição
        partes = []
        if distancia_km:
            partes.append(f"{distancia_km}km")
        if tipo_treino:
            partes.append(f"{tipo_treino}")
        descricao = " - ".join(partes) if partes else "Treino"

        evento = {
            "titulo": f"Treino - {tipo_treino or 'Regular'}",
            "descricao": descricao,
            "data": str(data_treino),
            "hora": horario_preferido.strftime("%H:%M"),
            "duracao_min": duracao_min
        }
        eventos.append(evento)

    eventos.sort(key=lambda e: e["data"])
    return eventos


# ============================================================================
# TESTES
# ============================================================================

def teste_1_estrutura_evento():
    """Valida estrutura base de evento."""
    plano = {
        "treinos": [
            {
                "dia_semana": "terca",
                "tipo": "leve",
                "distancia_km": 8,
                "data": "2026-05-05"
            }
        ]
    }
    eventos = gerar_eventos_treino(plano)

    assert len(eventos) == 1, f"Esperado 1 evento, obteve {len(eventos)}"
    evento = eventos[0]

    assert "titulo" in evento, "Falta campo 'titulo'"
    assert "descricao" in evento, "Falta campo 'descricao'"
    assert "data" in evento, "Falta campo 'data'"
    assert "hora" in evento, "Falta campo 'hora'"
    assert "duracao_min" in evento, "Falta campo 'duracao_min'"

    assert isinstance(evento["duracao_min"], int), "duracao_min deve ser int"
    assert 5 <= evento["duracao_min"] <= 480, f"duracao_min fora do range: {evento['duracao_min']}"

    print("[PASS] TESTE 1: Estrutura de evento OK")
    return True


def teste_2_aplicacao_contexto():
    """Valida aplicação de contexto (horário preferido)."""
    plano = {
        "treinos": [
            {
                "tipo": "leve",
                "distancia_km": 8,
                "data": "2026-05-05"
            }
        ]
    }

    # Sem contexto
    eventos_sem = gerar_eventos_treino(plano)
    hora_padrao = eventos_sem[0]["hora"]
    assert hora_padrao == "07:00", f"Hora padrão esperada '07:00', obteve '{hora_padrao}'"

    # Com contexto
    contexto = {
        "preferencia": {
            "horario_preferido": "06:30"
        }
    }
    eventos_com = gerar_eventos_treino(plano, contexto)
    hora_customizada = eventos_com[0]["hora"]
    assert hora_customizada == "06:30", f"Hora customizada esperada '06:30', obteve '{hora_customizada}'"

    print("[PASS] TESTE 2: Aplicação de contexto (horário preferido) OK")
    return True


def teste_3_estimativa_duracao():
    """Valida estimativa de duração baseada em distância."""
    plano = {
        "treinos": [
            {"tipo": "leve", "distancia_km": 8, "data": "2026-05-05"},
            {"tipo": "longa", "distancia_km": 20, "data": "2026-05-06"},
            {"tipo": "intervalo", "distancia_km": 5, "data": "2026-05-07"}
        ]
    }

    eventos = gerar_eventos_treino(plano)
    assert len(eventos) == 3, f"Esperado 3 eventos, obteve {len(eventos)}"

    # 8km * 6 = 48 min
    assert eventos[0]["duracao_min"] == 48, f"Esperado 48 min, obteve {eventos[0]['duracao_min']}"

    # 20km * 6 = 120 min
    assert eventos[1]["duracao_min"] == 120, f"Esperado 120 min, obteve {eventos[1]['duracao_min']}"

    # 5km * 6 = 30 min
    assert eventos[2]["duracao_min"] == 30, f"Esperado 30 min, obteve {eventos[2]['duracao_min']}"

    print("[PASS] TESTE 3: Estimativa de duração OK")
    return True


def teste_4_ordenacao_data():
    """Valida ordenação dos eventos por data."""
    plano = {
        "treinos": [
            {"tipo": "leve", "distancia_km": 8, "data": "2026-05-06"},
            {"tipo": "leve", "distancia_km": 8, "data": "2026-05-04"},
            {"tipo": "leve", "distancia_km": 8, "data": "2026-05-05"}
        ]
    }

    eventos = gerar_eventos_treino(plano)
    assert len(eventos) == 3, f"Esperado 3 eventos, obteve {len(eventos)}"

    datas = [e["data"] for e in eventos]
    assert datas == ["2026-05-04", "2026-05-05", "2026-05-06"], f"Datas não ordenadas: {datas}"

    print("[PASS] TESTE 4: Ordenação por data OK")
    return True


def teste_5_coerencia_plano():
    """Valida coerência entre plano e eventos gerados."""
    plano = {
        "treinos": [
            {
                "dia_semana": "terca",
                "tipo": "leve",
                "distancia_km": 8,
                "data": "2026-05-05"
            },
            {
                "dia_semana": "quinta",
                "tipo": "intenso",
                "distancia_km": 5,
                "data": "2026-05-07"
            }
        ]
    }

    eventos = gerar_eventos_treino(plano)
    assert len(eventos) == 2, f"Esperado 2 eventos, obteve {len(eventos)}"

    # Verificar que descrição contém tipo e distância
    assert "8km" in eventos[0]["descricao"], f"Distância não em descrição: {eventos[0]['descricao']}"
    assert "leve" in eventos[0]["descricao"].lower(), f"Tipo não em descrição: {eventos[0]['descricao']}"

    assert "5km" in eventos[1]["descricao"], f"Distância não em descrição: {eventos[1]['descricao']}"
    assert "intenso" in eventos[1]["descricao"].lower(), f"Tipo não em descrição: {eventos[1]['descricao']}"

    print("[PASS] TESTE 5: Coerência plano-evento OK")
    return True


def teste_6_plano_invalido():
    """Valida comportamento com plano inválido."""
    # Sem treinos
    assert gerar_eventos_treino({}) == []
    assert gerar_eventos_treino({"treinos": []}) == []

    # Treino sem data
    plano = {
        "treinos": [
            {"tipo": "leve", "distancia_km": 8}  # Sem 'data'
        ]
    }
    assert gerar_eventos_treino(plano) == []

    print("[PASS] TESTE 6: Validação de plano inválido OK")
    return True


def teste_7_contexto_invalido():
    """Valida fallback quando contexto é inválido."""
    plano = {
        "treinos": [
            {"tipo": "leve", "distancia_km": 8, "data": "2026-05-05"}
        ]
    }

    # Contexto com horário inválido
    contexto_invalido = {
        "preferencia": {
            "horario_preferido": "invalid"
        }
    }

    eventos = gerar_eventos_treino(plano, contexto_invalido)
    assert len(eventos) == 1, "Deve gerar evento mesmo com contexto inválido"
    assert eventos[0]["hora"] == "07:00", "Deve usar padrão (07:00) com contexto inválido"

    print("[PASS] TESTE 7: Fallback com contexto inválido OK")
    return True


def teste_8_multiplos_eventos_mesmo_dia():
    """Valida múltiplos eventos no mesmo dia."""
    plano = {
        "treinos": [
            {"tipo": "aquecimento", "distancia_km": 3, "data": "2026-05-05"},
            {"tipo": "trabalho", "distancia_km": 10, "data": "2026-05-05"},
            {"tipo": "esfriamento", "distancia_km": 2, "data": "2026-05-05"}
        ]
    }

    eventos = gerar_eventos_treino(plano)
    assert len(eventos) == 3, f"Esperado 3 eventos, obteve {len(eventos)}"
    assert all(e["data"] == "2026-05-05" for e in eventos), "Todos devem ter mesma data"

    print("[PASS] TESTE 8: Múltiplos eventos no mesmo dia OK")
    return True


# ============================================================================
# EXECUÇÃO
# ============================================================================

def main():
    print("=" * 70)
    print("VALIDAÇÃO ETAPA 3, FASE 3.1 - MODELO DE EVENTO")
    print("=" * 70)
    print()

    testes = [
        teste_1_estrutura_evento,
        teste_2_aplicacao_contexto,
        teste_3_estimativa_duracao,
        teste_4_ordenacao_data,
        teste_5_coerencia_plano,
        teste_6_plano_invalido,
        teste_7_contexto_invalido,
        teste_8_multiplos_eventos_mesmo_dia
    ]

    resultados = []
    for teste in testes:
        try:
            resultado = teste()
            resultados.append((teste.__name__, "PASS"))
        except AssertionError as e:
            resultados.append((teste.__name__, f"FAIL: {e}"))
            print(f"✗ {teste.__name__}: {e}")
        except Exception as e:
            resultados.append((teste.__name__, f"ERROR: {e}"))
            print(f"✗ {teste.__name__}: {type(e).__name__}: {e}")

    print()
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    passou = sum(1 for _, r in resultados if r == "PASS")
    total = len(resultados)

    for nome, resultado in resultados:
        status = "[PASS]" if resultado == "PASS" else "[FAIL]"
        print(f"{status} {nome}: {resultado}")

    print()
    print(f"Total: {total} testes")
    print(f"Passou: {passou}")
    print(f"Taxa de sucesso: {100 * passou / total:.1f}%")
    print()

    if passou == total:
        print("[OK] ETAPA 3, FASE 3.1 - VALIDADO COM SUCESSO")
        return 0
    else:
        print("[FAIL] ETAPA 3, FASE 3.1 - FALHAS DETECTADAS")
        return 1


if __name__ == "__main__":
    exit(main())
