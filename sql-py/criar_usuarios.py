import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    nivel TEXT NOT NULL -- admin, tecnico, usuario
)
''')
conn.commit()
conn.close()