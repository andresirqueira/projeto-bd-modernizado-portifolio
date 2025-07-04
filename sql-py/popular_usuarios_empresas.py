import sqlite3

DB_FILE = 'usuarios_empresas.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Limpa usuários, vínculos e empresas (mantém empresas já cadastradas)
c.execute('DELETE FROM usuario_empresas')
c.execute('DELETE FROM usuarios')

# Usuários por empresa
usuarios = [
    # username, senha, nome, nivel
    ('admin_wh', 'adminwh123', 'Admin WH', 'admin'),
    ('tecnico_wh', 'tecnicowh123', 'Técnico WH', 'tecnico'),
    ('usuario_wh', 'usuariowh123', 'Usuário WH', 'usuario'),
    ('admin_01', 'admin01123', 'Admin 01', 'admin'),
    ('tecnico_01', 'tecnico01123', 'Técnico 01', 'tecnico'),
    ('usuario_01', 'usuario01123', 'Usuário 01', 'usuario'),
    # Adicione mais conforme necessário
    ('master', 'master123', 'Master Admin', 'admin'),
]

for username, senha, nome, nivel in usuarios:
    c.execute("INSERT INTO usuarios (username, senha, nome, nivel) VALUES (?, ?, ?, ?)", (username, senha, nome, nivel))

# Busca ids
c.execute("SELECT id, username FROM usuarios")
usuarios_ids = {row[1]: row[0] for row in c.fetchall()}
c.execute("SELECT id, nome FROM empresas")
empresas_ids = {row[1]: row[0] for row in c.fetchall()}

# Vínculos
vinculos = [
    # (username, nome_empresa)
    ('admin_wh', 'WH'),
    ('tecnico_wh', 'WH'),
    ('usuario_wh', 'WH'),
    ('admin_01', 'Empresa 1'),
    ('tecnico_01', 'Empresa 1'),
    ('usuario_01', 'Empresa 1'),
    # Usuário master em todas as empresas
]
# Adiciona master em todas as empresas
for empresa_nome in empresas_ids:
    vinculos.append(('master', empresa_nome))

for username, nome_empresa in vinculos:
    usuario_id = usuarios_ids.get(username)
    empresa_id = empresas_ids.get(nome_empresa)
    if usuario_id and empresa_id:
        c.execute("INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (?, ?)", (usuario_id, empresa_id))

conn.commit()
conn.close()
print('Usuários e vínculos populados com sucesso em usuarios_empresas.db!') 