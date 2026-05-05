# GoJohnny - ETAPA 3, FASE 3.1: Modelo de Evento

**Data**: 2026-05-04  
**Status**: ✅ **VALIDADO COM SUCESSO**

---

## 🎯 Objetivo

Transformar plano estruturado (ETAPA 1) + contexto do usuário (ETAPA 2) em eventos de calendário.

**Resultado**: Eventos prontos para integração com Google Calendar (FASE 3.5).

---

## 📦 O QUE FOI IMPLEMENTADO

### 1. Schema Pydantic (`app/schemas/evento.py`)

```python
EventoTreinoRead {
    titulo: str          # "Treino leve"
    descricao: str       # "8km ritmo leve (terça)"
    data: date          # "2026-05-05"
    hora: time          # "07:00"
    duracao_min: int    # 60
}

CalendarioPreview {
    atleta_apelido: str
    total_eventos: int
    eventos: List[EventoTreinoRead]
    periodo_inicio: date
    periodo_fim: date
}
```

### 2. Serviço (`app/services/evento_service.py`)

**Função principal:**
```python
def gerar_eventos_treino(
    plano: Dict[str, Any],
    contexto: Optional[Dict[str, Any]] = None
) -> List[EventoTreinoRead]
```

**O que faz:**
- Lê treinos do plano (`plano["treinos"]`)
- Extrai contexto (horário preferido)
- Estima duração (baseado em distância)
- Constrói título e descrição
- Ordena por data
- Retorna eventos estruturados

**Funções auxiliares:**
- `_extrair_horario_preferido()` - Busca `contexto["preferencia"]["horario_preferido"]`
- `_estimar_duracao_treino()` - ~6 min/km
- `_construir_titulo_evento()` - Tipo + contexto
- `_construir_descricao_evento()` - Distância + tipo + dia

### 3. Endpoint (`app/routes/calendario.py`)

**Nova rota:**
```
GET /calendario/{apelido}/preview
```

**Resposta:**
```json
{
  "atleta_apelido": "johnny",
  "total_eventos": 8,
  "periodo_inicio": "2026-05-04",
  "periodo_fim": "2026-05-11",
  "eventos": [
    {
      "titulo": "Treino leve",
      "descricao": "8km - leve (terça)",
      "data": "2026-05-05",
      "hora": "07:00",
      "duracao_min": 48
    }
  ]
}
```

---

## 🧪 TESTES VALIDADOS (8/8)

| # | Teste | Status | Validação |
|---|-------|--------|-----------|
| 1 | Estrutura de evento | ✅ PASS | Todos campos presentes |
| 2 | Aplicação de contexto | ✅ PASS | Usa horario_preferido |
| 3 | Estimativa de duração | ✅ PASS | ~6 min/km |
| 4 | Ordenação por data | ✅ PASS | Crescente |
| 5 | Coerência plano-evento | ✅ PASS | Descrição contém tipo/dist |
| 6 | Plano inválido | ✅ PASS | Fallback a lista vazia |
| 7 | Contexto inválido | ✅ PASS | Usa padrão 07:00 |
| 8 | Múltiplos eventos/dia | ✅ PASS | Todos criados |

**Taxa de sucesso**: 100% (8/8)

---

## 🔗 INTEGRAÇÃO COM ETAPA 1 E ETAPA 2

### ETAPA 1 (Datas Reais)
```
plano["treinos"][0] = {
    "dia_semana": "terca",
    "tipo": "leve",
    "distancia_km": 8,
    "data": "2026-05-05"  ← Usa isso
}
```

### ETAPA 2 (Contexto)
```
contexto = {
    "preferencia": {
        "horario_preferido": "06:30"  ← Usa isso
    }
}
```

### FASE 3.1 (Evento)
```
evento = {
    "titulo": "Treino leve",
    "descricao": "8km - leve (terça)",
    "data": "2026-05-05",
    "hora": "06:30",        ← Do contexto
    "duracao_min": 48       ← Estimado
}
```

---

## 🚀 PRÓXIMAS FASES

### FASE 3.2 - Simulação de Calendário (Pronta)
- Endpoint `/calendario/{apelido}/preview` **JÁ IMPLEMENTADO**
- Testa lógica antes de Google

### FASE 3.3 - Estrutura de Integração (Próxima)
- Tabela `integracao_google`
- Flag `usar_google_calendar`

### FASE 3.4 - OAuth (Depois)
- Endpoints de login/callback
- Config: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

### FASE 3.5 - Criar Evento Real (Último)
- Integração com Google Calendar API
- Criação de eventos reais

---

## 📋 ARQUIVOS CRIADOS/ALTERADOS

### Novos
- `app/schemas/evento.py` - Schemas Pydantic
- `app/services/evento_service.py` - Lógica de evento
- `app/routes/calendario.py` - Endpoints
- `scripts/validate_etapa3_fase1.py` - Validação

### Alterado
- `app/main.py` - Adicionado routers `contexto` e `calendario`

---

## ⚠️ REGRAS RESPEITADAS

- ✅ Não quebra fluxo atual (ETAPA 1, 2)
- ✅ Tudo controlado por flag (vai vir em FASE 3.3)
- ✅ Não depende do Google
- ✅ Falha externa não quebra resposta
- ✅ Contexto é enriquecimento (nunca dependência)
- ✅ Dados já estruturados (ETAPA 1, 2)

---

## 🧭 PRÓXIMO PASSO

→ **FASE 3.2**: Validar endpoint `/calendario/{apelido}/preview`  
→ Depois: **FASE 3.3** (Estrutura de integração)
