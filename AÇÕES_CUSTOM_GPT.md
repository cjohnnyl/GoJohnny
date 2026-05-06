# 🎬 Todas as 14 Ações do Custom GPT - GoJohnny

**Schema:** `openapi-gpt-actions.json` (OpenAPI 3.1.0)  
**Status:** ✅ Validado e pronto para uso

---

## Tabela de Referência

| # | Action | Endpoint | Método | OperationId | Descrição |
|----|--------|----------|--------|-------------|-----------|
| 1 | Iniciar Sessão | `/sessao/iniciar` | POST | `iniciarSessao` | Identifica atleta, retorna plano e contexto |
| 2 | Criar Atleta | `/atletas` | POST | `criarAtleta` | Criar novo perfil de atleta |
| 3 | Buscar Atleta | `/atletas/{apelido}` | GET | `buscarAtleta` | Retorna dados completos do atleta |
| 4 | Atualizar Atleta | `/atletas/{apelido}` | PATCH | `atualizarAtleta` | Atualiza nome, objetivo, nível, etc |
| 5 | Atualizar Flags | `/atletas/{apelido}/flags` | PATCH | `atualizarFlags` | Ativa/desativa Google Calendar, Strava, etc |
| 6 | Criar Plano | `/planos-semanais` | POST | `criarPlano` | Cria novo plano semanal de treino |
| 7 | Buscar Plano Atual | `/planos-semanais/{apelido}/atual` | GET | `buscarPlanoAtual` | Retorna plano ativo do atleta |
| 8 | Listar Planos | `/planos-semanais/{apelido}` | GET | `listarPlanos` | Lista todos os planos (ativos + arquivados) |
| 9 | Criar Check-in | `/checkins` | POST | `criarCheckin` | Registra desempenho de uma semana |
| 10 | Listar Check-ins | `/checkins/{apelido}` | GET | `listarCheckins` | Retorna histórico de check-ins |
| 11 | Preview Calendário | `/calendario/{apelido}/preview` | GET | `previewCalendario` | Preview dos eventos (sem publicar) |
| 12 | Publicar Calendário | `/calendario/{apelido}/publicar` | POST | `publicarCalendario` | Publica eventos no Google Calendar |
| 13 | Login Google | `/oauth/google/login/{apelido}` | GET | `loginGoogle` | Gera URL para autenticação com Google |
| 14 | Status Google | `/oauth/google/status/{apelido}` | GET | `statusGoogle` | Verifica conexão com Google Calendar |

---

## 📋 Agrupado por Categoria

### 🔐 Sessão (1 ação)

```
POST /sessao/iniciar
├─ OperationId: iniciarSessao
├─ Body: { apelido: string }
└─ Response:
   ├─ status: "novo" | "existente"
   ├─ atleta: AtletaRead
   ├─ plano_atual: PlanoSemanalRead
   ├─ contexto_resumo: object
   ├─ flags: AtletaFlags
   └─ instrucao_continuacao: string
```

### 👤 Atletas (4 ações)

```
1. POST /atletas
   ├─ OperationId: criarAtleta
   ├─ Body: { nome, apelido, objetivo, nivel, dias_treino, ... }
   └─ Response: AtletaRead (201 Created)

2. GET /atletas/{apelido}
   ├─ OperationId: buscarAtleta
   ├─ Params: apelido
   └─ Response: AtletaRead

3. PATCH /atletas/{apelido}
   ├─ OperationId: atualizarAtleta
   ├─ Params: apelido
   ├─ Body: { nome?, objetivo?, nivel?, dias_treino?, ... }
   └─ Response: AtletaRead

4. PATCH /atletas/{apelido}/flags
   ├─ OperationId: atualizarFlags
   ├─ Params: apelido
   ├─ Body: { usar_datas_reais?, usar_contexto_atleta?, usar_google_calendar?, usar_strava? }
   └─ Response: AtletaFlags
```

### 📅 Planos Semanais (3 ações)

```
1. POST /planos-semanais
   ├─ OperationId: criarPlano
   ├─ Body: { apelido, semana_inicio, objetivo_semana, plano, novo_ciclo? }
   └─ Response: PlanoSemanalRead (201 Created)

2. GET /planos-semanais/{apelido}/atual
   ├─ OperationId: buscarPlanoAtual
   ├─ Params: apelido
   └─ Response: PlanoSemanalRead (status="ativo")

3. GET /planos-semanais/{apelido}
   ├─ OperationId: listarPlanos
   ├─ Params: apelido
   └─ Response: PlanoSemanalRead[] (ordenado por data desc)
```

