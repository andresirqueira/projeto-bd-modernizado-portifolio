import sqlite3

DB_FILE = 'usuarios_empresas.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Verifica se o campo já existe
c.execute("PRAGMA table_info(usuario_empresas)")
colunas = [row[1] for row in c.fetchall()]
if 'is_master' not in colunas:
    c.execute('ALTER TABLE usuario_empresas ADD COLUMN is_master INTEGER DEFAULT 0')
    print("Campo 'is_master' adicionado à tabela usuario_empresas.")
else:
    print("Campo 'is_master' já existe na tabela usuario_empresas.")

conn.commit()
conn.close() 