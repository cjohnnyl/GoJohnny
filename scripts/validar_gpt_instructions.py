#!/usr/bin/env python3
"""Validar que gpt_instructions.md foi atualizado corretamente."""

import os
import sys

print("=" * 70)
print("VALIDACAO: docs/gpt_instructions.md")
print("=" * 70)

checks = []

def check(nome, condicao):
    """Registrar um check."""
    status = "PASS" if condicao else "FAIL"
    checks.append((status, nome))
    print(f"  [{status}] {nome}")

# Ler arquivo
file_path = "docs/gpt_instructions.md"
if not os.path.exists(file_path):
    print(f"\nFALHA: {file_path} nao encontrado!")
    sys.exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("\n[VALIDACOES]\n")

# Validação 1: Menciona 18 actions (não 14)
check("Menciona '18 Total' (atualizado de 14)", "## LISTAR AÇÕES (18 Total)" in content)

# Validação 2: Inclui as 4 novas actions
check("Menciona 'salvarMemoria'", "salvarMemoria" in content)
check("Menciona 'buscarResumoMemorias'", "buscarResumoMemorias" in content)
check("Menciona 'buscarMemorias'", "buscarMemorias" in content)
check("Menciona 'salvarResumoSemanal'", "salvarResumoSemanal" in content)

# Validação 3: Tem as 4 seções de regras obrigatórias
check("Tem 'REGRA DE MEMÓRIA'", "## REGRA DE MEMÓRIA (OBRIGATÓRIA)" in content)
check("Tem 'REGRA DE RESUMO SEMANAL'", "## REGRA DE RESUMO SEMANAL (OBRIGATÓRIA)" in content)
check("Tem 'REGRA DE RECUPERAÇÃO DE HISTÓRICO'", "## REGRA DE RECUPERAÇÃO DE HISTÓRICO (OBRIGATÓRIA)" in content)
check("Tem 'SESSÃO COM MEMÓRIA'", "## SESSÃO COM MEMÓRIA (OBRIGATÓRIA)" in content)

# Validação 4: Tem exemplos de uso
check("Tem exemplos de salvarMemoria", "POST /memorias/{apelido}" in content)
check("Tem exemplos de buscar memorias", "GET /memorias/{apelido}/buscar" in content)
check("Tem exemplos de resumo semanal", "POST /memorias/{apelido}/resumo-semanal" in content)

# Validação 5: Menciona contexto_resumo enriquecido
check("Menciona 'contexto_resumo' enriquecido", "ultima_semana" in content and "memorias_relevantes" in content)
check("Menciona 'alertas_treinador'", "alertas_treinador" in content)

# Validação 6: Menciona que nunca deve inventar histórico
check("Avisa: nunca inventar histórico", "Nunca responder \"acho que foi...\" ou inventar histórico" in content)

# Validação 7: Versão atualizada
check("Versão atualizada para 1.1.0", "Versão:** 1.1.0" in content)

# Validação 8: Menciona "Memória e Knowledge Base"
check("Seção 'Memória e Knowledge Base' listada", "### Memória e Knowledge Base (4)" in content)

# Resumo
print("\n" + "=" * 70)
passed = sum(1 for status, _ in checks if status == "PASS")
failed = sum(1 for status, _ in checks if status == "FAIL")

print(f"TOTAL: {passed}/{len(checks)} checks passaram")

if failed == 0:
    print("\nTODAS AS VALIDACOES PASSARAM!")
    print("\nArquivo docs/gpt_instructions.md foi atualizado com sucesso:")
    print("  - 18 actions listadas (era 14)")
    print("  - 4 novas actions de memoria incluidas")
    print("  - 4 seções de regras obrigatórias adicionadas")
    print("  - Exemplos e documentação completos")
    sys.exit(0)
else:
    print(f"\n{failed} validacoes falharam!")
    sys.exit(1)
