# Handoff Fase 1 — GoJohnny

> Este documento existe para você (ou outra IA executora) retomar a Fase 1 do GoJohnny **sem perder contexto**. Leia primeiro este arquivo, depois `docs/QA_RELATORIO_FASE1.md`, depois `docs/runbooks/rollback.md`.

## Onde paramos

Branch `feat/fase-1` está com **toda a Fase 1 implementada e 102/102 testes verdes**. **Working tree tem 39 arquivos modificados/novos pendentes de commit.** O commit não foi feito a partir da sandbox de execução porque o filesystem do mount Windows não permitia ao git criar objects (`.git/objects/...: Operation not permitted`). **Você precisa commitar do Windows nativo** (PowerShell, Git Bash, ou seu IDE). Veja o passo 1 abaixo.

## Status das tasks (referência do briefing)

| # | Bloco | Status |
|---|-------|--------|
| 1 | Onboarding sem chamadas precoces | ✅ Resolvido nas instruções do GPT (`docs/gpt_instructions.md`) — falta Johnny aplicar |
| 2 | Identificação no início | ✅ `POST /sessao/iniciar` implementado |
| 3 | Continuidade entre chats | ✅ Mesmo endpoint retorna plano e contexto |
| 4 | Rollout seguro | ✅ Default false em todas as flags + arquitetura novo/existente |
| 5 | Feature flags | ✅ 4 colunas BOOLEAN dedicadas + `feature_flag_service.py` |
| 6 | Plano enriquecido | ✅ Campos novos opcionais + `versao_estrutura` |
| 7 | Engine de calendário | ✅ `services/calendar_engine.py` com 37 testes |
| 8 | Leitura tolerante | ✅ `services/plan_parser.py` com 25 testes |
| 9 | Proteção contra sobrescrita | ✅ 409 sem `novo_ciclo`, arquiva em vez de apagar |
| 10 | Contexto do atleta | ✅ Tabela + service + integração com onboarding |
| 11 | QA forte | ✅ 102 testes (71 unitários + 16 integração + 15 regressão/idempotência) |
| 12 | Documentação | ✅ README, runbook, gpt_instructions, QA, este handoff |

## O QUE AINDA FALTA (ações de Johnny, em ordem)

### 0. Limpar o `.git/index.lock` (se ainda existir)
A sandbox deixou um `.git/index.lock` que ela mesma não consegue apagar. No Windows nativo:
```powershell
del .git\index.lock
```

### 1. Commit + push da branch `feat/fase-1` — DO WINDOWS
```bash
cd C:\Users\Johnny\Projetos\GoJohnny
git status                        # confirmar branch feat/fase-1, 39 arquivos
git add .
git commit -m "feat(fase-1): sessao, feature flags, plano enriquecido, calendario, contexto, QA 102/102"
git push -u origin feat/fase-1
```
Em seguida, abra um PR `feat/fase-1 → main` no GitHub para revisão visual antes do deploy.

### 2. Pinar `requirements.txt` com versões de produção
No ambiente local (ou via shell do Render):
```bash
pip freeze > /tmp/freeze.txt
```
Cole o output no chat. Eu/IA atualizo o `requirements.txt` mantendo o mesmo conjunto de pacotes mas com versões pinadas. Não pinar agora aumenta risco de deploy quebrar por mudança transitiva.

### 3. Backup do Supabase (PRÉ-CONDIÇÃO obrigatória)
Caminho recomendado:
```bash
export DATABASE_URL="postgresql://postgres.[ref]:[senha]@aws-0-[region].compute.amazonaws.com:5432/postgres"
bash scripts/backup_pre_fase1.sh
```
Move `./backups/gojohnny_full_<timestamp>.sql` para fora do repositório (sugestão: `~/backups/gojohnny/`). Anote o filename.

Caminho alternativo (sem `pg_dump`): rode `scripts/backup_pre_fase1.sql` no SQL Editor do Supabase.

### 4. Aplicar migration 002
**SOMENTE APÓS o backup confirmado**:
```bash
psql "$DATABASE_URL" -f migrations/002_fase1_aditiva.sql
```
Ou colar o conteúdo no SQL Editor do Supabase. A query de verificação no final retorna `ok=1` em todas as linhas — confirmar.

A migration é 100% aditiva (4 colunas BOOLEAN em `atletas`, 4 colunas em `planos_semanais`, nova tabela `contexto_atleta`). Nenhuma coluna existente é tocada. Nenhum dado existente muda.

### 5. Atualizar instruções do Custom GPT
- Abra `docs/gpt_instructions.md`.
- Reveja cada bloco — cada parágrafo é uma decisão sua.
- Cole no painel da OpenAI: Custom GPT > Configure > Instructions (substituindo o anterior — guarde o texto antigo em algum lugar antes).

### 6. Atualizar Actions do Custom GPT
- Abra `openapi-gpt-actions.json` deste branch.
- No painel da OpenAI: Custom GPT > Configure > Actions > editar Schema.
- Substitua o JSON inteiro pelo conteúdo deste arquivo.
- Confirme que `/sessao/iniciar` aparece como Action disponível.

### 7. Deploy no Render
- Após PR aprovado e merge em `main`, o Render redeploya automaticamente.
- Smoke test em produção (ver runbook).

