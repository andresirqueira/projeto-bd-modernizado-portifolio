#!/bin/bash

# Script de Sincronização Rápida
# Uso: ./sync.sh [pull|push|status]

echo "🔄 Script de Sincronização - VS Code ↔ Workspace IA"
echo "=================================================="

case $1 in
    "pull")
        echo "📥 Baixando mudanças do repositório..."
        git pull origin main
        echo "✅ Sincronização concluída!"
        ;;
    "push")
        echo "📤 Enviando mudanças para o repositório..."
        git add .
        git commit -m "Sincronização automática - $(date)"
        git push origin main
        echo "✅ Mudanças enviadas!"
        ;;
    "status")
        echo "📊 Status do repositório:"
        git status
        echo ""
        echo "📝 Últimos commits:"
        git log --oneline -5
        ;;
    *)
        echo "❌ Uso: ./sync.sh [pull|push|status]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  pull   - Baixa mudanças do repositório"
        echo "  push   - Envia mudanças para o repositório"
        echo "  status - Mostra status atual"
        ;;
esac