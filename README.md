# GoJohnny API

Consultoria pessoal de corrida com IA. Backend FastAPI + Supabase/Postgres consumido por um Custom GPT via Actions.

> **Status atual (maio/2026):** Fase 1 implementada na branch `feat/fase-1`. Suite de testes 102/102 verde. Aguardando aplicação da migration 002 em produção e revisão das instruções do Custom GPT.

## O que entrou na Fase 1

- `POST /sessao/iniciar` — endpoint único de identificação no início de qualquer chat. Retorna status (novo|existente), plano atual, contexto e instrução de continuação para o GPT.
- Feature flags por atleta (4 colunas BOOLEAN dedicadas, default false): `usar_datas_reais`, `usar_contexto_atleta`, `usar_google_calendar`, `usar_strava`.
- Plano semanal enriquecido (aditivo): novos campos opcionais `data_inicio`, `data_prova`, `dias_treino_json`, `versao_estrutura`. Planos antigos continuam sendo lidos sem alteração.
- Engine de calendário determinística (`app/services/calendar_engine.py`) — segunda-feira como início de semana ISO, timezone America/Sao_Paulo.
- Leitura tolerante do plano (`app/services/plan_parser.py`) — mesma representação interna para planos legados e enriquecidos.
- Tabela `contexto_atleta` para memória persistente (chave/valor por tipo, com origem rastreável e idempotente via UNIQUE).
- Proteção contra sobrescrita: `POST /planos-semanais` retorna 409 se já existe plano ativo. Para iniciar novo ciclo, enviar `novo_ciclo: true`. O plano anterior é arquivado, nunca apagado.
- Logging estruturado de toda criação/atualização de plano.

## Estrutura do repositório

```
gojohnny/
├── app/
│   ├── main.py                       # FastAPI app, registra os routers
│   ├── core/                         # config, database, auth
│   ├── models/                       # SQLAlchemy ORM
│   │   ├── atleta.py                 # +4 flags Boolean
│   │   ├── checkin.py
│   │   ├── plano_semanal.py          # +4 campos opcionais (Fase 1)
│   │   └── contexto_atleta.py        # NOVO Fase 1
│   ├── schemas/                      # Pydantic v2
│   │   ├── atleta.py                 # +AtletaFlagsUpdate
│   │   ├── checkin.py
│   │   ├── plano_semanal.py          # +novo_ciclo, +campos enriquecidos
│   │   ├── contexto_atleta.py        # NOVO Fase 1
│   │   └── sessao.py                 # NOVO Fase 1
│   ├── routes/
│   │   ├── atletas.py
│   │   ├── checkins.py
│   │   ├── planos_semanais.py        # +protecao sobrescrita
│   │   └── sessao.py                 # NOVO Fase 1
│   └── services/
│       ├── atleta_service.py
│       ├── calendar_engine.py        # NOVO Fase 1 (37 testes)
│       ├── plan_parser.py            # NOVO Fase 1 (25 testes)
│       ├── feature_flag_service.py   # NOVO Fase 1
│       ├── context_service.py        # NOVO Fase 1
│       ├── plano_service.py          # NOVO Fase 1 (regra de sobrescrita)
│       └── session_service.py        # NOVO Fase 1
├── migrations/
│   ├── 001_add_timestamp_defaults.sql
│   └── 002_fase1_aditiva.sql         # NOVO Fase 1
├── scripts/
│   ├── backup_pre_fase1.sh           # NOVO Fase 1
│   └── backup_pre_fase1.sql          # NOVO Fase 1
├── docs/
│   ├── HANDOFF_FASE1.md              # PASSO A PASSO PARA CONTINUAR
│   ├── QA_RELATORIO_FASE1.md         # 102 testes documentados
│   ├── gpt_instructions.md           # texto do Custom GPT
│   └── runbooks/
│       └── rollback.md               # backup, deploy, rollback
├── tests/
│   ├── conftest.py                   # fixtures, sobe pgserver na sandbox
│   ├── services/                     # 71 testes unitários
│   └── integration/                  # 16 testes de integração (cenários A-E)
├── docker-compose.test.yml           # NOVO Fase 1 (Postgres efêmero)
├── requirements.txt
├── requirements-dev.txt              # NOVO Fase 1
├── pytest.ini                        # NOVO Fase 1
├── render.yaml
├── openapi-gpt-actions.json          # +/sessao/iniciar, +flags, +novo_ciclo
└── README.md
```

## Como rodar local

```bash
cp .env.example .env
# editar .env com DATABASE_URL e API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Como rodar a suite de testes

```bash
# 1. Sobe Postgres efêmero
docker compose -f docker-compose.test.yml up -d

# 2. Variável de teste
export TEST_DATABASE_URL=postgresql://gojohnny:gojohnny@localhost:55432/gojohnny_test

# 3. Dependências de dev
pip install -r requirements-dev.txt

# 4. Rodar
pytest -v
```

Resultado esperado: **102 passed**. Veja o detalhamento em `docs/QA_RELATORIO_FASE1.md`.

## Deploy da Fase 1 em produção

Siga o runbook em `docs/runbooks/rollback.md`. Resumo:
1. Backup com `scripts/backup_pre_fase1.sh`.
2. Aplicar `migrations/002_fase1_aditiva.sql`.
3. Atualizar `requirements.txt` com `pip freeze` do ambiente atual.
4. Push da branch `feat/fase-1`.
5. Aplicar `docs/gpt_instructions.md` no Custom GPT, atualizar Actions com `openapi-gpt-actions.json`.
6. Smoke test (ver runbook).

## Pendências para Fase 2

- Pinagem completa de `requirements.txt` (depende de `pip freeze` real de produção).
- Ambiente de staging dedicado (Render branch + Supabase project paralelo).
- Extração automática contínua de contexto a partir dos check-ins.
- Integrações Google Calendar e Strava (flags já existem; lógica não).
- Migrar para Alembic (atualmente migrations em SQL puro).

## Variáveis de ambiente

| Variável            | Onde                | Para que                                     |
|---------------------|---------------------|----------------------------------------------|
| `DATABASE_URL`      | produção e dev      | Postgres do Supabase                         |
| `API_KEY`           | produção e dev      | Auth `x-api-key` da API                      |
| `TEST_DATABASE_URL` | testes              | Postgres efêmero do docker-compose.test.yml  |
