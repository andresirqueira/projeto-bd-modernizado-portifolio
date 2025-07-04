import sqlite3

def check_and_fix_porta_01():
    conn = sqlite3.connect('audio_e_video.db')
    cur = conn.cursor()
    
    try:
        print("Verificando status da porta 01 do switch 01...")
        
        # Verificar status atual
        cur.execute('''
            SELECT sp.id, sp.numero_porta, sp.status, sp.descricao,
                   e.nome as equipamento_nome, e.tipo as equipamento_tipo
            FROM switch_portas sp
            LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
            LEFT JOIN equipamentos e ON c.equipamento_id = e.id
            WHERE sp.switch_id = 1 AND sp.numero_porta = 1
        ''')
        resultado = cur.fetchone()
        
        if resultado:
            porta_id, numero_porta, status, descricao, equipamento_nome, equipamento_tipo = resultado
            print(f"Porta ID: {porta_id}")
            print(f"Número da porta: {numero_porta}")
            print(f"Status atual: {status}")
            print(f"Descrição: {descricao}")
            print(f"Equipamento conectado: {equipamento_nome or 'Nenhum'}")
            print(f"Tipo do equipamento: {equipamento_tipo or 'N/A'}")
            
            # Se a porta não está livre, corrigir
            if status != 'livre':
                print(f"\nCorrigindo status de '{status}' para 'livre'...")
                cur.execute('''
                    UPDATE switch_portas SET status = 'livre' 
                    WHERE id = ?
                ''', (porta_id,))
                conn.commit()
                print("✅ Status corrigido para 'livre'!")
            else:
                print("✅ Porta já está com status 'livre'")
                
        else:
            print("❌ Porta 01 do switch 01 não encontrada!")
            
        # Verificar se há conexões inativas que precisam ser limpas
        cur.execute('''
            SELECT COUNT(*) FROM conexoes 
            WHERE porta_id = (SELECT id FROM switch_portas WHERE switch_id = 1 AND numero_porta = 1)
            AND status = 'inativa'
        ''')
        conexoes_inativas = cur.fetchone()[0]
        print(f"\nConexões inativas encontradas: {conexoes_inativas}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_fix_porta_01() 