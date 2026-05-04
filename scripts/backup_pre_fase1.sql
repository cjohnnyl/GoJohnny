-- ============================================================================
-- BACKUP PRÉ-FASE 1 DO GOJOHNNY (alternativa via SQL Editor do Supabase)
-- ============================================================================
--
-- Use este script SE você não tiver pg_dump instalado e prefere rodar
-- direto no SQL Editor do Supabase. Resultado: 3 tabelas espelhadas no
-- schema "public", com sufixo "_backup_pre_fase1".
--
-- VANTAGENS
--   - Roda direto no painel do Supabase, sem ferramentas extras
--   - Backup permanece no mesmo banco (consultável a qualquer momento)
--
-- DESVANTAGENS COMPARADO AO pg_dump
--   - Não exporta o backup para fora do banco
--   - Se o banco inteiro morrer, o backup morre junto
--   - Por isso: PREFIRA backup_pre_fase1.sh quando possível
--
-- COMO RODAR
--   1. Abra o painel Supabase > SQL Editor
--   2. Cole TODO o conteúdo deste arquivo
--   3. Execute (Run / Ctrl+Enter)
--   4. Confira a contagem de linhas no final
--   5. Guarde também um SELECT manual em CSV se possível:
--        SELECT * FROM public.atletas;
--        SELECT * FROM public.planos_semanais;
--        SELECT * FROM public.checkins;
--      e exporte cada um como CSV pelo painel.
--
-- COMO RESTAURAR (rollback)
--   Se a migration 002 causar problema, restaurar com:
--      BEGIN;
--      TRUNCATE public.atletas, public.planos_semanais, public.checkins CASCADE;
--      INSERT INTO public.atletas         SELECT * FROM public.atletas_backup_pre_fase1;
--      INSERT INTO public.planos_semanais SELECT * FROM public.planos_semanais_backup_pre_fase1;
--      INSERT INTO public.checkins        SELECT * FROM public.checkins_backup_pre_fase1;
--      COMMIT;
--   ATENÇÃO: rode o BEGIN/COMMIT só após inspecionar a contagem de linhas.
-- ============================================================================

BEGIN;

-- Limpar backups antigos com mesmo nome, se existirem
DROP TABLE IF EXISTS public.atletas_backup_pre_fase1;
DROP TABLE IF EXISTS public.planos_semanais_backup_pre_fase1;
DROP TABLE IF EXISTS public.checkins_backup_pre_fase1;

-- Criar cópias COM dados (snapshot estrutura + linhas)
CREATE TABLE public.atletas_backup_pre_fase1 AS
SELECT * FROM public.atletas;

CREATE TABLE public.planos_semanais_backup_pre_fase1 AS
SELECT * FROM public.planos_semanais;

CREATE TABLE public.checkins_backup_pre_fase1 AS
SELECT * FROM public.checkins;

-- Conferência: deve coincidir com a contagem das tabelas originais
SELECT 'atletas'         AS tabela, COUNT(*) AS linhas FROM public.atletas_backup_pre_fase1
UNION ALL
SELECT 'planos_semanais' AS tabela, COUNT(*) AS linhas FROM public.planos_semanais_backup_pre_fase1
UNION ALL
SELECT 'checkins'        AS tabela, COUNT(*) AS linhas FROM public.checkins_backup_pre_fase1;

COMMIT;
