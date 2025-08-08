#!/bin/bash

echo "🔄 Iniciando sincronização do portfólio..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Atualizar projeto principal
print_status "Atualizando projeto principal..."
cd ../

if [ -d ".git" ]; then
    print_status "Fazendo commit das mudanças no projeto principal..."
    git add .
    git commit -m "Atualização automática - $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    print_success "Projeto principal atualizado!"
else
    print_error "Não é um repositório Git válido!"
    exit 1
fi

# 2. Atualizar clone do portfólio
print_status "Atualizando clone do portfólio..."
cd projeto-bd-modernizado-portifolio

if [ -d ".git" ]; then
    print_status "Buscando mudanças do upstream..."
    git fetch upstream
    
    print_status "Fazendo merge das mudanças..."
    git merge upstream/main
    
    print_status "Enviando para o repositório do portfólio..."
    git push origin main
    
    print_success "Clone do portfólio atualizado!"
else
    print_error "Clone do portfólio não é um repositório Git válido!"
    exit 1
fi

echo ""
print_success "✅ Sincronização completa!"
print_status "O Render deve fazer deploy automático em alguns minutos."
echo ""
print_warning "💡 Dica: Execute este script sempre que fizer mudanças importantes no projeto principal."
