#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para excluir conexão de cabo inativo criada como teste
"""

import sqlite3
import sys
import os

def excluir_conexao_teste(db_file):
    """
    Exclui a conexão de cabo inativo criada como teste
    """
    if not os.path.exists(db_file):
        print(f"❌ Erro: Banco de dados '{db_file}' não encontrado!")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        print(f"🔍 Conectado ao banco: {db_file}")
        
        # Primeiro, vamos listar as conexões inativas para identificar qual excluir
        print("\n📋 Conexões inativas encontradas:")
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
        
        conexoes_inativas = cur.fetchall()
        
        if not conexoes_inativas:
            print("✅ Nenhuma conexão inativa encontrada!")
            return True
        
        print(f"📊 Total de conexões inativas: {len(conexoes_inativas)}")
        print("\n" + "="*80)
        
        for i, conexao in enumerate(conexoes_inativas, 1):
            print(f"\n{i}. ID: {conexao[0]}")
            print(f"   Cabo: {conexao[10]} ({conexao[11]})")
            print(f"   Origem: {conexao[12] or 'N/A'} - Porta: {conexao[4] or 'N/A'}")
            print(f"   Destino: {conexao[13] or 'N/A'} - Porta: {conexao[5] or 'N/A'}")
            print(f"   Sala: {conexao[14] or 'N/A'}")
            print(f"   Conectado em: {conexao[8]}")
            print(f"   Desconectado em: {conexao[9]}")
            print(f"   Observação: {conexao[7] or 'N/A'}")
            print("-" * 60)
        
        # Perguntar qual conexão excluir
        print("\n🔧 Qual conexão você deseja excluir?")
        print("   Digite o número da conexão ou '0' para cancelar:")
        
        try:
            escolha = int(input("   Sua escolha: ").strip())
            
            if escolha == 0:
                print("❌ Operação cancelada pelo usuário.")
                return False
            
            if escolha < 1 or escolha > len(conexoes_inativas):
                print("❌ Escolha inválida!")
                return False
            
            # Obter a conexão selecionada
            conexao_selecionada = conexoes_inativas[escolha - 1]
            conexao_id = conexao_selecionada[0]
            
            print(f"\n⚠️  Você está prestes a excluir a conexão ID {conexao_id}")
            print(f"   Cabo: {conexao_selecionada[10]} ({conexao_selecionada[11]})")
            print(f"   Origem: {conexao_selecionada[12]} → Destino: {conexao_selecionada[13]}")
            
            confirmacao = input("\n   Confirma a exclusão? (s/N): ").strip().lower()
            
            if confirmacao not in ['s', 'sim', 'y', 'yes']:
                print("❌ Exclusão cancelada!")
                return False
            
            # Excluir a conexão
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
                
        except ValueError:
            print("❌ Entrada inválida! Digite um número.")
            return False
        except KeyboardInterrupt:
            print("\n❌ Operação cancelada pelo usuário.")
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
    print("🔧 Script para excluir conexão de cabo inativo")
    print("=" * 50)
    
    # Verificar argumentos
    if len(sys.argv) != 2:
        print("❌ Uso: python excluir_conexao_teste.py <banco_dados>")
        print("   Exemplo: python excluir_conexao_teste.py empresa_wh.db")
        sys.exit(1)
    
    db_file = sys.argv[1]
    
    # Executar exclusão
    if excluir_conexao_teste(db_file):
        print("\n✅ Operação concluída com sucesso!")
    else:
        print("\n❌ Operação falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main() 