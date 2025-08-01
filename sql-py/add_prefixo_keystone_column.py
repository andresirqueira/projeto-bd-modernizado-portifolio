#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys

def add_prefixo_keystone_column():
    """Adiciona a coluna prefixo_keystone na tabela patch_panels"""
    
    # Obter o diretório raiz do projeto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    print("🔧 Adicionando coluna 'prefixo_keystone' na tabela patch_panels...")
    print(f"📁 Diretório do projeto: {project_root}")
    
    # Listar todos os arquivos de banco de dados das empresas
    db_files = [f for f in os.listdir('.') if f.startswith('empresa_') and f.endswith('.db') and f != 'usuarios_empresas.db']
    
    if not db_files:
        print("❌ Nenhum banco de dados de empresa encontrado!")
        return
    
    print(f"📊 Encontrados {len(db_files)} bancos de dados:")
    for db_file in db_files:
        print(f"   - {db_file}")
    
    success_count = 0
    error_count = 0
    
    for db_file in db_files:
        print(f"\n🔍 Processando: {db_file}")
        
        try:
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            
            # Verificar se a tabela patch_panels existe
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patch_panels'")
            if not cur.fetchone():
                print(f"   ⚠️  Tabela 'patch_panels' não existe em {db_file}")
                continue
            
            # Verificar se a coluna prefixo_keystone já existe
            cur.execute("PRAGMA table_info(patch_panels)")
            columns = [column[1] for column in cur.fetchall()]
            
            if 'prefixo_keystone' in columns:
                print(f"   ✅ Coluna 'prefixo_keystone' já existe em {db_file}")
                success_count += 1
                continue
            
            # Adicionar a coluna prefixo_keystone
            print(f"   ➕ Adicionando coluna 'prefixo_keystone'...")
            cur.execute("ALTER TABLE patch_panels ADD COLUMN prefixo_keystone TEXT")
            
            # Atualizar registros existentes com prefixo padrão baseado no andar
            print(f"   🔄 Atualizando registros existentes...")
            cur.execute("""
                UPDATE patch_panels 
                SET prefixo_keystone = 'PT' || (20 + andar) || '-01'
                WHERE prefixo_keystone IS NULL
            """)
            
            conn.commit()
            print(f"   ✅ Sucesso: {db_file}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Erro em {db_file}: {str(e)}")
            error_count += 1
            
        finally:
            if 'conn' in locals():
                conn.close()
    
    print(f"\n📊 Resumo:")
    print(f"   ✅ Sucessos: {success_count}")
    print(f"   ❌ Erros: {error_count}")
    print(f"   📁 Total processado: {len(db_files)}")
    
    if error_count == 0:
        print("\n🎉 Todas as colunas foram adicionadas com sucesso!")
    else:
        print(f"\n⚠️  {error_count} erro(s) encontrado(s). Verifique os logs acima.")

if __name__ == "__main__":
    add_prefixo_keystone_column() 