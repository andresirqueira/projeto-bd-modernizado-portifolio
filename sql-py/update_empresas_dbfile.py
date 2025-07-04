import sqlite3
import os

DB_FILE = 'usuarios.db'

# Mapeamento antigo -> novo
atualizacoes = [
    # (nome_empresa, novo_db_file)
    ('WH', 'empresa_wh.db'),
    ('Empresa 1', 'empresa_01.db'),
    ('Empresa 2', 'empresa_02.db'),
    # Adicione mais se necessário
]

if not os.path.exists(DB_FILE):
    print(f'Arquivo {DB_FILE} não encontrado!')
    exit(1)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

for nome_empresa, novo_db_file in atualizacoes:
    c.execute("UPDATE empresas SET db_file=? WHERE nome=?", (novo_db_file, nome_empresa))
    print(f"Empresa '{nome_empresa}' atualizada para db_file='{novo_db_file}'")

# Adiciona a empresa WH se não existir
c.execute("INSERT OR IGNORE INTO empresas (nome, db_file) VALUES (?, ?)", ('WH', 'empresa_wh.db'))

conn.commit()
conn.close()
print('Atualização concluída!') 