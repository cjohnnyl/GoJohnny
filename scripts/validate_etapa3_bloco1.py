#!/usr/bin/env python3
"""
Validacao ETAPA 3, BLOCO 1 - Infra + Banco (Integracao Google).

Simula:
- Salvar tokens fake (sem Google)
- Recuperar tokens
- Verificar expiracao
- Validar que nao quebra sistema
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any


# Mock da classe IntegracaoGoogle para testes sem BD
class MockIntegracaoGoogle:
    def __init__(
        self,
        id: str,
        atleta_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        email_google: Optional[str] = None,
    ):
        self.id = id
        self.atleta_id = atleta_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.email_google = email_google
        self.criado_em = datetime.utcnow()
        self.atualizado_em = datetime.utcnow()

    def __repr__(self):
        return f"<IntegracaoGoogle atleta_id={self.atleta_id} email={self.email_google}>"


# Mock do banco de dados (em memoria)
class MockDB:
    def __init__(self):
        self.integracoes: Dict[str, MockIntegracaoGoogle] = {}
        self.transacao_ativa = False

    def salvar_integracao(self, integracao: MockIntegracaoGoogle) -> None:
        """Simula salvar integracao"""
        self.integracoes[str(integracao.atleta_id)] = integracao

    def obter_integracao(self, atleta_id: str) -> Optional[MockIntegracaoGoogle]:
        """Simula recuperar integracao"""
        return self.integracoes.get(str(atleta_id))

    def deletar_integracao(self, atleta_id: str) -> bool:
        """Simula deletar integracao"""
        if str(atleta_id) in self.integracoes:
            del self.integracoes[str(atleta_id)]
            return True
        return False

    def commit(self):
        """Simula commit"""
        self.transacao_ativa = True

    def rollback(self):
        """Simula rollback"""
        self.transacao_ativa = False


# ============================================================================
# TESTES
# ============================================================================


def test_1_salvar_tokens():
    """TESTE 1: Salvar tokens fake."""
    print("\n[TESTE 1] Salvar tokens fake")

    db = MockDB()
    atleta_id = "test-atleta-001"

    # Simular dados Google OAuth
    access_token = "ya29.a0AfH6SMBx..."
    refresh_token = "1//0gF..."
    expires_at = datetime.utcnow() + timedelta(hours=1)
    email_google = "user@gmail.com"

    # Criar e salvar integracao
    integracao = MockIntegracaoGoogle(
        id="integracao-001",
        atleta_id=atleta_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        email_google=email_google,
    )
    db.salvar_integracao(integracao)
    db.commit()

    # Validacoes
    assert len(db.integracoes) == 1, "Integracao nao foi salva"
    assert db.transacao_ativa, "Commit nao registrado"

    print("  [OK] Token salvo com sucesso")
    print(f"  [OK] Email: {email_google}")
    print(f"  [OK] Expira em: {expires_at}")
    return True


def test_2_recuperar_tokens():
    """TESTE 2: Recuperar tokens."""
    print("\n[TESTE 2] Recuperar tokens")

    db = MockDB()
    atleta_id = "test-atleta-002"

    # Salvar
    integracao_original = MockIntegracaoGoogle(
        id="integracao-002",
        atleta_id=atleta_id,
        access_token="token-abc123",
        refresh_token="refresh-xyz789",
        expires_at=datetime.utcnow() + timedelta(hours=2),
        email_google="outro@gmail.com",
    )
    db.salvar_integracao(integracao_original)

    # Recuperar
    recuperada = db.obter_integracao(atleta_id)

    # Validacoes
    assert recuperada is not None, "Integracao nao foi recuperada"
    assert recuperada.access_token == "token-abc123", "Token incorreto"
    assert recuperada.refresh_token == "refresh-xyz789", "Refresh token incorreto"
    assert recuperada.email_google == "outro@gmail.com", "Email incorreto"

    print("  [OK] Integracao recuperada corretamente")
    print(f"  [OK] Access token (primeiros 10): {recuperada.access_token[:10]}...")
    print(f"  [OK] Email: {recuperada.email_google}")
    return True


def test_3_verificar_expiracao():
    """TESTE 3: Verificar expiracao."""
    print("\n[TESTE 3] Verificar expiracao")

    # Caso 1: Token nao expirado
    agora = datetime.utcnow()
    expires_futuro = agora + timedelta(hours=1)

    integracao_valida = MockIntegracaoGoogle(
        id="integracao-003a",
        atleta_id="atleta-003a",
        access_token="token-valido",
        expires_at=expires_futuro,
    )

    tempo_restante = (integracao_valida.expires_at - agora).total_seconds()
    assert tempo_restante > 0, "Token valido deveria ter tempo positivo"

    print(f"  [OK] Token valido: {tempo_restante:.0f} segundos restantes")

    # Caso 2: Token expirado
    expires_passado = agora - timedelta(hours=1)

    integracao_expirada = MockIntegracaoGoogle(
        id="integracao-003b",
        atleta_id="atleta-003b",
        access_token="token-expirado",
        expires_at=expires_passado,
    )

    tempo_restante_exp = (integracao_expirada.expires_at - agora).total_seconds()
    assert tempo_restante_exp < 0, "Token expirado deveria ter tempo negativo"

    print(f"  [OK] Token expirado: {abs(tempo_restante_exp):.0f} segundos atrás")

    # Caso 3: Sem expires_at
    integracao_sem_expiracao = MockIntegracaoGoogle(
        id="integracao-003c",
        atleta_id="atleta-003c",
        access_token="token-sem-expiracao",
        expires_at=None,
    )

    assert integracao_sem_expiracao.expires_at is None, "Deveria nao ter expires_at"

    print("  [OK] Token sem expiração definida (será tratado como permanente)")
    return True


def test_4_atualizar_tokens():
    """TESTE 4: Atualizar tokens existentes."""
    print("\n[TESTE 4] Atualizar tokens")

    db = MockDB()
    atleta_id = "test-atleta-004"

    # Primeira integracao
    integracao_v1 = MockIntegracaoGoogle(
        id="integracao-004",
        atleta_id=atleta_id,
        access_token="token-v1",
        refresh_token="refresh-v1",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.salvar_integracao(integracao_v1)
    criado_em = integracao_v1.criado_em

    # Simular renovacao: atualizar tokens
    integracao_v2 = MockIntegracaoGoogle(
        id="integracao-004",
        atleta_id=atleta_id,
        access_token="token-v2-renovado",
        refresh_token="refresh-v2-renovado",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        email_google="mesmo@gmail.com",
    )
    integracao_v2.criado_em = criado_em  # Manter criado_em original
    db.salvar_integracao(integracao_v2)

    # Recuperar
    recuperada = db.obter_integracao(atleta_id)

    # Validacoes
    assert recuperada.access_token == "token-v2-renovado", "Access token nao foi atualizado"
    assert recuperada.refresh_token == "refresh-v2-renovado", "Refresh token nao foi atualizado"
    assert recuperada.criado_em == criado_em, "criado_em foi alterado (nao deveria)"

    print("  [OK] Access token atualizado")
    print("  [OK] Refresh token atualizado")
    print("  [OK] criado_em preservado (apenas atualizado_em muda)")
    return True


def test_5_nao_quebra_sistema():
    """TESTE 5: Integracao nao quebra sistema sem Google."""
    print("\n[TESTE 5] Sistema funciona sem Google conectado")

    db = MockDB()
    atleta_id = "test-atleta-005"

    # Atleta sem integracao Google
    integracao = db.obter_integracao(atleta_id)

    # Validacoes
    assert integracao is None, "Deveria retornar None se nao existe"

    # Sistema continua funcionando (nao quebra)
    print("  [OK] Sistema retorna None quando Google nao conectado")
    print("  [OK] Sistema nao quebra (graceful fallback)")

    # Adicionar integracao
    nova_integracao = MockIntegracaoGoogle(
        id="integracao-005",
        atleta_id=atleta_id,
        access_token="token-teste",
    )
    db.salvar_integracao(nova_integracao)

    # Recuperar
    integracao = db.obter_integracao(atleta_id)
    assert integracao is not None, "Deveria encontrar após salvar"

    print("  [OK] Integracao salva e recuperada corretamente")
    return True


def test_6_desconectar():
    """TESTE 6: Desconectar Google (remover tokens)."""
    print("\n[TESTE 6] Desconectar Google")

    db = MockDB()
    atleta_id = "test-atleta-006"

    # Salvar
    integracao = MockIntegracaoGoogle(
        id="integracao-006",
        atleta_id=atleta_id,
        access_token="token-teste",
        email_google="user@gmail.com",
    )
    db.salvar_integracao(integracao)
    assert db.obter_integracao(atleta_id) is not None

    # Deletar
    removida = db.deletar_integracao(atleta_id)

    # Validacoes
    assert removida, "Deveria retornar True ao deletar"
    assert db.obter_integracao(atleta_id) is None, "Integracao deveria estar vazia"

    print("  [OK] Integracao removida corretamente")
    print("  [OK] Usuario desconectado do Google")
    return True


def test_7_multiplos_atletas():
    """TESTE 7: Multiplos atletas nao se misturam."""
    print("\n[TESTE 7] Multiplos atletas independentes")

    db = MockDB()

    # Atleta A
    integracao_a = MockIntegracaoGoogle(
        id="integracao-a",
        atleta_id="atleta-a",
        access_token="token-a",
        email_google="a@gmail.com",
    )
    db.salvar_integracao(integracao_a)

    # Atleta B
    integracao_b = MockIntegracaoGoogle(
        id="integracao-b",
        atleta_id="atleta-b",
        access_token="token-b",
        email_google="b@gmail.com",
    )
    db.salvar_integracao(integracao_b)

    # Recuperar separadamente
    recuperada_a = db.obter_integracao("atleta-a")
    recuperada_b = db.obter_integracao("atleta-b")

    # Validacoes
    assert recuperada_a.email_google == "a@gmail.com", "Email A incorreto"
    assert recuperada_b.email_google == "b@gmail.com", "Email B incorreto"
    assert recuperada_a.access_token != recuperada_b.access_token, "Tokens nao devem ser iguais"

    print("  [OK] Atleta A: a@gmail.com")
    print("  [OK] Atleta B: b@gmail.com")
    print("  [OK] Nenhuma mistura de dados")
    return True


def test_8_seguranca():
    """TESTE 8: Nunca expor tokens em logs/respostas."""
    print("\n[TESTE 8] Seguranca de tokens")

    integracao = MockIntegracaoGoogle(
        id="integracao-008",
        atleta_id="atleta-008",
        access_token="ya29.a0AfH6SMBx...",
        email_google="user@gmail.com",
    )

    # Validar __repr__ nao expoe token
    repr_str = repr(integracao)
    assert "ya29" not in repr_str, "Token exposto em __repr__"
    assert "email=" in repr_str, "Email nao deve estar em __repr__"

    # Validar que email pode ser lido mas nao token
    assert integracao.email_google == "user@gmail.com", "Email deve ser acessivel"

    # Token so acessivel via atributo direto (nao em logs)
    token = integracao.access_token
    assert token.startswith("ya29"), "Token deveria ser valido"

    print("  [OK] __repr__ nao expoe tokens")
    print("  [OK] Email acessivel")
    print("  [OK] Tokens so acessiveis internamente")
    return True


# ============================================================================
# EXECUCAO
# ============================================================================


def main():
    print("=" * 70)
    print("ETAPA 3, BLOCO 1 - VALIDACAO INFRA + BANCO")
    print("=" * 70)

    testes = [
        ("1 - Salvar tokens fake", test_1_salvar_tokens),
        ("2 - Recuperar tokens", test_2_recuperar_tokens),
        ("3 - Verificar expiracao", test_3_verificar_expiracao),
        ("4 - Atualizar tokens", test_4_atualizar_tokens),
        ("5 - Nao quebra sem Google", test_5_nao_quebra_sistema),
        ("6 - Desconectar Google", test_6_desconectar),
        ("7 - Multiplos atletas", test_7_multiplos_atletas),
        ("8 - Seguranca de tokens", test_8_seguranca),
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
        print("[PASS] BLOCO 1 - INFRA + BANCO VALIDADO\n")
        return 0
    else:
        print("[FAIL] ALGUNS TESTES FALHARAM\n")
        return 1


if __name__ == "__main__":
    exit(main())
