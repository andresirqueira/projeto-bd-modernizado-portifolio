import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()

# Verifica se a coluna já existe
cur.execute("PRAGMA table_info(equipamentos)")
columns = [row[1] for row in cur.fetchall()]
if 'defeito' not in columns:
    cur.execute("ALTER TABLE equipamentos ADD COLUMN defeito INTEGER DEFAULT 0;")
    print("Coluna 'defeito' adicionada com sucesso!")
else:
    print("Coluna 'defeito' já existe.")

conn.commit()
conn.close() 