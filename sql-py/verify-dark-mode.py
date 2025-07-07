#!/usr/bin/env python3
"""
Script para verificar se o dark mode está funcionando corretamente em todas as páginas.
"""

import os
import re
from pathlib import Path

def verify_dark_mode(file_path):
    """Verifica se o dark mode está funcionando corretamente em um arquivo HTML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # 1. Verificar se tem a configuração do Tailwind
        if 'tailwind.config = { darkMode: \'class\' }' not in content:
            issues.append("❌ Falta configuração do Tailwind dark mode")
        
        # 2. Verificar se tem a função toggleDarkMode correta
        if 'function toggleDarkMode()' not in content:
            issues.append("❌ Falta função toggleDarkMode")
        elif 'updateEmpresaLogo();' not in content:
            issues.append("❌ Função toggleDarkMode não chama updateEmpresaLogo")
        elif 'updateEmpresaLogo();\n        }\n        // Atualizar logo da empresa quando o tema mudar\n        updateEmpresaLogo();' in content:
            issues.append("❌ Função toggleDarkMode com código duplicado")
        
        # 3. Verificar se tem o script do LogoManager
        if 'logo-manager.js' not in content:
            issues.append("❌ Falta script do LogoManager")
        
        # 4. Verificar se usa LogoManager.loadEmpresaLogo
        if 'LogoManager.loadEmpresaLogo(data)' not in content:
            issues.append("❌ Não usa LogoManager.loadEmpresaLogo")
        
        # 5. Verificar se tem as classes dark mode no body
        if 'dark:bg-gradient-to-br' not in content:
            issues.append("❌ Falta classes dark mode no body")
        
        # 6. Verificar se tem o container da empresa-logada com fundo condicional
        if 'bg-gray-800 dark:bg-transparent' not in content:
            issues.append("❌ Container empresa-logada sem fundo condicional")
        
        if issues:
            print(f"⚠️  {file_path.name}:", flush=True)
            for issue in issues:
                print(f"   {issue}", flush=True)
            return False
        else:
            print(f"✅ {file_path.name}: Dark mode funcionando corretamente", flush=True)
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar {file_path}: {e}")
        return False

def main():
    """Função principal que verifica todas as páginas HTML."""
    # Diretório atual
    current_dir = Path('.')
    
    # Páginas específicas mencionadas pelo usuário
    target_pages = [
        'editar-sala.html',
        'excluir-sala.html', 
        'ver-salas.html',
        'upload-fotos-salas.html'
    ]
    
    working_count = 0
    total_count = 0
    
    print("🔍 Verificando dark mode nas páginas específicas...", flush=True)
    print("=" * 60, flush=True)
    
    for html_file in target_pages:
        file_path = current_dir / html_file
        if file_path.exists():
            total_count += 1
            if verify_dark_mode(file_path):
                working_count += 1
        else:
            print(f"⚠️  Arquivo não encontrado: {html_file}", flush=True)
    
    print("=" * 60, flush=True)
    print(f"📊 Resumo: {working_count}/{total_count} páginas com dark mode funcionando", flush=True)
    
    if working_count == total_count:
        print("🎉 Todas as páginas estão funcionando corretamente!", flush=True)
    else:
        print("⚠️  Algumas páginas ainda precisam de correção.", flush=True)

if __name__ == "__main__":
    main() 