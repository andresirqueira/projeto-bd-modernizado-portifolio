import sqlite3

try:
    conn = sqlite3.connect('empresa_wh.db')
    cur = conn.cursor()
    
    # Listar todas as tabelas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    
    print("Tabelas encontradas:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Verificar se existe tabela switches
    if any('switches' in table for table in tables):
        print("\nTabela switches encontrada!")
        cur.execute("SELECT id, nome, marca, modelo FROM switches")
        switches = cur.fetchall()
        print(f"Switches encontrados: {len(switches)}")
        for switch in switches:
            print(f"ID: {switch[0]}, Nome: {switch[1]}, Marca: {switch[2]}, Modelo: {switch[3]}")
        
        # Verificar portas dos switches
        print("\nVerificando portas dos switches:")
        for switch in switches:
            cur.execute("SELECT COUNT(*) FROM switch_portas WHERE switch_id = ?", (switch[0],))
            porta_count = cur.fetchone()[0]
            print(f"Switch {switch[1]}: {porta_count} portas")
            
            if porta_count > 0:
                cur.execute("SELECT numero_porta FROM switch_portas WHERE switch_id = ? ORDER BY numero_porta LIMIT 5", (switch[0],))
                portas = cur.fetchall()
                print(f"  Primeiras portas: {[p[0] for p in portas]}")
    else:
        print("\nTabela switches NÃO encontrada!")
    
    # Verificar estrutura da tabela salas
    print("\nVerificando estrutura da tabela salas:")
    cur.execute("PRAGMA table_info(salas)")
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Verificar salas que contêm "01"
    print("\nVerificando salas com '01':")
    cur.execute("SELECT id, nome FROM salas WHERE nome LIKE '%01%' ORDER BY nome")
    salas_01 = cur.fetchall()
    for sala in salas_01:
        print(f"Sala {sala[0]}: {sala[1]}")
        
        # Verificar equipamentos na sala
        cur.execute("SELECT COUNT(*) FROM equipamentos WHERE sala_id = ?", (sala[0],))
        equip_count = cur.fetchone()[0]
        print(f"  Equipamentos: {equip_count}")
        
        if equip_count > 0:
            cur.execute("SELECT nome, tipo FROM equipamentos WHERE sala_id = ? LIMIT 3", (sala[0],))
            equipamentos = cur.fetchall()
            for equip in equipamentos:
                print(f"    - {equip[0]} ({equip[1]})")
    
    # Verificar todas as salas
    print("\nTodas as salas:")
    cur.execute("SELECT id, nome FROM salas ORDER BY nome")
    salas = cur.fetchall()
    for sala in salas:
        print(f"Sala {sala[0]}: {sala[1]}")
        
        # Verificar equipamentos na sala
        cur.execute("SELECT COUNT(*) FROM equipamentos WHERE sala_id = ?", (sala[0],))
        equip_count = cur.fetchone()[0]
        print(f"  Equipamentos: {equip_count}")
        
        if equip_count > 0:
            cur.execute("SELECT nome, tipo FROM equipamentos WHERE sala_id = ? LIMIT 3", (sala[0],))
            equipamentos = cur.fetchall()
            for equip in equipamentos:
                print(f"    - {equip[0]} ({equip[1]})")
    
    # Verificar equipamentos da Sala 01 e suas conexões
    print("\nVerificando equipamentos da Sala 01:")
    cur.execute("SELECT id, nome, tipo FROM equipamentos WHERE sala_id = 1")
    equipamentos_sala_01 = cur.fetchall()
    for equip in equipamentos_sala_01:
        print(f"Equipamento: {equip[1]} ({equip[2]}) - ID: {equip[0]}")
        
        # Verificar se está conectado diretamente
        cur.execute("""
            SELECT sp.numero_porta, s.nome as switch_nome
            FROM conexoes c
            JOIN switch_portas sp ON c.porta_id = sp.id
            JOIN switches s ON sp.switch_id = s.id
            WHERE c.equipamento_id = ? AND c.status = 'ativa'
        """, (equip[0],))
        conexao_direta = cur.fetchone()
        if conexao_direta:
            print(f"  Conectado diretamente: Porta {conexao_direta[0]} do {conexao_direta[1]}")
        
        # Verificar se está conectado via patch panel
        cur.execute("""
            SELECT ppp.porta_switch, pp.nome as patch_panel, ppp.numero_porta as porta_patch
            FROM patch_panel_portas ppp
            JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
            WHERE ppp.equipamento_id = ?
        """, (equip[0],))
        conexao_patch = cur.fetchone()
        if conexao_patch:
            print(f"  Conectado via patch panel: Porta {conexao_patch[0]} do switch -> {conexao_patch[1]} porta {conexao_patch[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"Erro: {e}") 