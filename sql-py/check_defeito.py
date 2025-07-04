import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()
cur.execute("SELECT id, nome, defeito, sala_id FROM equipamentos WHERE nome LIKE '%teste%'")
rows = cur.fetchall()
for row in rows:
    print(f"id={row[0]}, nome={row[1]}, defeito={row[2]}, sala_id={row[3]}")
conn.close() 