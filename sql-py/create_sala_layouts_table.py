import sqlite3
import sys

if len(sys.argv) < 2:
    print('Uso: python create_sala_layouts_table.py <banco_empresa.db>')
    sys.exit(1)

DB_FILE = sys.argv[1]

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS sala_layouts (
    sala_id INTEGER PRIMARY KEY,
    layout_json TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()
print(f'Tabela sala_layouts criada (ou já existia) em {DB_FILE}!') 