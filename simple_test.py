import psycopg2

print("Teste simples de conexao")

try:
    conn = psycopg2.connect(
        host="dpg-d2b4i12dbo4c73ag4cj0-a",
        database="usuarios_empresas",
        user="usuarios_empresas",
        password="GvDFhGMH3wfrUfgPVcmW8NBUEbqPHmmA",
        port="5432"
    )
    print("Conexao OK!")
    conn.close()
except Exception as e:
    print(f"Erro: {e}")
