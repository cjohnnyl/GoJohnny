-- ============================================================================
-- Migration: 006_google_integrations
-- Data: 2026-05-11
-- Proposito:
--   Criar tabelas de integração Google que estavam no código mas sem migration:
--   1. integracao_google   - Tokens OAuth do Google por atleta
--   2. calendario_eventos_google - Eventos publicados no Google Calendar
--      (migration 003 existia no repo mas não havia sido aplicada)
--
-- SEGURANÇA:
--   - Usa IF NOT EXISTS em todas as operações (sem risco de perda de dados)
--   - FK para atletas.id sem CASCADE em integracao_google (delete manual necessário)
--   - FK com CASCADE em calendario_eventos_google (delete automático)
-- ============================================================================

BEGIN;

-- Extensão para gen_random_uuid() (PG <13 precisava de pgcrypto)
DO $$
BEGIN
  BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
  EXCEPTION WHEN feature_not_supported THEN
    RAISE NOTICE 'pgcrypto nao disponivel - gen_random_uuid() built-in (PG 13+).';
  END;
END$$;

-- ============================================================================
-- 1. integracao_google
--    Persiste tokens OAuth do Google por atleta.
--    Sem ON DELETE CASCADE: cleanup manual obrigatório antes de deletar atleta.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.integracao_google (
  id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id     UUID          NOT NULL REFERENCES public.atletas(id),
  access_token  TEXT          NOT NULL,
  refresh_token TEXT          NULL,
  expires_at    TIMESTAMPTZ   NULL,
  email_google  VARCHAR(255)  NULL,
  criado_em     TIMESTAMPTZ   NOT NULL DEFAULT now(),
  atualizado_em TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS integracao_google_atleta_id_idx
  ON public.integracao_google (atleta_id);

COMMENT ON TABLE public.integracao_google
  IS 'Tokens OAuth do Google por atleta. Deletar registros antes de remover atleta (sem CASCADE).';
COMMENT ON COLUMN public.integracao_google.access_token
  IS 'Token de acesso do Google. Nunca expor em logs ou respostas públicas.';
COMMENT ON COLUMN public.integracao_google.refresh_token
  IS 'Token de refresh. Nunca expor em logs ou respostas públicas.';

-- ============================================================================
-- 2. calendario_eventos_google
--    Persiste eventos publicados no Google Calendar com idempotência por hash.
--    Com ON DELETE CASCADE: deletar atleta remove automaticamente os eventos.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.calendario_eventos_google (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id             UUID        NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  hash_evento           TEXT        NOT NULL,
  status                TEXT        NOT NULL DEFAULT 'publicado',
  google_event_id       TEXT        NULL,
  titulo                TEXT        NULL,
  data_evento           DATE        NULL,
  erro_ultima_tentativa TEXT        NULL,
  criado_em             TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_calendario_eventos_google_atleta_id
  ON public.calendario_eventos_google (atleta_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_calendario_eventos_google_atleta_hash
  ON public.calendario_eventos_google (atleta_id, hash_evento);

COMMENT ON TABLE public.calendario_eventos_google
  IS 'Registro local dos eventos do Google Calendar para idempotência, retry e auditoria.';
COMMENT ON COLUMN public.calendario_eventos_google.hash_evento
  IS 'Hash determinístico do evento de treino gerado pelo GoJohnny.';
COMMENT ON COLUMN public.calendario_eventos_google.status
  IS 'Estado local da publicação. Valores: publicado, erro.';

-- ============================================================================
-- Verificação pós-criação
-- ============================================================================

SELECT
  table_name,
  'existe' AS status
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('integracao_google', 'calendario_eventos_google')
ORDER BY table_name;

COMMIT;
