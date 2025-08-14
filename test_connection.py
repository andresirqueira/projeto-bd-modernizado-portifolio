import psycopg2
import os

# Configuracoes do PostgreSQL
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT')
}

print("Testando conexao PostgreSQL...")
print(f"Host: {POSTGRES_CONFIG['host']}")
print(f"Database: {POSTGRES_CONFIG['database']}")
print(f"User: {POSTGRES_CONFIG['user']}")

try:
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    print("Conexao bem sucedida!")
    conn.close()
except Exception as e:
    print(f"Erro na conexao: {e}")
