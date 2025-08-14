#!/usr/bin/env python3
"""
Script para atualizar server.py para PostgreSQL
"""

import re

def update_server_py():
    """Atualiza server.py para usar PostgreSQL"""
    
    print("🔧 Atualizando server.py para PostgreSQL...")
    
    # Ler o arquivo server.py
    with open('server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Adicionar imports necessários
    if 'import psycopg2' not in content:
        content = content.replace(
            'import os\nimport sqlite3\nimport json',
            'import os\nimport sqlite3\nimport json\nimport psycopg2\nfrom psycopg2.extras import RealDictCursor'
        )
    
    # 2. Adicionar configuração PostgreSQL
    postgres_config = '''
# Configuração PostgreSQL
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'portfolio_unified'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def get_postgres_connection():
    """Retorna uma conexão com PostgreSQL"""
    return psycopg2.connect(**POSTGRES_CONFIG)

def get_postgres_dict_connection():
    """Retorna uma conexão com PostgreSQL usando RealDictCursor"""
    config = POSTGRES_CONFIG.copy()
    config['cursor_factory'] = RealDictCursor
    return psycopg2.connect(**config)
'''
    
    # Inserir configuração após imports
    if 'POSTGRES_CONFIG' not in content:
        content = content.replace(
            'import os\nimport sqlite3\nimport json\nimport psycopg2\nfrom psycopg2.extras import RealDictCursor',
            'import os\nimport sqlite3\nimport json\nimport psycopg2\nfrom psycopg2.extras import RealDictCursor' + postgres_config
        )
    
    # 3. Substituir conexões SQLite por PostgreSQL
    content = content.replace(
        "conn = sqlite3.connect('usuarios_empresas.db')",
        "conn = get_postgres_connection()"
    )
    
    content = content.replace(
        "conn = sqlite3.connect('empresa_wh.db')",
        "conn = get_postgres_connection()"
    )
    
    content = content.replace(
        "conn = sqlite3.connect(session['db'])",
        "conn = get_postgres_connection()"
    )
    
    # 4. Substituir funções SQLite por PostgreSQL
    content = content.replace('datetime(\'now\')', 'CURRENT_TIMESTAMP')
    content = content.replace('date(\'now\')', 'CURRENT_DATE')
    
    # 5. Substituir placeholders SQLite (? -> %s)
    # Esta é uma substituição mais cuidadosa
    content = re.sub(r'\?', '%s', content)
    
    # Escrever o arquivo atualizado
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ server.py atualizado para PostgreSQL")

def main():
    """Função principal"""
    print("🔧 Atualizando Server.py")
    print("=" * 30)
    
    # Atualizar server.py
    update_server_py()
    
    print("\n✅ Atualização concluída!")
    print("\n📋 Próximos passos:")
    print("1. Configure as variáveis no Render")
    print("2. Faça deploy da aplicação")
    print("3. Acesse com admin/admin123")

if __name__ == "__main__":
    main()
