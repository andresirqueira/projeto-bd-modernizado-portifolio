import sqlite3
import sys
import os

# Uso: python criar_novo_bd_empresa.py "Empresa 05" empresa_05.db
if len(sys.argv) != 3:
    print("Uso: python criar_novo_bd_empresa.py 'Nome da Empresa' arquivo_novo.db")
    sys.exit(1)

NOME_EMPRESA = sys.argv[1]
ARQUIVO_NOVO = sys.argv[2]
ARQUIVO_MODELO = 'empresa_wh.db'
USUARIOS_EMPRESAS_DB = 'usuarios_empresas.db'

if os.path.exists(ARQUIVO_NOVO):
    print(f"Arquivo {ARQUIVO_NOVO} já existe. Saindo para não sobrescrever.")
    sys.exit(1)

# Extrai o DDL do banco modelo
conn_modelo = sqlite3.connect(ARQUIVO_MODELO)
c_modelo = conn_modelo.cursor()
c_modelo.execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index','trigger','view') AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL")
ddls = [row[0] for row in c_modelo.fetchall()]
conn_modelo.close()

# Cria o novo banco e executa o DDL
conn_novo = sqlite3.connect(ARQUIVO_NOVO)
c_novo = conn_novo.cursor()
for ddl in ddls:
    c_novo.execute(ddl)
conn_novo.commit()
conn_novo.close()
print(f"Banco {ARQUIVO_NOVO} criado com a estrutura de {ARQUIVO_MODELO} (sem dados)")

# Adiciona a empresa na tabela empresas
db_empresas = sqlite3.connect(USUARIOS_EMPRESAS_DB)
c_emp = db_empresas.cursor()
c_emp.execute('INSERT INTO empresas (nome, db_file) VALUES (?, ?)', (NOME_EMPRESA, ARQUIVO_NOVO))
db_empresas.commit()
db_empresas.close()
print(f"Empresa '{NOME_EMPRESA}' adicionada ao sistema com o banco '{ARQUIVO_NOVO}'!") 