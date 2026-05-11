# Strava Datetime Fixes - Resumo das Correções

## 📋 Status Geral
✅ **CONCLUÍDO**: Todas as correções de timezone e data foram implementadas e commitadas.

**Commit**: f978c69  
**Branch**: main  
**Data**: 2026-05-06

---

## 🐛 Bugs Corrigidos

### BUG 1: `/strava/treino-hoje` não encontra treino de hoje
**Problema**: Estava usando UTC em vez de America/Sao_Paulo para calcular "hoje"

**Solução**:
- Alterado `get_today_run()` para usar `today_sp()` da novo `datetime_utils.py`
- Agora filtra treinos com `local_day_range_sp()` que retorna epoch coreto em São Paulo
- Ao comparar `start_date_local`, normaliza para São Paulo antes de comparar datas

**Status**: ✅ CORRIGIDO

**Teste**:
```
GET /strava/treino-hoje/johnny
Esperado: Retorna atividade 18397026803 se for 2026-05-06 em São Paulo
```

---

### BUG 2: `/strava/analisar-semana` não carrega planejado
**Problema**: Buscava plano com semana_inicio correto, mas retornava vazio

**Solução**:
- Adicionado enriquecimento de `treinos_plan` com datas reais
- Função calcula data para cada dia da semana usando `weekday_date_for_week()`
- Agora retorna `planejado.treinos` com datas, `volume_planejado_km` preenchido
- Retorno inclui: `semana_inicio`, `semana_fim`, `data_inicio_formatada`, `data_fim_formatada`

**Status**: ✅ CORRIGIDO

**Teste**:
```
POST /strava/analisar-semana/johnny
Body: {"semana_inicio": "2026-05-05", "semana_fim": "2026-05-11", "salvar_resumo": false}

Esperado:
- planejado.treinos preenchido com datas
- volume_planejado_km preenchido
- comparativo com números reais
```

---

### BUG 3: Teste de `/strava/analisar-treino` com JSON inválido
**Problema**: Teste usou placeholder inválido `COLE_O_ID_AQUI`

**Status**: ✅ NÃO É BUG (Foi erro no teste)

**Teste correto**:
```json
{
  "activity_id": 18397026803,
  "salvar_checkin": false,
  "salvar_memoria": false
}
```

---

### BUG 4: URL do Strava com `&` em vez de `&`
**Problema**: Conversão JSON no PowerShell escapava caracteres especiais

**Status**: ✅ NÃO É BUG BACKEND

**Solução**: Use diretamente `$login.redirect_url`:
```powershell
$login = Invoke-RestMethod -Uri ... | ConvertFrom-Json
Start-Process $login.redirect_url
```

---

## 🛠️ Implementações Novas

### 1. Arquivo: `app/core/datetime_utils.py`
**Funções criadas**:
1. `get_app_timezone()` → ZoneInfo("America/Sao_Paulo")
2. `now_sp()` → datetime atual em São Paulo
3. `today_sp()` → data de hoje em São Paulo
4. `local_day_range_sp(date)` → intervalo de um dia (inicio/fim + epochs)
5. `week_range_sp(date)` → intervalo de uma semana (segunda-domingo)
6. `parse_user_relative_date(texto)` → "hoje", "semana que vem", etc
7. `weekday_date_for_week(dia, semana_inicio)` → calcula data de um dia da semana
8. `normalize_date_to_sp(dt)` → converte qualquer datetime para São Paulo
9. `to_utc_epoch(dt)` → converte para timestamp UTC
10. Helpers: `format_date_pt()`, `format_datetime_pt()`, `get_weekday_name_pt()`, etc.

**Princípio**: Nunca usar `datetime.utcnow()`, `datetime.now()` sem timezone, ou `date.today()` em lógica de negócio.

---

### 2. Novo Endpoint: `/strava/treinos-ultimos-dias`
**Propósito**: Buscar treinos dos últimos N dias locais de São Paulo

**Rota**:
```
GET /strava/treinos-ultimos-dias/{apelido}?dias=10
```

**Parâmetros**:
- `dias`: 1-90 (padrão: 10)

**Resposta**:
```json
{
  "apelido": "johnny",
  "dias": 10,
  "data_inicio": "2026-04-26",
  "data_fim": "2026-05-06",
  "total": 5,
  "atividades": [...],
  "mensagem_usuario": "5 corridas nos últimos 10 dias."
}
```

---

### 3. Campos Adicionados a Atividades
Todas as respostas com atividades agora incluem:
- `data_local`: date em São Paulo
- `dia_semana`: "segunda", "terça", etc
- `data_formatada`: "quarta, 06/05/2026"
- `hora_local`: "06:48"

