import sqlite3
import sys
import os

# Uso: python criar_tabelas_cabos.py <nome_do_banco.db>
if len(sys.argv) < 2:
    print('Uso: python criar_tabelas_cabos.py <nome_do_banco.db>')
    sys.exit(1)

DB_FILE = sys.argv[1]

if not os.path.exists(DB_FILE):
    print(f'Erro: {DB_FILE} não encontrado!')
    sys.exit(1)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

print(f'Adicionando tabelas de cabos ao banco {DB_FILE}...')

# Tabela de cabos
c.execute('''
CREATE TABLE IF NOT EXISTS cabos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_unico TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    comprimento INTEGER,
    marca TEXT,
    modelo TEXT,
    descricao TEXT,
    foto TEXT,
    status TEXT DEFAULT 'funcionando',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabela de conexões de cabos
c.execute('''
CREATE TABLE IF NOT EXISTS conexoes_cabos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cabo_id INTEGER NOT NULL,
    equipamento_origem_id INTEGER,
    equipamento_destino_id INTEGER,
    porta_origem TEXT,
    porta_destino TEXT,
    sala_id INTEGER,
    observacao TEXT,
    data_conexao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_desconexao TIMESTAMP,
    FOREIGN KEY (cabo_id) REFERENCES cabos(id),
    FOREIGN KEY (equipamento_origem_id) REFERENCES equipamentos(id),
    FOREIGN KEY (equipamento_destino_id) REFERENCES equipamentos(id),
    FOREIGN KEY (sala_id) REFERENCES salas(id)
)
''')

# Tabela de tipos de cabos predefinidos
c.execute('''
CREATE TABLE IF NOT EXISTS tipos_cabos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    descricao TEXT,
    icone TEXT
)
''')

# Inserir tipos de cabos comuns
tipos_cabos = [
    ('HDMI', 'Cabo HDMI para vídeo e áudio digital', 'fas fa-tv'),
    ('USB', 'Cabo USB para dados e energia', 'fas fa-usb'),
    ('VGA', 'Cabo VGA para vídeo analógico', 'fas fa-desktop'),
    ('DVI', 'Cabo DVI para vídeo digital', 'fas fa-monitor'),
    ('DisplayPort', 'Cabo DisplayPort para vídeo digital', 'fas fa-display'),
    ('RCA', 'Cabo RCA para áudio/vídeo analógico', 'fas fa-volume-up'),
    ('XLR', 'Cabo XLR para áudio profissional', 'fas fa-microphone'),
    ('Jack 3.5mm', 'Cabo Jack 3.5mm para áudio', 'fas fa-headphones'),
    ('Ethernet', 'Cabo de rede Ethernet', 'fas fa-network-wired'),
    ('Power', 'Cabo de alimentação', 'fas fa-plug'),
    ('Coaxial', 'Cabo coaxial para RF', 'fas fa-satellite-dish'),
    ('Fibra Óptica', 'Cabo de fibra óptica', 'fas fa-lightbulb'),
    ('Serial', 'Cabo serial RS-232', 'fas fa-terminal'),
    ('Paralelo', 'Cabo paralelo', 'fas fa-print'),
    ('Outro', 'Outro tipo de cabo', 'fas fa-cable-car')
]

for tipo in tipos_cabos:
    c.execute('''
        INSERT OR IGNORE INTO tipos_cabos (nome, descricao, icone)
        VALUES (?, ?, ?)
    ''', tipo)

# Trigger para atualizar data_modificacao
c.execute('''
CREATE TRIGGER IF NOT EXISTS update_cabos_modificacao
    AFTER UPDATE ON cabos
    FOR EACH ROW
    BEGIN
        UPDATE cabos SET data_modificacao = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END
''')

conn.commit()
conn.close()

print('✅ Tabelas de cabos criadas com sucesso!')
print('📋 Tabelas criadas:')
print('   - cabos (informações dos cabos físicos)')
print('   - conexoes_cabos (conexões entre equipamentos)')
print('   - tipos_cabos (tipos predefinidos de cabos)')
print('🔧 Triggers criados para auditoria')
print('📝 Tipos de cabos predefinidos inseridos') 