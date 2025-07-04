import sqlite3

# Cria o banco de dados usuarios.db
conn = sqlite3.connect('../usuarios.db')
c = conn.cursor()

# Cria tabela de usuários
c.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    nome TEXT,
    nivel TEXT
)
''')

# Cria tabela de empresas
c.execute('''
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    db_file TEXT NOT NULL
)
''')

# Cria tabela de relacionamento usuário-empresa
c.execute('''
CREATE TABLE IF NOT EXISTS usuario_empresas (
    usuario_id INTEGER,
    empresa_id INTEGER,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY(empresa_id) REFERENCES empresas(id)
)
''')

# Insere dados de exemplo
c.execute("INSERT OR IGNORE INTO usuarios (username, senha, nome, nivel) VALUES ('admin', 'admin123', 'Administrador', 'admin')")
c.execute("INSERT OR IGNORE INTO usuarios (username, senha, nome, nivel) VALUES ('tecnico', 'tecnico123', 'Técnico', 'tecnico')")
c.execute("INSERT OR IGNORE INTO usuarios (username, senha, nome, nivel) VALUES ('user', 'user123', 'Usuário', 'usuario')")

c.execute("INSERT OR IGNORE INTO empresas (nome, db_file) VALUES ('Empresa 1', 'empresa1.db')")
c.execute("INSERT OR IGNORE INTO empresas (nome, db_file) VALUES ('Empresa 2', 'empresa2.db')")

# Relaciona admin com as duas empresas, tecnico só com empresa 1, user só com empresa 2
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (1, 1)")
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (1, 2)")
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (2, 1)")
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (3, 2)")

conn.commit()
conn.close()

print('usuarios.db criado com sucesso!') 