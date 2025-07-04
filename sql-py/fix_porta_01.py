import sqlite3

def fix_porta_01():
    conn = sqlite3.connect('audio_e_video.db')
    cur = conn.cursor()
    
    try:
        print("Iniciando correção da porta 01 do switch 01...")
        
        # 1. Buscar o ID da porta 01 do switch 01
        cur.execute('''
            SELECT id FROM switch_portas 
            WHERE switch_id = 1 AND numero_porta = 1
        ''')
        porta_result = cur.fetchone()
        
        if not porta_result:
            print("Porta 01 do switch 01 não encontrada!")
            return
        
        porta_id = porta_result[0]
        print(f"Porta ID encontrada: {porta_id}")
        
        # 2. Buscar conexões ativas para esta porta
        cur.execute('''
            SELECT id, equipamento_id FROM conexoes 
            WHERE porta_id = ? AND status = 'ativa'
        ''', (porta_id,))
        conexoes = cur.fetchall()
        
        print(f"Encontradas {len(conexoes)} conexões ativas")
        
        # 3. Marcar conexões como inativas
        for conexao_id, equipamento_id in conexoes:
            cur.execute('''
                UPDATE conexoes SET status = 'inativa' 
                WHERE id = ?
            ''', (conexao_id,))
            print(f"Desconectado equipamento {equipamento_id} da porta {porta_id}")
        
        # 4. Marcar a porta como livre
        cur.execute('''
            UPDATE switch_portas SET status = 'livre' 
            WHERE id = ?
        ''', (porta_id,))
        
        # 5. Commit das alterações
        conn.commit()
        print("✅ Porta 01 do switch 01 foi liberada com sucesso!")
        
        # 6. Verificar o resultado
        cur.execute('''
            SELECT sp.numero_porta, sp.status, e.nome as equipamento_nome
            FROM switch_portas sp
            LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
            LEFT JOIN equipamentos e ON c.equipamento_id = e.id
            WHERE sp.switch_id = 1 AND sp.numero_porta = 1
        ''')
        resultado = cur.fetchone()
        
        if resultado:
            numero_porta, status, equipamento = resultado
            print(f"Status atual: Porta {numero_porta} - {status}")
            if equipamento:
                print(f"Equipamento conectado: {equipamento}")
            else:
                print("Nenhum equipamento conectado")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_porta_01() 