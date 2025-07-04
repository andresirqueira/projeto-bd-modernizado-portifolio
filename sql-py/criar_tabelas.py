import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()

# Tabela de andares
cur.execute('''
CREATE TABLE IF NOT EXISTS andares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT
)
''')

# Tabela de salas
cur.execute('''
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
cur.execute('''
CREATE TABLE IF NOT EXISTS equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    foto TEXT,
    icone TEXT,
    led_switch TEXT,
    sala_id INTEGER,
    FOREIGN KEY (sala_id) REFERENCES salas(id)
)
''')

# Tabela de dados dos equipamentos (chave/valor)
cur.execute('''
CREATE TABLE IF NOT EXISTS dados_equipamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER,
    chave TEXT,
    valor TEXT,
    icone TEXT,
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
)
''')

conn.commit()
conn.close()