import os
import sqlite3
from pathlib import Path

def add_patch_panels_table():
    # Obter o diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Listar todos os arquivos de banco de dados de empresas
    db_files = [f for f in os.listdir('.') if f.startswith('empresa_') and f.endswith('.db') and f != 'usuarios_empresas.db']
    
    print(f"Encontrados {len(db_files)} bancos de dados de empresas para processar:")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    for db_file in db_files:
        print(f"\nProcessando {db_file}...")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Verificar se a tabela patch_panels já existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patch_panels'")
            if cursor.fetchone():
                print(f"  Tabela patch_panels já existe em {db_file}")
                
                # Verificar se a coluna porta_inicial existe
                cursor.execute("PRAGMA table_info(patch_panels)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'porta_inicial' not in columns:
                    print(f"  Adicionando coluna porta_inicial em {db_file}")
                    cursor.execute("ALTER TABLE patch_panels ADD COLUMN porta_inicial INTEGER DEFAULT 1")
                else:
                    print(f"  Coluna porta_inicial já existe em {db_file}")
            else:
                print(f"  Criando tabela patch_panels em {db_file}")
                cursor.execute('''
                    CREATE TABLE patch_panels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT UNIQUE NOT NULL,
                        nome TEXT NOT NULL,
                        andar INTEGER NOT NULL,
                        porta_inicial INTEGER DEFAULT 1,
                        num_portas INTEGER NOT NULL DEFAULT 48,
                        status TEXT DEFAULT 'ativo',
                        descricao TEXT,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Verificar se a tabela patch_panel_portas já existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patch_panel_portas'")
            if cursor.fetchone():
                print(f"  Tabela patch_panel_portas já existe em {db_file}")
            else:
                print(f"  Criando tabela patch_panel_portas em {db_file}")
                cursor.execute('''
                    CREATE TABLE patch_panel_portas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patch_panel_id INTEGER NOT NULL,
                        numero_porta INTEGER NOT NULL,
                        switch_id INTEGER,
                        porta_switch INTEGER,
                        status TEXT DEFAULT 'livre',
                        equipamento_id INTEGER,
                        data_conexao TIMESTAMP,
                        FOREIGN KEY (patch_panel_id) REFERENCES patch_panels (id),
                        FOREIGN KEY (switch_id) REFERENCES switches (id),
                        FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id),
                        UNIQUE(patch_panel_id, numero_porta)
                    )
                ''')
            
            # Verificar se a tabela historico_conexoes_patch_panel já existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historico_conexoes_patch_panel'")
            if cursor.fetchone():
                print(f"  Tabela historico_conexoes_patch_panel já existe em {db_file}")
            else:
                print(f"  Criando tabela historico_conexoes_patch_panel em {db_file}")
                cursor.execute('''
                    CREATE TABLE historico_conexoes_patch_panel (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patch_panel_id INTEGER NOT NULL,
                        porta_id INTEGER NOT NULL,
                        equipamento_id INTEGER,
                        switch_id INTEGER,
                        porta_switch INTEGER,
                        tipo_acao TEXT NOT NULL,
                        data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usuario_id INTEGER,
                        observacao TEXT,
                        FOREIGN KEY (patch_panel_id) REFERENCES patch_panels (id),
                        FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id),
                        FOREIGN KEY (switch_id) REFERENCES switches (id),
                        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                    )
                ''')
            
            # Verificar se a tabela equipamentos existe e adicionar coluna keystone se necessário
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipamentos'")
            if cursor.fetchone():
                # Verificar se a coluna keystone já existe
                cursor.execute("PRAGMA table_info(equipamentos)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'keystone' not in columns:
                    print(f"  Adicionando coluna keystone em equipamentos em {db_file}")
                    cursor.execute("ALTER TABLE equipamentos ADD COLUMN keystone TEXT")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipamentos_keystone ON equipamentos(keystone)")
                else:
                    print(f"  Coluna keystone já existe em equipamentos em {db_file}")
            else:
                print(f"  Tabela equipamentos não encontrada em {db_file}")
            
            # Remover tabelas antigas se existirem
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conexoes_rede_patch_panel'")
            if cursor.fetchone():
                print(f"  Removendo tabela antiga conexoes_rede_patch_panel de {db_file}")
                cursor.execute("DROP TABLE conexoes_rede_patch_panel")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keystones'")
            if cursor.fetchone():
                print(f"  Removendo tabela antiga keystones de {db_file}")
                cursor.execute("DROP TABLE keystones")
            
            conn.commit()
            conn.close()
            print(f"  ✅ {db_file} processado com sucesso!")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {db_file}: {str(e)}")
    
    print("\n🎉 Processamento concluído!")

if __name__ == "__main__":
    add_patch_panels_table() 