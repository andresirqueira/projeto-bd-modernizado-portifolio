import sqlite3
import os

def inicializar_portas_patch_panel():
    """Inicializa as portas dos patch panels existentes"""
    
    # Mudar para a pasta raiz do projeto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    # Lista de arquivos de banco de dados das empresas (na raiz do projeto)
    db_files = []
    for file in os.listdir('.'):
        if file.endswith('.db') and file.startswith('empresa_') and file != 'usuarios_empresas.db':
            db_files.append(file)
    
    if not db_files:
        print("Nenhum banco de dados de empresa encontrado!")
        return
    
    for db_file in db_files:
        print(f"\nProcessando: {db_file}")
        
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        try:
            # Buscar patch panels existentes
            cur.execute('SELECT id, num_portas FROM patch_panels')
            patch_panels = cur.fetchall()
            
            if not patch_panels:
                print(f"⚠️ Nenhum patch panel encontrado em {db_file}")
                continue
            
            for patch_panel_id, num_portas in patch_panels:
                print(f"  Processando patch panel ID {patch_panel_id} com {num_portas} portas")
                
                # Verificar se já existem portas para este patch panel
                cur.execute('SELECT COUNT(*) FROM patch_panel_portas WHERE patch_panel_id = ?', (patch_panel_id,))
                portas_existentes = cur.fetchone()[0]
                
                if portas_existentes == 0:
                    # Criar portas automaticamente
                    for porta in range(1, num_portas + 1):
                        cur.execute('''
                            INSERT INTO patch_panel_portas (patch_panel_id, numero_porta, status)
                            VALUES (?, ?, 'livre')
                        ''', (patch_panel_id, porta))
                    
                    print(f"    ✅ {num_portas} portas criadas para patch panel {patch_panel_id}")
                else:
                    print(f"    ⚠️ Patch panel {patch_panel_id} já possui {portas_existentes} portas")
            
            conn.commit()
            print(f"✅ Portas inicializadas com sucesso em {db_file}")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar portas em {db_file}: {e}")
            conn.rollback()
        
        finally:
            conn.close()

if __name__ == "__main__":
    inicializar_portas_patch_panel() 