# Relatório de QA — Fase 1 GoJohnny

**Data:** 2026-05-03
**Branch:** `feat/fase-1`
**Commit base:** `0c36857`

## Resumo executivo

102 testes automatizados executados, **102 passaram, 0 falharam** em 1.35s.

Cobertura por bloco do briefing:

| Bloco | Funcionalidade | Testes | Status |
|-------|---------------|-------:|--------|
| 1     | Onboarding sem chamadas precoces | n/a (responsabilidade do GPT, doc em `docs/gpt_instructions.md`) | Documentado |
| 2     | Identificação no início (POST /sessao/iniciar) | 4 | ✅ |
| 3     | Continuidade entre chats | 4 | ✅ |
| 4     | Rollout seguro novos vs existentes | implícito nos cenários A/B/D | ✅ |
| 5     | Feature flags por atleta | 9 unit + 1 integração | ✅ |
| 6     | Plano enriquecido com datas reais | 7 unit + cenário E | ✅ |
| 7     | Engine de calendário | 37 unit | ✅ |
| 8     | Leitura tolerante do plano | 25 unit | ✅ |
| 9     | Proteção contra sobrescrita | 2 integração + 7 unit | ✅ |
| 10    | Estrutura inicial de contexto | 8 unit + 1 integração | ✅ |
| 11    | Validação e QA | suite pytest completa | ✅ |
| 12    | README + runbook + handoff | docs/ + README atualizados | ✅ |

## Cenários A–E executados

### Cenário A — Usuário novo em chat novo
- `POST /sessao/iniciar` com apelido inexistente → `status = "novo"`, sem dados, instrução de onboarding.
- Após `POST /atletas`, `POST /sessao/iniciar` passa a retornar `status = "existente"` com o atleta preenchido.

### Cenário B — Usuário existente em chat novo
- Sem plano ativo: `status = "existente"`, `plano_atual = null`, instrução pede continuação sem reonboarding.
- Com plano ativo: o plano correto é retornado, com `versao_estrutura` correta para legado/enriquecido.

### Cenário C — Plano antigo continua legível
- Plano salvo com formato legado (sem datas) é lido sem erro.
- `data_inicio`, `data_prova`, `dias_treino_json` retornam `null`.
- `versao_estrutura = 1`.

### Cenário D — Feature flag desligada por padrão
- Atleta criado tem todas as 4 flags em `false`.
- Comportamento legado preservado.

### Cenário E — Plano enriquecido
- POST com `data_inicio`, `data_prova`, `dias_treino_json` cria plano com `versao_estrutura = 2`.
- Heurística do parser e do plano_service detecta corretamente a versão.

## Proteção contra sobrescrita

- 2º POST sem `novo_ciclo` → **409** com payload estruturado e instrução de como proceder.
- 2º POST com `novo_ciclo=true` → **201**, plano anterior automaticamente marcado como `arquivado`. `GET /atual` passa a retornar o novo. Nada é deletado.

## Idempotência

- 3 chamadas seguidas a `POST /sessao/iniciar` para o mesmo apelido não criam atleta nem entradas extras de contexto.
- `salvar_contexto` com mesma `(atleta_id, tipo, chave)` faz UPDATE, não INSERT.

## Regressão

- `POST /atletas` com apelido duplicado continua devolvendo **409**.
- `PATCH /atletas/{apelido}` continua atualizando campo individual.
- `POST /checkins` continua aceitando o payload atual sem mudanças.
- `GET /checkins/{apelido}` continua ordenando decrescente por `semana_inicio`.
- `GET /health` continua sem auth.

## Critérios de bloqueio de deploy (do briefing)

| Critério | Status |
|----------|--------|
| Múltiplas autorizações ainda acontecem | ✅ Resolvido (instruções GPT + endpoint único de sessão) |
| Usuário existente perde continuidade | ✅ Resolvido (POST /sessao/iniciar retorna plano e contexto) |
| Plano existente alterado sem consentimento | ✅ Resolvido (409 sem `novo_ciclo`) |
| Engine de calendário gera datas erradas | ✅ 37 testes cobrem incluindo virada de ano |
| Parsing do plano quebra com dado antigo | ✅ 25 testes contra planos legados e malformados |
| Endpoint de sessão falha em identificar | ✅ Cobertura novo/existente/sem plano/com plano |
| README não foi atualizado | ✅ README + docs/HANDOFF_FASE1.md + runbooks/ |
| Rollback não foi documentado | ✅ docs/runbooks/rollback.md e migrations/002_*.sql |
| Testes não foram executados e registrados | ✅ Este relatório + 102 testes verdes |

## Como reproduzir

```bash
# 1. Postgres de teste
docker compose -f docker-compose.test.yml up -d
export TEST_DATABASE_URL=postgresql://gojohnny:gojohnny@localhost:55432/gojohnny_test

# 2. Dependências de teste
pip install -r requirements-dev.txt

# 3. Rodar
pytest -v
```

A sandbox de desenvolvimento usa `pgserver` (binário portátil de Postgres) como fallback quando `TEST_DATABASE_URL` não está definida — o conftest sobe automaticamente.

## Pontos abertos

- Não há ambiente de staging. A migration 002 será aplicada direto em produção (Supabase) após backup.
- `requirements.txt` ainda não está pinado em versões de produção — depende do `pip freeze` que Johnny vai rodar localmente.
- Custom GPT instructions ainda não foram aplicadas no painel da OpenAI — depende de revisão manual de Johnny em `docs/gpt_instructions.md`.
