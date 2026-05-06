-- ============================================================================
-- Migration: 004_atleta_memorias
-- Data: 2026-05-05
-- Proposito:
--   Criar base de conhecimento persistente por atleta.
--   Armazenar memória útil, resumos semanais e decisões do treinador
--   para manter continuidade real entre chats.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.atleta_memorias (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  atleta_id         UUID        NOT NULL REFERENCES public.atletas(id) ON DELETE CASCADE,
  tipo              VARCHAR(50) NOT NULL,
  chave             VARCHAR(255) NOT NULL,
  valor_texto       TEXT        NULL,
  valor_json        JSONB       NULL,
  origem            VARCHAR(50) NOT NULL,
  importancia       INTEGER     NOT NULL DEFAULT 3,
  confianca         NUMERIC(3,2) NOT NULL DEFAULT 1.0,
  semana_inicio     DATE        NULL,
  ativo             BOOLEAN     NOT NULL DEFAULT true,
  criado_em         TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices para otimizar consultas
CREATE INDEX IF NOT EXISTS idx_atleta_memorias_atleta_id
  ON public.atleta_memorias (atleta_id);

CREATE INDEX IF NOT EXISTS idx_atleta_memorias_tipo
  ON public.atleta_memorias (tipo);

CREATE INDEX IF NOT EXISTS idx_atleta_memorias_semana_inicio
  ON public.atleta_memorias (semana_inicio DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_atleta_memorias_importancia
  ON public.atleta_memorias (importancia DESC);

CREATE INDEX IF NOT EXISTS idx_atleta_memorias_ativo
  ON public.atleta_memorias (ativo);

CREATE UNIQUE INDEX IF NOT EXISTS idx_atleta_memorias_uniq_tipo_chave
  ON public.atleta_memorias (atleta_id, tipo, chave)
  WHERE ativo = true;

-- Comentários de documentação
COMMENT ON TABLE public.atleta_memorias
  IS 'Knowledge base persistente por atleta. Armazena memórias úteis: feedback, objetivos, preferências, erros, orientações.';

COMMENT ON COLUMN public.atleta_memorias.tipo
  IS 'Tipo de memória: perfil, objetivo, preferencia, treino_realizado, feedback, erro_recorrente, orientacao_treinador, resumo_semanal, lesao_dor, prova, equipamento, decisao_plano, strava, observacao';

COMMENT ON COLUMN public.atleta_memorias.chave
  IS 'Identificador único da memória dentro do tipo. Exemplo: erro_regenerativo_forte';

COMMENT ON COLUMN public.atleta_memorias.origem
  IS 'Origem da memória: conversa, importacao_chat_antigo, sistema';

COMMENT ON COLUMN public.atleta_memorias.importancia
  IS 'Importância: 1 (baixa) até 5 (crítico). Prioriza recuperação em novos chats.';

COMMENT ON COLUMN public.atleta_memorias.confianca
  IS 'Confiança na memória: 0 (não confiável) até 1 (confiável).';

COMMENT ON COLUMN public.atleta_memorias.semana_inicio
  IS 'Data de início da semana se aplicável (para resumos semanais).';

COMMENT ON COLUMN public.atleta_memorias.ativo
  IS 'Flag de ativação. Memórias inativas não aparecem em buscas.';

-- Validação
SELECT 'atleta_memorias tabela existe' AS check, COUNT(*) AS ok
FROM information_schema.tables
WHERE table_schema='public' AND table_name='atleta_memorias'
UNION ALL
SELECT 'atleta_memorias idx atleta_id existe', COUNT(*)
FROM pg_indexes
WHERE schemaname='public' AND indexname='idx_atleta_memorias_atleta_id'
UNION ALL
SELECT 'atleta_memorias idx uniq existe', COUNT(*)
FROM pg_indexes
WHERE schemaname='public' AND indexname='idx_atleta_memorias_uniq_tipo_chave';

COMMIT;
