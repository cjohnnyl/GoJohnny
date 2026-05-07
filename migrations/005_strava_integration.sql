-- ============================================================================
-- Migration: 005_strava_integration
-- Data: 2026-05-06
-- Proposito:
--   Integracao Strava (FASE 1 do plano de integracao).
--   Strava e fonte de evidencia, nunca de decisao.
--   Toda consulta exige consentimento explicito do atleta.
--
-- Tabelas:
--   1. strava_preferences           - Preferencia do atleta sobre Strava
--   2. strava_connections           - Conexao OAuth + tokens (criptografados pelo backend)
--   3. strava_activity_cache        - Cache de atividades (resumo + detalhe)
--   4. strava_activity_streams_cache- Cache de streams ponto-a-ponto (uso futuro)
--   5. strava_training_analysis     - Analises planejado vs executado
--   6. strava_sync_logs             - Auditoria de chamadas a API Strava
-- ============================================================================

BEGIN;

-- pgcrypto (gen_random_uuid)
DO $$
BEGIN
  BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
  EXCEPTION WHEN feature_not_supported THEN
    RAISE NOTICE 'pgcrypto nao disponivel - usando gen_random_uuid() built-in (PG 13+).';
  END;
END$$;


-- ---------------------------------------------------------------------------
-- Trigger function para atualizar coluna atualizado_em
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.atualizado_em = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ---------------------------------------------------------------------------
-- 1. Preferencia Strava do atleta
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strava_preferences (
  id                       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id                UUID         NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  usa_strava               BOOLEAN      NULL,
  perguntar_strava         BOOLEAN      NOT NULL DEFAULT TRUE,
  oferta_conexao_exibida   BOOLEAN      NOT NULL DEFAULT FALSE,
  ultima_resposta_usuario  TEXT         NULL,
  origem                   TEXT         NOT NULL DEFAULT 'conversa',
  criado_em                TIMESTAMPTZ  NOT NULL DEFAULT now(),
  atualizado_em            TIMESTAMPTZ  NOT NULL DEFAULT now(),
  UNIQUE (atleta_id)
);

CREATE INDEX IF NOT EXISTS idx_strava_preferences_atleta_id
  ON public.strava_preferences (atleta_id);

DROP TRIGGER IF EXISTS trg_strava_preferences_updated_at ON public.strava_preferences;
CREATE TRIGGER trg_strava_preferences_updated_at
BEFORE UPDATE ON public.strava_preferences
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE  public.strava_preferences IS 'Preferencia do atleta sobre uso de Strava. usa_strava=NULL significa desconhecido.';
COMMENT ON COLUMN public.strava_preferences.usa_strava        IS 'TRUE = usuario usa Strava; FALSE = nao usa; NULL = ainda nao perguntado.';
COMMENT ON COLUMN public.strava_preferences.perguntar_strava  IS 'Se FALSE, GoJohnny nao deve insistir em oferecer Strava.';
COMMENT ON COLUMN public.strava_preferences.oferta_conexao_exibida IS 'Marca se ja oferecemos conexao para evitar repeticao no chat.';


-- ---------------------------------------------------------------------------
-- 2. Conexao OAuth Strava (tokens criptografados)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strava_connections (
  id                       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id                UUID         NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  strava_athlete_id        BIGINT       NOT NULL,
  access_token_encrypted   TEXT         NOT NULL,
  refresh_token_encrypted  TEXT         NOT NULL,
  expires_at               BIGINT       NOT NULL,
  expires_at_ts            TIMESTAMPTZ  NULL,
  token_type               TEXT         DEFAULT 'Bearer',
  scope                    TEXT         NULL,
  connected_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
  last_refresh_at          TIMESTAMPTZ  NULL,
  last_sync_at             TIMESTAMPTZ  NULL,
  active                   BOOLEAN      NOT NULL DEFAULT TRUE,
  revoked_at               TIMESTAMPTZ  NULL,
  raw_athlete_json         JSONB        NULL,
  criado_em                TIMESTAMPTZ  NOT NULL DEFAULT now(),
  atualizado_em            TIMESTAMPTZ  NOT NULL DEFAULT now(),
  UNIQUE (atleta_id),
  UNIQUE (strava_athlete_id)
);

CREATE INDEX IF NOT EXISTS idx_strava_connections_atleta_id
  ON public.strava_connections (atleta_id);

CREATE INDEX IF NOT EXISTS idx_strava_connections_active
  ON public.strava_connections (active);

