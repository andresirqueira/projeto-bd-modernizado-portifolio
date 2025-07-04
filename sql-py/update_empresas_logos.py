import sqlite3

logos = {
    'Empresa 1': 'static/img/logos/empresa1.png',
    'Empresa 2': 'static/img/logos/empresa2.png',
    'WH': 'static/img/logos/wh.png',
}

def main():
    db = '../usuarios_empresas.db' if __name__ == '__main__' else 'usuarios_empresas.db'
    try:
        conn = sqlite3.connect('usuarios_empresas.db')
        c = conn.cursor()
        for nome, logo in logos.items():
            c.execute("UPDATE empresas SET logo=? WHERE nome=?", (logo, nome))
        conn.commit()
        print('Logos atualizados com sucesso!')
    except Exception as e:
        print('Erro ao atualizar logos:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    main() 