#!/usr/bin/env python3
import os
import re

def fix_marca_logos():
    """Corrige os logos das marcas em todas as páginas HTML para usar o LogoManager"""
    
    # Padrões para encontrar renderização inline de logos de marcas
    patterns = [
        # Padrão 1: Logo com fundo condicional inline
        (
            r"const isDark = document\.documentElement\.classList\.contains\('dark'\);\s*const bgClass = isDark \? 'dark:bg-gray-700' : 'bg-gray-800';\s*html \+= `<div class='absolute top-2 left-2 w-8 h-8 \$\{bgClass\} rounded-lg flex items-center justify-center shadow-md'><img src='static/img/\$\{eq\.marca\.toLowerCase\(\)\}\.png' onerror=\"this\.style\.display='none'\" alt='\$\{eq\.marca\}' title='\$\{eq\.marca\}' class='max-w-full max-h-full object-contain'></div>`;",
            "html += LogoManager.renderMarcaLogo(eq.marca);"
        ),
        # Padrão 2: Logo simples sem fundo condicional
        (
            r"html \+= `<div class='absolute top-2 left-2 w-8 h-8 flex items-center justify-center'><img src='static/img/\$\{eq\.marca\.toLowerCase\(\)\}\.png' onerror=\"this\.style\.display='none'\" alt='\$\{eq\.marca\}' title='\$\{eq\.marca\}' class='max-w-full max-h-full object-contain'></div>`;",
            "html += LogoManager.renderMarcaLogo(eq.marca);"
        ),
        # Padrão 3: Logo com shadow-md
        (
            r"html \+= `<div class='absolute top-2 left-2 w-8 h-8 flex items-center justify-center shadow-md'><img src='static/img/\$\{eq\.marca\.toLowerCase\(\)\}\.png' onerror=\"this\.style\.display='none'\" alt='\$\{eq\.marca\}' title='\$\{eq\.marca\}' class='max-w-8 max-h-8 object-contain'></div>`;",
            "html += LogoManager.renderMarcaLogo(eq.marca);"
        )
    ]
    
    # Arquivos HTML para verificar
    html_files = [
        'gerenciar-equipamentos.html',
        'excluir-equipamento.html', 
        'ver-equipamento.html',
        'detalhes-equipamentos-sala.html',
        'visualizar-switch-sala.html'
    ]
    
    fixed_files = []
    
    for filename in html_files:
        if not os.path.exists(filename):
            continue
            
        print(f"Verificando {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Aplicar cada padrão
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # Se o conteúdo mudou, salvar o arquivo
        if content != original_content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_files.append(filename)
            print(f"  ✓ Corrigido {filename}")
        else:
            print(f"  - {filename} já está correto")
    
    print(f"\nResumo: {len(fixed_files)} arquivo(s) corrigido(s)")
    if fixed_files:
        print("Arquivos corrigidos:")
        for f in fixed_files:
            print(f"  - {f}")

if __name__ == "__main__":
    fix_marca_logos() 