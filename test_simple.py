import sqlite3

def test_simple():
    conn = sqlite3.connect('empresa_wh.db')
    cur = conn.cursor()
    
    sala_id = 1
    
    # Teste simples: buscar switches que têm equipamentos da sala 1
    cur.execute('''
        SELECT DISTINCT s.id, s.nome
        FROM switches s
        JOIN switch_portas sp ON s.id = sp.switch_id
        LEFT JOIN patch_panel_portas ppp ON sp.switch_id = ppp.switch_id AND sp.numero_porta = ppp.porta_switch
        LEFT JOIN equipamentos e ON ppp.equipamento_id = e.id
        WHERE e.sala_id = ?
    ''', (sala_id,))
    
    switches = cur.fetchall()
    print(f"Switches encontrados: {len(switches)}")
    for switch in switches:
        print(f"Switch ID: {switch[0]}, Nome: {switch[1]}")
        
        # Buscar portas deste switch que têm equipamentos da sala 1
        cur.execute('''
            SELECT DISTINCT sp.numero_porta, e.nome as equipamento
            FROM switch_portas sp
            LEFT JOIN patch_panel_portas ppp ON sp.switch_id = ppp.switch_id AND sp.numero_porta = ppp.porta_switch
            LEFT JOIN equipamentos e ON ppp.equipamento_id = e.id
            WHERE sp.switch_id = ? AND e.sala_id = ?
        ''', (switch[0], sala_id))
        
        portas = cur.fetchall()
        print(f"  Portas encontradas: {len(portas)}")
        for porta in portas:
            print(f"    Porta {porta[0]}: {porta[1]}")
    
    conn.close()

if __name__ == "__main__":
    test_simple() 