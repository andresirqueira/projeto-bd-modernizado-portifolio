import sqlite3

conn = sqlite3.connect('usuarios.db')
c = conn.cursor()

# Corrigir os nomes dos arquivos para o padrão correto
c.execute("UPDATE empresas SET db_file = 'empresa_05.db' WHERE nome = 'Empresa 5'")
c.execute("UPDATE empresas SET db_file = 'empresa_06.db' WHERE nome = 'Empresa 6'")

conn.commit()
conn.close()
print('db_file das empresas 5 e 6 corrigidos para o padrão empresa_05.db e empresa_06.db!') 