DROP TRIGGER IF EXISTS trg_strava_connections_updated_at ON public.strava_connections;
CREATE TRIGGER trg_strava_connections_updated_at
BEFORE UPDATE ON public.strava_connections
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE  public.strava_connections IS 'Conexao OAuth Strava por atleta. Tokens armazenados criptografados (Fernet via STRAVA_TOKEN_ENCRYPTION_KEY).';
COMMENT ON COLUMN public.strava_connections.access_token_encrypted  IS 'Access token criptografado pelo backend. Nunca armazenar em texto puro.';
COMMENT ON COLUMN public.strava_connections.refresh_token_encrypted IS 'Refresh token criptografado pelo backend. Nunca armazenar em texto puro.';
COMMENT ON COLUMN public.strava_connections.expires_at              IS 'Epoch (segundos) quando o access token expira (campo nativo Strava).';
COMMENT ON COLUMN public.strava_connections.expires_at_ts           IS 'Mesmo valor de expires_at em timestamptz para queries SQL.';


-- ---------------------------------------------------------------------------
-- 3. Cache de atividades Strava
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strava_activity_cache (
  id                          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id                   UUID         NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  strava_activity_id          BIGINT       NOT NULL,
  name                        TEXT         NULL,
  sport_type                  TEXT         NULL,
  type                        TEXT         NULL,
  start_date                  TIMESTAMPTZ  NULL,
  start_date_local            TIMESTAMPTZ  NULL,
  timezone                    TEXT         NULL,
  distance_m                  NUMERIC(12,2) NULL,
  moving_time_s               INTEGER      NULL,
  elapsed_time_s              INTEGER      NULL,
  total_elevation_gain_m      NUMERIC(10,2) NULL,
  average_speed_mps           NUMERIC(10,4) NULL,
  max_speed_mps               NUMERIC(10,4) NULL,
  average_pace_sec_km         INTEGER      NULL,
  average_pace_text           TEXT         NULL,
  average_heartrate           NUMERIC(8,2) NULL,
  max_heartrate               NUMERIC(8,2) NULL,
  average_cadence             NUMERIC(8,2) NULL,
  average_watts               NUMERIC(8,2) NULL,
  weighted_average_watts      NUMERIC(8,2) NULL,
  kilojoules                  NUMERIC(10,2) NULL,
  calories                    NUMERIC(10,2) NULL,
  suffer_score                INTEGER      NULL,
  has_heartrate               BOOLEAN      NULL,
  elev_high                   NUMERIC(10,2) NULL,
  elev_low                    NUMERIC(10,2) NULL,
  private                     BOOLEAN      NULL,
  visibility                  TEXT         NULL,
  raw_summary_json            JSONB        NULL,
  raw_detail_json             JSONB        NULL,
  synced_summary_at           TIMESTAMPTZ  NULL,
  synced_detail_at            TIMESTAMPTZ  NULL,
  criado_em                   TIMESTAMPTZ  NOT NULL DEFAULT now(),
  atualizado_em               TIMESTAMPTZ  NOT NULL DEFAULT now(),
  UNIQUE (atleta_id, strava_activity_id)
);

CREATE INDEX IF NOT EXISTS idx_strava_activity_cache_atleta_data
  ON public.strava_activity_cache (atleta_id, start_date_local DESC);

CREATE INDEX IF NOT EXISTS idx_strava_activity_cache_activity_id
  ON public.strava_activity_cache (strava_activity_id);

CREATE INDEX IF NOT EXISTS idx_strava_activity_cache_sport_type
  ON public.strava_activity_cache (sport_type);

DROP TRIGGER IF EXISTS trg_strava_activity_cache_updated_at ON public.strava_activity_cache;
CREATE TRIGGER trg_strava_activity_cache_updated_at
BEFORE UPDATE ON public.strava_activity_cache
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE  public.strava_activity_cache IS 'Cache de atividades Strava por atleta. Evita re-bater na API.';
COMMENT ON COLUMN public.strava_activity_cache.average_pace_sec_km IS 'Pace medio derivado em segundos por km (calculado pelo backend).';


-- ---------------------------------------------------------------------------
-- 4. Cache de streams Strava (uso futuro)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strava_activity_streams_cache (
  id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id           UUID         NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  strava_activity_id  BIGINT       NOT NULL,
  stream_types        TEXT[]       NOT NULL,
  streams_json        JSONB        NOT NULL,
  resolution          TEXT         NULL,
  series_type         TEXT         NULL,
  synced_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
  criado_em           TIMESTAMPTZ  NOT NULL DEFAULT now(),
  UNIQUE (atleta_id, strava_activity_id, stream_types)
);

