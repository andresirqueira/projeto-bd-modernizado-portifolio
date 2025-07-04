#!/usr/bin/env python3
"""
Script final para verificar e corrigir problemas com dark mode em todas as páginas HTML.
"""

import os
import re
from pathlib import Path

def final_fix_html_file(file_path):
    """Correção final para um arquivo HTML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # 1. Corrigir função toggleDarkMode com sintaxe duplicada
        if 'updateEmpresaLogo();\n        }\n        // Atualizar logo da empresa quando o tema mudar\n        updateEmpresaLogo();' in content:
            content = re.sub(
                r'updateEmpresaLogo\(\);\n        \}\n        // Atualizar logo da empresa quando o tema mudar\n        updateEmpresaLogo\(\);\n        \}\n        \}',
                'updateEmpresaLogo();\n      }',
                content
            )
            changes_made = True
        
        # 2. Corrigir função toggleDarkMode sem updateEmpresaLogo
        if 'function toggleDarkMode()' in content and 'updateEmpresaLogo();' not in content:
            content = re.sub(
                r'(function toggleDarkMode\(\) \{[^}]*\})',
                r'\1\n        // Atualizar logo da empresa quando o tema mudar\n        updateEmpresaLogo();',
                content,
                flags=re.DOTALL
            )
            changes_made = True
        
        # 3. Atualizar carregamento do logo da empresa para usar LogoManager
        if 'document.getElementById(\'empresa-logada\').innerHTML' in content:
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
            changes_made = True
        
        # 4. Garantir que o script do LogoManager está incluído
        if 'logo-manager.js' not in content and 'empresa-logada' in content:
            # Adicionar antes do </body>
            content = re.sub(
                r'(</body>)',
                r'    <script src="static/js/logo-manager.js"></script>\n\1',
                content
            )
            changes_made = True
        
        # Se houve mudanças, salvar o arquivo
        if changes_made:
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
    
    print("🔄 Correção final do dark mode em todas as páginas...")
    print("=" * 60)
    
    for html_file in html_files:
        file_path = current_dir / html_file
        if file_path.exists():
            total_count += 1
            if final_fix_html_file(file_path):
                updated_count += 1
        else:
            print(f"⚠️  Arquivo não encontrado: {html_file}")
    
    print("=" * 60)
    print(f"📊 Resumo: {updated_count}/{total_count} arquivos corrigidos")
    print("✅ Correção final concluída!")

if __name__ == "__main__":
    main() 