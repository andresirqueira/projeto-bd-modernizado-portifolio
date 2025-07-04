import sqlite3

DB_FILE = 'usuarios_empresas.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Descobre o id do usuário master
c.execute("SELECT id FROM usuarios WHERE username = 'master'")
row = c.fetchone()
if row:
    master_id = row[0]
    c.execute('DELETE FROM usuario_empresas WHERE usuario_id = ?', (master_id,))
    print(f"Todos os vínculos do usuário master (id={master_id}) foram removidos.")
else:
    print("Usuário master não encontrado.")

conn.commit()
conn.close() 