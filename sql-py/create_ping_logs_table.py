import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()
cur.execute('''
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
print('Tabela ping_logs criada (ou já existia).') 