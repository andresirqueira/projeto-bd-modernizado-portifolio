#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import glob

def corrigir_status_patch_panel():
    """
    Corrige os status das portas do patch panel baseado em:
    - equipamento_id: se tem equipamento = 'ocupada'
    - switch_id: se tem switch mas não equipamento = 'mapeada'
    - nenhum dos dois = 'livre'
    """
    
    # Encontrar todos os bancos de dados de empresas
    db_files = glob.glob('empresa_*.db')
    
    if not db_files:
        print("Nenhum banco de dados de empresa encontrado!")
        return
    
    for db_file in db_files:
        print(f"\n=== Processando: {db_file} ===")
        
        try:
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            
            # Verificar se a tabela patch_panel_portas existe
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patch_panel_portas'")
            if not cur.fetchone():
                print(f"  Tabela patch_panel_portas não encontrada em {db_file}")
                conn.close()
                continue
            
            # Buscar todas as portas do patch panel
            cur.execute('''
                SELECT id, equipamento_id, switch_id, status
                FROM patch_panel_portas
            ''')
            
            portas = cur.fetchall()
            print(f"  Encontradas {len(portas)} portas")
            
            corrigidas = 0
            
            for porta in portas:
                porta_id, equipamento_id, switch_id, status_atual = porta
                
                # Determinar o status correto
                if equipamento_id:
                    status_correto = 'ocupada'
                elif switch_id:
                    status_correto = 'mapeada'
                else:
                    status_correto = 'livre'
                
                # Se o status está incorreto, corrigir
                if status_atual != status_correto:
                    cur.execute('''
                        UPDATE patch_panel_portas 
                        SET status = ?
                        WHERE id = ?
                    ''', (status_correto, porta_id))
                    
                    print(f"    Porta {porta_id}: {status_atual} → {status_correto}")
                    corrigidas += 1
            
            conn.commit()
            print(f"  {corrigidas} portas corrigidas")
            
            conn.close()
            
        except Exception as e:
            print(f"  Erro ao processar {db_file}: {str(e)}")
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    print("=== CORREÇÃO DE STATUS DAS PORTAS DO PATCH PANEL ===")
    print("Este script corrige os status das portas baseado em:")
    print("- equipamento_id: se tem equipamento = 'ocupada'")
    print("- switch_id: se tem switch mas não equipamento = 'mapeada'")
    print("- nenhum dos dois = 'livre'")
    print()
    
    corrigir_status_patch_panel()
    
    print("\n=== CORREÇÃO CONCLUÍDA ===") 