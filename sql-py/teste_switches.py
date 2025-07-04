import requests
import json

# Criar uma sessão para manter cookies
session = requests.Session()

# Primeiro fazer login
print("=== Fazendo login ===")
login_data = {
    'username': 'admin',
    'senha': 'admin'
}

try:
    # Fazer login
    login_response = session.post('http://127.0.0.1:5000/login', json=login_data)
    print(f"Login status: {login_response.status_code}")
    print(f"Login response: {login_response.text}")
    
    # Testar rota de listar switches
    print("\n=== Testando rota /switches ===")
    response = session.get('http://127.0.0.1:5000/switches')
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Conteúdo: {response.text}")
    
    if response.status_code == 200:
        switches = response.json()
        print(f"Switches encontrados: {len(switches)}")
        for switch in switches:
            print(f"  - ID: {switch['id']}, Nome: {switch['nome']}, Marca: {switch['marca']}")
    else:
        print("Erro na resposta")
        
    # Testar rota de portas
    print("\n=== Testando rota /switch-portas/1 ===")
    response = session.get('http://127.0.0.1:5000/switch-portas/1')
    print(f"Status: {response.status_code}")
    print(f"Conteúdo: {response.text}")
    
    if response.status_code == 200:
        portas = response.json()
        print(f"Portas encontradas: {len(portas)}")
        for porta in portas:
            print(f"  - Porta {porta['numero_porta']}: {porta['status']}")
    else:
        print("Erro na resposta")
        
except Exception as e:
    print(f"Erro ao fazer requisição: {e}")
    print("Verifique se o servidor está rodando em http://127.0.0.1:5000") 