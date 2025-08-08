#!/usr/bin/env python3
"""
Script para testar a migração PostgreSQL
"""

import os
import psycopg2
import sqlite3

def test_postgres_connection():
    """Testa conexão com PostgreSQL"""
    try:
        # Configurações do PostgreSQL
        config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'portfolio_db'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        
        print("🔍 Testando conexão PostgreSQL...")
        print(f"Host: {config['host']}")
        print(f"Database: {config['database']}")
        print(f"User: {config['user']}")
        print(f"Port: {config['port']}")
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Testar consultas
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM empresas")
        empresas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM usuario_empresas")
        vinculos_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ PostgreSQL OK!")
        print(f"📊 Usuários: {usuarios_count}")
        print(f"📊 Empresas: {empresas_count}")
        print(f"📊 Vínculos: {vinculos_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro PostgreSQL: {e}")
        return False

def test_sqlite_connection():
    """Testa conexão com SQLite"""
    try:
        print("\n🔍 Testando conexão SQLite...")
        
        conn = sqlite3.connect('usuarios_empresas.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM empresas")
        empresas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM usuario_empresas")
        vinculos_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ SQLite OK!")
        print(f"📊 Usuários: {usuarios_count}")
        print(f"📊 Empresas: {empresas_count}")
        print(f"📊 Vínculos: {vinculos_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro SQLite: {e}")
        return False

def compare_data():
    """Compara dados entre SQLite e PostgreSQL"""
    try:
        print("\n🔍 Comparando dados...")
        
        # SQLite
        sqlite_conn = sqlite3.connect('usuarios_empresas.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # PostgreSQL
        config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'portfolio_db'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        postgres_conn = psycopg2.connect(**config)
        postgres_cursor = postgres_conn.cursor()
        
        # Comparar usuários
        sqlite_cursor.execute("SELECT COUNT(*) FROM usuarios")
        sqlite_users = sqlite_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM usuarios")
        postgres_users = postgres_cursor.fetchone()[0]
        
        # Comparar empresas
        sqlite_cursor.execute("SELECT COUNT(*) FROM empresas")
        sqlite_companies = sqlite_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM empresas")
        postgres_companies = postgres_cursor.fetchone()[0]
        
        # Comparar vínculos
        sqlite_cursor.execute("SELECT COUNT(*) FROM usuario_empresas")
        sqlite_links = sqlite_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM usuario_empresas")
        postgres_links = postgres_cursor.fetchone()[0]
        
        # Fechar conexões
        sqlite_conn.close()
        postgres_conn.close()
        
        # Resultado
        print(f"📊 Comparação:")
        print(f"  Usuários: SQLite={sqlite_users} | PostgreSQL={postgres_users}")
        print(f"  Empresas: SQLite={sqlite_companies} | PostgreSQL={postgres_companies}")
        print(f"  Vínculos: SQLite={sqlite_links} | PostgreSQL={postgres_links}")
        
        if (sqlite_users == postgres_users and 
            sqlite_companies == postgres_companies and 
            sqlite_links == postgres_links):
            print("✅ Migração 100% bem-sucedida!")
            return True
        else:
            print("⚠️  Alguns dados podem não ter sido migrados corretamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")
        return False

def main():
    """Função principal"""
    print("🧪 Testando Migração PostgreSQL")
    print("=" * 40)
    
    # Testar conexões
    sqlite_ok = test_sqlite_connection()
    postgres_ok = test_postgres_connection()
    
    if not sqlite_ok or not postgres_ok:
        print("\n❌ Falha nos testes de conexão")
        return False
    
    # Comparar dados
    data_ok = compare_data()
    
    if data_ok:
        print("\n🎉 Todos os testes passaram!")
        print("✅ Migração está pronta para produção")
    else:
        print("\n⚠️  Alguns problemas encontrados")
        print("🔧 Verifique os logs e execute novamente")
    
    return data_ok

if __name__ == "__main__":
    main()
