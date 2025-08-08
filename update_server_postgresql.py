#!/usr/bin/env python3
"""
Script para atualizar server.py para usar PostgreSQL
"""

import re
import os

def update_requirements():
    """Atualiza requirements.txt para incluir psycopg2"""
    requirements_file = 'requirements.txt'
    
    # Ler arquivo atual
    with open(requirements_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar psycopg2 se não existir
    if 'psycopg2' not in content:
        content += '\npsycopg2-binary==2.9.9\n'
        
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ psycopg2-binary adicionado ao requirements.txt")
    else:
        print("ℹ️  psycopg2 já está no requirements.txt")

def create_database_config():
    """Cria arquivo de configuração do banco"""
    config_content = '''import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuração do PostgreSQL (Render)
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'portfolio_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def get_postgres_connection():
    """Retorna uma conexão com PostgreSQL"""
    return psycopg2.connect(**POSTGRES_CONFIG)

def get_postgres_dict_connection():
    """Retorna uma conexão com PostgreSQL usando RealDictCursor"""
    config = POSTGRES_CONFIG.copy()
    config['cursor_factory'] = RealDictCursor
    return psycopg2.connect(**config)
'''
    
    with open('database_config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ Arquivo database_config.py criado")

def update_server_py():
    """Atualiza server.py para usar PostgreSQL"""
    
    # Ler o arquivo server.py
    with open('server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar import do PostgreSQL
    if 'import psycopg2' not in content:
        # Adicionar após os imports existentes
        content = re.sub(
            r'(import os\nimport sqlite3\nimport json)',
            r'\1\nimport psycopg2\nfrom psycopg2.extras import RealDictCursor\nfrom database_config import get_postgres_connection, get_postgres_dict_connection',
            content
        )
    
    # Substituir todas as conexões SQLite por PostgreSQL
    # Função para substituir conexões SQLite
    def replace_sqlite_connection(match):
        return 'conn = get_postgres_connection()'
    
    # Substituir conexões específicas do usuarios_empresas.db
    content = re.sub(
        r"conn = sqlite3\.connect\('usuarios_empresas\.db'\)",
        'conn = get_postgres_connection()',
        content
    )
    
    # Substituir fetchone() para PostgreSQL
    content = re.sub(
        r'cur\.fetchone\(\)',
        'cur.fetchone()',
        content
    )
    
    # Substituir fetchall() para PostgreSQL
    content = re.sub(
        r'cur\.fetchall\(\)',
        'cur.fetchall()',
        content
    )
    
    # Substituir placeholders de SQLite (? -> %s)
    content = re.sub(
        r'cur\.execute\(([^,]+),\s*\(([^)]+)\)\)',
        lambda m: f'cur.execute({m.group(1)}, ({m.group(2)}))',
        content
    )
    
    # Escrever o arquivo atualizado
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ server.py atualizado para usar PostgreSQL")

def create_migration_guide():
    """Cria um guia de migração"""
    guide_content = '''# 🚀 Guia de Migração para PostgreSQL

## 📋 Passos para Migração

### 1. **Configurar Variáveis de Ambiente no Render**

Adicione estas variáveis no seu projeto no Render:

```
POSTGRES_HOST=seu-host-postgres.render.com
POSTGRES_DB=portfolio_db
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_PORT=5432
```

### 2. **Executar Script de Migração**

```bash
# Instalar dependências
pip install psycopg2-binary

# Executar migração
python migrate_to_postgresql.py
```

### 3. **Verificar Migração**

O script irá:
- ✅ Testar conexões
- ✅ Criar tabelas no PostgreSQL
- ✅ Migrar dados do SQLite
- ✅ Verificar integridade dos dados

### 4. **Deploy no Render**

Após a migração:
1. Faça commit das mudanças
2. Push para o repositório
3. O Render irá fazer deploy automaticamente

## 🔧 Troubleshooting

### Erro de Conexão
- Verifique as variáveis de ambiente
- Confirme se o banco PostgreSQL está ativo
- Teste a conexão localmente

### Erro de Dados
- Execute o script de verificação
- Compare os logs de migração
- Restaure backup se necessário

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do Render
2. Teste localmente com PostgreSQL
3. Consulte a documentação do psycopg2

---
**Migração concluída! 🎉**
'''
    
    with open('MIGRATION_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Guia de migração criado (MIGRATION_GUIDE.md)")

def main():
    """Função principal"""
    print("🔧 Atualizando projeto para PostgreSQL")
    print("=" * 40)
    
    # Atualizar requirements.txt
    update_requirements()
    
    # Criar configuração do banco
    create_database_config()
    
    # Atualizar server.py
    update_server_py()
    
    # Criar guia de migração
    create_migration_guide()
    
    print("\n✅ Atualizações concluídas!")
    print("\n📋 Próximos passos:")
    print("1. Execute: python migrate_to_postgresql.py")
    print("2. Configure as variáveis de ambiente no Render")
    print("3. Faça deploy da aplicação")
    print("4. Teste todas as funcionalidades")

if __name__ == "__main__":
    main()
