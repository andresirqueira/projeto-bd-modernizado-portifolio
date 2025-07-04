import sqlite3

conn = sqlite3.connect('usuarios.db')
c = conn.cursor()

# Descobre o id do usuário 'admin'
c.execute("SELECT id FROM usuarios WHERE username = ?", ('admin',))
user_row = c.fetchone()
if not user_row:
    print("Usuário 'admin' não encontrado!")
    conn.close()
    exit(1)
user_id = user_row[0]

# Descobre o id da empresa WH
c.execute("SELECT id FROM empresas WHERE nome = ?", ('WH',))
empresa_row = c.fetchone()
if not empresa_row:
    print("Empresa 'WH' não encontrada!")
    conn.close()
    exit(1)
empresa_id = empresa_row[0]

# Vincula o usuário à empresa WH
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (?, ?)", (user_id, empresa_id))

conn.commit()
conn.close()
print(f"Usuário 'admin' vinculado à empresa WH com sucesso!") 