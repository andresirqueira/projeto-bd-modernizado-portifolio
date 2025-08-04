# 🚀 Guia de Workflow: VS Code ↔ Workspace IA

## 📋 Configuração Inicial

### No seu VS Code (empresa):
```bash
# Clone o repositório (se ainda não fez)
git clone https://github.com/andresirqueira/projeto-bd-modernizado.git
cd projeto-bd-modernizado

# Configure seu usuário Git (se necessário)
git config user.name "Seu Nome"
git config user.email "seu.email@empresa.com"
```

## 🔄 Workflow Diário

### 1. **Desenvolvimento no VS Code**
```bash
# Sempre comece atualizando
git pull origin main

# Faça suas modificações no VS Code
# Teste localmente

# Commit suas mudanças
git add .
git commit -m "Descrição das mudanças"
git push origin main
```

### 2. **Quando precisar de ajuda de IA**
- Venha para este workspace
- Execute: `git pull origin main`
- Peça ajuda para análise, correções, melhorias
- Implemente as sugestões no VS Code

### 3. **Sincronização**
```bash
# No VS Code: após fazer mudanças
git add .
git commit -m "Implementação das sugestões da IA"
git push origin main

# No workspace: para sincronizar
git pull origin main
```

## 🛠️ Comandos Úteis

### Verificar status
```bash
git status
git log --oneline -5  # Últimos 5 commits
```

### Desfazer mudanças (se necessário)
```bash
git checkout -- arquivo.html  # Desfazer arquivo específico
git reset --hard HEAD~1       # Desfazer último commit
```

### Branches (para features grandes)
```bash
git checkout -b feature/nova-funcionalidade
# Desenvolver...
git push origin feature/nova-funcionalidade
# Merge via Pull Request
```

## 📁 Estrutura do Projeto

```
projeto-bd-modernizado/
├── server.py              # Servidor principal
├── *.html                 # Páginas web
├── css/                   # Estilos
├── static/                # Arquivos estáticos
├── sql-py/                # Scripts SQL/Python
├── requirements.txt       # Dependências Python
└── WORKFLOW_GUIDE.md      # Este guia
```

## 🎯 Dicas de Produtividade

### 1. **Commits frequentes**
- Faça commits pequenos e frequentes
- Use mensagens descritivas
- Exemplo: "Adiciona validação de formulário de login"

### 2. **Testes locais**
- Sempre teste no VS Code antes de commitar
- Use `python server.py` para testar o servidor

### 3. **Backup**
- O Git é seu backup principal
- Considere fazer backup local adicional se necessário

## 🔧 Resolução de Conflitos

Se houver conflitos:
```bash
# Ver conflitos
git status

# Editar arquivos com conflitos
# Remover marcadores <<<<<<<, =======, >>>>>>>

# Resolver conflitos
git add .
git commit -m "Resolve conflitos"
git push origin main
```

## 📞 Quando usar cada ambiente

### VS Code (empresa):
- ✅ Desenvolvimento principal
- ✅ Testes locais
- ✅ Debugging
- ✅ Refatoração

### Workspace IA:
- ✅ Análise de código
- ✅ Sugestões de melhorias
- ✅ Correção de bugs
- ✅ Implementação de features complexas
- ✅ Otimização de performance

## 🚨 Importante

- **Sempre faça pull antes de começar** a trabalhar
- **Commit e push frequentemente** para não perder trabalho
- **Teste localmente** antes de commitar
- **Use branches** para features grandes

---

**Pronto para começar?** 🎉