### ✅ Check-ins (2 ações)

```
1. POST /checkins
   ├─ OperationId: criarCheckin
   ├─ Body: { apelido, semana_inicio, treinos_planejados, treinos_realizados, volume_realizado_km, sensacao_geral, ... }
   └─ Response: CheckinRead (201 Created)

2. GET /checkins/{apelido}
   ├─ OperationId: listarCheckins
   ├─ Params: apelido
   └─ Response: CheckinRead[]
```

### 📆 Calendário (2 ações)

```
1. GET /calendario/{apelido}/preview
   ├─ OperationId: previewCalendario
   ├─ Params: apelido
   └─ Response:
      ├─ atleta_apelido: string
      ├─ total_eventos: number
      ├─ eventos: EventoTreino[]
      ├─ periodo_inicio: date
      └─ periodo_fim: date

2. POST /calendario/{apelido}/publicar
   ├─ OperationId: publicarCalendario
   ├─ Params: apelido
   └─ Response:
      ├─ publicado: boolean
      ├─ eventos_criados: number
      ├─ eventos_ignorados: number
      └─ erros: string[]
```

### 🔑 OAuth / Google (2 ações)

```
1. GET /oauth/google/login/{apelido}
   ├─ OperationId: loginGoogle
   ├─ Params: apelido
   └─ Response: { redirect_url: string }

2. GET /oauth/google/status/{apelido}
   ├─ OperationId: statusGoogle
   ├─ Params: apelido
   └─ Response:
      ├─ conectado: boolean
      ├─ email_google: string?
      ├─ expirado: boolean
      └─ tempo_restante_segundos: number?
```

---

## 🔄 Fluxos Recomendados de Conversa

### Fluxo 1: Novo Atleta Completo

```
1. iniciarSessao (apelido) → status="novo"
2. criarAtleta (nome, apelido, objetivo, nivel, dias_treino)
3. atualizarAtleta (apelido) → adicionar dados opcionais
4. criarPlano (apelido, semana_inicio, plano)
5. [opcional] atualizarFlags (apelido) → ativar Google Calendar
```

### Fluxo 2: Atleta Existente com Novo Plano

```
1. iniciarSessao (apelido) → status="existente", plano_atual
2. buscarPlanoAtual (apelido) → ler plano atual
3. criarPlano (apelido, semana_inicio, plano, novo_ciclo=true) → novo ciclo
```

### Fluxo 3: Check-in Semanal

```
1. iniciarSessao (apelido) → contexto
2. buscarPlanoAtual (apelido) → plano da semana
3. criarCheckin (apelido, semana_inicio, treinos_realizados, sensacao_geral)
4. listarCheckins (apelido) → mostrar histórico
```

### Fluxo 4: Publicar no Google Calendar

```
1. iniciarSessao (apelido) → verificar flags.usar_google_calendar
2. statusGoogle (apelido) → verificar se está conectado
   ├─ if conectado=false → loginGoogle (apelido) → exibir URL
   └─ if conectado=true → previewCalendario (apelido) → publicarCalendario (apelido)
```

---

## 📊 Mapeamento de Dados

### AtletaCreate → AtletaRead

```
Input (POST /atletas):
{
  "nome": "João Silva",
  "apelido": "joao",
  "objetivo": "Correr 21km",
  "nivel": "iniciante",
  "dias_treino": 3
}

Output (201):
{
  "id": "uuid-1234",
  "nome": "João Silva",
  "apelido": "joao",
  "objetivo": "Correr 21km",
  "nivel": "iniciante",
  "dias_treino": 3,
  "usar_datas_reais": false,
  "usar_contexto_atleta": false,
  "usar_google_calendar": false,
  "usar_strava": false,
  "criado_em": "2026-05-06T01:00:00Z"
}
```

### PlanoSemanalCreate → PlanoSemanalRead

