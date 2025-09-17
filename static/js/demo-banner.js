// Script para adicionar banner de demonstração em todas as páginas
(function() {
  'use strict';
  
  // Verificar se o banner já existe
  if (document.querySelector('.demo-banner')) {
    return;
  }
  
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
    const link = document.createElement('link');
    link.id = 'demo-banner-css';
    link.rel = 'stylesheet';
    link.href = 'static/css/demo-banner.css';
    document.head.appendChild(link);
  }
  
  // Adicionar o banner no início do body
  document.body.insertBefore(banner, document.body.firstChild);
  
  // Ajustar padding do body
  document.body.style.paddingTop = '40px';
  
  console.log('🚧 Banner de demonstração adicionado');
})();
