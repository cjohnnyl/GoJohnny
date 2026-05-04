-- ============================================================================
-- Migration: 002_fase1_aditiva
-- Data: 2026-05-02
-- Branch: feat/fase-1
-- Pré-requisito: ter executado scripts/backup_pre_fase1.sh OU
--                scripts/backup_pre_fase1.sql ANTES desta migration.
--
-- PROPÓSITO
--   Preparar o banco para a Fase 1 do GoJohnny de forma 100% aditiva:
--     - feature flags por atleta (4 colunas BOOLEAN com default false)
--     - tabela contexto_atleta para memória persistente do atleta
--     - campos opcionais em planos_semanais para datas reais e versão de
--       estrutura, mantendo compatibilidade total com planos atuais
--
-- GARANTIAS
--   - Nenhuma coluna existente é renomeada
--   - Nenhuma coluna existente é removida
--   - Nenhuma coluna existente passa a ser NOT NULL nesta migration
--   - Todos os ADD COLUMN são idempotentes (IF NOT EXISTS)
--   - Defaults seguros para usuários atuais (flags = false)
--   - Sem constraint UNIQUE nova em planos_semanais — a regra de
--     "um plano ativo por atleta" é aplicada em código (service),
--     justamente para não falhar a migration caso existam duplicações
--     históricas em produção que ainda não foram inspecionadas.
--
-- COMO RODAR
--   1. Confirme que o backup pré-Fase 1 foi gerado e guardado.
--   2. Abra o SQL Editor do Supabase OU rode via psql contra o
--      DATABASE_URL de produção.
--   3. Cole TODO o conteúdo deste arquivo.
--   4. Execute. Postgres roda o script inteiro em uma única transação.
--   5. Inspecione o resultado da query final de verificação.
--
-- COMO REVERTER
--   Esta migration é aditiva. Reverter consiste em rodar:
--     BEGIN;
--       ALTER TABLE public.atletas
--         DROP COLUMN IF EXISTS usar_datas_reais,
--         DROP COLUMN IF EXISTS usar_contexto_atleta,
--         DROP COLUMN IF EXISTS usar_google_calendar,
--         DROP COLUMN IF EXISTS usar_strava;
--       ALTER TABLE public.planos_semanais
--         DROP COLUMN IF EXISTS data_inicio,
--         DROP COLUMN IF EXISTS data_prova,
--         DROP COLUMN IF EXISTS dias_treino_json,
--         DROP COLUMN IF EXISTS versao_estrutura;
--       DROP TABLE IF EXISTS public.contexto_atleta;
--     COMMIT;
--   IMPORTANTE: só reverta se nenhum dado relevante já tiver sido
--   gravado nas novas colunas/tabela. Se houver, restaure do backup.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) Garantir extension necessária para gen_random_uuid().
--    Supabase normalmente já tem pgcrypto habilitada, mas garantimos.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  -- pgcrypto e usada para gen_random_uuid() em PG < 13.
  -- Em PG 13+, gen_random_uuid() ja e nativo. Em ambientes onde a
  -- extension nao esta disponivel (alguns binarios portateis), seguimos
  -- sem ela e a funcao continua disponivel pela built-in.
  BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
  EXCEPTION WHEN feature_not_supported THEN
    RAISE NOTICE 'pgcrypto nao disponivel - usando gen_random_uuid() built-in (PG 13+).';
  END;
END$$;

-- ---------------------------------------------------------------------------
-- 2) Feature flags por atleta (Bloco 5)
--    Default false significa que TODOS os usuários existentes mantêm o
--    comportamento atual. Apenas usuários novos ou explicitamente migrados
--    receberão flags em true. A leitura/escrita acontece via
--    services/feature_flag_service.py (centralizada).
-- ---------------------------------------------------------------------------
ALTER TABLE public.atletas
  ADD COLUMN IF NOT EXISTS usar_datas_reais     BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS usar_contexto_atleta BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS usar_google_calendar BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS usar_strava          BOOLEAN NOT NULL DEFAULT false;

-- ---------------------------------------------------------------------------
-- 3) Campos opcionais em planos_semanais (Bloco 6)
--    Permitem que NOVOS planos descrevam datas reais e dias de treino
--    estruturados. Planos antigos não usam esses campos e continuam
--    funcionando — todos NULL por padrão.
--
--    versao_estrutura indica para o plan_parser qual schema está dentro
--    do JSONB "plano":
--      1 = formato atual (legado), sem datas
--      2 = formato enriquecido com datas reais (Fase 1)
-- ---------------------------------------------------------------------------
ALTER TABLE public.planos_semanais
  ADD COLUMN IF NOT EXISTS data_inicio       DATE     NULL,
  ADD COLUMN IF NOT EXISTS data_prova        DATE     NULL,
  ADD COLUMN IF NOT EXISTS dias_treino_json  JSONB    NULL,
  ADD COLUMN IF NOT EXISTS versao_estrutura  SMALLINT NOT NULL DEFAULT 1;

