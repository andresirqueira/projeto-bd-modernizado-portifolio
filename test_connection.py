#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL
"""

import os
import psycopg2

def test_connection():
    """Testa conexão com PostgreSQL"""
    
    # Configurações do PostgreSQL (Render)
    config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'usuarios_empresas'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    print("🔍 Testando conexão PostgreSQL...")
    print(f"Host: {config['host']}")
    print(f"Database: {config['database']}")
    print(f"User: {config['user']}")
    print(f"Port: {config['port']}")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Testar versão
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexão PostgreSQL OK!")
        print(f"📊 Versão: {version[0]}")
        
        # Testar se as tabelas existem
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 Tabelas encontradas: {[table[0] for table in tables]}")
        else:
            print("📋 Nenhuma tabela encontrada (normal para banco novo)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro PostgreSQL: {e}")
        print("\n💡 Para configurar as variáveis de ambiente:")
        print("1. Obtenha as credenciais no dashboard do Render")
        print("2. Configure as variáveis de ambiente:")
        print("   POSTGRES_HOST=dpg-xxxxx-a.oregon-postgres.render.com")
        print("   POSTGRES_DB=usuarios_empresas")
        print("   POSTGRES_USER=usuarios_empresas_user")
        print("   POSTGRES_PASSWORD=sua_senha")
        print("   POSTGRES_PORT=5432")
        return False

if __name__ == "__main__":
    test_connection()
