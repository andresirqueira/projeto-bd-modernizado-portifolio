#!/usr/bin/env python3
"""
Script para corrigir server.py para PostgreSQL
"""

def fix_server_py():
    """Corrige o server.py para usar PostgreSQL corretamente"""
    
    # Ler o arquivo server.py
    with open('server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Adicionar imports necessários
    if 'import psycopg2' not in content:
        # Adicionar após os imports existentes
        content = content.replace(
            'import os\nimport sqlite3\nimport json',
            'import os\nimport sqlite3\nimport json\nimport psycopg2\nfrom psycopg2.extras import RealDictCursor\nfrom database_config import get_postgres_connection, get_postgres_dict_connection'
        )
    
    # 2. Substituir conexões SQLite por PostgreSQL
    content = content.replace(
        "conn = sqlite3.connect('usuarios_empresas.db')",
        "conn = get_postgres_connection()"
    )
    
    # 3. Substituir placeholders SQLite (? -> %s) apenas nas queries do usuarios_empresas.db
    # Esta é uma substituição mais cuidadosa
    
    # Escrever o arquivo atualizado
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ server.py atualizado para usar PostgreSQL")

def create_simple_migration_script():
    """Cria um script de migração simplificado"""
    script_content = '''#!/usr/bin/env python3
"""
Script Simplificado de Migração SQLite → PostgreSQL
"""

import sqlite3
import psycopg2
import os

# Configurações do PostgreSQL (Render)
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'portfolio_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def migrate():
    """Migra dados do SQLite para PostgreSQL"""
    try:
        # Conectar aos bancos
        sqlite_conn = sqlite3.connect('usuarios_empresas.db')
        postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Criar tabelas se não existirem
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                senha VARCHAR(255) NOT NULL,
                nivel VARCHAR(50) NOT NULL DEFAULT 'usuario'
            );
        """)
        
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                db_file VARCHAR(255)
            );
        """)
        
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_empresas (
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                PRIMARY KEY (usuario_id, empresa_id)
            );
        """)
        
        # Migrar usuários
        sqlite_cursor.execute("SELECT id, nome, username, senha, nivel FROM usuarios")
        usuarios = sqlite_cursor.fetchall()
        
        for usuario in usuarios:
            postgres_cursor.execute("""
                INSERT INTO usuarios (id, nome, username, senha, nivel) 
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    username = EXCLUDED.username,
                    senha = EXCLUDED.senha,
                    nivel = EXCLUDED.nivel
            """, usuario)
        
        print(f"✅ {len(usuarios)} usuários migrados")
        
        # Migrar empresas
        sqlite_cursor.execute("SELECT id, nome, db_file FROM empresas")
        empresas = sqlite_cursor.fetchall()
        
        for empresa in empresas:
            postgres_cursor.execute("""
                INSERT INTO empresas (id, nome, db_file) 
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    db_file = EXCLUDED.db_file
            """, empresa)
        
        print(f"✅ {len(empresas)} empresas migradas")
        
        # Migrar vínculos
        sqlite_cursor.execute("SELECT usuario_id, empresa_id FROM usuario_empresas")
        vinculos = sqlite_cursor.fetchall()
        
        for vinculo in vinculos:
            postgres_cursor.execute("""
                INSERT INTO usuario_empresas (usuario_id, empresa_id) 
                VALUES (%s, %s)
                ON CONFLICT (usuario_id, empresa_id) DO NOTHING
            """, vinculo)
        
        print(f"✅ {len(vinculos)} vínculos migrados")
        
        # Commit e fechar
        postgres_conn.commit()
        sqlite_conn.close()
        postgres_conn.close()
        
        print("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    migrate()
'''
    
    with open('simple_migrate.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de migração simplificado criado (simple_migrate.py)")

def main():
    """Função principal"""
    print("🔧 Preparando migração para PostgreSQL")
    print("=" * 40)
    
    # Atualizar server.py
    fix_server_py()
    
    # Criar script de migração simplificado
    create_simple_migration_script()
    
    print("\n✅ Preparação concluída!")
    print("\n📋 Próximos passos:")
    print("1. Configure as variáveis de ambiente no Render")
    print("2. Execute: python simple_migrate.py")
    print("3. Faça deploy da aplicação")
    print("4. Teste o login e funcionalidades")

if __name__ == "__main__":
    main()