COMMENT ON COLUMN public.planos_semanais.data_inicio
  IS 'Data real de início do plano. NULL para planos antigos sem datas.';
COMMENT ON COLUMN public.planos_semanais.data_prova
  IS 'Data da prova alvo. NULL se não houver ou se for plano antigo.';
COMMENT ON COLUMN public.planos_semanais.dias_treino_json
  IS 'Array de strings com os dias da semana do treino, ex: ["segunda","quarta","sexta"].';
COMMENT ON COLUMN public.planos_semanais.versao_estrutura
  IS '1=legado (sem datas), 2=enriquecido com datas reais (Fase 1).';

-- ---------------------------------------------------------------------------
-- 4) Tabela contexto_atleta (Bloco 10)
--    Estrutura inicial de memória persistente do atleta. Apenas a estrutura
--    e a gravação a partir do onboarding são feitas na Fase 1. Extração
--    automática contínua e uso massivo no prompt ficam para a Fase 2.
--
--    Modelo chave/valor com tipo (categoria), confianca (0..1) e origem
--    rastreável. UNIQUE (atleta_id, tipo, chave) evita duplicação cega:
--    a mesma chave dentro do mesmo tipo só existe uma vez por atleta;
--    novas observações para a mesma chave passam por UPDATE no service.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.contexto_atleta (
  id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id      UUID         NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  tipo           TEXT         NOT NULL,
  chave          TEXT         NOT NULL,
  valor          TEXT         NULL,
  confianca      NUMERIC(3,2) NOT NULL DEFAULT 1.0
                 CHECK (confianca >= 0 AND confianca <= 1),
  origem         TEXT         NOT NULL,
  criado_em      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  atualizado_em  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT uniq_contexto_atleta_chave UNIQUE (atleta_id, tipo, chave)
);

CREATE INDEX IF NOT EXISTS idx_contexto_atleta_atleta_id
  ON public.contexto_atleta (atleta_id);

CREATE INDEX IF NOT EXISTS idx_contexto_atleta_atleta_tipo
  ON public.contexto_atleta (atleta_id, tipo);

COMMENT ON TABLE public.contexto_atleta
  IS 'Memória persistente do atleta. Modelo chave/valor com origem rastreável.';
COMMENT ON COLUMN public.contexto_atleta.tipo
  IS 'Categoria do contexto. Ex: objetivo, historico, preferencia.';
COMMENT ON COLUMN public.contexto_atleta.chave
  IS 'Identificador da informação dentro do tipo. Ex: dias_treino, pace_confortavel.';
COMMENT ON COLUMN public.contexto_atleta.confianca
  IS 'Grau de confiança da informação (0..1). 1.0 quando dado pelo próprio atleta.';
COMMENT ON COLUMN public.contexto_atleta.origem
  IS 'De onde veio o dado. Ex: onboarding, checkin, manual.';

-- ---------------------------------------------------------------------------
-- 5) Verificação final (não altera estado, apenas reporta)
-- ---------------------------------------------------------------------------
SELECT 'atletas.usar_datas_reais existe'         AS check, COUNT(*) AS ok
FROM information_schema.columns
WHERE table_schema='public' AND table_name='atletas' AND column_name='usar_datas_reais'
UNION ALL
SELECT 'atletas.usar_contexto_atleta existe',    COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='atletas' AND column_name='usar_contexto_atleta'
UNION ALL
SELECT 'atletas.usar_google_calendar existe',    COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='atletas' AND column_name='usar_google_calendar'
UNION ALL
SELECT 'atletas.usar_strava existe',             COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='atletas' AND column_name='usar_strava'
UNION ALL
SELECT 'planos_semanais.data_inicio existe',     COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='planos_semanais' AND column_name='data_inicio'
UNION ALL
SELECT 'planos_semanais.data_prova existe',      COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='planos_semanais' AND column_name='data_prova'
UNION ALL
SELECT 'planos_semanais.dias_treino_json existe', COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='planos_semanais' AND column_name='dias_treino_json'
UNION ALL
SELECT 'planos_semanais.versao_estrutura existe', COUNT(*)
FROM information_schema.columns
WHERE table_schema='public' AND table_name='planos_semanais' AND column_name='versao_estrutura'
UNION ALL
SELECT 'contexto_atleta tabela existe',           COUNT(*)
FROM information_schema.tables
WHERE table_schema='public' AND table_name='contexto_atleta';
-- Cada linha deve retornar ok=1.

COMMIT;
