import sqlite3

# Conecte ao banco de dados (ajuste o caminho se necessário)
conn = sqlite3.connect('audio_e_video.db')
cur = conn.cursor()

# Crie a tabela se não existir
cur.execute("""
CREATE TABLE IF NOT EXISTS equipamento_dados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipamento_id INTEGER,
    chave TEXT,
    valor TEXT,
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
)
""")

conn.commit()
conn.close()

print("Tabela 'equipamento_dados' criada com sucesso!")