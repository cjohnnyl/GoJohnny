-- ============================================================================
-- Migration: 003_google_calendar_publicacao
-- Data: 2026-05-04
-- Proposito:
--   Persistir publicacoes do Google Calendar com idempotencia por hash_evento,
--   suporte a retry seguro e falha parcial por evento.
-- ============================================================================

BEGIN;

DO $$
BEGIN
  BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
  EXCEPTION WHEN feature_not_supported THEN
    RAISE NOTICE 'pgcrypto nao disponivel - usando gen_random_uuid() built-in (PG 13+).';
  END;
END$$;

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
  IS 'Registro local dos eventos do Google Calendar para idempotencia, retry e auditoria.';
COMMENT ON COLUMN public.calendario_eventos_google.hash_evento
  IS 'Hash deterministico do evento de treino gerado pelo GoJohnny.';
COMMENT ON COLUMN public.calendario_eventos_google.status
  IS 'Estado local da publicacao. Valores esperados: publicado, erro.';
COMMENT ON COLUMN public.calendario_eventos_google.google_event_id
  IS 'ID retornado pelo Google Calendar para o evento criado. Fica NULL em tentativas com erro.';

SELECT 'calendario_eventos_google tabela existe' AS check, COUNT(*) AS ok
FROM information_schema.tables
WHERE table_schema='public' AND table_name='calendario_eventos_google'
UNION ALL
SELECT 'calendario_eventos_google idx hash existe', COUNT(*)
FROM pg_indexes
WHERE schemaname='public' AND indexname='idx_calendario_eventos_google_atleta_hash';

COMMIT;
