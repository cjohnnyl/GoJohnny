# Runbook — Backup, Deploy e Rollback da Fase 1

## Pré-condições antes de qualquer mudança em produção

- [ ] Branch `feat/fase-1` mergeada em revisão (PR aprovado).
- [ ] Backup pré-Fase 1 gerado (ver "Backup" abaixo) e arquivado em local seguro.
- [ ] Suite de testes verde localmente: `pytest` retorna `102 passed`.
- [ ] `requirements.txt` pinado com versões reais de produção (rodar `pip freeze` no ambiente atual e atualizar).
- [ ] `docs/gpt_instructions.md` revisado e aplicado no painel do Custom GPT.

## Backup

Caminho recomendado (`pg_dump`):
```bash
export DATABASE_URL="postgresql://postgres.[ref]:[senha]@aws-0-[region].compute.amazonaws.com:5432/postgres"
bash scripts/backup_pre_fase1.sh
```
Saída em `./backups/gojohnny_full_<timestamp>.sql`. **Mover este arquivo para fora do repositório**.

Caminho alternativo (sem `pg_dump`): rodar `scripts/backup_pre_fase1.sql` no SQL Editor do Supabase. Cria 3 tabelas `*_backup_pre_fase1` no mesmo banco.

## Deploy

1. Aplicar migration:
   ```bash
   psql "$DATABASE_URL" -f migrations/002_fase1_aditiva.sql
   ```
   Ou colar no SQL Editor do Supabase.
2. Confirmar resultado: a query final retorna `ok=1` em todas as linhas.
3. Push da branch `feat/fase-1` para `main` (ou merge do PR). O Render redeploya automaticamente.
4. Aplicar `docs/gpt_instructions.md` no Custom GPT, atualizar o JSON de Actions com `openapi-gpt-actions.json` deste branch.
5. Smoke test em produção:
   - `GET /health` → `{"status": "ok"}`
   - `POST /sessao/iniciar` com apelido conhecido → status `existente`
   - `POST /sessao/iniciar` com apelido inventado → status `novo`

## Rollback

### Rollback do código (Render)
- Painel do Render → Service `gojohnny-api` → Deploys → escolher o deploy anterior → "Redeploy".
- Em paralelo, no GitHub: `git revert <merge-commit>` ou rebase, conforme política de branches.

### Rollback do schema (banco)
A migration 002 é aditiva. Reverter executando:
```sql
BEGIN;
  ALTER TABLE public.atletas
    DROP COLUMN IF EXISTS usar_datas_reais,
    DROP COLUMN IF EXISTS usar_contexto_atleta,
    DROP COLUMN IF EXISTS usar_google_calendar,
    DROP COLUMN IF EXISTS usar_strava;
  ALTER TABLE public.planos_semanais
    DROP COLUMN IF EXISTS data_inicio,
    DROP COLUMN IF EXISTS data_prova,
    DROP COLUMN IF EXISTS dias_treino_json,
    DROP COLUMN IF EXISTS versao_estrutura;
  DROP TABLE IF EXISTS public.contexto_atleta;
COMMIT;
```
**Só faça isso se NENHUM dado relevante novo foi gravado**. Se houver, restore do backup.

### Rollback do dados
```bash
psql "$DATABASE_URL" -f gojohnny_full_<timestamp>.sql
```

## Janela de mudança recomendada
- Horário de baixo uso (madrugada SP).
- Comunicar usuários ativos previamente, se houver.
