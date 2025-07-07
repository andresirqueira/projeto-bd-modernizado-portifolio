#!/usr/bin/env python3
"""
Script para atualizar automaticamente todas as páginas HTML
para incluir fundo condicional nos logos da empresa e marcas.
"""

import os
import re
from pathlib import Path

def update_html_file(file_path):
    """Atualiza um arquivo HTML para incluir fundo condicional nos logos."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Atualizar container empresa-logada
        content = re.sub(
            r'<div id="empresa-logada" class="absolute top-4 right-4 text-indigo-500 font-bold"></div>',
            '<div id="empresa-logada" class="absolute top-4 right-4 text-indigo-500 font-bold bg-gray-800 dark:bg-transparent rounded-lg p-2"></div>',
            content
        )
        
        # 2. Adicionar script do LogoManager se não existir
        if 'logo-manager.js' not in content:
            # Encontrar o último </script> antes do </body>
            script_pattern = r'(</script>\s*)(</body>)'
            if re.search(script_pattern, content):
                content = re.sub(
                    script_pattern,
                    r'\1    <script src="static/js/logo-manager.js"></script>\n    \2',
                    content
                )
        
        # 3. Atualizar função toggleDarkMode para incluir updateEmpresaLogo
        content = re.sub(
            r'(function toggleDarkMode\(\) \{[^}]*\})',
            r'\1\n        // Atualizar logo da empresa quando o tema mudar\n        updateEmpresaLogo();',
            content
        )
        
        # 4. Atualizar carregamento do logo da empresa para usar LogoManager
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
        
        # 5. Atualizar renderização de logos de marcas para usar LogoManager
        content = re.sub(
            r'<div class=\'absolute top-2 left-2 w-8 h-8 flex items-center justify-center\'><img src=\'static/img/\$\{eq\.marca\.toLowerCase\(\)\}\.png\' onerror="this\.style\.display=\'none\'" alt=\'\$\{eq\.marca\}\' title=\'\$\{eq\.marca\}\' class=\'max-w-full max-h-full object-contain\'></div>',
            '${(eq.marca ? LogoManager.renderMarcaLogo(eq.marca) : \'\')}',
            content
        )
        
        # 6. Atualizar outros padrões de logos de marcas
        content = re.sub(
            r'<div class=\'absolute top-3 right-3 w-10 h-10 bg-white dark:bg-gray-700 rounded-lg flex items-center justify-center shadow-md\'><img src=\'static/img/\$\{eq\.marca\.toLowerCase\(\)\}\.png\' onerror="this\.style\.display=\'none\'" alt=\'\$\{eq\.marca\}\' title=\'\$\{eq\.marca\}\' class=\'max-w-8 max-h-8 object-contain\'></div>',
            '${(eq.marca ? LogoManager.renderMarcaLogo(eq.marca) : \'\')}',
            content
        )
        
        # Se houve mudanças, salvar o arquivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Atualizado: {file_path}")
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
        'config-admin.html',
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
    
    print("🔄 Iniciando atualização dos logos em todas as páginas...")
    print("=" * 60)
    
    for html_file in html_files:
        file_path = current_dir / html_file
        if file_path.exists():
            total_count += 1
            if update_html_file(file_path):
                updated_count += 1
        else:
            print(f"⚠️  Arquivo não encontrado: {html_file}")
    
    print("=" * 60)
    print(f"📊 Resumo: {updated_count}/{total_count} arquivos atualizados")
    print("✅ Atualização concluída!")

if __name__ == "__main__":
    main() 