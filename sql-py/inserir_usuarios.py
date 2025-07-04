import sqlite3

usuarios = [
    ('admin', 'admin123', 'admin'),
    ('tecnico', 'tecnico123', 'tecnico'),
    ('usuario', 'usuario123', 'usuario')
]

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()
for u in usuarios:
    try:
        cur.execute('INSERT INTO usuarios (username, senha, nivel) VALUES (?, ?, ?)', u)
    except sqlite3.IntegrityError:
        pass  # Usuário já existe
conn.commit()
conn.close()