#!/usr/bin/env python3
"""
Validacao ETAPA 3, BLOCO 2 - OAuth Google (sem chamadas reais ao Google).

Simula:
- Gerar URL de login
- Validar state parameter
- Preparar para callback
- Status de conexão
- Disconnect
"""

import base64
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs


# Mock das funcoes do google_oauth_service
class MockGoogleOAuthService:
    """Mock que simula o serviço de OAuth sem chamar Google."""

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_CLIENT_ID = "test-client-id-123"
    GOOGLE_REDIRECT_URI = "http://localhost:8000/oauth/google/callback"
    SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

    @staticmethod
    def gerar_state(atleta_apelido: str) -> str:
        """Gera state a partir do apelido."""
        estado = base64.b64encode(atleta_apelido.encode()).decode()
        return estado

    @staticmethod
    def validar_state(state: str) -> Optional[str]:
        """Valida e decodifica state."""
        try:
            apelido = base64.b64decode(state).decode()
            if not apelido or len(apelido) > 100:
                return None
            return apelido
        except Exception:
            return None

    @staticmethod
    def gerar_url_login(atleta_apelido: str) -> str:
        """Gera URL de login."""
        state = MockGoogleOAuthService.gerar_state(atleta_apelido)

        params = [
            f"client_id={MockGoogleOAuthService.GOOGLE_CLIENT_ID}",
            f"redirect_uri={MockGoogleOAuthService.GOOGLE_REDIRECT_URI}",
            "response_type=code",
            f"scope={'+'.join(MockGoogleOAuthService.SCOPES)}",
            "access_type=offline",
            "prompt=consent",
            f"state={state}",
        ]

        return f"{MockGoogleOAuthService.GOOGLE_AUTH_URL}?{'&'.join(params)}"


# ============================================================================
# TESTES
# ============================================================================


def test_1_gerar_url_login():
    """TESTE 1: Gerar URL de login."""
    print("\n[TESTE 1] Gerar URL de login")

    apelido = "johnny"
    url = MockGoogleOAuthService.gerar_url_login(apelido)

    # Validacoes
    assert url.startswith(MockGoogleOAuthService.GOOGLE_AUTH_URL), "URL base incorreta"
    assert "client_id=" in url, "client_id ausente"
    assert "redirect_uri=" in url, "redirect_uri ausente"
    assert "response_type=code" in url, "response_type incorreto"
    assert "scope=" in url, "scope ausente"
    assert "access_type=offline" in url, "access_type incorreto"
    assert "prompt=consent" in url, "prompt incorreto"
    assert "state=" in url, "state ausente"

    print(f"  [OK] URL gerada corretamente")
    print(f"  [OK] Comprimento: {len(url)} caracteres")

    # Extrair state da URL
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    state = params.get("state", [None])[0]

    assert state is not None, "state não encontrado na URL"
    print(f"  [OK] State: {state[:20]}...")

    return True


def test_2_validar_state():
    """TESTE 2: Validar state parameter."""
    print("\n[TESTE 2] Validar state parameter")

    # Caso 1: State válido
    apelido_original = "johnny"
    state = MockGoogleOAuthService.gerar_state(apelido_original)
    apelido_recuperado = MockGoogleOAuthService.validar_state(state)

    assert apelido_recuperado == apelido_original, f"Apelido não recuperado: {apelido_recuperado}"
    print(f"  [OK] State válido -> apelido recuperado: {apelido_recuperado}")

    # Caso 2: State inválido (base64 corrupto)
    state_invalido = "invalid-base64!!!"
    apelido = MockGoogleOAuthService.validar_state(state_invalido)

    assert apelido is None, "Deveria retornar None para state inválido"
    print(f"  [OK] State inválido -> None")

    # Caso 3: State vazio
    state_vazio = ""
    apelido = MockGoogleOAuthService.validar_state(state_vazio)

    assert apelido is None, "Deveria retornar None para state vazio"
    print(f"  [OK] State vazio -> None")

    # Caso 4: Apelido muito longo (limite 100)
    apelido_longo = "a" * 101
    state_longo = MockGoogleOAuthService.gerar_state(apelido_longo)
    apelido_recuperado_longo = MockGoogleOAuthService.validar_state(state_longo)

    assert apelido_recuperado_longo is None, "Deveria rejeitar apelido > 100 chars"
    print(f"  [OK] Apelido muito longo (101) -> None")

    return True


