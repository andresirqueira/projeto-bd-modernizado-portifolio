// Logo Manager - Gerencia logos da empresa e marcas com fundo condicional
class LogoManager {
    constructor() {
        this.init();
    }

    init() {
        // Atualizar logos quando o tema mudar
        this.updateAllLogos();
        
        // Observar mudanças no tema
        this.observeThemeChanges();
    }

    updateAllLogos() {
        this.updateEmpresaLogo();
        this.updateMarcaLogos();
    }

    updateEmpresaLogo() {
        const empresaDiv = document.getElementById('empresa-logada');
        if (empresaDiv && empresaDiv.querySelector('img')) {
            const isDark = document.documentElement.classList.contains('dark');
            const bgClass = isDark ? 'dark:bg-transparent' : 'bg-gray-800';
            empresaDiv.className = `absolute top-4 right-4 text-indigo-500 font-bold ${bgClass} rounded-lg p-2`;
        }
    }

    updateMarcaLogos() {
        // Atualizar todos os logos de marcas na página
        const marcaLogos = document.querySelectorAll('[data-marca-logo]');
        marcaLogos.forEach(logo => {
            const isDark = document.documentElement.classList.contains('dark');
            const bgClass = isDark ? 'dark:bg-gray-700' : 'bg-gray-800';
            logo.className = `absolute top-2 left-2 w-8 h-8 ${bgClass} rounded-lg flex items-center justify-center shadow-md`;
        });
    }

    observeThemeChanges() {
        // Observar mudanças no atributo class do html
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    this.updateAllLogos();
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class']
        });
    }

    // Função para renderizar logo de marca com fundo condicional
    static renderMarcaLogo(marca) {
        if (!marca) return '';
        
        const isDark = document.documentElement.classList.contains('dark');
        const bgClass = isDark ? 'dark:bg-gray-700' : 'bg-gray-800';
        
        return `<div class='absolute top-2 left-2 w-8 h-8 ${bgClass} rounded-lg flex items-center justify-center shadow-md' data-marca-logo>
                    <img src='static/img/${marca.toLowerCase()}.png' 
                         onerror="this.style.display='none'" 
                         alt='${marca}' 
                         title='${marca}' 
                         class='max-w-full max-h-full object-contain'>
                </div>`;
    }

    // Função para carregar logo da empresa com fundo condicional
    static loadEmpresaLogo(data) {
        const empresaDiv = document.getElementById('empresa-logada');
        if (!empresaDiv) return;

        if (data.logo) {
            const isDark = document.documentElement.classList.contains('dark');
            const bgClass = isDark ? 'dark:bg-transparent' : 'bg-gray-800';
            empresaDiv.className = `absolute top-4 right-4 text-indigo-500 font-bold ${bgClass} rounded-lg p-2`;
            empresaDiv.innerHTML = `<img src="${data.logo}" alt="Logo da empresa" style="max-height:40px;max-width:120px;object-fit:contain;">`;
        } else if (data.nome) {
            empresaDiv.innerText = 'Empresa: ' + data.nome;
        }
    }
}

// Inicializar o Logo Manager quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.logoManager = new LogoManager();
});

// Função global para atualizar logos (usada pelo toggleDarkMode)
function updateEmpresaLogo() {
    if (window.logoManager) {
        window.logoManager.updateAllLogos();
    }
} 