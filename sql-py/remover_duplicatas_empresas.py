import sqlite3

DB_FILE = 'usuarios_empresas.db'
DB_FILE_EMPRESA = 'empresa_04.db'  # Altere para o db_file desejado

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Remove duplicatas, mantendo o menor id para o db_file
c.execute('''
DELETE FROM empresas
WHERE db_file = ?
  AND id NOT IN (
    SELECT MIN(id) FROM empresas WHERE db_file = ?
  )
''', (DB_FILE_EMPRESA, DB_FILE_EMPRESA))

conn.commit()
conn.close()
print(f"Duplicatas de db_file '{DB_FILE_EMPRESA}' removidas da tabela empresas.") 