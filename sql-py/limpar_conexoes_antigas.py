#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar conexões de cabos antigas que foram desconectadas
"""

import sqlite3
import sys
import os

def limpar_conexoes_antigas(db_file):
    """
    Remove conexões de cabos que foram desconectadas (data_desconexao IS NOT NULL)
    """
    if not os.path.exists(db_file):
        print(f"❌ Erro: Banco de dados '{db_file}' não encontrado!")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        print(f"🔍 Conectado ao banco: {db_file}")
        
        # Primeiro, vamos listar as conexões desconectadas
        print("\n📋 Conexões desconectadas encontradas:")
        cur.execute('''
            SELECT cc.id, cc.cabo_id, cc.equipamento_origem_id, cc.equipamento_destino_id,
                   cc.porta_origem, cc.porta_destino, cc.sala_id, cc.observacao,
                   cc.data_conexao, cc.data_desconexao,
                   c.codigo_unico as codigo_cabo, c.tipo as tipo_cabo,
                   eo.nome as equipamento_origem, ed.nome as equipamento_destino,
                   s.nome as sala_nome
            FROM conexoes_cabos cc
            JOIN cabos c ON cc.cabo_id = c.id
            LEFT JOIN equipamentos eo ON cc.equipamento_origem_id = eo.id
            LEFT JOIN equipamentos ed ON cc.equipamento_destino_id = ed.id
            LEFT JOIN salas s ON cc.sala_id = s.id
            WHERE cc.data_desconexao IS NOT NULL
            ORDER BY cc.data_desconexao DESC
        ''')
        
        conexoes_desconectadas = cur.fetchall()
        
        if not conexoes_desconectadas:
            print("✅ Nenhuma conexão desconectada encontrada!")
            return True
        
        print(f"📊 Total de conexões desconectadas: {len(conexoes_desconectadas)}")
        print("\n" + "="*80)
        
        for i, conexao in enumerate(conexoes_desconectadas, 1):
            print(f"{i:2d}. ID: {conexao[0]:3d} | Cabo: {conexao[10]} ({conexao[11]})")
            print(f"    Origem: {conexao[12]} → Destino: {conexao[13]}")
            print(f"    Sala: {conexao[14]} | Conectado: {conexao[8]} | Desconectado: {conexao[9]}")
            print()
        
        print("="*80)
        print("⚠️  ATENÇÃO: Estas conexões serão PERMANENTEMENTE removidas do banco!")
        print("   Elas não aparecem mais na interface, mas ainda estão no banco.")
        
        confirmacao = input("\n   Confirma a limpeza? (s/N): ").strip().lower()
        
        if confirmacao not in ['s', 'sim', 'y', 'yes']:
            print("❌ Limpeza cancelada!")
            return False
        
        # Remover todas as conexões desconectadas
        print(f"\n🗑️  Removendo {len(conexoes_desconectadas)} conexões desconectadas...")
        cur.execute('DELETE FROM conexoes_cabos WHERE data_desconexao IS NOT NULL')
        
        if cur.rowcount > 0:
            conn.commit()
            print(f"✅ {cur.rowcount} conexões removidas com sucesso!")
            
            # Verificar se ainda existem conexões desconectadas
            cur.execute('SELECT COUNT(*) FROM conexoes_cabos WHERE data_desconexao IS NOT NULL')
            total_restantes = cur.fetchone()[0]
            print(f"📊 Conexões desconectadas restantes: {total_restantes}")
            
            return True
        else:
            print("❌ Erro: Nenhuma conexão foi removida!")
            return False
        
    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python limpar_conexoes_antigas.py <nome_do_banco.db>")
        sys.exit(1)
    
    db_file = sys.argv[1]
    sucesso = limpar_conexoes_antigas(db_file)
    
    if sucesso:
        print("\n🎉 Limpeza concluída com sucesso!")
        print("💡 Agora o botão 'Dados reais' deve mostrar apenas conexões ativas.")
    else:
        print("\n❌ Erro durante a limpeza!")
        sys.exit(1) 