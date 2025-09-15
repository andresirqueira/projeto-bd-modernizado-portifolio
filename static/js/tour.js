class SistemaTour {
    constructor() {
        this.passoAtual = 0;
        this.passos = [];
        this.ativo = false;
        this.intervalo = null;
        this.elementoAtual = null;
        this.tooltip = null;
        
        this.inicializar();
    }
    
    inicializar() {
        this.criarTooltip();
        this.criarControles();
        this.criarOverlay();
        this.carregarConfiguracoes();
    }
    
    criarTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.id = 'tour-tooltip';
        this.tooltip.className = 'tour-tooltip hidden';
        this.tooltip.innerHTML = `
            <div class="tour-tooltip-content">
                <div class="tour-tooltip-title"></div>
                <div class="tour-tooltip-description"></div>
                <div class="tour-tooltip-progress"></div>
            </div>
        `;
        document.body.appendChild(this.tooltip);
    }
    
    criarControles() {
        const controles = document.createElement('div');
        controles.id = 'tour-controles';
        controles.className = 'tour-controles hidden';
        controles.innerHTML = `
            <div class="tour-controles-content">
                <div style="margin-bottom: 8px; font-size: 12px; color: #6b7280; text-align: center;">
                    <strong>Controles do Tour</strong>
                </div>
                <button id="tour-pausar" class="tour-btn">
                    <i class="fas fa-pause"></i> Pausar
                </button>
                                 <button id="tour-pular" class="tour-btn">
                     <i class="fas fa-forward"></i> Pular
                 </button>
                 <button id="tour-parar" class="tour-btn tour-btn-danger">
                     <i class="fas fa-stop"></i> Sair
                 </button>
            </div>
        `;
        document.body.appendChild(controles);
        
                 // Event listeners
         document.getElementById('tour-pausar').addEventListener('click', () => this.pausar());
         document.getElementById('tour-pular').addEventListener('click', () => this.proximoPasso());
         document.getElementById('tour-parar').addEventListener('click', () => this.parar());
    }
    
    criarOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'tour-overlay';
        overlay.className = 'tour-overlay';
        document.body.appendChild(overlay);
    }
    
         carregarConfiguracoes() {
         // Configurações básicas do tour
         this.config = {
             duracaoPasso: 6000, // Aumentado de 3000 para 6000 ms (6 segundos)
             transicao: 500,
             corHighlight: '#3b82f6',
             corTooltip: '#1f2937'
         };
     }
    
    iniciarTour(tipo = 'completo') {
        if (this.ativo) {
            this.parar();
        }
        
        this.ativo = true;
        this.passoAtual = 0;
        this.passos = this.obterPassos(tipo);
        
        // Salvar estado do tour
        sessionStorage.setItem('tourAtivo', 'true');
        sessionStorage.setItem('tourTipo', tipo);
        sessionStorage.setItem('tourPasso', '0');
        
        document.getElementById('tour-controles').classList.remove('hidden');
        // Ativar o overlay para focar no tour
        document.getElementById('tour-overlay').classList.add('active');
        document.getElementById('tour-overlay').style.pointerEvents = 'auto';
        
        this.executarPasso();
    }
    
    continuarTour(tipo, passo) {
        this.ativo = true;
        this.passoAtual = passo;
        this.passos = this.obterPassos(tipo);
        
        document.getElementById('tour-controles').classList.remove('hidden');
        // Ativar o overlay para focar no tour
        document.getElementById('tour-overlay').classList.add('active');
        document.getElementById('tour-overlay').style.pointerEvents = 'auto';
        
        this.executarPasso();
    }
    
         obterPassos(tipo) {
         const passos = {
                          'config-admin': [
                 {
                     titulo: '🎯 Tour: Painel Administrativo',
                     descricao: 'Bem-vindo ao painel administrativo! Vou mostrar todas as funcionalidades disponíveis na ordem visual da tela. Use os controles para navegar.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: '🏢 Linha 1: Gerenciamento de Salas',
                     descricao: 'Vamos começar pela primeira linha - gerenciamento de salas. Esta linha contém todas as funcionalidades relacionadas ao gerenciamento de salas.',
                     acao: 'destacar',
                     seletor: 'div.flex.flex-row.gap-1:nth-of-type(1)'
                 },
                 {
                     titulo: '➕ Adicionar Sala',
                     descricao: 'Cria uma nova sala no sistema. Permite definir nome, tipo, descrição e vincular equipamentos.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="adicionar-sala.html"]'
                 },
                 {
                     titulo: '✏️ Editar Sala',
                     descricao: 'Modifica informações de uma sala existente. Permite alterar dados e equipamentos vinculados.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="editar-sala.html"]'
                 },
                 {
                     titulo: '🗑️ Excluir Sala',
                     descricao: 'Remove uma sala do sistema. Atenção: esta ação é irreversível!',
                     acao: 'destacar',
                     seletor: 'button[onclick*="excluir-sala.html"]'
                 },
                 {
                     titulo: '👁️ Ver Salas',
                     descricao: 'Visualiza todas as salas cadastradas com seus detalhes e equipamentos.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="ver-salas.html"]'
                 },
                 {
                     titulo: '📤 Upload Fotos',
                     descricao: 'Faz upload de imagens para usar nas salas. Suporta múltiplos formatos.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="upload-fotos-salas.html"]'
                 },
                 {
                     titulo: '🏢 Logo da Empresa',
                     descricao: 'Gerencia o logo da empresa que aparece no sistema. Pode adicionar ou remover.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="gerenciar-logo-empresa.html"]'
                 },
                 {
                     titulo: '🔧 Linha 2: Gerenciamento de Equipamentos',
                     descricao: 'Agora vamos para a segunda linha - gerenciamento de equipamentos. Esta linha contém todas as funcionalidades relacionadas ao gerenciamento de equipamentos.',
                     acao: 'destacar',
                     seletor: 'div.flex.flex-row.gap-1:nth-of-type(2)'
                 },
                 {
                     titulo: '➕ Adicionar Equipamento',
                     descricao: 'Cadastra um novo equipamento no sistema com todas suas especificações.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="adicionar-equipamento.html"]'
                 },
                 {
                     titulo: '✏️ Editar Equipamento',
                     descricao: 'Modifica dados de um equipamento existente.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="editar-equipamento.html"]'
                 },
                 {
                     titulo: '🗑️ Excluir Equipamento',
                     descricao: 'Remove um equipamento do sistema. Cuidado: ação irreversível!',
                     acao: 'destacar',
                     seletor: 'button[onclick*="excluir-equipamento.html"]'
                 },
                 {
                     titulo: '👁️ Ver Equipamentos',
                     descricao: 'Lista todos os equipamentos cadastrados com filtros e busca.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="ver-equipamento.html"]'
                 },
                 {
                     titulo: '🔧 Gerenciar Equipamentos',
                     descricao: 'Interface avançada para gerenciar equipamentos em lote.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="gerenciar-equipamentos.html"]'
                 },
                 {
                     titulo: '📦 Equipamentos em Estoque',
                     descricao: 'Visualiza equipamentos que não estão vinculados a salas.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="estoque-equipamentos.html"]'
                 },
                 {
                     titulo: '🔌 Linha 3: Gerenciamento de Cabos',
                     descricao: 'Agora vamos para a terceira linha - gerenciamento de cabos. Esta linha contém todas as funcionalidades relacionadas ao gerenciamento de cabos.',
                     acao: 'destacar',
                     seletor: 'div.flex.flex-row.gap-1:nth-of-type(3)'
                 },
                 {
                     titulo: '➕ Adicionar Cabo',
                     descricao: 'Cadastra um novo cabo no sistema com especificações técnicas.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="adicionar-cabo.html"]'
                 },
                 {
                     titulo: '✏️ Editar Cabo',
                     descricao: 'Modifica informações de um cabo existente.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="editar-cabo.html"]'
                 },
                 {
                     titulo: '🗑️ Excluir Cabo',
                     descricao: 'Remove um cabo do sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="excluir-cabo.html"]'
                 },
                 {
                     titulo: '👁️ Ver Cabos',
                     descricao: 'Lista todos os cabos cadastrados.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="ver-cabos.html"]'
                 },
                 {
                     titulo: '🔗 Conexões',
                     descricao: 'Gerencia as conexões entre cabos e equipamentos.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="conexoes-cabos.html"]'
                 },
                 {
                     titulo: '📦 Cabos em Estoque',
                     descricao: 'Visualiza cabos disponíveis para uso.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="cabos-estoque.html"]'
                 },
                 {
                     titulo: '🌐 Linha 4: Gerenciamento de Switches',
                     descricao: 'Agora vamos para a quarta linha - gerenciamento de switches. Esta linha contém todas as funcionalidades relacionadas ao gerenciamento de switches.',
                     acao: 'destacar',
                     seletor: 'div.flex.flex-row.gap-1:nth-of-type(4)'
                 },
                 {
                     titulo: '➕ Adicionar Switch',
                     descricao: 'Cadastra um novo switch no sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="adicionar-switch.html"]'
                 },
                 {
                     titulo: '✏️ Editar Switch',
                     descricao: 'Modifica configurações de um switch existente.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="editar-switch.html"]'
                 },
                 {
                     titulo: '🗑️ Excluir Switch',
                     descricao: 'Remove um switch do sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="excluir-switch.html"]'
                 },
                 {
                     titulo: '👁️ Ver Switches',
                     descricao: 'Lista todos os switches cadastrados.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="ver-switch.html"]'
                 },
                 {
                     titulo: '🔌 Gerenciar Portas Switch',
                     descricao: 'Gerencia as portas dos switches e suas conexões.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="gerenciar-portas-switch.html"]'
                 },
                 {
                     titulo: '🔧 Linha 5: Gerenciamento de Patch Panels',
                     descricao: 'Agora vamos para a quinta linha - gerenciamento de patch panels. Esta linha contém todas as funcionalidades relacionadas ao gerenciamento de patch panels.',
                     acao: 'destacar',
                     seletor: 'div.flex.flex-row.gap-1:nth-of-type(5)'
                 },
                 {
                     titulo: '➕ Adicionar Patch Panel',
                     descricao: 'Cadastra um novo patch panel no sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="adicionar-patch-panel.html"]'
                 },
                 {
                     titulo: '✏️ Editar Patch Panel',
                     descricao: 'Modifica configurações de um patch panel existente.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="editar-patch-panel.html"]'
                 },
                 {
                     titulo: '🗑️ Excluir Patch Panel',
                     descricao: 'Remove um patch panel do sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="excluir-patch-panel.html"]'
                 },
                 {
                     titulo: '👁️ Ver Patch Panels',
                     descricao: 'Lista todos os patch panels cadastrados.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="ver-patch-panel.html"]'
                 },
                 {
                     titulo: '🔌 Gerenciar Portas Patch Panel',
                     descricao: 'Gerencia as portas dos patch panels.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="gerenciar-portas-patch-panel.html"]'
                 },
                 {
                     titulo: '📊 Linha 6: Sistema e Relatórios',
                     descricao: 'Finalmente, vamos para a última linha - funcionalidades de sistema e relatórios. Esta linha contém funcionalidades de sistema e relatórios.',
                     acao: 'destacar',
                     seletor: 'div.flex.flex-row.gap-1:nth-of-type(6)'
                 },
                 {
                     titulo: '📈 Dashboard',
                     descricao: 'Visualiza estatísticas e gráficos do sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="dashboard.html"]'
                 },
                 {
                     titulo: '📋 Visualizar Logs',
                     descricao: 'Acessa o histórico de atividades do sistema.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="visualizar-logs.html"]'
                 },
                 {
                     titulo: '🔗 Conexões de Equipamentos',
                     descricao: 'Visualiza e gerencia conexões entre equipamentos.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="conexoes-equipamentos.html"]'
                 },
                 {
                     titulo: '📥 Exportar Dados',
                     descricao: 'Exporta dados do sistema em diferentes formatos.',
                     acao: 'destacar',
                     seletor: 'button[onclick*="exportar-dados.html"]'
                 },
                 {
                     titulo: '🚪 Sair',
                     descricao: 'Faz logout do sistema e retorna à tela de login.',
                     acao: 'destacar',
                     seletor: 'button[onclick="logout()"]'
                 },
                 {
                     titulo: '🎉 Tour Concluído!',
                     descricao: 'Parabéns! Você conheceu todas as funcionalidades do painel administrativo na ordem visual da tela. Agora pode usar o sistema com confiança!',
                     acao: 'mensagem'
                 }
             ],
                                     'adicionar-sala': [
                {
                    titulo: '🎯 Tour: Adicionar Nova Sala',
                    descricao: 'Bem-vindo ao formulário de cadastro de sala! Vou demonstrar como preencher todos os campos automaticamente.',
                    acao: 'mensagem'
                },
                {
                    titulo: '📝 Campo Nome da Sala',
                    descricao: 'Este é o campo obrigatório para o nome da sala. Vou preenchê-lo com "Sala de Reunião Principal".',
                    acao: 'preencher',
                    seletor: '#nome',
                    valor: 'Sala de Reunião Principal'
                },
                {
                    titulo: '📝 Campo Tipo da Sala',
                    descricao: 'Agora vou definir o tipo da sala como "Reunião".',
                    acao: 'preencher',
                    seletor: '#tipo',
                    valor: 'Reunião'
                },
                {
                    titulo: '📝 Campo Descrição',
                    descricao: 'Vou adicionar uma descrição detalhada da sala.',
                    acao: 'preencher',
                    seletor: '#descricao',
                    valor: 'Sala equipada para videoconferências e apresentações, com capacidade para 20 pessoas.'
                },
                {
                    titulo: '🖼️ Escolher Imagem da Sala',
                    descricao: 'Aqui você pode selecionar uma imagem já enviada para a sala. Se não houver imagens disponíveis, use o link de upload.',
                    acao: 'destacar',
                    seletor: '#fotoExistente'
                },
                {
                    titulo: '📤 Upload de Fotos',
                    descricao: 'Se não houver imagens disponíveis ou se a imagem desejada não estiver na lista, clique neste link para fazer upload de novas fotos.',
                    acao: 'destacar',
                    seletor: 'a[href="upload-fotos-salas.html"]'
                },
                {
                    titulo: '🏢 Selecionar Andar',
                    descricao: 'Vou selecionar o andar 1 para esta sala.',
                    acao: 'preencher',
                    seletor: '#andar_id',
                    valor: '1'
                },
                {
                    titulo: '🔧 Vincular Equipamentos',
                    descricao: 'Aqui você pode vincular equipamentos que estão em estoque. Marque os checkboxes dos equipamentos desejados.',
                    acao: 'destacar',
                    seletor: '#equipamentosSemSalaTabela'
                },
                {
                    titulo: '✅ Botão Cadastrar',
                    descricao: 'Após preencher todos os campos obrigatórios, clique aqui para salvar a sala no sistema.',
                    acao: 'destacar',
                    seletor: 'button[type="submit"]'
                },
                {
                    titulo: '🧹 Limpando Formulário',
                    descricao: 'Agora vou limpar todos os campos para que você possa preencher com seus próprios dados.',
                    acao: 'limpar_formulario'
                },
                {
                    titulo: '🎉 Tour Concluído!',
                    descricao: 'Parabéns! Agora você sabe como cadastrar uma nova sala. Todos os campos foram limpos e você pode começar a usar o formulário!',
                    acao: 'mensagem'
                }
            ],
             'criar-sala': [
                 {
                     titulo: '🎯 Tour: Criar Nova Sala',
                     descricao: 'Vamos demonstrar como criar uma nova sala no sistema. Clique em "Pular" para pular este passo ou "Parar" para sair do tour.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: 'Navegando para a página...',
                     descricao: 'Aguarde enquanto navegamos para a página de criação de sala.',
                     acao: 'navegar',
                     destino: 'adicionar-sala.html'
                 },
                 {
                     titulo: '📝 Campo Nome da Sala',
                     descricao: 'Este é o campo para o nome da sala. Vou preenchê-lo automaticamente com "Sala Demo Tour".',
                     acao: 'preencher',
                     seletor: '#nome',
                     valor: 'Sala Demo Tour'
                 },
                 {
                     titulo: '📝 Campo Tipo da Sala',
                     descricao: 'Agora vou preencher o tipo da sala com "Reunião".',
                     acao: 'preencher',
                     seletor: '#tipo',
                     valor: 'Reunião'
                 },
                 {
                     titulo: '📝 Campo Descrição',
                     descricao: 'Vou adicionar uma descrição para a sala.',
                     acao: 'preencher',
                     seletor: '#descricao',
                     valor: 'Sala criada durante demonstração do sistema'
                 },
                 {
                     titulo: '✅ Botão Cadastrar',
                     descricao: 'Agora vou clicar no botão "Cadastrar" para salvar a sala. Note que isso realmente criará a sala no sistema!',
                     acao: 'clicar',
                     seletor: 'button[type="submit"]'
                 },
                 {
                     titulo: '🎉 Tour Concluído!',
                     descricao: 'Parabéns! Você viu como criar uma sala no sistema. O tour foi concluído com sucesso.',
                     acao: 'mensagem'
                 }
             ],
                         'gerenciar-logo-empresa': [
                 {
                     titulo: '🎯 Tour: Gerenciar Logo da Empresa',
                     descricao: 'Bem-vindo! Vou mostrar como selecionar, enviar e visualizar o logo da empresa.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: '📁 Selecionar Logo',
                     descricao: 'Clique aqui para selecionar o arquivo de imagem que será usado como logo da empresa.',
                     acao: 'destacar',
                     seletor: '.file-input-wrapper'
                 },
                 {
                     titulo: '📤 Enviar Logo',
                     descricao: 'Após selecionar o arquivo, clique aqui para fazer o upload do logo para o sistema.',
                     acao: 'destacar',
                     seletor: 'button[type="submit"]'
                 },
                 {
                     titulo: '🖼️ Visualizar Logo',
                     descricao: 'Aqui você pode ver como o logo aparecerá no sistema após o upload.',
                     acao: 'destacar',
                     seletor: '#logoAtual'
                 },
                 {
                     titulo: '🎉 Tour Concluído!',
                     descricao: 'Pronto! Agora você sabe como gerenciar o logo da empresa.',
                     acao: 'mensagem'
                 }
             ],
             'upload-fotos-salas': [
                 {
                     titulo: '🎯 Tour: Upload de Fotos de Salas',
                     descricao: 'Bem-vindo! Vou mostrar como fazer upload e gerenciar imagens para as salas.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: '📁 Selecionar Imagem',
                     descricao: 'Clique aqui para selecionar uma imagem que será usada nas salas do sistema.',
                     acao: 'destacar',
                     seletor: '#inputFoto'
                 },
                 {
                     titulo: '📤 Enviar Imagem',
                     descricao: 'Após selecionar a imagem, clique aqui para fazer o upload para o sistema.',
                     acao: 'destacar',
                     seletor: 'button[type="submit"]'
                 },
                 {
                     titulo: '🖼️ Galeria de Imagens',
                     descricao: 'Aqui você pode ver todas as imagens já enviadas e gerenciá-las.',
                     acao: 'destacar',
                     seletor: '#galeriaImgs'
                 },
                 {
                     titulo: '🗑️ Excluir Imagens',
                     descricao: 'Cada imagem tem um botão X para excluí-la. Clique no X para remover a imagem.',
                     acao: 'destacar',
                     seletor: '#galeriaImgs'
                 },
                 {
                     titulo: '🎉 Tour Concluído!',
                     descricao: 'Pronto! Agora você sabe como fazer upload e gerenciar imagens das salas.',
                     acao: 'mensagem'
                 }
             ],
                                                                                   'editar-sala': [
                    {
                        titulo: '🎯 Tour: Editar Sala',
                        descricao: 'Bem-vindo! Vou mostrar como editar uma sala existente no sistema.',
                        acao: 'mensagem'
                    },
                    {
                        titulo: '📋 Verificando Salas Disponíveis',
                        descricao: 'Primeiro vou verificar se há salas cadastradas no sistema.',
                        acao: 'verificar_salas_simples'
                    }
               ],
                               'excluir-sala': [
                     {
                         titulo: '🎯 Tour: Excluir Sala',
                         descricao: 'Bem-vindo! Vou mostrar como excluir uma sala do sistema de forma segura.',
                         acao: 'mensagem'
                     },
                     {
                         titulo: '📋 Verificando Salas Disponíveis',
                         descricao: 'Primeiro vou verificar se há salas cadastradas no sistema.',
                         acao: 'verificar_salas_excluir'
                     }
                ],
                'ver-salas': [
                     {
                         titulo: '🎯 Tour: Visualizar Salas',
                         descricao: 'Bem-vindo! Vou mostrar como visualizar e gerenciar todas as salas do sistema.',
                         acao: 'mensagem'
                     },
                     {
                         titulo: '📋 Verificando Salas Disponíveis',
                         descricao: 'Primeiro vou verificar se há salas cadastradas no sistema.',
                         acao: 'verificar_salas_visualizar'
                     }
                ],
             'completo': [
                 {
                     titulo: '🎯 Bem-vindo ao Sistema',
                     descricao: 'Vamos fazer um tour completo do sistema. Use os controles no canto superior direito para pausar, pular ou parar o tour.',
                     acao: 'mensagem'
                 }
             ]
        };
        
        return passos[tipo] || passos['completo'];
    }
    
         executarPasso() {
         if (!this.ativo || this.passoAtual >= this.passos.length) {
             this.finalizar();
             return;
         }
         
         const passo = this.passos[this.passoAtual];
         
         // Aguardar um pouco antes de executar o passo
         setTimeout(() => {
                                         let aguardarPreenchimento = false;
              
                             switch (passo.acao) {
                   case 'navegar':
                       this.navegarPara(passo.destino);
                       break;
                   case 'preencher':
                       aguardarPreenchimento = this.preencherCampo(passo.seletor, passo.valor);
                       break;
                   case 'clicar':
                       this.clicarElemento(passo.seletor);
                       break;
                   case 'destacar':
                       this.destacarElemento(passo.seletor);
                       break;
                   case 'mensagem':
                       this.mostrarMensagem(passo.titulo, passo.descricao);
                       break;
                   case 'verificar_imagens':
                       this.verificarImagensDisponiveis();
                       break;
                   case 'limpar_formulario':
                       this.limparFormulario();
                       break;
                   case 'clicar_primeira_sala':
                       this.clicarPrimeiraSala();
                       break;
                                       case 'clicar_cancelar':
                        this.clicarCancelar();
                        break;


                   case 'verificar_salas':
                       this.verificarSalasDisponiveis();
                       break;
                                       case 'verificar_salas_simples':
                        this.verificarSalasSimples();
                        break;
                    case 'verificar_salas_excluir':
                        this.verificarSalasExcluir();
                        break;
                    case 'verificar_salas_visualizar':
                        this.verificarSalasVisualizar();
                        break;
               }
              
              this.mostrarTooltip(passo.titulo, passo.descricao);
              this.atualizarProgresso();
              
              // Auto-avançar após um tempo (exceto se estiver preenchendo)
              if (passo.acao !== 'navegar' && !aguardarPreenchimento) {
                  this.intervalo = setTimeout(() => {
                      this.proximoPasso();
                  }, this.config.duracaoPasso);
              }
         }, 2000);
     }
    
    navegarPara(pagina) {
        // Salvar o próximo passo antes de navegar
        sessionStorage.setItem('tourPasso', (this.passoAtual + 1).toString());
        
        // Aguardar um pouco antes de navegar para mostrar o tooltip
        setTimeout(() => {
            window.location.href = pagina;
        }, 2000);
    }
    
         preencherCampo(seletor, valor) {
         const elemento = document.querySelector(seletor);
         if (elemento) {
             this.highlightElemento(elemento);
             
             // Simular digitação
             elemento.focus();
             elemento.value = '';
             
             let i = 0;
             const typeInterval = setInterval(() => {
                 if (i < valor.length) {
                     elemento.value += valor[i];
                     elemento.dispatchEvent(new Event('input', { bubbles: true }));
                     i++;
                 } else {
                     clearInterval(typeInterval);
                     // Aguardar um pouco após terminar de preencher antes de continuar
                     setTimeout(() => {
                         if (this.ativo) {
                             this.proximoPasso();
                         }
                     }, 2000);
                 }
             }, 150);
             
             // Não auto-avançar neste passo, aguardar o preenchimento terminar
             return true;
         }
         return false;
     }
    
    clicarElemento(seletor) {
        const elemento = document.querySelector(seletor);
        if (elemento) {
            this.highlightElemento(elemento);
            setTimeout(() => {
                elemento.click();
            }, 4000);
        }
    }
    
    destacarElemento(seletor) {
        const elemento = document.querySelector(seletor);
        if (elemento) {
            this.highlightElemento(elemento);
        }
    }
    
         mostrarMensagem(titulo, descricao) {
         this.mostrarTooltip(titulo, descricao);
     }
     
           verificarImagensDisponiveis() {
          const selectImagens = document.getElementById('fotoExistente');
          if (selectImagens) {
              const opcoes = selectImagens.options;
              const temImagens = opcoes.length > 1; // Mais de 1 porque sempre tem a opção "Nenhuma"
              
              if (temImagens) {
                  this.mostrarTooltip('🖼️ Imagens Disponíveis', 'Ótimo! Há imagens disponíveis para seleção. Você pode escolher uma delas para a sala.');
              } else {
                  this.mostrarTooltip('📤 Nenhuma Imagem Disponível', 'Não há imagens disponíveis. Clique no link "Upload Fotos" para fazer upload de novas imagens.');
              }
          }
      }
      
             limparFormulario() {
           // Limpar todos os campos do formulário
           const campos = ['#nome', '#tipo', '#descricao', '#andar_id', '#fotoExistente'];
           campos.forEach(seletor => {
               const campo = document.querySelector(seletor);
               if (campo) {
                   campo.value = '';
                   campo.dispatchEvent(new Event('input', { bubbles: true }));
               }
           });
           
           // Limpar preview de imagem
           const preview = document.getElementById('foto-preview-container');
           if (preview) {
               preview.innerHTML = "<span style='color:#aaa;'>Sem foto cadastrada</span>";
           }
           
           // Desmarcar todos os checkboxes de equipamentos
           const checkboxes = document.querySelectorAll('.equipamento-checkbox');
           checkboxes.forEach(checkbox => {
               checkbox.checked = false;
           });
       }
       
               clicarPrimeiraSala() {
            // Aguardar um pouco para garantir que as salas foram carregadas
            setTimeout(() => {
                const primeiraSala = document.querySelector('.card-sala-editar');
                if (primeiraSala) {
                    this.highlightElemento(primeiraSala);
                    setTimeout(() => {
                        primeiraSala.click();
                    }, 4000);
                } else {
                    // Se não há salas disponíveis, mostrar mensagem e pular para o próximo passo
                    this.mostrarTooltip('📋 Nenhuma Sala Disponível', 'Não há salas cadastradas no sistema. Primeiro você precisa criar algumas salas usando a funcionalidade "Adicionar Sala".');
                    setTimeout(() => {
                        if (this.ativo) {
                            this.proximoPasso();
                        }
                    }, 5000);
                }
            }, 2000);
        }
       
                               clicarCancelar() {
             const botaoCancelar = document.querySelector('button[onclick="cancelarEdicao()"]');
             if (botaoCancelar) {
                 this.highlightElemento(botaoCancelar);
                 setTimeout(() => {
                     botaoCancelar.click();
                 }, 4000);
             } else {
                 // Se o botão cancelar não está disponível, mostrar mensagem e pular para o próximo passo
                 this.mostrarTooltip('ℹ️ Formulário Não Aberto', 'O formulário de edição não está aberto, então não há necessidade de cancelar. Vamos continuar com o tour.');
                 setTimeout(() => {
                     if (this.ativo) {
                         this.proximoPasso();
                     }
                 }, 5000);
             }
         }
         
                   
         
         
       
                               verificarSalasDisponiveis() {
             setTimeout(() => {
                 const salas = document.querySelectorAll('.card-sala-editar');
                 if (salas.length === 0) {
                     this.mostrarTooltip('📋 Nenhuma Sala Disponível', 'Não há salas cadastradas no sistema. Para usar esta funcionalidade, primeiro crie algumas salas usando "Adicionar Sala".');
                     // Pular os passos que dependem de salas existentes
                     setTimeout(() => {
                         if (this.ativo) {
                             // Pular para o passo final
                             this.passoAtual = this.passos.length - 2; // Penúltimo passo
                             this.proximoPasso();
                         }
                     }, 6000);
                 } else {
                     this.mostrarTooltip('📋 Salas Disponíveis', `Encontradas ${salas.length} sala(s) disponível(is) para edição. Vamos continuar com o tour.`);
                     setTimeout(() => {
                         if (this.ativo) {
                             this.proximoPasso();
                         }
                     }, 4000);
                 }
             }, 2000);
         }
        
                                   verificarSalasSimples() {
              setTimeout(() => {
                  const salas = document.querySelectorAll('.card-sala-editar');
                  if (salas.length === 0) {
                      // Tour para quando não há salas
                      this.executarTourSemSalas();
                  } else {
                      // Tour para quando há salas
                      this.executarTourComSalas();
                  }
              }, 2000);
          }
          
                     verificarSalasExcluir() {
               setTimeout(() => {
                   const salas = document.querySelectorAll('.bg-gray-100.dark\\:bg-gray-800');
                   if (salas.length === 0) {
                       // Tour para quando não há salas
                       this.executarTourExcluirSemSalas();
                   } else {
                       // Tour para quando há salas
                       this.executarTourExcluirComSalas();
                   }
               }, 2000);
           }
           
           verificarSalasVisualizar() {
               setTimeout(() => {
                   const salas = document.querySelectorAll('.bg-gray-100.dark\\:bg-gray-800');
                   if (salas.length === 0) {
                       // Tour para quando não há salas
                       this.executarTourVisualizarSemSalas();
                   } else {
                       // Tour para quando há salas
                       this.executarTourVisualizarComSalas();
                   }
               }, 2000);
           }
        
        executarTourSemSalas() {
            const passosSemSalas = [
                {
                    titulo: '📋 Nenhuma Sala Disponível',
                    descricao: 'Não há salas cadastradas no sistema para editar.',
                    acao: 'mensagem'
                },
                {
                    titulo: '🔍 Campo de Busca',
                    descricao: 'Este campo permite buscar salas por nome, tipo ou descrição quando houver salas cadastradas.',
                    acao: 'destacar',
                    seletor: '#filtroSala'
                },
                {
                    titulo: '🏷️ Filtros por Tipo',
                    descricao: 'Estes botões permitem filtrar salas por tipo: Todas, Reunião, Escritório ou Outro.',
                    acao: 'destacar',
                    seletor: '.mb-6.flex.flex-wrap.gap-4.justify-center'
                },
                {
                    titulo: '📋 Área de Listagem',
                    descricao: 'Aqui aparecerão as salas quando forem cadastradas. Para começar, use "Adicionar Sala" no painel administrativo.',
                    acao: 'destacar',
                    seletor: '#salas-cards-container'
                },
                {
                    titulo: '➕ Próximo Passo',
                    descricao: 'Para usar esta funcionalidade, primeiro crie algumas salas usando o botão "Adicionar Sala" no painel administrativo.',
                    acao: 'mensagem'
                },
                {
                    titulo: '🎉 Tour Concluído!',
                    descricao: 'Agora você entende como funciona a edição de salas. Quando houver salas cadastradas, você poderá editá-las aqui.',
                    acao: 'mensagem'
                }
            ];
            
            // Substituir os passos atuais pelos passos sem salas
            this.passos = passosSemSalas;
            this.passoAtual = 0;
            this.executarPasso();
        }
        
        executarTourComSalas() {
            const passosComSalas = [
                {
                    titulo: '📋 Salas Disponíveis',
                    descricao: `Encontradas ${document.querySelectorAll('.card-sala-editar').length} sala(s) para editar. Vou demonstrar o processo.`,
                    acao: 'mensagem'
                },
                {
                    titulo: '🔍 Buscar Sala',
                    descricao: 'Use este campo para buscar uma sala específica pelo nome, tipo ou descrição.',
                    acao: 'destacar',
                    seletor: '#filtroSala'
                },
                {
                    titulo: '🏷️ Filtros por Tipo',
                    descricao: 'Use estes botões para filtrar salas por tipo: Todas, Reunião, Escritório ou Outro.',
                    acao: 'destacar',
                    seletor: '.mb-6.flex.flex-wrap.gap-4.justify-center'
                },
                {
                    titulo: '📋 Lista de Salas',
                    descricao: 'Aqui você vê todas as salas disponíveis. Clique em uma sala para editá-la.',
                    acao: 'destacar',
                    seletor: '#salas-cards-container'
                },
                {
                    titulo: '🖱️ Selecionando Sala',
                    descricao: 'Vou clicar na primeira sala para mostrar o formulário de edição.',
                    acao: 'clicar_primeira_sala'
                },
                {
                    titulo: '✏️ Formulário de Edição',
                    descricao: 'O formulário de edição apareceu! Aqui você pode modificar todos os dados da sala.',
                    acao: 'destacar',
                    seletor: '#formEditarSala'
                },
                {
                    titulo: '💾 Salvar Alterações',
                    descricao: 'Após fazer as alterações, clique aqui para salvar as modificações na sala.',
                    acao: 'destacar',
                    seletor: 'button[type="submit"]'
                },
                {
                    titulo: '❌ Cancelar Edição',
                    descricao: 'Se quiser cancelar as alterações, clique aqui para voltar à lista de salas.',
                    acao: 'destacar',
                    seletor: 'button[onclick="cancelarEdicao()"]'
                },
                {
                    titulo: '🔄 Voltando à Lista',
                    descricao: 'Vou cancelar a edição para demonstrar como voltar à lista de salas.',
                    acao: 'clicar_cancelar'
                },
                {
                    titulo: '🎉 Tour Concluído!',
                    descricao: 'Pronto! Agora você sabe como editar salas no sistema.',
                    acao: 'mensagem'
                }
            ];
            
                         // Substituir os passos atuais pelos passos com salas
             this.passos = passosComSalas;
             this.passoAtual = 0;
             this.executarPasso();
         }
         
         executarTourExcluirSemSalas() {
             const passosSemSalas = [
                 {
                     titulo: '📋 Nenhuma Sala Disponível',
                     descricao: 'Não há salas cadastradas no sistema para excluir.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: '🔍 Campo de Busca',
                     descricao: 'Este campo permite buscar salas por nome, tipo, descrição ou andar quando houver salas cadastradas.',
                     acao: 'destacar',
                     seletor: '#filtroSala'
                 },
                 {
                     titulo: '🏷️ Filtros por Tipo',
                     descricao: 'Estes botões permitem filtrar salas por tipo: Total, Reunião, Escritório ou Outro.',
                     acao: 'destacar',
                     seletor: '#resumoSalas'
                 },
                 {
                     titulo: '📋 Área de Listagem',
                     descricao: 'Aqui aparecerão as salas quando forem cadastradas. Para começar, use "Adicionar Sala" no painel administrativo.',
                     acao: 'destacar',
                     seletor: '#cardsSalasContainer'
                 },
                 {
                     titulo: '⚠️ Importante',
                     descricao: 'A exclusão de salas é uma ação irreversível. Sempre confirme antes de excluir.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: '🎉 Tour Concluído!',
                     descricao: 'Agora você entende como funciona a exclusão de salas. Quando houver salas cadastradas, você poderá excluí-las aqui.',
                     acao: 'mensagem'
                 }
             ];
             
             // Substituir os passos atuais pelos passos sem salas
             this.passos = passosSemSalas;
             this.passoAtual = 0;
             this.executarPasso();
         }
         
         executarTourExcluirComSalas() {
             const passosComSalas = [
                 {
                     titulo: '📋 Salas Disponíveis',
                     descricao: `Encontradas ${document.querySelectorAll('.bg-gray-100.dark\\:bg-gray-800').length} sala(s) para excluir. Vou mostrar como funciona.`,
                     acao: 'mensagem'
                 },
                 {
                     titulo: '🔍 Campo de Busca',
                     descricao: 'Use este campo para buscar uma sala específica pelo nome, tipo, descrição ou andar.',
                     acao: 'destacar',
                     seletor: '#filtroSala'
                 },
                 {
                     titulo: '🏷️ Filtros por Tipo',
                     descricao: 'Use estes botões para filtrar salas por tipo: Total, Reunião, Escritório ou Outro.',
                     acao: 'destacar',
                     seletor: '#resumoSalas'
                 },
                 {
                     titulo: '📋 Lista de Salas',
                     descricao: 'Aqui você vê todas as salas disponíveis. Cada sala tem um botão "Excluir" para removê-la.',
                     acao: 'destacar',
                     seletor: '#cardsSalasContainer'
                 },
                 {
                     titulo: '🗑️ Botão Excluir',
                     descricao: 'Cada sala tem um botão "Excluir". Clique nele para iniciar o processo de exclusão.',
                     acao: 'destacar',
                     seletor: '.bg-gray-100.dark\\:bg-gray-800 button[onclick*="excluirSala"]'
                 },
                 {
                     titulo: '⚠️ Importante',
                     descricao: 'A exclusão de salas é uma ação irreversível. O sistema sempre pedirá confirmação antes de excluir.',
                     acao: 'mensagem'
                 },
                 {
                     titulo: '🎉 Tour Concluído!',
                     descricao: 'Pronto! Agora você sabe como excluir salas no sistema de forma segura.',
                     acao: 'mensagem'
                 }
             ];
             
                           // Substituir os passos atuais pelos passos com salas
              this.passos = passosComSalas;
              this.passoAtual = 0;
              this.executarPasso();
          }
          
          executarTourVisualizarSemSalas() {
              const passosSemSalas = [
                  {
                      titulo: '📋 Nenhuma Sala Disponível',
                      descricao: 'Não há salas cadastradas no sistema para visualizar.',
                      acao: 'mensagem'
                  },
                  {
                      titulo: '🔍 Campo de Busca',
                      descricao: 'Este campo permite buscar salas por nome, tipo, descrição ou andar quando houver salas cadastradas.',
                      acao: 'destacar',
                      seletor: '#filtroSala'
                  },
                  {
                      titulo: '🏷️ Filtros por Tipo',
                      descricao: 'Estes botões permitem filtrar salas por tipo: Total, Reunião, Escritório ou Outro.',
                      acao: 'destacar',
                      seletor: '#resumoSalas'
                  },
                  {
                      titulo: '📋 Área de Listagem',
                      descricao: 'Aqui aparecerão as salas quando forem cadastradas. Cada sala terá botões para ver detalhes e mostrar equipamentos vinculados.',
                      acao: 'destacar',
                      seletor: '#cardsSalasContainer'
                  },
                                     {
                       titulo: '➕ Adicionar Sala (Admin)',
                       descricao: 'Se você for administrador, aqui aparecerá um card para adicionar novas salas. Vou demonstrar como funciona.',
                       acao: 'destacar',
                       seletor: '.bg-gradient-to-br.from-green-400'
                   },
                   {
                       titulo: '🖱️ Clicando no Card Adicionar Sala',
                       descricao: 'Vou clicar no card para abrir o modal de adicionar sala.',
                       acao: 'clicar',
                       seletor: '.bg-gradient-to-br.from-green-400'
                   },
                   {
                       titulo: '📋 Modal Adicionar Sala',
                       descricao: 'Este modal tem exatamente a mesma funcionalidade do botão "Adicionar Sala" da tela config-admin. Permite criar uma nova sala com todos os dados.',
                       acao: 'destacar',
                       seletor: '#modalAddSala'
                   },
                   {
                       titulo: '❌ Fechando o Modal',
                       descricao: 'Vou fechar o modal para demonstrar como voltar à visualização das salas.',
                       acao: 'clicar',
                       seletor: '#addSala-fechar'
                   },
                  {
                      titulo: '⚠️ Importante',
                      descricao: 'Para usar esta funcionalidade, primeiro crie algumas salas usando "Adicionar Sala" no painel administrativo.',
                      acao: 'mensagem'
                  },
                  {
                      titulo: '🎉 Tour Concluído!',
                      descricao: 'Agora você entende como funciona a visualização de salas. Quando houver salas cadastradas, você poderá visualizá-las aqui.',
                      acao: 'mensagem'
                  }
              ];
              
              // Substituir os passos atuais pelos passos sem salas
              this.passos = passosSemSalas;
              this.passoAtual = 0;
              this.executarPasso();
          }
          
          executarTourVisualizarComSalas() {
              const passosComSalas = [
                  {
                      titulo: '📋 Salas Disponíveis',
                      descricao: `Encontradas ${document.querySelectorAll('.bg-gray-100.dark\\:bg-gray-800').length} sala(s) para visualizar. Vou mostrar como funciona.`,
                      acao: 'mensagem'
                  },
                  {
                      titulo: '🔍 Campo de Busca',
                      descricao: 'Use este campo para buscar uma sala específica pelo nome, tipo, descrição ou andar.',
                      acao: 'destacar',
                      seletor: '#filtroSala'
                  },
                  {
                      titulo: '🏷️ Filtros por Tipo',
                      descricao: 'Use estes botões para filtrar salas por tipo: Total, Reunião, Escritório ou Outro.',
                      acao: 'destacar',
                      seletor: '#resumoSalas'
                  },
                  {
                      titulo: '📋 Lista de Salas',
                      descricao: 'Aqui você vê todas as salas disponíveis. Cada sala mostra suas informações básicas.',
                      acao: 'destacar',
                      seletor: '#cardsSalasContainer'
                  },
                  {
                      titulo: '👁️ Botão Ver Detalhes',
                      descricao: 'Clique aqui para ver informações detalhadas de uma sala específica.',
                      acao: 'destacar',
                      seletor: 'button[onclick*="detalhes-sala.html"]'
                  },
                                     {
                       titulo: '🔌 Botão Mostrar Equipamentos',
                       descricao: 'Clique aqui para ver os equipamentos vinculados a esta sala.',
                       acao: 'destacar',
                       seletor: '.btn-equipamentos'
                   },
                   {
                       titulo: '🖱️ Clicando em Mostrar Equipamentos',
                       descricao: 'Vou clicar no botão para demonstrar como visualizar os equipamentos da sala.',
                       acao: 'clicar',
                       seletor: '.btn-equipamentos'
                   },
                   {
                       titulo: '📋 Lista de Equipamentos',
                       descricao: 'Aqui aparecem todos os equipamentos vinculados à sala. Você pode ver o status de cada um (funcionando ou com defeito).',
                       acao: 'destacar',
                       seletor: '.flex.flex-col.gap-2.mt-2'
                   },
                                     {
                       titulo: '➕ Adicionar Sala (Admin)',
                       descricao: 'Se você for administrador, aqui aparecerá um card para adicionar novas salas diretamente. Vou demonstrar como funciona.',
                       acao: 'destacar',
                       seletor: '.bg-gradient-to-br.from-green-400'
                   },
                   {
                       titulo: '🖱️ Clicando no Card Adicionar Sala',
                       descricao: 'Vou clicar no card para abrir o modal de adicionar sala.',
                       acao: 'clicar',
                       seletor: '.bg-gradient-to-br.from-green-400'
                   },
                   {
                       titulo: '📋 Modal Adicionar Sala',
                       descricao: 'Este modal tem exatamente a mesma funcionalidade do botão "Adicionar Sala" da tela config-admin. Permite criar uma nova sala com todos os dados.',
                       acao: 'destacar',
                       seletor: '#modalAddSala'
                   },
                   {
                       titulo: '❌ Fechando o Modal',
                       descricao: 'Vou fechar o modal para demonstrar como voltar à visualização das salas.',
                       acao: 'clicar',
                       seletor: '#addSala-fechar'
                   },
                  {
                      titulo: '🎉 Tour Concluído!',
                      descricao: 'Pronto! Agora você sabe como visualizar e gerenciar salas no sistema.',
                      acao: 'mensagem'
                  }
              ];
              
              // Substituir os passos atuais pelos passos com salas
              this.passos = passosComSalas;
              this.passoAtual = 0;
              this.executarPasso();
          }
    
    highlightElemento(elemento) {
        if (this.elementoAtual) {
            this.elementoAtual.style.outline = '';
            this.elementoAtual.style.outlineOffset = '';
            this.elementoAtual.style.transform = '';
            this.elementoAtual.style.zIndex = '';
        }
        
        this.elementoAtual = elemento;
        elemento.style.outline = `4px solid ${this.config.corHighlight}`;
        elemento.style.outlineOffset = '3px';
        elemento.style.transform = 'scale(1.05)';
        elemento.style.zIndex = '1000';
        elemento.style.transition = 'all 0.3s ease';
        elemento.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
         mostrarTooltip(titulo, descricao) {
         const tooltip = document.getElementById('tour-tooltip');
         const tituloEl = tooltip.querySelector('.tour-tooltip-title');
         const descricaoEl = tooltip.querySelector('.tour-tooltip-description');
         
         tituloEl.textContent = titulo;
         descricaoEl.textContent = descricao;
         
         tooltip.classList.remove('hidden');
         
                   // Posicionar tooltip ao lado do elemento se houver elemento específico
          if (this.elementoAtual) {
              const rect = this.elementoAtual.getBoundingClientRect();
              const tooltipWidth = tooltip.offsetWidth;
              const tooltipHeight = tooltip.offsetHeight;
              const windowWidth = window.innerWidth;
              const windowHeight = window.innerHeight;
              
              // Remover classes anteriores
              tooltip.classList.remove('tooltip-above', 'tooltip-below', 'tooltip-left', 'tooltip-right');
              
              // Verificar se o elemento está visível na tela
              const isElementVisible = rect.top >= 0 && rect.bottom <= windowHeight && rect.left >= 0 && rect.right <= windowWidth;
              
              if (!isElementVisible) {
                  // Se o elemento não está visível, posicionar no centro da tela
                  tooltip.style.top = '50%';
                  tooltip.style.left = '50%';
                  tooltip.style.transform = 'translate(-50%, -50%)';
                  return;
              }
              
              // Verificar se há espaço suficiente à direita
              if (rect.right + tooltipWidth + 20 < windowWidth) {
                  // Posicionar à direita do elemento
                  tooltip.style.top = `${rect.top + (rect.height / 2) - (tooltipHeight / 2)}px`;
                  tooltip.style.left = `${rect.right + 15}px`;
                  tooltip.style.transform = 'none';
                  tooltip.classList.add('tooltip-right');
              } else if (rect.left - tooltipWidth - 20 > 0) {
                  // Posicionar à esquerda do elemento
                  tooltip.style.top = `${rect.top + (rect.height / 2) - (tooltipHeight / 2)}px`;
                  tooltip.style.left = `${rect.left - tooltipWidth - 15}px`;
                  tooltip.style.transform = 'none';
                  tooltip.classList.add('tooltip-left');
              } else if (rect.top > tooltipHeight + 20) {
                  // Posicionar em cima do elemento
                  tooltip.style.top = `${rect.top - 15}px`;
                  tooltip.style.left = `${rect.left}px`;
                  tooltip.style.transform = 'translateY(-100%)';
                  tooltip.classList.add('tooltip-above');
              } else {
                  // Posicionar embaixo do elemento
                  tooltip.style.top = `${rect.bottom + 15}px`;
                  tooltip.style.left = `${rect.left}px`;
                  tooltip.style.transform = 'none';
                  tooltip.classList.add('tooltip-below');
              }
              
              // Garantir que o tooltip não saia da tela
              const tooltipRect = tooltip.getBoundingClientRect();
              if (tooltipRect.right > windowWidth) {
                  tooltip.style.left = `${windowWidth - tooltipWidth - 10}px`;
              }
              if (tooltipRect.left < 0) {
                  tooltip.style.left = '10px';
              }
              if (tooltipRect.bottom > windowHeight) {
                  tooltip.style.top = `${windowHeight - tooltipHeight - 10}px`;
              }
              if (tooltipRect.top < 0) {
                  tooltip.style.top = '10px';
              }
          } else {
              // Posicionar no centro da tela
              tooltip.style.top = '50%';
              tooltip.style.left = '50%';
              tooltip.style.transform = 'translate(-50%, -50%)';
          }
     }
    
    atualizarProgresso() {
        const progresso = document.querySelector('.tour-tooltip-progress');
        const percentual = ((this.passoAtual + 1) / this.passos.length) * 100;
        progresso.innerHTML = `${this.passoAtual + 1} de ${this.passos.length}`;
    }
    
    proximoPasso() {
        this.passoAtual++;
        this.executarPasso();
    }
    
    passoAnterior() {
        if (this.passoAtual > 0) {
            this.passoAtual--;
            this.executarPasso();
        }
    }
    
    pausar() {
        if (this.intervalo) {
            clearTimeout(this.intervalo);
            this.intervalo = null;
        }
    }
    
    continuar() {
        if (this.ativo && !this.intervalo) {
            this.intervalo = setTimeout(() => {
                this.proximoPasso();
            }, this.config.duracaoPasso);
        }
    }
    

    
         parar() {
         this.ativo = false;
         this.passoAtual = 0;
         
         // Limpar estado do tour
         sessionStorage.removeItem('tourAtivo');
         sessionStorage.removeItem('tourTipo');
         sessionStorage.removeItem('tourPasso');
         
         if (this.intervalo) {
             clearTimeout(this.intervalo);
             this.intervalo = null;
         }
         
         if (this.elementoAtual) {
             this.elementoAtual.style.outline = '';
             this.elementoAtual.style.outlineOffset = '';
             this.elementoAtual.style.transform = '';
             this.elementoAtual.style.zIndex = '';
             this.elementoAtual.style.transition = '';
             this.elementoAtual = null;
         }
         
         document.getElementById('tour-tooltip').classList.add('hidden');
         document.getElementById('tour-controles').classList.add('hidden');
         document.getElementById('tour-overlay').classList.remove('active');
         document.getElementById('tour-overlay').style.pointerEvents = 'none';
         
         // Se estiver na página de adicionar sala, limpar o formulário
         if (window.location.pathname.includes('adicionar-sala.html') || 
             window.location.pathname.includes('adicionar-sala')) {
             this.limparFormulario();
         }
     }
    
    finalizar() {
        this.parar();
        
        // Mostrar mensagem de conclusão mais elegante
        const mensagem = document.createElement('div');
        mensagem.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            z-index: 10003;
            text-align: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            animation: tourFadeIn 0.3s ease-in-out;
        `;
        mensagem.innerHTML = `
            <div style="font-size: 24px; margin-bottom: 10px;">🎉</div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">Tour Concluído!</div>
            <div style="font-size: 14px;">Obrigado por conhecer o sistema.</div>
        `;
        
        document.body.appendChild(mensagem);
        
        setTimeout(() => {
            mensagem.remove();
        }, 3000);
    }
}

// Inicializar o sistema de tour quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.sistemaTour = new SistemaTour();
    
    // Verificar se há um tour em andamento
    if (sessionStorage.getItem('tourAtivo') === 'true') {
        const tourTipo = sessionStorage.getItem('tourTipo');
        const tourPasso = parseInt(sessionStorage.getItem('tourPasso') || '0');
        
        setTimeout(() => {
            window.sistemaTour.continuarTour(tourTipo, tourPasso);
        }, 1000);
    }
});
