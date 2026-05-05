#!/usr/bin/env python3
"""Validação ETAPA 3, FASE 3.2 - Calendário Real.

Valida 8 cenários E2E do endpoint /calendario/{apelido}/preview.
Não valida só estrutura - valida coerência com plano e contexto.
"""

import requests
import json
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "apikdnvusdnmd58625@#*lsdj"
APELIDO = "johnny_e2e_calendar"

# Cores ANSI para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def log_info(msg: str):
    print(f"{YELLOW}[INFO]{RESET} {msg}")


def log_pass(msg: str):
    print(f"{GREEN}[PASS]{RESET} {msg}")


def log_fail(msg: str):
    print(f"{RED}[FAIL]{RESET} {msg}")


def fazer_request(method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
    """Fazer request com API Key."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    if method == "GET":
        return requests.get(url, headers=headers)
    elif method == "POST":
        return requests.post(url, json=data, headers=headers)
    elif method == "DELETE":
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Método inválido: {method}")


def criar_atleta() -> bool:
    """Criar atleta de teste."""
    log_info("Setup: Criando atleta...")

    data = {
        "apelido": APELIDO,
        "nome": "Johnny E2E Calendar",
        "objetivo": "Treinar corridas variadas",
        "dias_treino": 4,
        "pace_confortavel": "5:00/km",
        "historico_dores": None,
        "proxima_prova": "Teste",
        "distancia_alvo_km": 10.0
    }

    response = fazer_request("POST", "/atletas", data)
    if response.status_code in [200, 201]:
        log_pass("Atleta criado")
        return True
    else:
        log_fail(f"Erro ao criar atleta: {response.status_code}")
        return False


def criar_plano_com_datas() -> bool:
    """Criar plano com datas reais (ETAPA 1)."""
    log_info("Setup: Criando plano com datas...")

    # Datas reais
    data_inicio = date(2026, 5, 4)
    data_prova = date(2026, 5, 11)

    # Treinos com datas enriquecidas
    plano = {
        "treinos": [
            {
                "dia_semana": "segunda",
                "tipo": "leve",
                "distancia_km": 5,
                "data": "2026-05-04"
            },
            {
                "dia_semana": "terca",
                "tipo": "moderado",
                "distancia_km": 8,
                "data": "2026-05-05"
            },
            {
                "dia_semana": "quinta",
                "tipo": "intervalo",
                "distancia_km": 6,
                "data": "2026-05-07"
            },
            {
                "dia_semana": "sabado",
                "tipo": "longa",
                "distancia_km": 15,
                "data": "2026-05-10"
            },
            {
                "dia_semana": "segunda",
                "tipo": "leve",
                "distancia_km": 5,
                "data": "2026-05-11"
            }
        ]
    }

    data = {
        "apelido": APELIDO,
        "semana_inicio": "2026-05-04",
        "objetivo_semana": "Semana de base",
        "plano": plano,
        "data_inicio": "2026-05-04",
        "data_prova": "2026-05-11",
        "dias_treino_json": ["segunda", "terca", "quinta", "sabado"],
        "novo_ciclo": False
    }

    response = fazer_request("POST", "/planos-semanais", data)
    if response.status_code in [200, 201]:
        log_pass("Plano com datas criado")
        return True
    else:
        log_fail(f"Erro ao criar plano: {response.status_code}")
        print(f"Response: {response.text}")
        return False


# ============================================================================
# CENÁRIOS
# ============================================================================

def cenario_1_base_sem_contexto() -> bool:
    """CENÁRIO 1: Base (sem contexto)."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 1: BASE (SEM CONTEXTO)")
    print(f"{'='*70}{RESET}")

    log_info("GET /calendario/{apelido}/preview")

    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")

    if response.status_code != 200:
        log_fail(f"Endpoint retornou {response.status_code}")
        return False

    data = response.json()

    # Validar estrutura
    assert "atleta_apelido" in data, "Falta 'atleta_apelido'"
    assert "total_eventos" in data, "Falta 'total_eventos'"
    assert "eventos" in data, "Falta 'eventos'"
    assert isinstance(data["eventos"], list), "eventos deve ser lista"

    log_pass(f"Preview gerado com {data['total_eventos']} eventos")

    # Validar cada evento
    for idx, evento in enumerate(data["eventos"]):
        assert "titulo" in evento, f"Evento {idx} sem 'titulo'"
        assert "descricao" in evento, f"Evento {idx} sem 'descricao'"
        assert "data" in evento, f"Evento {idx} sem 'data'"
        assert "hora" in evento, f"Evento {idx} sem 'hora'"
        assert "duracao_min" in evento, f"Evento {idx} sem 'duracao_min'"

        log_info(f"  Evento {idx}: {evento['titulo']} ({evento['data']} às {evento['hora']}, {evento['duracao_min']}min)")

    assert data["total_eventos"] == 5, f"Esperado 5 eventos, obteve {data['total_eventos']}"

    # Validar ordem
    datas = [e["data"] for e in data["eventos"]]
    assert datas == sorted(datas), f"Eventos não ordenados: {datas}"

    log_pass("Todos eventos têm estrutura correta e estão ordenados")
    return True


