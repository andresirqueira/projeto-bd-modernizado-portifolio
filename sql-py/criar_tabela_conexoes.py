import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()
cur.execute('''
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
conn.commit()
conn.close()
print("Tabela conexoes criada com sucesso!") 