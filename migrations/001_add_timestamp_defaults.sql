-- Migration: Add timestamp defaults to all tables
-- Date: 2026-04-27
-- Purpose: Fix NOT NULL constraint violations on criado_em and atualizado_em columns

-- Set defaults for atletas table
ALTER TABLE public.atletas
ALTER COLUMN criado_em SET DEFAULT now();

ALTER TABLE public.atletas
ALTER COLUMN atualizado_em SET DEFAULT now();

-- Set defaults for planos_semanais table
ALTER TABLE public.planos_semanais
ALTER COLUMN criado_em SET DEFAULT now();

ALTER TABLE public.planos_semanais
ALTER COLUMN atualizado_em SET DEFAULT now();

-- Set default for checkins table
ALTER TABLE public.checkins
ALTER COLUMN criado_em SET DEFAULT now();

-- Add NOT NULL constraints if not present
ALTER TABLE public.atletas
ALTER COLUMN criado_em SET NOT NULL;

ALTER TABLE public.atletas
ALTER COLUMN atualizado_em SET NOT NULL;

ALTER TABLE public.planos_semanais
ALTER COLUMN criado_em SET NOT NULL;

ALTER TABLE public.planos_semanais
ALTER COLUMN atualizado_em SET NOT NULL;

ALTER TABLE public.checkins
ALTER COLUMN criado_em SET NOT NULL;

-- Add NOT NULL constraint to plano column in planos_semanais
ALTER TABLE public.planos_semanais
ALTER COLUMN plano SET NOT NULL;
