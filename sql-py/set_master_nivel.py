import sqlite3

DB_FILE = 'usuarios_empresas.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Atualiza o campo nivel do usuário master
c.execute("UPDATE usuarios SET nivel = 'master' WHERE username = 'master'")

conn.commit()
conn.close()
print("Campo nivel do usuário 'master' atualizado para 'master'.") 