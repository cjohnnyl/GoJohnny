#!/usr/bin/env bash
# Backup completo pré-Fase 1 do GoJohnny
#
# OBJETIVO
#   Gerar um dump lógico das 3 tabelas (atletas, planos_semanais, checkins)
#   ANTES de aplicar a migration 002. Esse arquivo é a sua âncora de
#   rollback em caso de qualquer problema.
#
# QUANDO RODAR
#   - Antes de aplicar migrations/002_fase1_aditiva.sql
#   - Sempre que for fazer mudanças estruturais no banco
#
# COMO RODAR
#   1. Tenha pg_dump >= 14 instalado localmente (vem com PostgreSQL).
#      No Windows: https://www.postgresql.org/download/windows/
#      No macOS:  brew install postgresql@16
#
#   2. Pegue a DATABASE_URL no painel do Supabase
#      (Project Settings > Database > Connection string > URI).
#      Use o modo "Session" (porta 5432), NÃO o pooler 6543, porque
#      pg_dump precisa de conexão direta.
#
#   3. Defina a variável de ambiente DATABASE_URL e execute:
#         export DATABASE_URL="postgresql://postgres.[ref]:[senha]@aws-0-[region].compute.amazonaws.com:5432/postgres"
#         bash scripts/backup_pre_fase1.sh
#
#   4. Verifique que o arquivo gerado tem tamanho > 0 e abre como texto.
#
#   5. Guarde o arquivo .sql em local seguro (fora do repositório, fora
#      do drive sincronizado público). Sugestão: ~/backups/gojohnny/.
#
# COMO RESTAURAR (rollback)
#      psql "$DATABASE_URL" -f gojohnny_backup_<timestamp>.sql
#
#   IMPORTANTE: o restore com pg_dump --data-only assume que as tabelas
#   já existem com o schema de hoje. Se a Fase 1 já adicionou colunas
#   novas, o restore vai funcionar (colunas extras ficam NULL para os
#   dados restaurados).

set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERRO: variável de ambiente DATABASE_URL não definida." >&2
  echo "Veja as instruções no topo deste arquivo." >&2
  exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUT_DIR="${OUT_DIR:-./backups}"
mkdir -p "$OUT_DIR"

SCHEMA_FILE="$OUT_DIR/gojohnny_schema_${TIMESTAMP}.sql"
DATA_FILE="$OUT_DIR/gojohnny_data_${TIMESTAMP}.sql"
FULL_FILE="$OUT_DIR/gojohnny_full_${TIMESTAMP}.sql"

echo ">> Backup pré-Fase 1 do GoJohnny"
echo ">> Timestamp: $TIMESTAMP"
echo ">> Destino:   $OUT_DIR"
echo

echo "[1/3] Dump do schema das tabelas alvo..."
pg_dump "$DATABASE_URL" \
  --schema-only \
  --no-owner \
  --no-privileges \
  --table=public.atletas \
  --table=public.planos_semanais \
  --table=public.checkins \
  > "$SCHEMA_FILE"
echo "      $SCHEMA_FILE  ($(wc -c < "$SCHEMA_FILE") bytes)"

echo "[2/3] Dump dos dados (data-only, INSERTs explícitos)..."
pg_dump "$DATABASE_URL" \
  --data-only \
  --inserts \
  --no-owner \
  --no-privileges \
  --table=public.atletas \
  --table=public.planos_semanais \
  --table=public.checkins \
  > "$DATA_FILE"
echo "      $DATA_FILE  ($(wc -c < "$DATA_FILE") bytes)"

echo "[3/3] Dump combinado (schema + dados em arquivo único)..."
pg_dump "$DATABASE_URL" \
  --no-owner \
  --no-privileges \
  --table=public.atletas \
  --table=public.planos_semanais \
  --table=public.checkins \
  > "$FULL_FILE"
echo "      $FULL_FILE  ($(wc -c < "$FULL_FILE") bytes)"

echo
echo ">> Concluído com sucesso."
echo ">> Antes de prosseguir com a migration 002, confirme:"
echo "   - Os 3 arquivos têm tamanho > 0"
echo "   - Você guardou cópia FORA do repositório"
echo "   - Anotou no docs/runbooks/rollback.md o nome do arquivo full"
