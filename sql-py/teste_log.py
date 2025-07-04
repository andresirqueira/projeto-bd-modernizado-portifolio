import os
from datetime import datetime

# Configuração do sistema de logs
LOG_FILE = 'sistema_logs.txt'

def registrar_log(usuario, acao, detalhes, status='sucesso'):
    """
    Registra uma ação no arquivo de log
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Usuario: {usuario} | Acao: {acao} | Detalhes: {detalhes} | Status: {status}\n"
        
        print(f"DEBUG: Tentando registrar log: {log_entry.strip()}")
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"DEBUG: Log registrado com sucesso no arquivo: {LOG_FILE}")
        print(f"DEBUG: Diretório atual: {os.getcwd()}")
        
        # Verificar se o arquivo foi criado
        if os.path.exists(LOG_FILE):
            print(f"DEBUG: Arquivo existe, tamanho: {os.path.getsize(LOG_FILE)} bytes")
        else:
            print("DEBUG: Arquivo não foi criado!")
            
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
        print(f"DEBUG: Arquivo de log: {LOG_FILE}")
        print(f"DEBUG: Diretório atual: {os.getcwd()}")

# Teste
if __name__ == "__main__":
    print("Testando sistema de logs...")
    registrar_log("teste", "TESTE_LOG", "Teste de funcionamento do sistema de logs", "sucesso")
    print("Teste concluído!") 