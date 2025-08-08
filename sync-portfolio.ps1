# Script PowerShell para sincronizar projeto principal e portfólio
# Execute: .\sync-portfolio.ps1

Write-Host "🔄 Iniciando sincronização do portfólio..." -ForegroundColor Cyan
Write-Host ""

# Função para exibir mensagens coloridas
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 1. Atualizar projeto principal
Write-Status "Atualizando projeto principal..."
# Não mudar de diretório, já estamos no projeto principal

if (Test-Path ".git") {
    Write-Status "Fazendo commit das mudanças no projeto principal..."
    git add .
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "Atualização automática - $timestamp"
    git push origin main
    Write-Success "Projeto principal atualizado!"
} else {
    Write-Error "Não é um repositório Git válido!"
    exit 1
}

# 2. Atualizar clone do portfólio
Write-Status "Atualizando clone do portfólio..."
Set-Location ..\projeto-bd-modernizado-portifolio

if (Test-Path ".git") {
    Write-Status "Buscando mudanças do upstream..."
    git fetch upstream
    
    Write-Status "Fazendo merge das mudanças..."
    git merge upstream/main
    
    Write-Status "Enviando para o repositório do portfólio..."
    git push origin main
    
    Write-Success "Clone do portfólio atualizado!"
} else {
    Write-Error "Clone do portfólio não é um repositório Git válido!"
    exit 1
}

Write-Host ""
Write-Success "✅ Sincronização completa!"
Write-Status "O Render deve fazer deploy automático em alguns minutos."
Write-Host ""
Write-Warning "💡 Dica: Execute este script sempre que fizer mudanças importantes no projeto principal."
