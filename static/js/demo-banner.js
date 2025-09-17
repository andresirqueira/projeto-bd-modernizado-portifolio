// Script para adicionar banner de demonstração em todas as páginas
(function() {
  'use strict';
  
  console.log('🚧 Iniciando script demo-banner.js');
  
  // Função para adicionar o banner
  function addBanner() {
    // Verificar se o banner já existe
    if (document.querySelector('.demo-banner')) {
      console.log('🚧 Banner já existe, saindo');
      return;
    }
    
    console.log('🚧 Criando banner...');
    
    // Criar o banner
    const banner = document.createElement('div');
    banner.className = 'demo-banner';
    banner.innerHTML = `
      <span class="demo-icon">🚧</span>
      VERSÃO DE DEMONSTRAÇÃO - SISTEMA EM DESENVOLVIMENTO
      <span class="demo-icon">🚧</span>
    `;
    
    // Adicionar CSS se não existir
    if (!document.querySelector('#demo-banner-css')) {
      console.log('🚧 Adicionando CSS...');
      const link = document.createElement('link');
      link.id = 'demo-banner-css';
      link.rel = 'stylesheet';
      link.href = 'static/css/demo-banner.css';
      document.head.appendChild(link);
    }
    
    // Adicionar o banner no final do body (rodapé)
    if (document.body) {
      document.body.appendChild(banner);
      document.body.style.paddingBottom = '40px';
      console.log('🚧 Banner adicionado no rodapé com sucesso!');
    } else {
      console.log('🚧 Body não encontrado, tentando novamente em 100ms...');
      setTimeout(addBanner, 100);
    }
  }
  
  // Executar quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addBanner);
  } else {
    addBanner();
  }
})();
