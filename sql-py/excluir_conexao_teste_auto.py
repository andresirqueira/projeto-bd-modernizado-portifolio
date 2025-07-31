#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script automatizado para excluir conexão de cabo inativo criada como teste
"""

import sqlite3
import sys
import os

def excluir_conexao_teste_automatico(db_file):
    """
    Exclui automaticamente a conexão de cabo inativo criada como teste
    """
    if not os.path.exists(db_file):
        print(f"❌ Erro: Banco de dados '{db_file}' não encontrado!")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        print(f"🔍 Conectado ao banco: {db_file}")
        
        # Buscar a conexão de teste (HDMI-0000001 que foi desconectada)
        print("\n🔍 Procurando conexão de teste...")
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
            AND c.codigo_unico = 'HDMI-0000001'
            ORDER BY cc.data_desconexao DESC
        ''')
        
        conexao_teste = cur.fetchone()
        
        if not conexao_teste:
            print("✅ Nenhuma conexão de teste encontrada!")
            return True
        
        conexao_id = conexao_teste[0]
        
        print(f"📋 Conexão de teste encontrada:")
        print(f"   ID: {conexao_id}")
        print(f"   Cabo: {conexao_teste[10]} ({conexao_teste[11]})")
        print(f"   Origem: {conexao_teste[12]} - Porta: {conexao_teste[4]}")
        print(f"   Destino: {conexao_teste[13]} - Porta: {conexao_teste[5]}")
        print(f"   Sala: {conexao_teste[14]}")
        print(f"   Conectado em: {conexao_teste[8]}")
        print(f"   Desconectado em: {conexao_teste[9]}")
        
        # Excluir a conexão
        print(f"\n🗑️  Excluindo conexão ID {conexao_id}...")
        cur.execute('DELETE FROM conexoes_cabos WHERE id = ?', (conexao_id,))
        
        if cur.rowcount > 0:
            conn.commit()
            print(f"✅ Conexão ID {conexao_id} excluída com sucesso!")
            
            # Verificar se ainda existem conexões inativas
            cur.execute('SELECT COUNT(*) FROM conexoes_cabos WHERE data_desconexao IS NOT NULL')
            total_restantes = cur.fetchone()[0]
            print(f"📊 Conexões inativas restantes: {total_restantes}")
            
            return True
        else:
            print("❌ Erro: Nenhuma conexão foi excluída!")
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

def main():
    """
    Função principal
    """
    print("🔧 Script automatizado para excluir conexão de teste")
    print("=" * 55)
    
    # Verificar argumentos
    if len(sys.argv) != 2:
        print("❌ Uso: python excluir_conexao_teste_auto.py <banco_dados>")
        print("   Exemplo: python excluir_conexao_teste_auto.py empresa_wh.db")
        sys.exit(1)
    
    db_file = sys.argv[1]
    
    # Executar exclusão
    if excluir_conexao_teste_automatico(db_file):
        print("\n✅ Operação concluída com sucesso!")
    else:
        print("\n❌ Operação falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main() 