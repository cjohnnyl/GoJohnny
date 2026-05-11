# Script para testar as correções do Strava com timezones America/Sao_Paulo

# Configuração
$apiKey = $env:GOJOHNNY_API_KEY  # Deve estar configurada no ambiente
if (-not $apiKey) {
    Write-Host "ERRO: GOJOHNNY_API_KEY nao configurada" -ForegroundColor Red
    exit 1
}

$baseUrl = "https://gojohnny.onrender.com"
$apelido = "johnny"

function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Uri,
        [string]$Body = "",
        [string]$TestName
    )

    Write-Host "`n=== $TestName ===" -ForegroundColor Cyan
    Write-Host "Method: $Method" -ForegroundColor Gray
    Write-Host "Uri: $Uri" -ForegroundColor Gray

    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = @{ "x-api-key" = $apiKey }
            ErrorAction = "Stop"
        }

        if ($Body -ne "") {
            $params.Body = $Body
            $params.ContentType = "application/json"
        }

        $response = Invoke-RestMethod @params
        $json = $response | ConvertTo-Json -Depth 10
        Write-Host $json -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $errorBody = $reader.ReadToEnd()
                Write-Host "Response: $errorBody" -ForegroundColor Red
            }
            catch {}
        }
        return $null
    }
}

Write-Host "Iniciando testes de Strava com America/Sao_Paulo" -ForegroundColor Yellow
Write-Host "Base URL: $baseUrl" -ForegroundColor Yellow
Write-Host "Atleta: $apelido" -ForegroundColor Yellow

# Teste 1: Status
Test-Endpoint -Method GET `
    -Uri "$baseUrl/strava/status/$apelido" `
    -TestName "1. Status Strava"

# Teste 2: Treino de hoje (BUG 1)
Test-Endpoint -Method GET `
    -Uri "$baseUrl/strava/treino-hoje/$apelido" `
    -TestName "2. Treino de Hoje (BUG 1 - Should find today's run in SP timezone)"

# Teste 3: Treinos recentes (com data_local, dia_semana)
Test-Endpoint -Method GET `
    -Uri "$baseUrl/strava/treinos-recentes/$apelido`?limit=10" `
    -TestName "3. Treinos Recentes (Should include data_local, dia_semana, data_formatada, hora_local)"

# Teste 4: Últimos 10 dias (novo endpoint)
Test-Endpoint -Method GET `
    -Uri "$baseUrl/strava/treinos-ultimos-dias/$apelido`?dias=10" `
    -TestName "4. Treinos Últimos Dias (novo endpoint)"

# Teste 5: Treinos da semana (BUG 2 - Should load planejado)
$body = @{
    semana_inicio = "2026-05-05"
    semana_fim = "2026-05-11"
    salvar_resumo = $false
} | ConvertTo-Json

Test-Endpoint -Method POST `
    -Uri "$baseUrl/strava/analisar-semana/$apelido" `
    -Body $body `
    -TestName "5. Analisar Semana (BUG 2 - Should load planejado with dates)"

# Teste 6: Analisar treino individual (BUG 3)
$body = @{
    activity_id = 18397026803
    salvar_checkin = $false
    salvar_memoria = $false
} | ConvertTo-Json

Test-Endpoint -Method POST `
    -Uri "$baseUrl/strava/analisar-treino/$apelido" `
    -Body $body `
    -TestName "6. Analisar Treino Individual"

Write-Host "`n=== Testes Concluídos ===" -ForegroundColor Yellow
Write-Host "Verifique se:" -ForegroundColor Yellow
Write-Host "  1. treino-hoje encontrou a atividade 18397026803" -ForegroundColor Gray
Write-Host "  2. analisar-semana retornou planejado e executado" -ForegroundColor Gray
Write-Host "  3. Todas as datas estão em America/Sao_Paulo" -ForegroundColor Gray
Write-Host "  4. Campos de data_local, dia_semana, data_formatada aparecem" -ForegroundColor Gray
