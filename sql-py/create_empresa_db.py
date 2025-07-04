import sqlite3
import sys
import os

# Uso: python create_empresa_db.py empresa1.db
if len(sys.argv) < 2:
    print('Uso: python create_empresa_db.py <nome_do_banco.db>')
    sys.exit(1)

DB_FILE = sys.argv[1]

if os.path.exists(DB_FILE):
    print(f'Atenção: {DB_FILE} já existe! O script só criará tabelas que não existem.')

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Tabela de andares
c.execute('''
CREATE TABLE IF NOT EXISTS andares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT
)
''')

# Tabela de salas
c.execute('''
CREATE TABLE IF NOT EXISTS salas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    tipo TEXT,
    descricao TEXT,
    foto TEXT,
    fotos TEXT,
    andar_id INTEGER,
    FOREIGN KEY (andar_id) REFERENCES andares(id)
)
''')

# Tabela de equipamentos
c.execute('''
CREATE TABLE IF NOT EXISTS equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    tipo TEXT,
    marca TEXT,
    modelo TEXT,
    partnumber TEXT,
    tamanho TEXT,
    firmware TEXT,
    serie TEXT,
    descricao TEXT,
    foto TEXT,
    icone TEXT,
    sala_id INTEGER,
    ip1 TEXT,
    mac1 TEXT,
    ip2 TEXT,
    mac2 TEXT,
    defeito INTEGER DEFAULT 0,
    FOREIGN KEY (sala_id) REFERENCES salas(id)
)
''')

# Tabela de dados dos equipamentos (chave/valor)
c.execute('''
CREATE TABLE IF NOT EXISTS equipamento_dados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER,
    chave TEXT,
    valor TEXT,
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
)
''')

# Tabela de switches
c.execute('''
CREATE TABLE IF NOT EXISTS switches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    marca TEXT,
    modelo TEXT,
    ip TEXT,
    local TEXT,
    observacao TEXT
)
''')

# Tabela de portas dos switches
c.execute('''
CREATE TABLE IF NOT EXISTS switch_portas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    switch_id INTEGER,
    numero_porta INTEGER,
    status TEXT,
    FOREIGN KEY (switch_id) REFERENCES switches(id)
)
''')

# Tabela de conexões
c.execute('''
CREATE TABLE IF NOT EXISTS conexoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    porta_id INTEGER NOT NULL,
    equipamento_id INTEGER NOT NULL,
    data_conexao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'ativa',
    FOREIGN KEY (porta_id) REFERENCES switch_portas (id),
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id)
)
''')

# Tabela de logs de ping
ec = conn.cursor()
ec.execute('''
CREATE TABLE IF NOT EXISTS ping_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER,
    nome_equipamento TEXT,
    ip TEXT,
    resultado TEXT,
    sucesso INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print(f'Estrutura criada em {DB_FILE}!') 