import sqlite3
import os

# Caminho absoluto para o usuarios.db na raiz do projeto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usuarios.db')

conn = sqlite3.connect(DB_PATH)
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

# Insere dados de exemplo (apenas se não existirem)
c.execute("INSERT OR IGNORE INTO usuarios (id, username, senha, nome, nivel) VALUES (1, 'admin', 'admin123', 'Administrador', 'admin')")
c.execute("INSERT OR IGNORE INTO usuarios (id, username, senha, nome, nivel) VALUES (2, 'tecnico', 'tecnico123', 'Técnico', 'tecnico')")
c.execute("INSERT OR IGNORE INTO usuarios (id, username, senha, nome, nivel) VALUES (3, 'user', 'user123', 'Usuário', 'usuario')")

c.execute("INSERT OR IGNORE INTO empresas (id, nome, db_file) VALUES (1, 'Empresa 1', 'empresa1.db')")
c.execute("INSERT OR IGNORE INTO empresas (id, nome, db_file) VALUES (2, 'Empresa 2', 'empresa2.db')")

# Relaciona admin com as duas empresas, tecnico só com empresa 1, user só com empresa 2
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (1, 1)")
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (1, 2)")
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (2, 1)")
c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (3, 2)")

conn.commit()
conn.close()

print('Tabelas criadas e dados de exemplo inseridos em usuarios.db!') 