```
Input (POST /planos-semanais):
{
  "apelido": "joao",
  "semana_inicio": "2026-05-05",
  "objetivo_semana": "Consolidar base",
  "plano": "{\"segunda\": \"8km\", \"quarta\": \"10km\", \"sexta\": \"6km\"}",
  "novo_ciclo": false
}

Output (201):
{
  "id": "uuid-5678",
  "atleta_id": "uuid-1234",
  "semana_inicio": "2026-05-05",
  "objetivo_semana": "Consolidar base",
  "status": "ativo",
  "plano": "{\"segunda\": \"8km\", ...}",
  "criado_em": "2026-05-06T01:00:00Z"
}
```

---

## ⚠️ Restrições Importantes

### 1. Apelido é Único

- Não pode criar dois atletas com mesmo apelido
- Erro: HTTP 409 Conflict

### 2. Plano Ativo é Único

- Cada atleta pode ter apenas 1 plano com status="ativo"
- Para criar novo plano: `novo_ciclo=true`
- Erro: HTTP 409 Conflict

### 3. Check-in é para Semana Específica

- Identificado por `apelido` + `semana_inicio`
- Se já existe check-in para essa semana, será sobrescrito

### 4. Google Calendar Requer Conexão

- Não pode publicar sem `statusGoogle.conectado=true`
- Usar `loginGoogle` para gerar URL de autenticação

### 5. Parâmetro {apelido} é Case-Sensitive

- ⚠️ **Importante:** Use sempre lowercase
- Recomendação: "joao", não "Joao" ou "JOAO"

---

## 🎯 Exemplos de Chamadas

### iniciarSessao

```bash
POST /sessao/iniciar
x-api-key: [sua-chave]

{
  "apelido": "johnny"
}

# Resposta
{
  "status": "existente",
  "atleta": { ... },
  "plano_atual": { ... },
  "instrucao_continuacao": "Usuario JA EXISTE e tem plano ativo..."
}
```

### criarAtleta

```bash
POST /atletas
x-api-key: [sua-chave]

{
  "nome": "Johnny Silva",
  "apelido": "johnny",
  "objetivo": "Correr 21km",
  "nivel": "intermediario",
  "dias_treino": 4
}

# Resposta (201)
{
  "id": "8c7d4783-2706-451e-b268-ea390139c4ae",
  "nome": "Johnny Silva",
  ...
}
```

### criarPlano

```bash
POST /planos-semanais
x-api-key: [sua-chave]

{
  "apelido": "johnny",
  "semana_inicio": "2026-05-05",
  "objetivo_semana": "Consolidar base aeróbia",
  "plano": "{\"segunda\": \"8km\", \"quarta\": \"10km\", \"sexta\": \"6km\"}",
  "novo_ciclo": false
}

# Resposta (201)
{
  "id": "3e65f946-a7b0-4686-8040-9b9f29b55f49",
  "status": "ativo",
  ...
}
```

### criarCheckin

```bash
POST /checkins
x-api-key: [sua-chave]

{
  "apelido": "johnny",
  "semana_inicio": "2026-05-05",
  "treinos_planejados": 3,
  "treinos_realizados": 3,
  "volume_realizado_km": 24.5,
  "sensacao_geral": "Muito bom, sem dores"
}

# Resposta (201)
{
  "id": "uuid",
  "atleta_id": "uuid",
  ...
}
```

---

## 📈 Status Codes Esperados

| Code | Significado | Quando |
|------|-------------|--------|
| 200 | OK | GET bem-sucedido, PATCH bem-sucedido |
| 201 | Created | POST bem-sucedido (criou recurso novo) |
| 400 | Bad Request | Dados inválidos na request |
| 401 | Unauthorized | API key ausente ou inválida |
| 404 | Not Found | Atleta/recurso não encontrado |
| 409 | Conflict | Apelido duplicado, plano ativo já existe |
| 422 | Validation Error | Erro de validação dos dados |
| 500 | Internal Server Error | Erro no servidor |

---

## ✅ Checklist de Validação

Antes de usar no Custom GPT, verificar:

- [ ] Arquivo `openapi-gpt-actions.json` existe
- [ ] JSON é válido (`python3 -m json.tool openapi-gpt-actions.json`)
- [ ] 14 `operationId` únicos estão presentes
- [ ] API key (`x-api-key`) está configurada no Custom GPT
- [ ] Security scheme é global (não em cada endpoint)
- [ ] Servidor está em `servers[0].url`
- [ ] Todas as ações aparecem no Custom GPT editor

---

**Última atualização:** 2026-05-06T01:00:00Z  
**Mantido por:** Claude Code
