#!/usr/bin/env python3
"""
Script para corrigir a função toggleDarkMode em todas as páginas HTML.
"""

import os
import re
from pathlib import Path

def fix_dark_mode_function(file_path):
    """Corrige a função toggleDarkMode em um arquivo HTML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Corrigir função toggleDarkMode com erro de sintaxe
        content = re.sub(
            r'function toggleDarkMode\(\) \{[^}]*if \(document\.documentElement\.classList\.contains\(\'dark\'\)\) \{[^}]*document\.documentElement\.classList\.remove\(\'dark\'\);[^}]*localStorage\.setItem\(\'theme\', \'light\'\);[^}]*\}\s*// Atualizar logo da empresa quando o tema mudar\s*updateEmpresaLogo\(\); else \{[^}]*document\.documentElement\.classList\.add\(\'dark\'\);[^}]*localStorage\.setItem\(\'theme\', \'dark\'\);[^}]*\}',
            '''function toggleDarkMode() {
        if (document.documentElement.classList.contains('dark')) {
          document.documentElement.classList.remove('dark');
          localStorage.setItem('theme', 'light');
        } else {
          document.documentElement.classList.add('dark');
          localStorage.setItem('theme', 'dark');
        }
        // Atualizar logo da empresa quando o tema mudar
        updateEmpresaLogo();
      }''',
            content,
            flags=re.DOTALL
        )
        
        # Corrigir função toggleDarkMode sem updateEmpresaLogo
        content = re.sub(
            r'function toggleDarkMode\(\) \{[^}]*if \(document\.documentElement\.classList\.contains\(\'dark\'\)\) \{[^}]*document\.documentElement\.classList\.remove\(\'dark\'\);[^}]*localStorage\.setItem\(\'theme\', \'light\'\);[^}]*\} else \{[^}]*document\.documentElement\.classList\.add\(\'dark\'\);[^}]*localStorage\.setItem\(\'theme\', \'dark\'\);[^}]*\}',
            '''function toggleDarkMode() {
        if (document.documentElement.classList.contains('dark')) {
          document.documentElement.classList.remove('dark');
          localStorage.setItem('theme', 'light');
        } else {
          document.documentElement.classList.add('dark');
          localStorage.setItem('theme', 'dark');
        }
        // Atualizar logo da empresa quando o tema mudar
        updateEmpresaLogo();
      }''',
            content,
            flags=re.DOTALL
        )
        
        # Atualizar carregamento do logo da empresa para usar LogoManager
        content = re.sub(
            r'window\.addEventListener\(\'DOMContentLoaded\', function\(\) \{[^}]*fetch\(\'/empresa_atual\'\)[^}]*\.then\(resp => resp\.json\(\)\)[^}]*\.then\(data => \{[^}]*if \(data\.logo\) \{[^}]*document\.getElementById\(\'empresa-logada\'\)\.innerHTML = `<img src="\$\{data\.logo\}" alt="Logo da empresa" style="max-height:40px;max-width:120px;object-fit:contain;">`;[^}]*\} else if \(data\.nome\) \{[^}]*document\.getElementById\(\'empresa-logada\'\)\.innerText = \'Empresa: \' \+ data\.nome;[^}]*\}[^}]*\}[^}]*\}[^}]*\}\);',
            '''window.addEventListener('DOMContentLoaded', function() {
            fetch('/empresa_atual')
                .then(resp => resp.json())
                .then(data => {
                    LogoManager.loadEmpresaLogo(data);
                });
        });''',
            content,
            flags=re.DOTALL
        )
        
        # Se houve mudanças, salvar o arquivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Corrigido: {file_path}")
            return True
        else:
            print(f"⏭️  Sem mudanças: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {e}")
        return False

def main():
    """Função principal que processa todos os arquivos HTML."""
    # Diretório atual
    current_dir = Path('.')
    
    # Lista de arquivos HTML para processar
    html_files = [
        'adicionar-sala.html',
        'adicionar-switch.html',
        'adicionar-equipamento.html',
        'config-usuario.html',
        'config-tecnico.html',
        'editar-sala.html',
        'editar-equipamento.html',
        'editar-switch.html',
        'excluir-sala.html',
        'excluir-equipamento.html',
        'excluir-switch.html',
        'gerenciar-equipamentos.html',
        'gerenciar-portas-switch.html',
        'ping-equipamentos.html',
        'upload-fotos-salas.html',
        'ver-salas.html',
        'ver-equipamento.html',
        'ver-switch.html',
        'visualizar-logs.html',
        'visualizar-layout-sala.html',
        'visualizar-switch-sala.html',
        'detalhes-sala.html',
        'detalhes-equipamentos-sala.html'
    ]
    
    updated_count = 0
    total_count = 0
    
    print("🔄 Corrigindo função toggleDarkMode em todas as páginas...")
    print("=" * 60)
    
    for html_file in html_files:
        file_path = current_dir / html_file
        if file_path.exists():
            total_count += 1
            if fix_dark_mode_function(file_path):
                updated_count += 1
        else:
            print(f"⚠️  Arquivo não encontrado: {html_file}")
    
    print("=" * 60)
    print(f"📊 Resumo: {updated_count}/{total_count} arquivos corrigidos")
    print("✅ Correção concluída!")

if __name__ == "__main__":
    main() 