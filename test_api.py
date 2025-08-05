import sqlite3

def test_sala_01_switches():
    conn = sqlite3.connect('empresa_wh.db')
    cur = conn.cursor()
    
    sala_id = 1  # Sala 01
    
    print(f"Testando API para Sala ID: {sala_id}")
    
    # Buscar switches que têm conexão com equipamentos da sala específica
    cur.execute('''
        SELECT DISTINCT s.id as switch_id, s.nome as switch_nome, s.marca as switch_marca, s.modelo as switch_modelo
        FROM switches s
        JOIN switch_portas sp ON s.id = sp.switch_id
        LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
        LEFT JOIN equipamentos e ON c.equipamento_id = e.id
        LEFT JOIN patch_panel_portas ppp ON sp.switch_id = ppp.switch_id AND sp.numero_porta = ppp.porta_switch
        LEFT JOIN equipamentos e2 ON ppp.equipamento_id = e2.id
        WHERE (e.sala_id = ? OR e2.sala_id = ?)
        ORDER BY s.id
    ''', (sala_id, sala_id))
    
    switches_rows = cur.fetchall()
    print(f"Switches encontrados: {len(switches_rows)}")
    
    for switch_id, switch_nome, switch_marca, switch_modelo in switches_rows:
        print(f"\nSwitch: {switch_nome}")
        
        # Buscar apenas as portas do switch que têm conexão com equipamentos da sala
        cur.execute('''
            SELECT DISTINCT sp.id, sp.numero_porta, sp.descricao
            FROM switch_portas sp
            LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
            LEFT JOIN equipamentos e ON c.equipamento_id = e.id
            LEFT JOIN patch_panel_portas ppp ON sp.switch_id = ppp.switch_id AND sp.numero_porta = ppp.porta_switch
            LEFT JOIN equipamentos e2 ON ppp.equipamento_id = e2.id
            WHERE sp.switch_id = ? AND (e.sala_id = ? OR e2.sala_id = ?)
            ORDER BY sp.numero_porta
        ''', (switch_id, sala_id, sala_id))
        
        portas_rows = cur.fetchall()
        print(f"Portas encontradas: {len(portas_rows)}")
        
        for porta_row in portas_rows:
            porta_id, numero_porta, descricao = porta_row
            print(f"  Porta {numero_porta}:")
            
            # Verificar conexão direta
            cur.execute('''
                SELECT e.id, e.nome, e.tipo, e.marca, e.foto, s.nome as sala_nome
                FROM conexoes c
                JOIN equipamentos e ON c.equipamento_id = e.id
                LEFT JOIN salas s ON e.sala_id = s.id
                WHERE c.porta_id = ? AND c.status = 'ativa' AND e.sala_id = ?
            ''', (porta_id, sala_id))
            
            equipamento_row = cur.fetchone()
            if equipamento_row:
                print(f"    Conexão direta: {equipamento_row[1]} ({equipamento_row[2]})")
            else:
                # Verificar patch panel
                cur.execute('''
                    SELECT pp.nome, ppp.numero_porta, ppp.equipamento_id
                    FROM patch_panel_portas ppp
                    JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
                    LEFT JOIN equipamentos e ON ppp.equipamento_id = e.id
                    WHERE ppp.switch_id = ? AND ppp.porta_switch = ?
                ''', (switch_id, numero_porta))
                
                patch_panel_row = cur.fetchone()
                if patch_panel_row:
                    patch_panel_nome, porta_patch_panel, equipamento_id = patch_panel_row
                    print(f"    Patch Panel: {patch_panel_nome} porta {porta_patch_panel}")
                    
                    if equipamento_id:
                        cur.execute('''
                            SELECT e.nome, e.tipo, e.marca, s.nome as sala_nome
                            FROM equipamentos e
                            LEFT JOIN salas s ON e.sala_id = s.id
                            WHERE e.id = ? AND e.sala_id = ?
                        ''', (equipamento_id, sala_id))
                        
                        equip_row = cur.fetchone()
                        if equip_row:
                            print(f"    Equipamento: {equip_row[0]} ({equip_row[1]}) - Sala: {equip_row[3]}")
                        else:
                            print(f"    Equipamento não encontrado ou não é da sala {sala_id}")
    
    conn.close()

if __name__ == "__main__":
    test_sala_01_switches() 