# Sistema de Gerenciamento de Portas de Switches

## Visão Geral

Este sistema permite gerenciar portas de switches de forma flexível, incluindo criação automática, edição e reconfiguração. Foi desenvolvido para resolver o problema de switches criados sem portas configuradas.

## Problema Original

- Switches novos não possuíam portas configuradas automaticamente
- Usuários não conseguiam acessar portas para gerenciamento
- Impossibilidade de mapear switches com patch panels
- Falta de flexibilidade para ajustar número de portas

## Solução Implementada

### Frontend (`gerenciar-portas-switch.html`)
- Interface intuitiva para gerenciar portas de switches
- Modal de gerenciamento com múltiplas opções
- Botões para diferentes operações (criar, editar, recriar, adicionar)
- Validações e confirmações para operações destrutivas

### Backend (`server.py`)
- Novas rotas para operações avançadas de portas
- Validações de segurança e integridade
- Sistema de logs para auditoria
- Tratamento de erros robusto

## Funcionalidades Implementadas

### 1. Criação Automática de Portas
- **Rota**: `POST /switches`
- **Descrição**: Quando um novo switch é criado, as portas são criadas automaticamente baseadas no modelo
- **Lógica**: 
  - Switches com "48" no modelo → 48 portas
  - Switches com "12" ou "16" no modelo → 16 portas  
  - Switches com "8" no modelo → 8 portas
  - Switches com "4" no modelo → 4 portas
  - Outros → 24 portas (padrão)

### 2. Criação Manual de Portas
- **Rota**: `POST /switch-portas`
- **Descrição**: Permite criar portas individuais para switches existentes
- **Parâmetros**: `switch_id`, `numero_porta`, `descricao`

### 3. Criação de Portas Padrão para Switches Existentes
- **Rota**: `POST /switch-portas/<switch_id>/criar-portas-padrao`
- **Descrição**: Cria portas padrão para switches que não possuem portas configuradas
- **Lógica**: Mesma lógica da criação automática baseada no modelo

### 4. Recriação de Portas (⚠️ Funcionalidade Destrutiva)
- **Rota**: `POST /switch-portas/<switch_id>/recriar-portas`
- **Descrição**: Remove TODAS as portas existentes e cria novas com o número especificado
- **⚠️ ATENÇÃO**: Esta operação remove todas as conexões e mapeamentos existentes
- **Parâmetros**: `numero_portas` (1-100)
- **Casos de Uso**: Mudar de 24 para 48 portas, corrigir configuração incorreta

### 5. Adição de Portas
- **Rota**: `POST /switch-portas/<switch_id>/adicionar-portas`
- **Descrição**: Adiciona novas portas mantendo as existentes
- **Parâmetros**: `numero_portas` (1-50)
- **Casos de Uso**: Expandir capacidade do switch sem perder configurações

### 6. Edição de Portas Individuais
- **Rota**: `PUT /switch-portas/<porta_id>`
- **Descrição**: Permite editar a descrição de uma porta específica
- **Parâmetros**: `descricao`
- **Casos de Uso**: Renomear portas, adicionar informações específicas

### 7. Deleção de Portas Individuais
- **Rota**: `DELETE /switch-portas/<porta_id>`
- **Descrição**: Remove uma porta específica do switch
- **⚠️ ATENÇÃO**: Só permite deletar portas livres (sem conexões ou mapeamentos)
- **Casos de Uso**: Remover portas danificadas, ajustar configuração

## Como Usar

### Interface Principal
1. Acesse `gerenciar-portas-switch.html`
2. Selecione um switch da lista
3. Use o botão "GERENCIAR PORTAS" para abrir o modal de gerenciamento

### Modal de Gerenciamento
O modal oferece três opções principais:

#### ⚠️ Recriar Portas
- **Uso**: Quando você quer mudar completamente o número de portas
- **Exemplo**: Mudar de 24 para 48 portas
- **⚠️ Cuidado**: Remove todas as configurações existentes

#### ➕ Adicionar Mais Portas
- **Uso**: Expandir a capacidade sem perder configurações
- **Exemplo**: Adicionar 4 portas extras a um switch de 24
- **✅ Seguro**: Mantém todas as configurações existentes

#### 🔧 Editar Portas Individuais
- **Uso**: Modificar descrições ou remover portas específicas
- **Exemplo**: Renomear "Porta 1" para "Uplink Principal"
- **✅ Seguro**: Modificações pontuais e controladas

## Casos de Uso Comuns

### Caso 1: Switch com 24 portas, quer 48
1. Abra o modal de gerenciamento
2. Use "Recriar Portas" com 48 portas
3. Confirme a operação
4. Todas as portas serão recriadas (conexões perdidas)

### Caso 2: Switch com 24 portas, quer expandir
1. Abra o modal de gerenciamento
2. Use "Adicionar Mais Portas" com o número desejado
3. As novas portas serão adicionadas às existentes
4. Todas as configurações são mantidas

### Caso 3: Editar descrições específicas
1. Abra o modal de gerenciamento
2. Use "Editar Portas Individuais"
3. Modifique as descrições desejadas
4. Salve as alterações

## Segurança e Validações

### Validações de Entrada
- Número de portas: 1-100 para recriar, 1-50 para adicionar
- Verificação de existência do switch
- Verificação de permissões de administrador

### Proteções de Dados
- Não permite deletar portas ocupadas
- Não permite deletar portas mapeadas para patch panels
- Confirmações para operações destrutivas

### Auditoria
- Todas as operações são logadas
- Logs incluem usuário, ação, detalhes e status
- Logs separados por empresa

## Arquivos Modificados

### Backend
- `server.py`: Novas rotas para gerenciar portas

### Frontend
- `gerenciar-portas-switch.html`: Interface de gerenciamento
- `teste-gerenciar-portas.html`: Arquivo de teste

## Testando as Funcionalidades

### Arquivo de Teste
Use `teste-gerenciar-portas.html` para testar todas as funcionalidades:

1. **Criar Switch**: Testa criação automática de portas
2. **Ver Portas**: Lista portas existentes
3. **Recriar Portas**: Testa funcionalidade destrutiva
4. **Adicionar Portas**: Testa expansão segura
5. **Editar Porta**: Testa modificação individual
6. **Deletar Porta**: Testa remoção segura

### Fluxo de Teste Recomendado
1. Crie um switch com modelo "48-Port"
2. Verifique se foram criadas 48 portas
3. Teste recriar com 24 portas
4. Teste adicionar 4 portas extras
5. Teste editar descrições
6. Teste deletar uma porta livre

## Troubleshooting

### Erro: "Switch não encontrado"
- Verifique se o ID do switch está correto
- Confirme se o switch existe na empresa selecionada

### Erro: "Porta já existe"
- Use "Recriar Portas" para limpar e recriar
- Ou use "Adicionar Portas" para expandir

### Erro: "Não é possível deletar porta ocupada"
- Desconecte equipamentos primeiro
- Desmapeie patch panels primeiro
- Use "Recriar Portas" se necessário

### Erro: "Nenhuma empresa selecionada"
- Faça login novamente
- Selecione uma empresa válida

## Considerações Futuras

### Melhorias Possíveis
- Backup automático antes de operações destrutivas
- Histórico de alterações de portas
- Validação de modelos de switch mais inteligente
- Interface para importar configurações de portas

### Limitações Atuais
- Operações destrutivas não podem ser desfeitas
- Não há validação de compatibilidade de hardware
- Descrições de portas são limitadas a texto simples

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema
2. Use o arquivo de teste para validar funcionalidades
3. Confirme permissões de administrador
4. Verifique a conexão com o banco de dados
