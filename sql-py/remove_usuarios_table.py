import sqlite3
import os

DB_FILE = 'wh.db'

if not os.path.exists(DB_FILE):
    print(f'Arquivo {DB_FILE} não encontrado!')
    exit(1)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Verifica se a tabela usuarios existe
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
if c.fetchone():
    c.execute('DROP TABLE usuarios')
    print('Tabela usuarios removida de wh.db!')
else:
    print('Tabela usuarios não existe em wh.db.')

conn.commit()
conn.close() 