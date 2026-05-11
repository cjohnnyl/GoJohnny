# Plano de Execução — Correções P0 e P1 GoJohnny

Data: 2026-05-11
Status: Em execução

## Análise pré-execução

### P0 — Correções críticas

#### P0.1 — Padronizar erro de Strava sem conexão
- **Status:** ✅ JÁ IMPLEMENTADO
- **Evidência:** `strava_service.py:637` lança `PermissionError("Sem token Strava valido. Reconectar.")`
- **Rotas:** `treino-hoje`, `treinos-recentes`, `treinos-semana`, `atividade`, `analisar-treino`, `analisar-semana`, `treinos-ultimos-dias` todas tratam com 409
- **Ação necessária:** Nenhuma. Já funciona conforme esperado.

#### P0.2 — Garantir isolamento entre usuários
- **Status:** ⚠️ PRECISA REVIEW E AJUSTES
- **Achados:**
  - Strava queries usam `atleta_id` ✓
  - Planos queries usam `atleta_id` ✓
  - Memórias queries usam `atleta_id` ✓
  - Contexto queries usam `atleta_id` ✓
- **Ação necessária:** 
  1. Revisar `get_atleta_by_apelido` — certifica-se que normaliza apelido
  2. Testar isolamento após fix de case-sensitivity

#### P0.3 — Criar logs estruturados com request_id
- **Status:** ❌ NÃO IMPLEMENTADO
- **Arquivos envolvidos:** `app/main.py`, novo `app/core/logging.py`
- **Ação necessária:**
  1. Criar middleware de request_id
  2. Logar: request_id, method, path, apelido, status, duration_ms, error_type
  3. Nunca logar: x-api-key, tokens, auth headers

#### P0.4 — Melhorar resposta para timeout, 503, cold start
- **Status:** ⚠️ PARCIAL
- **Atual:** Render pode retornar 503, mas não trata com mensagem amigável
- **Ação necessária:**
  1. Adicionar global exception handler para `TimeoutError` e `ConnectionError`
  2. Retornar mensagem: "O sistema pode estar acordando. Tente novamente em alguns segundos."

### P1 — Correções importantes

#### P1.1 — Criar endpoint de cleanup para QA
- **Status:** ❌ NÃO IMPLEMENTADO
- **Arquivo novo:** `app/routes/qa.py`
- **Endpoint:** `DELETE /qa/cleanup/{apelido}`
- **Regras:**
  - Apenas apelidos com prefixo `qa_`
  - Exigir x-api-key
  - Remover: atleta, planos, check-ins, memórias, contexto, conexões OAuth, cache Strava

#### P1.2 — Separar API key de QA
- **Status:** ⚠️ PARCIAL
- **Atual:** Uma chave única em `GJ_API_KEY`
- **Ação:** Suportar múltiplas chaves (lista separada por vírgula em `GJ_API_KEYS`)

#### P1.3 — Classificar rotas POST por risco
- **Status:** ⚠️ DOCUMENTAÇÃO
- **Ação:** Adicionar comentários em docstrings indicando risco: safe_read, alters_state, qa_only, requires_confirmation, dangerous_in_production

#### P1.4 — Criar suíte de testes automatizados
- **Status:** ❌ NÃO IMPLEMENTADO
- **Arquivo:** `tests/test_qa_suite.py`
- **Testes:** healthcheck, auth, johnny read-only, usuario inexistente, qa crud, isolamento, payload inválido, cleanup

#### P1.5 — Atualizar OpenAPI
- **Status:** ⚠️ DEPENDE DE MUDANÇAS
- **Ação:** Após implementar, gerar novo OpenAPI

---

## Arquivos a alterar

| Arquivo | Mudança | P0/P1 | Prioridade |
|---|---|---|---|
| `app/core/utils.py` (novo) | Helper `normalize_apelido()` | P0 | 1 |
| `app/routes/atletas.py` | Normalizar lookup de apelido | P0 | 1 |
| `app/routes/calendario.py` | Normalizar lookup de apelido | P0 | 2 |
| `app/routes/oauth.py` | Normalizar lookup de apelido (3 casos) | P0 | 2 |
| `app/routes/sessao.py` | Revisar normalização | P0 | 2 |
| `app/routes/planos_semanais.py` | Revisar normalização | P0 | 2 |
| `app/routes/contexto.py` | Revisar normalização | P0 | 2 |
| `app/routes/checkins.py` | Revisar normalização | P0 | 2 |
| `app/routes/memorias.py` | Revisar normalização | P0 | 2 |
| `app/main.py` | Adicionar middleware request_id | P0 | 3 |
| `app/core/logging.py` (novo) | Logging estruturado | P0 | 3 |
| `app/routes/qa.py` (novo) | Cleanup endpoint | P1 | 4 |
| `app/core/auth.py` | Suportar múltiplas API keys | P1 | 5 |
| `tests/test_qa_suite.py` (novo) | Testes automatizados | P1 | 6 |

---

## Execução sequencial

1. ✅ P0.1 — Já implementado
2. 🔄 P0.2 — Review e normalização de apelido
3. 🔄 P0.3 — Middleware request_id
4. 🔄 P0.4 — Global exception handler
5. 🔄 P1.1 — Cleanup endpoint
6. 🔄 P1.2 — Múltiplas API keys
7. 🔄 P1.3 — Documentação de risco
8. 🔄 P1.4 — Testes automatizados
9. 🔄 P1.5 — Atualizar OpenAPI

---

## Testes pós-execução

Para cada mudança:
1. Rodar suite automatizada (`pytest`)
2. Testar johnny read-only (sem alterar)
3. Criar/limpar qa_test_{ts}
4. Validar isolamento (qa vs johnny)

---

## Estimativas

| Item | Esforço | Tempo |
|---|---|---|
| P0.2 normalização | Baixo | 15 min |
| P0.3 logging | Médio | 30 min |
| P0.4 exception handler | Baixo | 15 min |
| P1.1 cleanup endpoint | Baixo | 20 min |
| P1.2 múltiplas chaves | Médio | 20 min |
| P1.3 documentação | Baixo | 10 min |
| P1.4 testes | Alto | 45 min |
| P1.5 OpenAPI | Baixo | 10 min |
| Testes finais | Médio | 30 min |
| **Total** | | **~3h** |