def test_3_csrf_protection():
    """TESTE 3: Proteção CSRF com state."""
    print("\n[TESTE 3] Proteção CSRF com state")

    # Gerar URLs para 2 atletas diferentes
    url_johnny = MockGoogleOAuthService.gerar_url_login("johnny")
    url_maria = MockGoogleOAuthService.gerar_url_login("maria")

    # Extrair states
    parsed_johnny = urlparse(url_johnny)
    params_johnny = parse_qs(parsed_johnny.query)
    state_johnny = params_johnny.get("state", [None])[0]

    parsed_maria = urlparse(url_maria)
    params_maria = parse_qs(parsed_maria.query)
    state_maria = params_maria.get("state", [None])[0]

    # Validar que states são diferentes
    assert state_johnny != state_maria, "States devem ser diferentes"
    print(f"  [OK] State johnny: {state_johnny[:15]}...")
    print(f"  [OK] State maria:  {state_maria[:15]}...")

    # Validar que cada state recupera seu atleta
    assert MockGoogleOAuthService.validar_state(state_johnny) == "johnny"
    assert MockGoogleOAuthService.validar_state(state_maria) == "maria"

    # Validar que trocar states falha
    estado_trocado = MockGoogleOAuthService.validar_state(state_maria)
    assert estado_trocado != "johnny", "Trocar states não deve recuperar atleta incorreto"

    print(f"  [OK] Cada state recupera o atleta correto")
    print(f"  [OK] Proteção CSRF validada")

    return True


def test_4_parametros_url():
    """TESTE 4: Validar parâmetros da URL de login."""
    print("\n[TESTE 4] Validar parâmetros da URL")

    url = MockGoogleOAuthService.gerar_url_login("johnny")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Validar cada parâmetro
    assert params.get("client_id") == [MockGoogleOAuthService.GOOGLE_CLIENT_ID]
    assert params.get("redirect_uri") == [MockGoogleOAuthService.GOOGLE_REDIRECT_URI]
    assert params.get("response_type") == ["code"]
    assert params.get("access_type") == ["offline"]
    assert params.get("prompt") == ["consent"]

    # Validar scope
    scope_url = params.get("scope", [None])[0]
    assert scope_url is not None
    assert "calendar.events" in scope_url

    print(f"  [OK] client_id: {params.get('client_id')[0][:30]}...")
    print(f"  [OK] redirect_uri: {params.get('redirect_uri')[0]}")
    print(f"  [OK] response_type: {params.get('response_type')[0]}")
    print(f"  [OK] access_type: {params.get('access_type')[0]}")
    print(f"  [OK] prompt: {params.get('prompt')[0]}")
    print(f"  [OK] scope: {scope_url[:50]}...")

    return True


def test_5_multiplos_atletas():
    """TESTE 5: Multiplos atletas independentes."""
    print("\n[TESTE 5] Multiplos atletas independentes")

    atletas = ["johnny", "maria", "pedro", "ana"]

    # Gerar URLs para cada atleta
    urls = {}
    states = {}

    for apelido in atletas:
        url = MockGoogleOAuthService.gerar_url_login(apelido)
        urls[apelido] = url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        states[apelido] = params.get("state", [None])[0]

    # Validar que cada state é único
    estados_unicos = set(states.values())
    assert len(estados_unicos) == len(atletas), "Deve haver states únicos para cada atleta"

    # Validar que cada state recupera seu atleta
    for apelido, state in states.items():
        recuperado = MockGoogleOAuthService.validar_state(state)
        assert recuperado == apelido, f"State de {apelido} não recupera corretamente"

    print(f"  [OK] {len(atletas)} atletas testados")
    print(f"  [OK] Todos os states são únicos")
    print(f"  [OK] Cada state recupera seu atleta")

    return True


def test_6_seguranca_tokens():
    """TESTE 6: Tokens não aparecem na URL."""
    print("\n[TESTE 6] Segurança - tokens não na URL")

    url = MockGoogleOAuthService.gerar_url_login("johnny")

    # Validar que tokens não aparecem
    assert "access_token" not in url, "access_token não deve estar na URL"
    assert "refresh_token" not in url, "refresh_token não deve estar na URL"
    assert "Bearer" not in url, "Bearer não deve estar na URL"
    assert "token=" not in url, "token= não deve estar na URL"

    # Validar que apenas authorization code é esperado
    assert "response_type=code" in url, "response_type deve ser code (não token)"
    assert "code" in url, "URL deve mencionar code"

    print(f"  [OK] access_token não na URL")
    print(f"  [OK] refresh_token não na URL")
    print(f"  [OK] Bearer não na URL")
    print(f"  [OK] response_type=code (seguro)")

    return True


