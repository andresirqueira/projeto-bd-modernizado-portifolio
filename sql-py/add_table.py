import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()


cur.execute('DROP TABLE IF EXISTS equipamentos')
cur.execute('''
CREATE TABLE equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
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
    FOREIGN KEY (sala_id) REFERENCES salas(id)
)
''')

conn.commit()

cur.execute('SELECT * FROM equipamentos')
rows = cur.fetchall()

# Para mostrar os nomes das colunas:
col_names = [description[0] for description in cur.description]
print(col_names)

# Para mostrar os dados:
for row in rows:
    print(row)

conn.close()
print('Tabela equipamentos criada com os campos ip1, mac1, ip2, mac2, partnumber e tamanho!')