CREATE INDEX IF NOT EXISTS idx_strava_streams_atleta_activity
  ON public.strava_activity_streams_cache (atleta_id, strava_activity_id);

COMMENT ON TABLE public.strava_activity_streams_cache IS 'Streams ponto-a-ponto de atividades. Buscar somente quando necessario para analise detalhada.';


-- ---------------------------------------------------------------------------
-- 5. Analises Strava do GoJohnny (planejado vs executado)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strava_training_analysis (
  id                        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id                 UUID         NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  plano_id                  UUID         NULL,
  strava_activity_id        BIGINT       NULL,
  periodo                   TEXT         NOT NULL,
  data_inicio               DATE         NULL,
  data_fim                  DATE         NULL,
  titulo                    TEXT         NULL,
  treino_planejado_json     JSONB        NULL,
  treino_executado_json     JSONB        NULL,
  comparativo_json          JSONB        NULL,
  aderencia                 TEXT         NULL,
  pontos_positivos          JSONB        NULL,
  pontos_atencao            JSONB        NULL,
  decisao_treinador         TEXT         NULL,
  plano_deve_mudar          BOOLEAN      NOT NULL DEFAULT FALSE,
  tipo_acao_recomendada     TEXT         NULL,
  memoria_criada            BOOLEAN      NOT NULL DEFAULT FALSE,
  checkin_criado            BOOLEAN      NOT NULL DEFAULT FALSE,
  resumo_semanal_criado     BOOLEAN      NOT NULL DEFAULT FALSE,
  raw_input_json            JSONB        NULL,
  criado_em                 TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_strava_training_analysis_atleta_data
  ON public.strava_training_analysis (atleta_id, criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_strava_training_analysis_activity
  ON public.strava_training_analysis (strava_activity_id);

COMMENT ON TABLE public.strava_training_analysis IS 'Comparativos planejado vs executado gerados pelo GoJohnny. Sugestoes, nunca alteracoes automaticas.';
COMMENT ON COLUMN public.strava_training_analysis.periodo IS 'treino | semana | tendencia';
COMMENT ON COLUMN public.strava_training_analysis.aderencia IS 'boa | parcial | baixa | risco';
COMMENT ON COLUMN public.strava_training_analysis.tipo_acao_recomendada IS 'manter | ajustar | substituir | descansar';


-- ---------------------------------------------------------------------------
-- 6. Logs de sync Strava (auditoria + rate limit)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strava_sync_logs (
  id                       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id                UUID         NULL REFERENCES public.atletas(id) ON DELETE SET NULL,
  endpoint                 TEXT         NOT NULL,
  metodo                   TEXT         NOT NULL DEFAULT 'GET',
  status_code              INTEGER      NULL,
  sucesso                  BOOLEAN      NOT NULL DEFAULT FALSE,
  erro_texto               TEXT         NULL,
  rate_limit_limit         TEXT         NULL,
  rate_limit_usage         TEXT         NULL,
  read_rate_limit_limit    TEXT         NULL,
  read_rate_limit_usage    TEXT         NULL,
  request_params_json      JSONB        NULL,
  response_resumo_json     JSONB        NULL,
  criado_em                TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_strava_sync_logs_atleta_data
  ON public.strava_sync_logs (atleta_id, criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_strava_sync_logs_sucesso
  ON public.strava_sync_logs (sucesso);

COMMENT ON TABLE public.strava_sync_logs IS 'Auditoria de chamadas a API Strava: status, erros e rate limit headers.';


-- ---------------------------------------------------------------------------
-- Verificacoes finais
-- ---------------------------------------------------------------------------
SELECT 'strava_preferences existe'           AS check, COUNT(*) AS ok FROM information_schema.tables WHERE table_schema='public' AND table_name='strava_preferences'
UNION ALL
SELECT 'strava_connections existe',           COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='strava_connections'
UNION ALL
SELECT 'strava_activity_cache existe',        COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='strava_activity_cache'
UNION ALL
SELECT 'strava_activity_streams_cache existe',COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='strava_activity_streams_cache'
UNION ALL
SELECT 'strava_training_analysis existe',     COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='strava_training_analysis'
UNION ALL
SELECT 'strava_sync_logs existe',             COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='strava_sync_logs';

COMMIT;