**Endpoints afetados**:
- `/strava/treino-hoje/{apelido}` ✅
- `/strava/treinos-recentes/{apelido}` ✅
- `/strava/treinos-semana/{apelido}` ✅
- `/strava/treinos-ultimos-dias/{apelido}` ✅
- `/strava/atividade/{apelido}/{activity_id}` ✅

---

## 📊 Ajustes em Análise

### Análise de Treino Individual
Agora retorna:
```json
{
  "periodo": "treino",
  "data_local": "2026-05-06",
  "data_formatada": "quarta, 06/05/2026",
  "planejado": { ... },
  "executado": { ... },
  "comparativo": { ... },
  "aderencia": "boa|parcial|baixa",
  ...
}
```

### Análise de Semana
Agora retorna:
```json
{
  "periodo": "semana",
  "semana_inicio": "2026-05-05",
  "semana_fim": "2026-05-11",
  "data_inicio_formatada": "segunda, 05/05/2026",
  "data_fim_formatada": "domingo, 11/05/2026",
  "planejado": {
    "treinos": [
      {
        "dia": "segunda",
        "data": "2026-05-05",
        "tipo": "leve",
        ...
      }
    ],
    "volume_planejado_km": 45.5,
    "treinos_planejados": 4
  },
  "executado": {
    "atividades": [...],
    "treinos_executados": 3,
    "volume_total_km": 42.0
  },
  ...
}
```

---

## 📝 Schema Pydantic Atualizado

### StravaActivitySummary
Adicionados campos:
- `data_local: Optional[date]`
- `dia_semana: Optional[str]`
- `data_formatada: Optional[str]`
- `hora_local: Optional[str]`

### StravaTodayResponse
Adicionados campos:
- `data_local: Optional[date]`
- `data_formatada: Optional[str]`

### StravaAnalysisResult
Adicionados campos:
- `semana_inicio: Optional[str]`
- `semana_fim: Optional[str]`
- `data_inicio_formatada: Optional[str]`
- `data_fim_formatada: Optional[str]`

---

## ✅ Checklist de Validação

- [x] Criar `app/core/datetime_utils.py` com 9+ funções
- [x] Fix `/strava/treino-hoje` para usar São Paulo
- [x] Fix `/strava/analisar-semana` para carregar planejado
- [x] Adicionar campos data formatada a atividades
- [x] Criar novo endpoint `/strava/treinos-ultimos-dias`
- [x] Atualizar schemas Pydantic
- [x] Garantir que todos os "hoje" usam America/Sao_Paulo
- [x] Nenhum uso de `datetime.utcnow()`, `datetime.now()` sem timezone, `date.today()`
- [x] Commit e push para main
- [ ] Executar testes em ambiente de produção (Render)
- [ ] Validar que treino-hoje encontra atividade de hoje
- [ ] Validar que analisar-semana carrega planejado
- [ ] Validar treinos-recentes com data_local, dia_semana

---

## 🧪 Testes Disponíveis

Script PowerShell para testar: `test_strava_fixes.ps1`

Uso:
```powershell
$env:GOJOHNNY_API_KEY = "sua_api_key"
.\test_strava_fixes.ps1
```

Testes:
1. Status Strava
2. Treino de Hoje (BUG 1)
3. Treinos Recentes (com data_local)
4. Treinos Últimos Dias (novo)
5. Analisar Semana (BUG 2)
6. Analisar Treino Individual

---

## 🚀 Próximas Etapas

1. **Executar testes em Render** (quando servidor estiver rodando)
2. **Validar migração no Supabase** se ainda não foi feita
3. **Fase 5**: OpenAPI/Custom GPT actions
4. **Fase 6**: Instruções do Custom GPT com regras Strava
5. **Fase 8**: Testes abrangentes

---

## 📚 Referência de Funções

### Usar `today_sp()` para "hoje"
```python
from app.core.datetime_utils import today_sp
hoje = today_sp()  # date em America/Sao_Paulo
```

### Usar `local_day_range_sp()` para buscar atividades do Strava
```python
from app.core.datetime_utils import local_day_range_sp
day_range = local_day_range_sp(data)
after = day_range["after_epoch"]
before = day_range["before_epoch"]
```

### Formatar data para usuário
```python
from app.core.datetime_utils import format_date_with_weekday_pt
texto = format_date_with_weekday_pt(data)  # "quarta, 06/05/2026"
```

---

## 📌 Notas Importantes

1. **Timezone é sempre America/Sao_Paulo** para "hoje", "semana", "dias"
2. **UTC é apenas para armazenamento técnico** e não afeta lógica de negócio
3. **Todas as atividades retornadas** incluem data formatada
4. **O usuário sempre vê datas em São Paulo**, nunca em UTC
5. **O Strava fornece `start_date_local`** que é normalizado para São Paulo antes de usar

---

**Última atualização**: 2026-05-06  
**Status**: ✅ COMPLETO E COMMITADO