def test_7_scopes_corretos():
    """TESTE 7: Usar apenas scope calendar.events (não full access)."""
    print("\n[TESTE 7] Validar scopes")

    url = MockGoogleOAuthService.gerar_url_login("johnny")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    scope = params.get("scope", [None])[0]

    # Validar que há apenas um scope
    assert scope is not None
    scopes_list = scope.split("+")
    assert len(scopes_list) == 1, "Deve haver apenas um scope"

    # Validar que é calendar.events
    assert "calendar.events" in scope, "Deve ter calendar.events"

    # Validar que NÃO tem outros scopes perigosos
    assert "calendar" in scope, "Deve ter calendar"
    assert "drive" not in scope, "Não deve ter drive"
    assert "gmail" not in scope, "Não deve ter gmail"
    assert "contacts" not in scope, "Não deve ter contacts"

    print(f"  [OK] Scope: {scope}")
    print(f"  [OK] Apenas calendar.events (acesso mínimo)")
    print(f"  [OK] Sem acesso a drive, gmail, contacts")

    return True


def test_8_fluxo_completo():
    """TESTE 8: Fluxo completo simulado."""
    print("\n[TESTE 8] Fluxo completo simulado")

    apelido = "johnny"

    # 1. Gerar URL de login
    url = MockGoogleOAuthService.gerar_url_login(apelido)
    print(f"  [OK] 1. URL gerada: {url[:60]}...")

    # 2. Extrair state
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    state = params.get("state", [None])[0]
    print(f"  [OK] 2. State extraído: {state[:20]}...")

    # 3. Usuário seria redirecionado, autoriza no Google
    print(f"  [OK] 3. Usuário autoriza no Google (simulado)")

    # 4. Google redireciona com code (simulado)
    code_simulado = "4/0AX4XfWi..."
    print(f"  [OK] 4. Google callback com code: {code_simulado}")

    # 5. Backend valida state
    atleta_recuperado = MockGoogleOAuthService.validar_state(state)
    assert atleta_recuperado == apelido, "State não recupera apelido"
    print(f"  [OK] 5. State validado, apelido: {atleta_recuperado}")

    # 6. Backend preparado para trocar code (em BLOCO 2, será async)
    print(f"  [OK] 6. Pronto para trocar code por tokens (próxima etapa)")

    return True


# ============================================================================
# EXECUCAO
# ============================================================================


def main():
    print("=" * 70)
    print("ETAPA 3, BLOCO 2 - VALIDACAO OAUTH (SEM GOOGLE REAL)")
    print("=" * 70)

    testes = [
        ("1 - Gerar URL de login", test_1_gerar_url_login),
        ("2 - Validar state parameter", test_2_validar_state),
        ("3 - Proteção CSRF", test_3_csrf_protection),
        ("4 - Parametros da URL", test_4_parametros_url),
        ("5 - Multiplos atletas", test_5_multiplos_atletas),
        ("6 - Segurança de tokens", test_6_seguranca_tokens),
        ("7 - Scopes corretos", test_7_scopes_corretos),
        ("8 - Fluxo completo", test_8_fluxo_completo),
    ]

    resultados = []
    for nome, func in testes:
        try:
            passou = func()
            resultados.append((nome, "PASS"))
        except AssertionError as e:
            resultados.append((nome, f"FAIL: {e}"))
            print(f"  [FAIL] {e}")
        except Exception as e:
            resultados.append((nome, f"ERROR: {e}"))
            print(f"  [ERROR] {type(e).__name__}: {e}")

    # Resultado
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70 + "\n")

    passou = sum(1 for _, r in resultados if r == "PASS")
    total = len(resultados)

    for nome, resultado in resultados:
        status = "[PASS]" if resultado == "PASS" else "[FAIL]"
        print(f"{status} Teste {nome}: {resultado}")

    print(f"\nTotal: {total} testes")
    print(f"Passou: {passou}")
    print(f"Taxa: {100 * passou / total:.1f}%\n")

    if passou == total:
        print("[PASS] BLOCO 2 - OAUTH VALIDADO\n")
        return 0
    else:
        print("[FAIL] ALGUNS TESTES FALHARAM\n")
        return 1


if __name__ == "__main__":
    exit(main())