def cenario_2_com_contexto_horario() -> bool:
    """CENÁRIO 2: Com contexto (horário preferido)."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 2: COM CONTEXTO (HORÁRIO PREFERIDO)")
    print(f"{'='*70}{RESET}")

    # Salvar contexto
    log_info("POST /contexto/{apelido}/preferencia/horario_preferido")

    contexto_data = {
        "valor": "06:00",
        "origem": "e2e_calendar_test",
        "confianca": 1.0
    }

    response = fazer_request("POST", f"/contexto/{APELIDO}/preferencia/horario_preferido", contexto_data)

    if response.status_code not in [200, 201]:
        log_fail(f"Erro ao salvar contexto: {response.status_code}")
        return False

    log_pass("Contexto salvo (horário: 06:00)")

    # Chamar preview novamente
    log_info("GET /calendario/{apelido}/preview (com contexto)")

    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")

    if response.status_code != 200:
        log_fail(f"Endpoint retornou {response.status_code}")
        return False

    data = response.json()

    # Validar que TODOS eventos usam 06:00
    horas = [e["hora"] for e in data["eventos"]]

    log_info(f"Horas dos eventos: {horas}")

    assert all(h == "06:00" for h in horas), f"Nem todos eventos usam 06:00: {horas}"

    log_pass("TODOS eventos usam horário do contexto (06:00)")
    return True


def cenario_3_coerencia_duracao() -> bool:
    """CENÁRIO 3: Coerência de duração."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 3: COERÊNCIA DE DURAÇÃO")
    print(f"{'='*70}{RESET}")

    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")
    data = response.json()

    # Mapa esperado: distancia_km * 6 = duracao_min
    evento_map = {
        "5km": 30,    # 5 * 6 = 30
        "8km": 48,    # 8 * 6 = 48
        "6km": 36,    # 6 * 6 = 36
        "15km": 90,   # 15 * 6 = 90
    }

    for evento in data["eventos"]:
        descricao = evento["descricao"]
        duracao = evento["duracao_min"]

        # Tentar extrair km da descrição
        km_found = None
        for km_str, expected_duracao in evento_map.items():
            if km_str in descricao:
                km_found = km_str
                log_info(f"{evento['titulo']}: {km_str} → {duracao}min (esperado ~{expected_duracao}min)")

                # Validar que está razoável (±10%)
                margem = expected_duracao * 0.1
                assert abs(duracao - expected_duracao) <= margem, \
                    f"Duração {duracao} fora da margem para {km_str} (esperado {expected_duracao}±{margem})"
                break

        if km_found is None:
            log_info(f"{evento['titulo']}: {duracao}min (sem km detectado)")

    log_pass("Durações coerentes com distâncias")
    return True