## Decisões arquiteturais já tomadas (não mexer sem motivo)

- **Identificador**: `apelido` (UNIQUE INDEX em `atletas`). Sem fuzzy match. Sem email na Fase 1.
- **Início de semana ISO**: segunda-feira.
- **Sobrescrita de plano**: 409 sem `novo_ciclo`, arquiva o anterior com `novo_ciclo=true`. Sem UNIQUE INDEX no banco para não falhar a migration.
- **Feature flags**: 4 colunas BOOLEAN dedicadas em `atletas`, default false.
- **Testes**: pytest contra Postgres real. `docker-compose.test.yml` no dev. `pgserver` (binário portátil) na sandbox como fallback.
- **Migrations**: SQL puro, sem Alembic (Fase 1). Migrar para Alembic é trabalho da Fase 2.

## Bugs conhecidos do ambiente de execução (sandbox)

### Mount Windows-em-Linux trunca arquivos médios/grandes
Sintoma: `Write` ou `Edit` retornam sucesso mas o arquivo no disco fica cortado. Solução adotada: escrever em `/tmp` primeiro e usar `cp` + `sync`:
```bash
cat > /tmp/foo.py <<'PYEOF'
...conteudo...
PYEOF
cp /tmp/foo.py app/foo.py
sync; sleep 0.2
```

### Mount Windows não deixa o git criar objects/lock
`Operation not permitted` no `.git/objects/*/tmp_obj_*` e no `.git/index.lock`. Solução: commitar do Windows nativo.

### Pycaches do mount não são deletados
`find -delete` falha silenciosamente nos `__pycache__/*.pyc`. Solução: rodar pytest com `PYTHONPYCACHEPREFIX=/tmp/pyc_gojohnny`.

### `exec_driver_sql` do SQLAlchemy 2 + psycopg2 quebra com `immutabledict`
Resolvido no `conftest.py`: aplico migrations via `psycopg2` puro com `set_isolation_level(AUTOCOMMIT)`.

### `pgserver` não tem extension `pgcrypto`
A migration tem um `DO $$ ... EXCEPTION WHEN feature_not_supported ...` que tenta criar e segue mesmo se falhar. Em PG 13+ `gen_random_uuid()` é built-in. O Supabase tem pgcrypto; em produção não há diferença.

### CRLF vs LF
`core.autocrlf` no clone Windows estava vazio. A sandbox setou `git config core.autocrlf input` localmente para que `git add` normalize CRLF→LF nos novos commits.

## Como retomar daqui (próxima sessão)

Em uma nova sessão de Cowork (ou Claude Code), comece com **este arquivo + `docs/QA_RELATORIO_FASE1.md`**. Em seguida:

1. Confira o status do git: `git status`, `git log --oneline -5`, `git branch`.
2. Rode a suite e confirme que ainda está verde:
   ```bash
   pip install -r requirements-dev.txt
   docker compose -f docker-compose.test.yml up -d
   export TEST_DATABASE_URL=postgresql://gojohnny:gojohnny@localhost:55432/gojohnny_test
   pytest -v
   ```
   Resultado esperado: `102 passed`.
3. Avance pelos itens "O QUE AINDA FALTA" acima, em ordem.

## Sumário rápido de comandos úteis

```bash
# Ver todas as rotas registradas
python -c "from app.main import app; [print(sorted(r.methods or []), r.path) for r in app.routes if hasattr(r,'methods')]"

# Smoke test em produção (após deploy)
curl https://gojohnny.onrender.com/health
curl -X POST https://gojohnny.onrender.com/sessao/iniciar \
  -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"apelido": "johnny"}'
```

## Inventário de arquivos da Fase 1

**Modificados:**
- `README.md`, `app/main.py`, `app/models/atleta.py`, `app/models/plano_semanal.py`,
  `app/routes/planos_semanais.py`, `app/schemas/atleta.py`, `app/schemas/plano_semanal.py`,
  `openapi-gpt-actions.json`, `.gitignore`

**Novos:**
- `app/models/contexto_atleta.py`
- `app/routes/sessao.py`
- `app/schemas/contexto_atleta.py`, `app/schemas/sessao.py`
- `app/services/calendar_engine.py`, `app/services/context_service.py`,
  `app/services/feature_flag_service.py`, `app/services/plan_parser.py`,
  `app/services/plano_service.py`, `app/services/session_service.py`
- `migrations/002_fase1_aditiva.sql`
- `scripts/backup_pre_fase1.sh`, `scripts/backup_pre_fase1.sql`
- `docs/HANDOFF_FASE1.md`, `docs/QA_RELATORIO_FASE1.md`,
  `docs/gpt_instructions.md`, `docs/runbooks/rollback.md`
- `tests/__init__.py`, `tests/conftest.py`,
  `tests/integration/__init__.py`, `tests/integration/test_api_integration.py`,
  `tests/services/__init__.py`, `tests/services/test_calendar_engine.py`,
  `tests/services/test_context_service_unit.py`, `tests/services/test_feature_flag_service.py`,
  `tests/services/test_plan_parser.py`, `tests/services/test_plano_service_unit.py`
- `docker-compose.test.yml`, `pytest.ini`, `requirements-dev.txt`
