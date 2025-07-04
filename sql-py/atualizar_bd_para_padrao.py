import sqlite3
import sys

# Uso: python atualizar_bd_para_padrao.py banco_alvo.db
if len(sys.argv) != 2:
    print("Uso: python atualizar_bd_para_padrao.py banco_alvo.db")
    sys.exit(1)

ARQUIVO_PADRAO = 'empresa_wh.db'
ARQUIVO_ALVO = sys.argv[1]

conn_padrao = sqlite3.connect(ARQUIVO_PADRAO)
conn_alvo = sqlite3.connect(ARQUIVO_ALVO)
c_padrao = conn_padrao.cursor()
c_alvo = conn_alvo.cursor()

# Função para obter o esquema de uma tabela
def get_table_schema(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1]: row[2] for row in cursor.fetchall()}

# 1. Adicionar tabelas que não existem
c_padrao.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
tabelas_padrao = {row[0]: row[1] for row in c_padrao.fetchall()}
c_alvo.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas_alvo = set(row[0] for row in c_alvo.fetchall())

for tabela, sql in tabelas_padrao.items():
    if tabela not in tabelas_alvo:
        print(f"Criando tabela {tabela}...")
        c_alvo.execute(sql)

# 2. Adicionar colunas que não existem
for tabela in tabelas_padrao:
    if tabela in tabelas_alvo:
        schema_padrao = get_table_schema(c_padrao, tabela)
        schema_alvo = get_table_schema(c_alvo, tabela)
        for coluna, tipo in schema_padrao.items():
            if coluna not in schema_alvo:
                print(f"Adicionando coluna {coluna} ({tipo}) na tabela {tabela}...")
                c_alvo.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")

conn_alvo.commit()
conn_padrao.close()
conn_alvo.close()
print(f"Banco {ARQUIVO_ALVO} atualizado para o padrão de {ARQUIVO_PADRAO}!") 