# 🚀 Sistema de Portfólio - PostgreSQL

## 📋 Arquivos Principais

### 🎯 **Scripts Python (.py):**

1. **`setup_postgresql.py`** - Cria banco PostgreSQL vazio
2. **`update_server.py`** - Atualiza server.py para PostgreSQL

### 📄 **Arquivos de Configuração:**

- **`server.py`** - Aplicação principal Flask
- **`requirements.txt`** - Dependências Python
- **`login.html`** - Página de login
- **`index.html`** - Página inicial

### 🗄️ **Bancos de Dados (Backup):**

- **`usuarios_empresas.db`** - Banco SQLite original (usuários)
- **`empresa_wh.db`** - Banco SQLite original (dados)

## 🚀 Como Usar

### 1. **Criar Banco PostgreSQL:**
```bash
python setup_postgresql.py
```

### 2. **Atualizar Server.py:**
```bash
python update_server.py
```

### 3. **Configurar no Render:**
```
POSTGRES_HOST=seu-host-postgres.render.com
POSTGRES_DB=portfolio_unified
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_PORT=5432
```

### 4. **Fazer Deploy**

### 5. **Acessar Sistema:**
- **Usuário:** `admin`
- **Senha:** `admin123`

## 📊 Estrutura do Banco

**15 Tabelas PostgreSQL:**
- `usuarios` - Usuários do sistema
- `andares` - Andares da empresa
- `salas` - Salas por andar
- `equipamentos` - Equipamentos de TI
- `switches` - Switches de rede
- `switch_portas` - Portas dos switches
- `patch_panels` - Patch panels
- `patch_panel_portas` - Portas dos patch panels
- `cabos` - Cabos de rede
- `conexoes_cabos` - Conexões de cabos
- `tipos_cabos` - Tipos de cabos
- `sala_layouts` - Layouts das salas
- `ping_logs` - Logs de ping
- `historico_conexoes_patch_panel` - Histórico
- `sistema_logs` - Logs do sistema

## 🔑 Credenciais

- **Usuário:** `admin`
- **Senha:** `admin123`
- **Nível:** Master (acesso completo)

## 📁 Extensões dos Arquivos

- **`.py`** - Scripts Python
- **`.md`** - Documentação Markdown
- **`.html`** - Páginas web
- **`.txt`** - Arquivos de texto
- **`.db`** - Bancos SQLite (backup)

---
**Sistema limpo e organizado! 🎉**
