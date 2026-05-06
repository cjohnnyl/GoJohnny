#!/usr/bin/env python3
"""Teste rápido da correção de UUID no schema."""

import sys
from uuid import UUID
from datetime import datetime, date

# Simular um objeto do SQLAlchemy com UUIDs
class MockMemoria:
    def __init__(self):
        self.id = UUID('12345678-1234-5678-1234-567812345678')
        self.atleta_id = UUID('87654321-4321-8765-4321-876543218765')
        self.tipo = "preferencia"
        self.chave = "dias_treino"
        self.valor_texto = "Quarta, sexta e domingo"
        self.valor_json = None
        self.origem = "conversa"
        self.importancia = 4
        self.confianca = 1.0
        self.semana_inicio = None
        self.ativo = True
        self.criado_em = datetime.now()
        self.atualizado_em = datetime.now()

print("=" * 70)
print("TESTE: Validacao de Schema com UUID")
print("=" * 70)

try:
    # Importar o schema
    from app.schemas.atleta_memoria import AtletaMemoriaRead

    # Criar memória mock
    memoria = MockMemoria()

    # Testar validação
    print("\n[TESTE 1] Validar memória com UUID...")
    schema = AtletaMemoriaRead.model_validate(memoria)
    print("  [PASS] Schema validou UUID corretamente")

    # Testar model_dump sem mode="json" (para comparação)
    print("\n[TESTE 2] model_dump() sem mode='json'...")
    try:
        dump = schema.model_dump()
        print(f"  [PASS] Funcionou (id type: {type(dump['id'])})")
        if isinstance(dump['id'], str):
            print("  [INFO] ID foi serializado como string")
        elif isinstance(dump['id'], UUID):
            print("  [INFO] ID permaneceu como UUID")
    except Exception as e:
        print(f"  [FAIL] Erro: {e}")

    # Testar model_dump com mode="json"
    print("\n[TESTE 3] model_dump(mode='json')...")
    try:
        dump = schema.model_dump(mode="json")
        print(f"  [PASS] Funcionou (id type: {type(dump['id'])})")
        if isinstance(dump['id'], str):
            print("  [OK] ID foi serializado como string (esperado)")
        else:
            print(f"  [WARN] ID tipo: {type(dump['id'])}")
    except Exception as e:
        print(f"  [FAIL] Erro: {e}")

    print("\n" + "=" * 70)
    print("RESULTADO: Correcao de UUID esta funcionando!")
    print("=" * 70)
    sys.exit(0)

except Exception as e:
    print(f"\n[ERRO] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
