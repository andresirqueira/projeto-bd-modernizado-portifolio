import sqlite3

DB_FILE = 'usuarios_empresas.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# 1. Renomeia a tabela antiga
c.execute('ALTER TABLE usuario_empresas RENAME TO usuario_empresas_old')

# 2. Cria a nova tabela sem o campo is_master
c.execute('''
CREATE TABLE usuario_empresas (
    usuario_id INTEGER,
    empresa_id INTEGER,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY(empresa_id) REFERENCES empresas(id)
)
''')

# 3. Copia os dados antigos (sem o campo is_master)
c.execute('''
INSERT INTO usuario_empresas (usuario_id, empresa_id)
SELECT usuario_id, empresa_id FROM usuario_empresas_old
''')

# 4. Remove a tabela antiga
c.execute('DROP TABLE usuario_empresas_old')

conn.commit()
conn.close()
print("Campo 'is_master' removido da tabela usuario_empresas.") 