import sqlite3
import sys
import os

# Uso: python atualizar_tipos_cabos.py <nome_do_banco.db>
if len(sys.argv) < 2:
    print('Uso: python atualizar_tipos_cabos.py <nome_do_banco.db>')
    sys.exit(1)

DB_FILE = sys.argv[1]

if not os.path.exists(DB_FILE):
    print(f'Erro: {DB_FILE} não encontrado!')
    sys.exit(1)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

print(f'Atualizando tipos de cabos no banco {DB_FILE}...')

# Primeiro, vamos remover os tipos antigos genéricos
tipos_para_remover = ['USB', 'HDMI', 'VGA', 'DVI', 'DisplayPort', 'RCA', 'XLR', 'Jack 3.5mm', 'Ethernet', 'Power', 'Coaxial', 'Fibra Óptica', 'Serial', 'Paralelo']

for tipo in tipos_para_remover:
    c.execute('DELETE FROM tipos_cabos WHERE nome = ?', (tipo,))
    print(f'Removido tipo genérico: {tipo}')

# Agora vamos inserir os tipos mais específicos
tipos_cabos_detalhados = [
    # USB - Tipos específicos
    ('USB-A para USB-A', 'Cabo USB tipo A para tipo A', 'fas fa-usb'),
    ('USB-A para USB-B', 'Cabo USB tipo A para tipo B (printer)', 'fas fa-usb'),
    ('USB-A para USB-C', 'Cabo USB tipo A para tipo C', 'fas fa-usb'),
    ('USB-C para USB-C', 'Cabo USB tipo C para tipo C', 'fas fa-usb'),
    ('USB-A para Micro-USB', 'Cabo USB tipo A para Micro-USB', 'fas fa-usb'),
    ('USB-C para Micro-USB', 'Cabo USB tipo C para Micro-USB', 'fas fa-usb'),
    ('USB-A para Mini-USB', 'Cabo USB tipo A para Mini-USB', 'fas fa-usb'),
    
    # HDMI - Versões específicas
    ('HDMI Standard', 'Cabo HDMI Standard (1.4)', 'fas fa-tv'),
    ('HDMI High Speed', 'Cabo HDMI High Speed (2.0)', 'fas fa-tv'),
    ('HDMI Ultra High Speed', 'Cabo HDMI Ultra High Speed (2.1)', 'fas fa-tv'),
    ('HDMI para DVI', 'Cabo HDMI para DVI', 'fas fa-tv'),
    ('Mini HDMI', 'Cabo Mini HDMI', 'fas fa-tv'),
    ('Micro HDMI', 'Cabo Micro HDMI', 'fas fa-tv'),
    
    # Vídeo - Tipos específicos
    ('VGA 15-pin', 'Cabo VGA 15 pinos', 'fas fa-desktop'),
    ('DVI-D', 'Cabo DVI Digital', 'fas fa-monitor'),
    ('DVI-I', 'Cabo DVI Integrado (Digital + Analógico)', 'fas fa-monitor'),
    ('DVI-A', 'Cabo DVI Analógico', 'fas fa-monitor'),
    ('DisplayPort 1.2', 'Cabo DisplayPort versão 1.2', 'fas fa-display'),
    ('DisplayPort 1.4', 'Cabo DisplayPort versão 1.4', 'fas fa-display'),
    ('Mini DisplayPort', 'Cabo Mini DisplayPort', 'fas fa-display'),
    
    # Áudio - Tipos específicos
    ('RCA Vídeo', 'Cabo RCA amarelo para vídeo', 'fas fa-volume-up'),
    ('RCA Áudio L/R', 'Cabo RCA vermelho/branco para áudio', 'fas fa-volume-up'),
    ('RCA Componente', 'Cabo RCA componente (Y/Pb/Pr)', 'fas fa-volume-up'),
    ('XLR Macho para Fêmea', 'Cabo XLR macho para fêmea', 'fas fa-microphone'),
    ('XLR Fêmea para Macho', 'Cabo XLR fêmea para macho', 'fas fa-microphone'),
    ('Jack 3.5mm para 3.5mm', 'Cabo Jack 3.5mm para 3.5mm', 'fas fa-headphones'),
    ('Jack 3.5mm para 6.35mm', 'Cabo Jack 3.5mm para 6.35mm', 'fas fa-headphones'),
    ('Jack 6.35mm para 6.35mm', 'Cabo Jack 6.35mm para 6.35mm', 'fas fa-headphones'),
    
    # Rede - Tipos específicos
    ('Ethernet Cat5e', 'Cabo Ethernet Cat5e', 'fas fa-network-wired'),
    ('Ethernet Cat6', 'Cabo Ethernet Cat6', 'fas fa-network-wired'),
    ('Ethernet Cat6a', 'Cabo Ethernet Cat6a', 'fas fa-network-wired'),
    ('Ethernet Cat7', 'Cabo Ethernet Cat7', 'fas fa-network-wired'),
    ('Ethernet Cat8', 'Cabo Ethernet Cat8', 'fas fa-network-wired'),
    
    # Energia - Tipos específicos
    ('Power IEC C13', 'Cabo de alimentação IEC C13', 'fas fa-plug'),
    ('Power IEC C14', 'Cabo de alimentação IEC C14', 'fas fa-plug'),
    ('Power NEMA 5-15', 'Cabo de alimentação NEMA 5-15', 'fas fa-plug'),
    ('Power NEMA 5-20', 'Cabo de alimentação NEMA 5-20', 'fas fa-plug'),
    ('Power DC 5.5x2.1mm', 'Cabo de alimentação DC 5.5x2.1mm', 'fas fa-plug'),
    ('Power DC 5.5x2.5mm', 'Cabo de alimentação DC 5.5x2.5mm', 'fas fa-plug'),
    ('Power DC 3.5x1.35mm', 'Cabo de alimentação DC 3.5x1.35mm', 'fas fa-plug'),
    
    # Especializados
    ('Coaxial RG6', 'Cabo coaxial RG6', 'fas fa-satellite-dish'),
    ('Coaxial RG59', 'Cabo coaxial RG59', 'fas fa-satellite-dish'),
    ('Fibra Óptica Multimodo', 'Cabo de fibra óptica multimodo', 'fas fa-lightbulb'),
    ('Fibra Óptica Monomodo', 'Cabo de fibra óptica monomodo', 'fas fa-lightbulb'),
    ('Serial DB9', 'Cabo serial DB9', 'fas fa-terminal'),
    ('Serial DB25', 'Cabo serial DB25', 'fas fa-terminal'),
    ('Paralelo DB25', 'Cabo paralelo DB25', 'fas fa-print'),
    
    # Outros tipos comuns
    ('SATA', 'Cabo SATA para dados', 'fas fa-hdd'),
    ('eSATA', 'Cabo eSATA externo', 'fas fa-hdd'),
    ('FireWire 400', 'Cabo FireWire 400', 'fas fa-fire'),
    ('FireWire 800', 'Cabo FireWire 800', 'fas fa-fire'),
    ('Thunderbolt 2', 'Cabo Thunderbolt 2', 'fas fa-bolt'),
    ('Thunderbolt 3', 'Cabo Thunderbolt 3', 'fas fa-bolt'),
    ('Thunderbolt 4', 'Cabo Thunderbolt 4', 'fas fa-bolt'),
    ('PS/2', 'Cabo PS/2 para teclado/mouse', 'fas fa-keyboard'),
    ('SCSI', 'Cabo SCSI', 'fas fa-server'),
    ('Outro', 'Outro tipo de cabo', 'fas fa-cable-car')
]

for tipo in tipos_cabos_detalhados:
    c.execute('''
        INSERT OR IGNORE INTO tipos_cabos (nome, descricao, icone)
        VALUES (?, ?, ?)
    ''', tipo)
    print(f'Adicionado: {tipo[0]}')

conn.commit()
conn.close()

print('✅ Tipos de cabos atualizados com sucesso!')
print(f'📝 Total de tipos disponíveis: {len(tipos_cabos_detalhados)}')
print('🔧 Agora você pode selecionar tipos mais específicos ao adicionar cabos') 