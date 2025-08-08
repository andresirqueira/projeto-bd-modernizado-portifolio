#!/usr/bin/env python3
"""
Script de Migração: SQLite para PostgreSQL
Migra o banco usuarios_empresas.db para PostgreSQL no Render
"""

import sqlite3
import psycopg2
import os
from datetime import datetime
import sys

# Configurações do PostgreSQL (Render)
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'portfolio_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

# Arquivo SQLite original
SQLITE_DB = 'usuarios_empresas.db'

def test_sqlite_connection():
    """Testa conexão com SQLite"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Conexão SQLite OK. Tabelas encontradas: {[table[0] for table in tables]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com SQLite: {e}")
        return False

def test_postgres_connection():
    """Testa conexão com PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexão PostgreSQL OK. Versão: {version[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com PostgreSQL: {e}")
        print("Verifique as variáveis de ambiente:")
        print(f"  POSTGRES_HOST: {POSTGRES_CONFIG['host']}")
        print(f"  POSTGRES_DB: {POSTGRES_CONFIG['database']}")
        print(f"  POSTGRES_USER: {POSTGRES_CONFIG['user']}")
        print(f"  POSTGRES_PORT: {POSTGRES_CONFIG['port']}")
        return False

def create_postgres_tables():
    """Cria as tabelas no PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Criar tabela usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                senha VARCHAR(255) NOT NULL,
                nivel VARCHAR(50) NOT NULL DEFAULT 'usuario'
            );
        """)
        
        # Criar tabela empresas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                db_file VARCHAR(255)
            );
        """)
        
        # Criar tabela usuario_empresas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuario_empresas (
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                PRIMARY KEY (usuario_id, empresa_id)
            );
        """)
        
        conn.commit()
        print("✅ Tabelas criadas com sucesso no PostgreSQL")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def migrate_data():
    """Migra os dados do SQLite para PostgreSQL"""
    try:
        # Conectar aos dois bancos
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Migrar usuarios
        print("🔄 Migrando usuários...")
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
        print("🔄 Migrando empresas...")
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
        
        # Migrar vinculos usuario_empresas
        print("🔄 Migrando vínculos usuário-empresa...")
        sqlite_cursor.execute("SELECT usuario_id, empresa_id FROM usuario_empresas")
        vinculos = sqlite_cursor.fetchall()
        
        for vinculo in vinculos:
            postgres_cursor.execute("""
                INSERT INTO usuario_empresas (usuario_id, empresa_id) 
                VALUES (%s, %s)
                ON CONFLICT (usuario_id, empresa_id) DO NOTHING
            """, vinculo)
        
        print(f"✅ {len(vinculos)} vínculos migrados")
        
        # Commit das mudanças
        postgres_conn.commit()
        
        # Fechar conexões
        sqlite_conn.close()
        postgres_conn.close()
        
        print("✅ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False

def verify_migration():
    """Verifica se a migração foi bem-sucedida"""
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Verificar usuários
        sqlite_cursor.execute("SELECT COUNT(*) FROM usuarios")
        sqlite_users = sqlite_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM usuarios")
        postgres_users = postgres_cursor.fetchone()[0]
        
        print(f"📊 Usuários: SQLite={sqlite_users}, PostgreSQL={postgres_users}")
        
        # Verificar empresas
        sqlite_cursor.execute("SELECT COUNT(*) FROM empresas")
        sqlite_companies = sqlite_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM empresas")
        postgres_companies = postgres_cursor.fetchone()[0]
        
        print(f"📊 Empresas: SQLite={sqlite_companies}, PostgreSQL={postgres_companies}")
        
        # Verificar vínculos
        sqlite_cursor.execute("SELECT COUNT(*) FROM usuario_empresas")
        sqlite_links = sqlite_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM usuario_empresas")
        postgres_links = postgres_cursor.fetchone()[0]
        
        print(f"📊 Vínculos: SQLite={sqlite_links}, PostgreSQL={postgres_links}")
        
        sqlite_conn.close()
        postgres_conn.close()
        
        if (sqlite_users == postgres_users and 
            sqlite_companies == postgres_companies and 
            sqlite_links == postgres_links):
            print("✅ Verificação: Todos os dados foram migrados corretamente!")
            return True
        else:
            print("⚠️  Verificação: Alguns dados podem não ter sido migrados corretamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def create_migration_log():
    """Cria um log da migração"""
    log_entry = f"""
=== LOG DE MIGRAÇÃO ===
Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Arquivo SQLite: {SQLITE_DB}
Configuração PostgreSQL:
  Host: {POSTGRES_CONFIG['host']}
  Database: {POSTGRES_CONFIG['database']}
  User: {POSTGRES_CONFIG['user']}
  Port: {POSTGRES_CONFIG['port']}
========================
"""
    
    with open('migration_log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print("📝 Log de migração salvo em 'migration_log.txt'")

def main():
    """Função principal"""
    print("🚀 Iniciando migração SQLite → PostgreSQL")
    print("=" * 50)
    
    # Verificar se o arquivo SQLite existe
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Arquivo {SQLITE_DB} não encontrado!")
        return False
    
    # Testar conexões
    if not test_sqlite_connection():
        return False
    
    if not test_postgres_connection():
        return False
    
    # Criar tabelas
    if not create_postgres_tables():
        return False
    
    # Migrar dados
    if not migrate_data():
        return False
    
    # Verificar migração
    if not verify_migration():
        return False
    
    # Criar log
    create_migration_log()
    
    print("\n🎉 Migração concluída com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Atualize as variáveis de ambiente no Render")
    print("2. Modifique o código para usar PostgreSQL")
    print("3. Teste a aplicação no ambiente de produção")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
