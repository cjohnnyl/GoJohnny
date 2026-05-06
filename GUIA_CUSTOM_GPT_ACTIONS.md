# 📋 Guia de Integração: Custom GPT Actions - GoJohnny

**Arquivo:** `openapi-gpt-actions.json`  
**Versão:** 2.0.0  
**Compatibilidade:** OpenAPI 3.1.0 + Custom GPT Actions  
**Tamanho:** 32 KB (1054 linhas)

---

## 📝 Resumo das Actions Disponíveis

O schema expõe **14 actions** (endpoints) para o Custom GPT operar o GoJohnny:

### Sessão
1. **`iniciarSessao`** — POST `/sessao/iniciar`
   - Identifica o atleta e retorna plano ativo + contexto

### Atletas (5 actions)
2. **`criarAtleta`** — POST `/atletas`
   - Criar novo perfil de atleta
   
3. **`buscarAtleta`** — GET `/atletas/{apelido}`
   - Buscar dados completos de um atleta
   
4. **`atualizarAtleta`** — PATCH `/atletas/{apelido}`
   - Atualizar dados pessoais (nome, objetivo, nível, etc)
   
5. **`atualizarFlags`** — PATCH `/atletas/{apelido}/flags`
   - Ativar/desativar funcionalidades (Google Calendar, Strava, etc)

### Planos Semanais (3 actions)
6. **`criarPlano`** — POST `/planos-semanais`
   - Criar novo plano de treino
   
7. **`buscarPlanoAtual`** — GET `/planos-semanais/{apelido}/atual`
   - Buscar plano ativo do atleta
   
8. **`listarPlanos`** — GET `/planos-semanais/{apelido}`
   - Listar todos os planos (ativos e arquivados)

### Check-ins (2 actions)
9. **`criarCheckin`** — POST `/checkins`
   - Registrar desempenho de uma semana
   
10. **`listarCheckins`** — GET `/checkins/{apelido}`
    - Listar histórico de check-ins

### Calendário (2 actions)
11. **`previewCalendario`** — GET `/calendario/{apelido}/preview`
    - Preview dos eventos (sem publicar)
    
12. **`publicarCalendario`** — POST `/calendario/{apelido}/publicar`
    - Publicar eventos no Google Calendar

### OAuth / Google (2 actions)
13. **`loginGoogle`** — GET `/oauth/google/login/{apelido}`
    - Gerar URL para autenticar com Google
    
14. **`statusGoogle`** — GET `/oauth/google/status/{apelido}`
    - Verificar status da conexão com Google

---

## 🔐 Autenticação

### API Key
- **Header:** `x-api-key`
- **Valor:** Fornecido pelo GoJohnny
- **Aplicação:** Global (automaticamente em todas as requests)

### No Custom GPT
A API key é configurada **uma única vez** nas configurações do Custom GPT:
```
Authentication > API Key Authentication
Key: x-api-key
Value: [cole sua chave aqui]
```

**Não é necessário** incluir `x-api-key` como parâmetro em cada action — ele é adicionado automaticamente.

---

## 🚀 Como Integrar no Custom GPT

### Passo 1: Copiar o URL do Schema

```
https://gojohnny.onrender.com/openapi.json

OU

[upload direto do arquivo openapi-gpt-actions.json]
```

### Passo 2: Configurar no Custom GPT

1. Abra seu Custom GPT em https://platform.openai.com/gpts/editor
2. Vá para **"Configure" → "Actions"**
3. Clique em **"Create new action"** ou **"Import from URL"**
4. Cole a URL do schema acima
5. Configure Authentication:
   - Type: **API Key**
   - Auth Type: **Header**
   - Key: **x-api-key**
   - Value: [sua chave do GoJohnny]

### Passo 3: Testar as Actions

No editor do GPT, teste uma action simples:

```
User: Qual é meu apelido?
GPT: Vou iniciar sua sessão. Qual é seu apelido?
User: johnny
GPT: [chama POST /sessao/iniciar com apelido="johnny"]
Resposta: Você é Johnny, seu objetivo é...
```

---

## 📌 Exemplo de Fluxo de Conversa

### Novo Atleta

```
User: Quero começar a treinar para corrida
GPT: Ótimo! Qual é seu apelido? (algo como johnny, maria, pedro)
User: johnny
GPT: [POST /sessao/iniciar apelido="johnny"]
Resposta: Usuário não encontrado (status=novo)
GPT: Vamos criar seu perfil! Qual é seu nome completo?
User: João Silva
GPT: Qual é seu objetivo principal?
User: Correr 21km sem parar
GPT: [POST /atletas] Criei seu perfil!
```

### Atleta Existente

```
User: Oi, é o Johnny
GPT: [POST /sessao/iniciar apelido="johnny"]
Resposta: Usuário encontrado (status=existente)
✅ Plano ativo: Semana de 2026-05-05
✅ Objetivo: Evoluir no 21k
GPT: Bem-vindo de volta, Johnny! Seu plano desta semana é...
```

### Criar Plano

