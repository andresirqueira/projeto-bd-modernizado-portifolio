import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS equipamento_dados')
cur.execute('DROP TABLE IF EXISTS equipamentos')
cur.execute('DROP TABLE IF EXISTS salas')
cur.execute('DROP TABLE IF EXISTS usuarios')

cur.execute('''
CREATE TABLE salas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT,
    descricao TEXT,
    foto TEXT,
    fotos TEXT,
    andar_id INTEGER
)
''')

cur.execute('''
CREATE TABLE equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    foto TEXT,
    icone TEXT,
    sala_id INTEGER,
    FOREIGN KEY (sala_id) REFERENCES salas(id)
)
''')

cur.execute('''
CREATE TABLE equipamento_dados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER,
    chave TEXT,
    valor TEXT,
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
)
''')

cur.execute('''
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    senha TEXT NOT NULL,
    nivel TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print('Tabelas criadas do zero!')