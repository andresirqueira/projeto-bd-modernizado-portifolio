-- Script para criar banco PostgreSQL unificado
-- Execute este script no seu cliente PostgreSQL conectado ao Render

-- 1. TABELA USUARIOS
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    nome VARCHAR(255),
    nivel VARCHAR(50) DEFAULT 'usuario'
);

-- 2. TABELA ANDARES
CREATE TABLE IF NOT EXISTS andares (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    descricao TEXT
);

-- 3. TABELA SALAS
CREATE TABLE IF NOT EXISTS salas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(100),
    descricao TEXT,
    foto TEXT,
    fotos TEXT,
    andar_id INTEGER REFERENCES andares(id) ON DELETE SET NULL
);

-- 4. TABELA EQUIPAMENTOS
CREATE TABLE IF NOT EXISTS equipamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(100),
    marca VARCHAR(100),
    modelo VARCHAR(100),
    descricao TEXT,
    foto TEXT,
    icone TEXT,
    sala_id INTEGER REFERENCES salas(id) ON DELETE SET NULL,
    ip1 VARCHAR(45),
    mac1 VARCHAR(17),
    ip2 VARCHAR(45),
    mac2 VARCHAR(17),
    defeito BOOLEAN DEFAULT FALSE,
    keystone VARCHAR(100),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABELA SWITCHES
CREATE TABLE IF NOT EXISTS switches (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    sala_id INTEGER REFERENCES salas(id) ON DELETE SET NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABELA SWITCH_PORTAS
CREATE TABLE IF NOT EXISTS switch_portas (
    id SERIAL PRIMARY KEY,
    switch_id INTEGER NOT NULL REFERENCES switches(id) ON DELETE CASCADE,
    numero_porta INTEGER NOT NULL,
    descricao TEXT,
    status VARCHAR(50) DEFAULT 'livre',
    equipamento_id INTEGER REFERENCES equipamentos(id) ON DELETE SET NULL,
    data_conexao TIMESTAMP,
    UNIQUE(switch_id, numero_porta)
);

-- 7. TABELA PATCH_PANELS
CREATE TABLE IF NOT EXISTS patch_panels (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    andar INTEGER NOT NULL,
    num_portas INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'ativo',
    descricao TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    porta_inicial INTEGER DEFAULT 1,
    prefixo_keystone VARCHAR(50)
);

-- 8. TABELA PATCH_PANEL_PORTAS
CREATE TABLE IF NOT EXISTS patch_panel_portas (
    id SERIAL PRIMARY KEY,
    patch_panel_id INTEGER NOT NULL REFERENCES patch_panels(id) ON DELETE CASCADE,
    numero_porta INTEGER NOT NULL,
    switch_id INTEGER REFERENCES switches(id) ON DELETE SET NULL,
    porta_switch INTEGER,
    status VARCHAR(50) DEFAULT 'livre',
    equipamento_id INTEGER REFERENCES equipamentos(id) ON DELETE SET NULL,
    data_conexao TIMESTAMP,
    UNIQUE(patch_panel_id, numero_porta)
);

-- 9. TABELA CABOS
CREATE TABLE IF NOT EXISTS cabos (
    id SERIAL PRIMARY KEY,
    codigo_unico VARCHAR(100) UNIQUE NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    comprimento INTEGER,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    descricao TEXT,
    foto TEXT,
    status VARCHAR(50) DEFAULT 'estoque',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. TABELA CONEXOES_CABOS
CREATE TABLE IF NOT EXISTS conexoes_cabos (
    id SERIAL PRIMARY KEY,
    cabo_id INTEGER NOT NULL REFERENCES cabos(id) ON DELETE CASCADE,
    equipamento_origem_id INTEGER REFERENCES equipamentos(id) ON DELETE SET NULL,
    equipamento_destino_id INTEGER REFERENCES equipamentos(id) ON DELETE SET NULL,
    porta_origem VARCHAR(100),
    porta_destino VARCHAR(100),
    sala_id INTEGER REFERENCES salas(id) ON DELETE SET NULL,
    observacao TEXT,
    data_conexao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_desconexao TIMESTAMP
);

-- 11. TABELA TIPOS_CABOS
CREATE TABLE IF NOT EXISTS tipos_cabos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descricao TEXT,
    icone VARCHAR(100)
);

-- 12. TABELA SALA_LAYOUTS
CREATE TABLE IF NOT EXISTS sala_layouts (
    sala_id INTEGER PRIMARY KEY REFERENCES salas(id) ON DELETE CASCADE,
    layout_json TEXT,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. TABELA PING_LOGS
CREATE TABLE IF NOT EXISTS ping_logs (
    id SERIAL PRIMARY KEY,
    equipamento_id INTEGER REFERENCES equipamentos(id) ON DELETE SET NULL,
    nome_equipamento VARCHAR(255),
    ip VARCHAR(45),
    resultado TEXT,
    sucesso BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. TABELA HISTORICO_CONEXOES_PATCH_PANEL
CREATE TABLE IF NOT EXISTS historico_conexoes_patch_panel (
    id SERIAL PRIMARY KEY,
    patch_panel_id INTEGER NOT NULL REFERENCES patch_panels(id) ON DELETE CASCADE,
    porta_patch_panel INTEGER NOT NULL,
    equipamento_id INTEGER NOT NULL REFERENCES equipamentos(id) ON DELETE CASCADE,
    switch_id INTEGER REFERENCES switches(id) ON DELETE SET NULL,
    porta_switch INTEGER,
    tipo_operacao VARCHAR(50) NOT NULL,
    data_operacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    observacao TEXT
);

-- 15. TABELA SISTEMA_LOGS
CREATE TABLE IF NOT EXISTS sistema_logs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    acao VARCHAR(100) NOT NULL,
    detalhes TEXT,
    status VARCHAR(50) DEFAULT 'sucesso',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar usuario admin
INSERT INTO usuarios (username, senha, nome, nivel) 
VALUES ('admin', 'admin123', 'Administrador', 'master')
ON CONFLICT (username) DO UPDATE SET
    senha = EXCLUDED.senha,
    nome = EXCLUDED.nome,
    nivel = EXCLUDED.nivel;

-- Verificar tabelas criadas
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
