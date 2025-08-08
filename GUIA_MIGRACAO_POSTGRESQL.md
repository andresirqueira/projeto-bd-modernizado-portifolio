# 🚀 Guia Completo: Migração SQLite → PostgreSQL no Render

## 📋 Visão Geral

Este guia irá te ajudar a migrar seu banco de dados `usuarios_empresas.db` do SQLite para PostgreSQL no Render.

## 🎯 Objetivo

Migrar as seguintes tabelas:
- `usuarios` - Usuários do sistema
- `empresas` - Empresas cadastradas
- `usuario_empresas` - Relacionamento entre usuários e empresas

## 📦 Arquivos Criados

1. `migrate_to_postgresql.py` - Script completo de migração
2. `simple_migrate.py` - Script simplificado de migração
3. `database_config.py` - Configuração do PostgreSQL
4. `fix_server_postgresql.py` - Script para atualizar server.py

## 🔧 Passo a Passo

### 1. **Configurar PostgreSQL no Render**

1. Acesse o [Render Dashboard](https://dashboard.render.com)
2. Clique em "New" → "PostgreSQL"
3. Configure:
   - **Name**: `portfolio-db` (ou nome de sua preferência)
   - **Database**: `portfolio_db`
   - **User**: `portfolio_user`
   - **Region**: Escolha a mais próxima
4. Clique em "Create Database"

### 2. **Obter Credenciais do PostgreSQL**

Após criar o banco, você receberá:
- **Host**: `dpg-xxxxx-a.oregon-postgres.render.com`
- **Database**: `portfolio_db`
- **User**: `portfolio_user`
- **Password**: `sua_senha_gerada`
- **Port**: `5432`

### 3. **Configurar Variáveis de Ambiente no Render**

No seu projeto web no Render, adicione estas variáveis:

```
POSTGRES_HOST=dpg-xxxxx-a.oregon-postgres.render.com
POSTGRES_DB=portfolio_db
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=sua_senha_gerada
POSTGRES_PORT=5432
```

### 4. **Executar Migração Localmente**

```bash
# Instalar dependências
pip install psycopg2-binary

# Executar migração
python simple_migrate.py
```

### 5. **Verificar Migração**

O script irá mostrar:
- ✅ Conexão SQLite OK
- ✅ Conexão PostgreSQL OK
- ✅ Tabelas criadas
- ✅ X usuários migrados
- ✅ X empresas migradas
- ✅ X vínculos migrados

### 6. **Atualizar Código**

Execute o script para atualizar o `server.py`:

```bash
python fix_server_postgresql.py
```

### 7. **Deploy no Render**

1. Commit das mudanças:
```bash
git add .
git commit -m "Migração para PostgreSQL"
git push origin main
```

2. O Render fará deploy automaticamente

## 🔍 Verificação Pós-Migração

### Testar Login
1. Acesse sua aplicação no Render
2. Tente fazer login com usuários existentes
3. Verifique se consegue acessar as empresas

### Verificar Dados
```sql
-- No PostgreSQL do Render
SELECT COUNT(*) FROM usuarios;
SELECT COUNT(*) FROM empresas;
SELECT COUNT(*) FROM usuario_empresas;
```

## 🛠️ Troubleshooting

### Erro: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### Erro: "Connection refused"
- Verifique as variáveis de ambiente
- Confirme se o banco PostgreSQL está ativo
- Teste a conexão localmente

### Erro: "Table already exists"
- O script usa `CREATE TABLE IF NOT EXISTS`
- Pode executar novamente sem problemas

### Erro: "Duplicate key value"
- O script usa `ON CONFLICT` para evitar duplicatas
- Pode executar novamente sem problemas

## 📊 Monitoramento

### Logs do Render
- Acesse o dashboard do seu projeto
- Vá em "Logs" para ver erros
- Verifique se a aplicação está rodando

### Teste de Conexão
```python
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    port=os.getenv('POSTGRES_PORT')
)
print("Conexão OK!")
conn.close()
```

## 🔄 Rollback (Se Necessário)

Se precisar voltar para SQLite:

1. Restaure o backup do `server.py`
2. Remova as variáveis de ambiente do PostgreSQL
3. Faça deploy novamente

## 📞 Suporte

### Logs Úteis
- `migration_log.txt` - Log da migração
- Logs do Render - Erros de aplicação
- Console do navegador - Erros de frontend

### Comandos Úteis
```bash
# Verificar status do banco
python -c "import psycopg2; print('PostgreSQL OK')"

# Testar conexão
python simple_migrate.py

# Ver logs
tail -f migration_log.txt
```

## 🎉 Conclusão

Após seguir este guia:
1. ✅ Seu banco estará migrado para PostgreSQL
2. ✅ A aplicação estará rodando no Render
3. ✅ Todos os dados estarão preservados
4. ✅ O sistema estará mais robusto e escalável

---

**Migração concluída! 🚀**

Se encontrar problemas, verifique:
1. Variáveis de ambiente no Render
2. Logs da aplicação
3. Status do banco PostgreSQL
4. Conexão de rede
