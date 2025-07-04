import sqlite3

conn = sqlite3.connect('usuarios.db')
c = conn.cursor()

# Adiciona a empresa WH se não existir
db_file = 'empresa_wh.db'
nome = 'WH'
c.execute("INSERT OR IGNORE INTO empresas (nome, db_file) VALUES (?, ?)", (nome, db_file))

conn.commit()
conn.close()
print('Empresa WH adicionada com sucesso!') 