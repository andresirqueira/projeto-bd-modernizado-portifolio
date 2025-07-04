import sqlite3

DB_FILE = 'usuarios_empresas.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Verifica se o campo já existe
c.execute("PRAGMA table_info(usuarios)")
colunas = [row[1] for row in c.fetchall()]
if 'nome' not in colunas:
    c.execute('ALTER TABLE usuarios ADD COLUMN nome TEXT')
    print("Campo 'nome' adicionado à tabela usuarios.")
else:
    print("Campo 'nome' já existe na tabela usuarios.")

conn.commit()
conn.close() 