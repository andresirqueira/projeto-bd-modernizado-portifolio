import sqlite3

conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS dados_equipamento')
print("Tabela 'dados_equipamento' removida (se existia).")
conn.commit()
conn.close() 