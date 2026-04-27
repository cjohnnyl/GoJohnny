# GoJohnny API

Consultoria pessoal de corrida com IA. Backend em FastAPI conectado ao Supabase/Postgres,
projetado para ser consumido por um Custom GPT via GPT Actions.

## Estrutura de pastas

```
gojohnny/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py       # variáveis de ambiente
│   │   ├── database.py     # engine, SessionLocal, get_db
│   │   └── auth.py         # verificação de API key
│   ├── models/
│   │   ├── atleta.py
│   │   ├── checkin.py
│   │   └── plano_semanal.py
│   ├── schemas/
│   │   ├── atleta.py
│   │   ├── checkin.py
│   │   └── plano_semanal.py
│   ├── routes/
│   │   ├── atletas.py
│   │   ├── checkins.py
│   │   └── planos_semanais.py
│   └── services/
│       └── atleta_service.py
├── requirements.txt
├── render.yaml
├── .env.example
├── .gitignore
└── README.md
```

## Como configurar .env

Copie o arquivo de exemplo e preencha com seus dados reais:

```bash
cp .env.example .env
```

Edite `.env`:

```
DATABASE_URL=postgresql://usuario:senha@host:5432/postgres
API_KEY=sua_chave_api_secreta
```

## Como instalar dependências

```bash
pip install -r requirements.txt
```

## Como rodar local

```bash
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`.

## Como testar /health

```bash
curl http://localhost:8000/health
```

Resposta esperada:

```json
{"status": "ok"}
```

## Como testar /docs

Abra no navegador: `http://localhost:8000/docs`

O Swagger UI exibe todas as rotas disponíveis e permite testá-las diretamente.

## Exemplos curl

Substitua `SUA_API_KEY` pela chave definida no `.env`.

### GET /health

```bash
curl http://localhost:8000/health
```

### GET /atletas/johnny

```bash
curl http://localhost:8000/atletas/johnny \
  -H "x-api-key: SUA_API_KEY"
```

### PATCH /atletas/johnny

```bash
curl -X PATCH http://localhost:8000/atletas/johnny \
  -H "x-api-key: SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"peso_kg": 72.5, "pace_confortavel": "6:15"}'
```

### POST /checkins

```bash
curl -X POST http://localhost:8000/checkins \
  -H "x-api-key: SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "apelido": "johnny",
    "semana_inicio": "2026-04-27",
    "treinos_planejados": 3,
    "treinos_realizados": 3,
    "volume_planejado_km": 25,
    "volume_realizado_km": 24,
    "pace_medio": "6:30",
    "cansaco_0_10": 6,
    "dores": "sem dor",
    "sono": "bom",
    "sensacao_geral": "semana adequada",
    "observacoes": "longão feito bem"
  }'
```

### GET /checkins/johnny

```bash
curl http://localhost:8000/checkins/johnny \
  -H "x-api-key: SUA_API_KEY"
```

### POST /planos-semanais

```bash
curl -X POST http://localhost:8000/planos-semanais \
  -H "x-api-key: SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "apelido": "johnny",
    "semana_inicio": "2026-04-27",
    "objetivo_semana": "aumentar volume com segurança",
    "volume_planejado_km": 28,
    "status": "ativo",
    "plano": {
      "treinos": [
        {
          "dia": "terça",
          "tipo": "leve",
          "distancia_km": 6,
          "intensidade": "confortável",
          "objetivo": "manter base aeróbica"
        }
      ]
    }
  }'
```

### GET /planos-semanais/johnny/atual

```bash
curl http://localhost:8000/planos-semanais/johnny/atual \
  -H "x-api-key: SUA_API_KEY"
```

## Como fazer deploy no Render

1. Faça push do projeto para um repositório GitHub.
2. Acesse [render.com](https://render.com) e crie um novo **Web Service**.
3. Conecte ao repositório GitHub.
4. O Render detecta o `render.yaml` automaticamente e configura o serviço.
5. Configure as variáveis de ambiente conforme a seção abaixo.
6. Clique em **Deploy**.

## Variáveis de ambiente no Render

No painel do Render, vá em **Environment** e adicione:

| Variável       | Valor                                              |
|----------------|----------------------------------------------------|
| `DATABASE_URL` | URL de conexão do Supabase (modo pooler ou direto) |
| `API_KEY`      | Chave secreta para autenticar as chamadas da API   |

A URL do Supabase segue o formato:

```
postgresql://postgres.[ref]:[senha]@aws-0-[region].pooler.supabase.com:6543/postgres
```
