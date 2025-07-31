import sqlite3

# Caminho do seu banco de dados (ajuste se necessário)
db_path = r'C:\Users\andre.sirqueira\OneDrive - Convergint\Desktop\projeto-bd-modernizado\empresa_wh.db' # ou o nome do seu arquivo .db

# Lista de andares (adicione/remova conforme necessário)
andares = [
    (0, 'Térreo', 'Andar térreo'),
    (1, '1º Andar', 'Primeiro andar'),
    (2, '2º Andar', 'Segundo andar'),
    (3, '3º Andar', 'Terceiro andar'),
    (4, '4º Andar', 'Quarto andar'),
    (5, '5º Andar', 'Quinto andar'),
    (6, '6º Andar', 'Sexto andar'),
    (7, '7º Andar', 'Sétimo andar'),
    (8, '8º Andar', 'Oitavo andar'),
    (9, '9º Andar', 'Nono andar'),
    (10, '10º Andar', 'Décimo andar'),
]

conn = sqlite3.connect(db_path)
cur = conn.cursor()

for andar in andares:
    cur.execute(
        "INSERT OR IGNORE INTO andares (id, titulo, descricao) VALUES (?, ?, ?)",
        andar
    )

conn.commit()
conn.close()

print("Tabela 'andares' populada com sucesso!")