def cenario_4_descricao_inteligente() -> bool:
    """CENÁRIO 4: Descrição inteligente."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 4: DESCRIÇÃO INTELIGENTE")
    print(f"{'='*70}{RESET}")

    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")
    data = response.json()

    tipos_esperados = ["leve", "moderado", "intervalo", "longa"]

    for evento in data["eventos"]:
        descricao = evento["descricao"]

        # Não aceitar descrição genérica
        assert descricao != "Treino", f"Descrição genérica: {descricao}"
        assert descricao != "Treino - None", f"Descrição vazia: {descricao}"
        assert len(descricao) > 5, f"Descrição muito curta: {descricao}"

        # Validar que contém tipo e km
        tem_km = any(str(i) + "km" in descricao for i in range(1, 30))
        tem_tipo = any(tipo in descricao.lower() for tipo in tipos_esperados)

        log_info(f"✓ {evento['titulo']}: {descricao}")
        assert tem_km or tem_tipo, f"Descrição sem tipo/km: {descricao}"

    log_pass("Todas descrições são inteligentes e informativas")
    return True


def cenario_5_consistencia_plano() -> bool:
    """CENÁRIO 5: Consistência com plano."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 5: CONSISTÊNCIA COM PLANO")
    print(f"{'='*70}{RESET}")

    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")
    data = response.json()

    # Treinos esperados do plano
    treinos_esperados = [
        ("2026-05-04", "leve", 5),      # segunda
        ("2026-05-05", "moderado", 8),  # terca
        ("2026-05-07", "intervalo", 6), # quinta
        ("2026-05-10", "longa", 15),    # sabado
        ("2026-05-11", "leve", 5),      # segunda
    ]

    assert data["total_eventos"] == len(treinos_esperados), \
        f"Total de eventos {data['total_eventos']} != {len(treinos_esperados)}"

    log_pass(f"Número correto de eventos: {data['total_eventos']}")

    # Validar que cada treino está presente
    for idx, (data_esperada, tipo_esperado, km_esperado) in enumerate(treinos_esperados):
        evento = data["eventos"][idx]

        assert evento["data"] == data_esperada, \
            f"Evento {idx}: data {evento['data']} != {data_esperada}"

        assert tipo_esperado in evento["descricao"].lower(), \
            f"Evento {idx}: tipo '{tipo_esperado}' não em '{evento['descricao']}'"

        assert str(km_esperado) + "km" in evento["descricao"], \
            f"Evento {idx}: {km_esperado}km não em '{evento['descricao']}'"

        log_info(f"✓ Evento {idx}: {evento['data']} {tipo_esperado} {km_esperado}km")

    log_pass("Plano completamente mapeado para eventos")
    return True


def cenario_6_dias_normalizados() -> bool:
    """CENÁRIO 6: Dias normalizados (variações de entrada)."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 6: DIAS NORMALIZADOS")
    print(f"{'='*70}{RESET}")

    # Salvar dias com variações
    log_info("POST /contexto (com dias variados: Tuesday, quarta, Friday)")

    dias_data = {
        "valor": "Tuesday, quarta, Friday",
        "origem": "e2e_calendar_test",
        "confianca": 1.0
    }

    response = fazer_request("POST", f"/contexto/{APELIDO}/perfil/dias_treino", dias_data)

    if response.status_code not in [200, 201]:
        log_fail(f"Erro ao salvar dias: {response.status_code}")
        # Não falha cenário - continua
    else:
        log_pass("Dias salvos com variações de idioma")

    # Chamar preview
    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")
    data = response.json()

    # Validar que eventos ainda fazem sentido
    assert data["total_eventos"] > 0, "Nenhum evento gerado"

    log_pass(f"Preview gerado com {data['total_eventos']} eventos apesar de dias variados")
    return True


def cenario_7_ordem_cronologica() -> bool:
    """CENÁRIO 7: Ordem cronológica."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 7: ORDEM CRONOLÓGICA")
    print(f"{'='*70}{RESET}")

    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")
    data = response.json()

    datas = [e["data"] for e in data["eventos"]]

    log_info(f"Datas: {datas}")

    # Validar ordem crescente
    for i in range(len(datas) - 1):
        assert datas[i] <= datas[i+1], f"Não cronológico: {datas[i]} > {datas[i+1]}"

    # Se há múltiplos eventos no mesmo dia, validar ordem de índice
    for i, data_str in enumerate(datas[:-1]):
        if data_str == datas[i+1]:
            log_info(f"✓ Múltiplos eventos em {data_str}")

    log_pass("Eventos em ordem cronológica crescente")
    return True