```
User: Cria um plano para mim
GPT: Ótimo! Qual é seu apelido?
User: johnny
GPT: [GET /atletas/johnny] Encontrado.
GPT: Qual é o objetivo dessa semana?
User: Consolidar base aeróbia
GPT: Quantos dias você pode treinar?
User: 3 dias
GPT: [POST /planos-semanais] Seu plano foi criado!
```

---

## ⚙️ Estrutura do Schema

### OpenAPI 3.1.0 Features

✅ **Securityschemes** globais
```json
{
  "security": [{"ApiKeyAuth": []}],
  "components": {
    "securitySchemes": {
      "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "x-api-key"
      }
    }
  }
}
```

✅ **Schemas bem-estruturados**
- SessaoIniciarResponse
- AtletaCreate / AtletaRead / AtletaUpdate
- PlanoSemanalCreate / PlanoSemanalRead
- CheckinCreate / CheckinRead
- CalendarioPreview / CalendarioPublicacaoResponse
- OAuthLoginResponse / OAuthStatusResponse

✅ **OperationIds claros e curtos**
- `iniciarSessao` (não `post_iniciar_sessao_sessao_iniciar_post`)
- `criarAtleta` (não `create_atleta_atletas_post`)
- Fácil para o GPT reconhecer e chamar

✅ **Descrições úteis**
- Cada endpoint tem `summary` e `description`
- Cada parâmetro tem `description`
- Cada schema tem campos documentados

---

## 🔍 Validação

### ✅ Checklist de Compatibilidade

- [x] OpenAPI 3.1.0 válido
- [x] JSON bem-formado (1054 linhas, 32 KB)
- [x] 14 actions documentadas
- [x] OperationIds únicos e descritivos
- [x] Security scheme global (sem x-api-key em cada endpoint)
- [x] Schemas sem `nullable` (OpenAPI 3.1 usa `null` type)
- [x] Não inclui endpoints desnecessários (/health, /, callback)
- [x] Descrições em português (compatível com GPT)

### Teste de Compatibilidade

```bash
# Validar JSON
python3 -m json.tool openapi-gpt-actions.json

# Verificar actions
grep '"operationId"' openapi-gpt-actions.json | wc -l
# Esperado: 14

# Verificar security scheme
grep '"ApiKeyAuth"' openapi-gpt-actions.json
# Esperado: 2 ocorrências (definição + uso)
```

---

## 🎯 Boas Práticas de Uso

### 1. Sempre Iniciar com `/sessao/iniciar`

```
GPT deve SEMPRE começar chamando iniciarSessao
para identificar o atleta e recuperar contexto.
```

### 2. Validar Status da Resposta

```
if status == "novo":
  → Fazer onboarding completo
else:
  → Trattar como continuação
```

### 3. Usar Plano Ativo

```
GET /planos-semanais/{apelido}/atual
antes de sugerir alterações
```

### 4. Registrar Check-ins Semanalmente

```
POST /checkins
para manter histórico de treinos realizados
```

---

## 📊 Comparação: OpenAPI Local vs Custom GPT

| Aspecto | OpenAPI FastAPI | OpenAPI Custom GPT |
|---------|-----------------|-------------------|
| OperationIds | Longos (post_iniciar_sessao...) | Curtos (iniciarSessao) |
| Endpoints | 19 (inclui /health, /oauth callback) | 14 (curado, essenciais) |
| Security | x-api-key em cada endpoint | Global (security scheme) |
| Schemas | Gigantescos (nullable, complexos) | Simplificados, Custom GPT-friendly |
| Tamanho | ~35 KB | ~32 KB |
| Legibilidade | Técnica, gerada automaticamente | Legível, documentação clara |

---

## 🐛 Troubleshooting

### "Action não aparece no Custom GPT"

**Causa:** Endpoint pode não estar em `paths`  
**Solução:** Verificar se `operationId` está bem definido e único

### "Erro 401 Unauthorized"

**Causa:** API key ausente ou inválida  
**Solução:** Verificar se x-api-key foi configurada corretamente no Custom GPT

### "Parâmetro {apelido} não funciona"

**Causa:** Apelido case-sensitive no backend  
**Solução:** Usar lowercase consistentemente (ex: "johnny", não "Johnny")

### "Custom GPT não reconhece schemas"

**Causa:** Schemas podem estar muito complexos ou mal estruturados  
**Solução:** Usar o schema Custom GPT (este arquivo), não o FastAPI

---

## 📚 Referências

- **OpenAPI 3.1.0 Spec:** https://spec.openapis.org/oas/v3.1.0
- **Custom GPT Actions:** https://platform.openai.com/docs/guides/gpts/actions
- **GoJohnny Backend:** https://gojohnny.onrender.com

---

## 📝 Changelog

### v2.0.0 (2026-05-06)

- ✨ Schema custom otimizado para Custom GPT Actions
- ✨ 14 operations essenciais (não 19 endpoints genéricos)
- ✨ Security scheme global (sem x-api-key repetido)
- ✨ Schemas simplificados (Custom GPT-friendly)
- ✨ OperationIds curtos e descritivos
- ✨ Documentação em português
- ✨ Removido: /health, /, oauth callback, oauth disconnect

---

**Mantido por:** Claude Code  
**Última atualização:** 2026-05-06T01:00:00Z
