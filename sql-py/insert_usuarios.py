import sqlite3
import os

# Caminho absoluto para o usuarios.db na raiz do projeto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usuarios.db')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Exemplos de todos os níveis: admin, tecnico e usuario
novos_usuarios = [
    # username, senha, nome, nivel
    ('admin2', 'admin456', 'Administrador 2', 'admin'),
    ('tecnico2', 'tecnico456', 'Técnico 2', 'tecnico'),
    ('usuario2', 'usuario456', 'Usuário 2', 'usuario'),
    ('ana', 'ana123', 'Ana Paula', 'usuario'),
    ('carlos', 'carlos123', 'Carlos Lima', 'tecnico'),
    ('superadmin', 'super123', 'Super Admin', 'admin'),
]

for username, senha, nome, nivel in novos_usuarios:
    c.execute("INSERT OR IGNORE INTO usuarios (username, senha, nome, nivel) VALUES (?, ?, ?, ?)", (username, senha, nome, nivel))

# Novas empresas para exemplo
novas_empresas = [
    # nome, db_file
    ('Empresa 5', 'empresa5.db'),
    ('Empresa 6', 'empresa6.db'),
]

for nome, db_file in novas_empresas:
    c.execute("INSERT OR IGNORE INTO empresas (nome, db_file) VALUES (?, ?)", (nome, db_file))

# Vincular usuários a empresas
c.execute("SELECT id, username FROM usuarios")
usuarios = {row[1]: row[0] for row in c.fetchall()}
c.execute("SELECT id, nome FROM empresas")
empresas = {row[1]: row[0] for row in c.fetchall()}

vinculos = [
    # (username, nome_empresa)
    ('admin2', 'Empresa 1'),
    ('tecnico2', 'Empresa 2'),
    ('usuario2', 'Empresa 3'),
    ('ana', 'Empresa 4'),
    ('carlos', 'Empresa 5'),
    ('superadmin', 'Empresa 6'),
    ('superadmin', 'Empresa 1'), # superadmin em mais de uma empresa
]

for username, nome_empresa in vinculos:
    usuario_id = usuarios.get(username)
    empresa_id = empresas.get(nome_empresa)
    if usuario_id and empresa_id:
        c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (?, ?)", (usuario_id, empresa_id))

conn.commit()
conn.close()

print('Novos usuários, empresas e vínculos inseridos com sucesso!') 