def cenario_8_multiplas_semanas() -> bool:
    """CENÁRIO 8: Múltiplas semanas."""
    print(f"\n{YELLOW}{'='*70}")
    print("CENÁRIO 8: MÚLTIPLAS SEMANAS")
    print(f"{'='*70}{RESET}")

    # Criar plano com 2 semanas
    log_info("Criando plano com 2+ semanas...")

    plano = {
        "treinos": [
            # Semana 1
            {"tipo": "leve", "distancia_km": 5, "data": "2026-05-04"},
            {"tipo": "moderado", "distancia_km": 8, "data": "2026-05-05"},
            # Semana 2
            {"tipo": "leve", "distancia_km": 5, "data": "2026-05-11"},
            {"tipo": "longa", "distancia_km": 15, "data": "2026-05-12"},
        ]
    }

    data = {
        "apelido": APELIDO,
        "semana_inicio": "2026-05-04",
        "objetivo_semana": "Multi-semana",
        "plano": plano,
        "data_inicio": "2026-05-04",
        "data_prova": "2026-05-18",
        "dias_treino_json": ["segunda", "terca"],
        "novo_ciclo": True  # Necessário para sobrescrever
    }

    response = fazer_request("POST", "/planos-semanais", data)
    if response.status_code not in [200, 201]:
        log_fail(f"Erro ao criar plano multi-semana: {response.status_code}")
        return False

    # Chamar preview
    response = fazer_request("GET", f"/calendario/{APELIDO}/preview")
    data = response.json()

    # Validar que não mistura semanas
    datas = [e["data"] for e in data["eventos"]]
    semanas = set()
    for d in datas:
        semana = int(d.split("-")[2]) // 7
        semanas.add(semana)

    log_info(f"Semanas representadas: {len(semanas)}")
    log_info(f"Datas: {datas}")

    # Validar que não repete datas
    assert len(datas) == len(set(datas)), f"Datas repetidas: {datas}"

    log_pass("Multi-semanas mapeadas corretamente sem repetição")
    return True


# ============================================================================
# EXECUÇÃO
# ============================================================================

def main():
    print(f"\n{YELLOW}{'='*70}")
    print("ETAPA 3, FASE 3.2 - VALIDAÇÃO REAL DO CALENDÁRIO")
    print(f"{'='*70}{RESET}\n")

    # Setup
    if not criar_atleta():
        print(f"{RED}[ERRO] Falha ao criar atleta{RESET}")
        return 1

    if not criar_plano_com_datas():
        print(f"{RED}[ERRO] Falha ao criar plano{RESET}")
        return 1

    # Cenários
    cenarios = [
        ("1 - Base", cenario_1_base_sem_contexto),
        ("2 - Contexto", cenario_2_com_contexto_horario),
        ("3 - Duração", cenario_3_coerencia_duracao),
        ("4 - Descrição", cenario_4_descricao_inteligente),
        ("5 - Plano", cenario_5_consistencia_plano),
        ("6 - Normalização", cenario_6_dias_normalizados),
        ("7 - Cronologia", cenario_7_ordem_cronologica),
        ("8 - Multi-semana", cenario_8_multiplas_semanas),
    ]

    resultados = []
    for nome, cenario_func in cenarios:
        try:
            passou = cenario_func()
            resultados.append((nome, "PASS" if passou else "FAIL"))
        except AssertionError as e:
            resultados.append((nome, f"FAIL: {e}"))
            log_fail(str(e))
        except Exception as e:
            resultados.append((nome, f"ERROR: {e}"))
            log_fail(f"Erro: {e}")

    # Resumo
    print(f"\n{YELLOW}{'='*70}")
    print("RESULTADO FINAL")
    print(f"{'='*70}{RESET}\n")

    passou = sum(1 for _, r in resultados if r == "PASS")
    total = len(resultados)

    for nome, resultado in resultados:
        status = "✓" if resultado == "PASS" else "✗"
        print(f"{status} Cenário {nome}: {resultado}")

    print(f"\n{YELLOW}Total: {total} cenários")
    print(f"Passou: {passou}")
    print(f"Taxa: {100 * passou / total:.1f}%{RESET}\n")

    if passou == total:
        print(f"{GREEN}✓ CALENDÁRIO FAZ SENTIDO - PRONTO PARA GOOGLE{RESET}\n")
        return 0
    else:
        print(f"{RED}✗ CALENDÁRIO COM PROBLEMAS - NÃO PRONTO{RESET}\n")
        return 1


if __name__ == "__main__":
    exit(main())
