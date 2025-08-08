import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuração do PostgreSQL (Render)
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'usuarios_empresas'),
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
