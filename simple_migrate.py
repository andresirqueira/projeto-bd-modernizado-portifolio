#!/usr/bin/env python3
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
