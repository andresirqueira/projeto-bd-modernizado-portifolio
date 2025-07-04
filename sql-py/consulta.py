import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()

cur.execute("SELECT id, nome, sala_id FROM equipamentos")
rows = cur.fetchall()

# Para mostrar os nomes das colunas:
col_names = [description[0] for description in cur.description]
print(col_names)

# Para mostrar os dados:
for row in rows:
    print(row)

conn.close()