import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
# Configuração PostgreSQL
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'portfolio_unified'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def get_postgres_connection():
    """Retorna uma conexão com PostgreSQL"""
    return psycopg2.connect(**POSTGRES_CONFIG)

def get_postgres_dict_connection():
    """Retorna uma conexão com PostgreSQL usando RealDictCursor"""
    config = POSTGRES_CONFIG.copy()
    config['cursor_factory'] = RealDictCursor
    return psycopg2.connect(**config)

from database_config import get_postgres_connection, get_postgres_dict_connection
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import subprocess
from typing import cast
import glob
import re

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração do sistema de logs
LOG_FILE = 'sistema_logs.txt'

def registrar_log(usuario, acao, detalhes, status='sucesso'):
    """
    Registra uma ação no arquivo de log
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Usuario: {usuario} | Acao: {acao} | Detalhes: {detalhes} | Status: {status}\n"
        
        print(f"DEBUG: Tentando registrar log: {log_entry.strip()}")  # Debug
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"DEBUG: Log registrado com sucesso no arquivo: {LOG_FILE}")  # Debug
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
        print(f"DEBUG: Arquivo de log: {LOG_FILE}")  # Debug
        print(f"DEBUG: Diretório atual: {os.getcwd()}")  # Debug

# Função decorator para log automático (NÃO USADO)
# def log_action(acao):
#     """
#     Decorator para registrar ações automaticamente
#     """
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             try:
#                 result = f(*args, **kwargs)
#                 usuario = session.get('username', 'desconhecido')
#                 detalhes = f"Função: {f.__name__}, Args: {args}, Kwargs: {kwargs}"
#                 registrar_log(usuario, acao, detalhes, 'sucesso')
#                 return result
#             except Exception as e:
#                 usuario = session.get('username', 'desconhecido')
#                 detalhes = f"Erro: {str(e)}, Função: {f.__name__}"
#                 registrar_log(usuario, acao, detalhes, 'erro')
#                 raise
#         return decorated_function
#     return decorator

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nivel, nome FROM usuarios WHERE username=%s AND senha=%s', (dados['username'], dados['senha']))
    user = cur.fetchone()
    if not user:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Usuário ou senha inválidos'}), 401
    user_id, nivel, nome = user
    conn.close()
    session['user_id'] = user_id
    session['nivel'] = nivel
    session['username'] = dados['username']
    session['nome'] = nome
    # Para banco unificado, sempre redireciona para o painel
    return jsonify({'status': 'ok', 'redirect': '/painel.html'})



@app.route('/logout')
def logout():
    session.clear()
    return '', 204

@app.route('/perfil')
def perfil():
    if 'user_id' in session:
        return jsonify({'nivel': session.get('nivel')})
    return jsonify({'nivel': None})

# --- ROTAS PÚBLICAS ---

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/login.html')
def login_html():
    return send_from_directory(os.path.dirname(__file__), 'login.html')

# --- ROTAS PROTEGIDAS (LOGIN OBRIGATÓRIO) ---

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login.html')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('nivel') != 'admin':
            return redirect('/login.html')
        return f(*args, **kwargs)
    return decorated_function

def tecnico_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('nivel') not in ['admin', 'tecnico']:
            return redirect('/login.html')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/painel.html')
@login_required
def painel_html():
    return send_from_directory(os.path.dirname(__file__), 'painel.html')


@app.route('/adicionar-sala.html')
@login_required
def salas_com_equipamentos_html():
    return send_from_directory(os.path.dirname(__file__), 'adicionar-sala.html')

@app.route('/editar-sala.html')
@login_required
def editar_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'editar-sala.html')

@app.route('/config-admin.html')
@admin_required
def config_admin_html():
    return send_from_directory(os.path.dirname(__file__), 'config-admin.html')

@app.route('/excluir-sala.html')
@admin_required
def excluir_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'excluir-sala.html')

@app.route('/ver-salas.html')
@login_required
def salas_simples_html():
    return send_from_directory(os.path.dirname(__file__), 'ver-salas.html')

@app.route('/detalhes-equipamentos-sala.html')
@login_required
def detalhes_equipamentos_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'detalhes-equipamentos-sala.html')

@app.route('/adicionar-equipamento.html')
@login_required
def adicionar_equipamento_html():
    return send_from_directory(os.path.dirname(__file__), 'adicionar-equipamento.html')

@app.route('/editar-equipamento.html')
@login_required
def editar_equipamento_html():
    return send_from_directory(os.path.dirname(__file__), 'editar-equipamento.html')

@app.route('/excluir-equipamento.html')
@login_required
def excluir_equipamento_html():
    return send_from_directory(os.path.dirname(__file__), 'excluir-equipamento.html')

@app.route('/ver-equipamento.html')
@login_required
def ver_equipamento_html():
    return send_from_directory(os.path.dirname(__file__), 'ver-equipamento.html')

@app.route('/detalhes-sala.html')
def detalhes_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'detalhes-sala.html')

# --- API DE SALAS (PROTEGIDA) ---

@app.route('/salas', methods=['GET'])
@login_required
def listar_salas():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT s.id, s.nome, s.tipo, s.descricao, s.foto, s.fotos, s.andar_id, a.titulo as andar
        FROM salas s
        LEFT JOIN andares a ON s.andar_id = a.id
    ''')
    salas = [
        dict(id=row[0], nome=row[1], tipo=row[2], descricao=row[3], foto=row[4], fotos=row[5], andar_id=row[6], andar=row[7])
        for row in cur.fetchall()
    ]
    conn.close()
    return jsonify(salas)

@app.route('/salas', methods=['POST'])
@admin_required
def criar_sala():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    # Verificação de nome duplicado (case-insensitive)
    nome = dados['nome']
    cur.execute('SELECT 1 FROM salas WHERE LOWER(nome) = LOWER(%s)', (nome,))
    if cur.fetchone():
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Já existe uma sala com esse nome!'}), 400
    cur.execute('''
        INSERT INTO salas (nome, tipo, descricao, foto, fotos, andar_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (
        dados['nome'],
        dados.get('tipo'),
        dados.get('descricao'),
        dados.get('foto'),
        dados.get('fotos'),
        dados.get('andar_id')
    ))
    sala_id = cur.lastrowid
    equipamentos_ids = request.form.getlist('equipamentos_ids[]')
    for eq_id in equipamentos_ids:
        cur.execute('UPDATE equipamentos SET sala_id=%s WHERE id=%s', (sala_id, eq_id))
    conn.commit()
    conn.close()
    # Log de criação de sala
    detalhes = f"Sala criada: ID={sala_id}, Nome={dados['nome']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SALA', detalhes, 'sucesso')
    return jsonify({'status': 'ok', 'id': sala_id})

@app.route('/salas/<int:id>', methods=['GET'])
@login_required
def get_sala(id):
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, descricao, foto, fotos, andar_id FROM salas WHERE id=%s', (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(dict(id=row[0], nome=row[1], tipo=row[2], descricao=row[3], foto=row[4], fotos=row[5], andar_id=row[6]))
    return jsonify({'erro': 'Sala não encontrada'}), 404

@app.route('/salas/<int:id>', methods=['PUT'])
@admin_required
def atualizar_sala(id):
    dados = request.json
    if not dados:
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SALA', f'Sala ID={id}: Dados JSON inválidos', 'erro')
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Busca equipamentos atualmente vinculados à sala
    cur.execute('SELECT id FROM equipamentos WHERE sala_id = %s', (id,))
    equipamentos_atuais = [row[0] for row in cur.fetchall()]
    
    # Atualiza dados da sala
    cur.execute('''
        UPDATE salas SET nome=%s, tipo=%s, descricao=%s, foto=%s, fotos=%s, andar_id=%s
        WHERE id=%s
    ''', (
        dados['nome'],
        dados.get('tipo'),
        dados.get('descricao'),
        dados.get('foto'),
        dados.get('fotos'),
        dados.get('andar_id'),
        id
    ))
    
    # Atualiza vínculo dos equipamentos
    equipamentos_ids = dados.get('equipamentos_ids', [])
    
    # Identifica equipamentos que foram desatrelados
    equipamentos_desatrelados = []
    for eq_id in equipamentos_atuais:
        if str(eq_id) not in equipamentos_ids:
            equipamentos_desatrelados.append(eq_id)
    
    # Desconecta equipamentos desatrelados de suas portas de switch
    for eq_id in equipamentos_desatrelados:
        # Busca a porta conectada ao equipamento
        cur.execute('''
            SELECT porta_id FROM conexoes 
            WHERE equipamento_id = %s AND status = 'ativa'
        ''', (eq_id,))
        porta_result = cur.fetchone()
        
        if porta_result:
            porta_id = porta_result[0]
            # Marca a conexão como inativa
            cur.execute('''
                UPDATE conexoes SET status = 'inativa' 
                WHERE equipamento_id = %s AND status = 'ativa'
            ''', (eq_id,))
            
            # Marca a porta como livre
            cur.execute('''
                UPDATE switch_portas SET status = 'livre' 
                WHERE id = %s
            ''', (porta_id,))
    
    # Desvincula todos os equipamentos da sala
    cur.execute('UPDATE equipamentos SET sala_id=NULL WHERE sala_id=%s', (id,))
    
    # Vincula os selecionados
    for eq_id in equipamentos_ids:
        cur.execute('UPDATE equipamentos SET sala_id=%s WHERE id=%s', (id, eq_id))
    
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Sala atualizada: ID={id}, Nome={dados['nome']}, Equipamentos desatrelados={len(equipamentos_desatrelados)}, Equipamentos vinculados={len(equipamentos_ids)}"
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SALA', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok'})

@app.route('/salas/<int:id>', methods=['DELETE'])
@admin_required
def excluir_sala(id):
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT nome FROM salas WHERE id=%s', (id,))
    row = cur.fetchone()
    nome_sala = row[0] if row else ''
    cur.execute('UPDATE equipamentos SET sala_id=NULL WHERE sala_id=%s', (id,))
    cur.execute('DELETE FROM salas WHERE id=%s', (id,))
    conn.commit()
    conn.close()
    # Log de exclusão de sala
    detalhes = f"Sala excluída: ID={id}, Nome={nome_sala}"
    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_SALA', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/adicionar-sala', methods=['POST'])
@admin_required
def criar_sala_com_equipamentos():
    UPLOAD_FOLDER = os.path.join('static', 'img')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    nome = request.form.get('nome')
    tipo = request.form.get('tipo')
    descricao = request.form.get('descricao')
    andar_id = request.form.get('andar_id')
    if andar_id is not None and andar_id != '':
        andar_id = int(andar_id)
    else:
        andar_id = None
    # Processa foto principal
    foto = request.files.get('foto')
    caminho_foto = None
    if foto and foto.filename:
        filename = secure_filename(foto.filename)
        caminho_foto = os.path.join(UPLOAD_FOLDER, filename)
        foto.save(caminho_foto)
        caminho_foto = f'img/{filename}'
    elif request.form.get('foto'):
        caminho_foto = request.form.get('foto')
    # Processa fotos extras
    caminhos_fotos = []
    if 'fotos' in request.files:
        fotos = request.files.getlist('fotos')
        for f in fotos:
            if f and f.filename:
                filename = secure_filename(f.filename)
                caminho = os.path.join(UPLOAD_FOLDER, filename)
                f.save(caminho)
                caminhos_fotos.append(f'img/{filename}')
    fotos_str = ','.join(caminhos_fotos) if caminhos_fotos else None
    # Processa equipamentos
    equipamentos = []
    if 'equipamentos' in request.form:
        try:
            equipamentos = json.loads(request.form['equipamentos'])
        except Exception:
            equipamentos = []
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    # Verificação de nome duplicado (case-insensitive)
    cur.execute('SELECT 1 FROM salas WHERE LOWER(nome) = LOWER(%s)', (nome,))
    if cur.fetchone():
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Já existe uma sala com esse nome!'}), 400
    # Cria a sala
    cur.execute('''
        INSERT INTO salas (nome, tipo, descricao, foto, fotos, andar_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (
        nome,
        tipo,
        descricao,
        caminho_foto,
        fotos_str,
        andar_id
    ))
    sala_id = cur.lastrowid
    # Cria os equipamentos
    for eq in equipamentos:
        # Gera caminho da foto automaticamente
        tipo = (eq.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
        marca = (eq.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
        modelo = (eq.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
        caminho_foto = f'img/{tipo}-{marca}-{modelo}.png' if tipo and marca and modelo else None
        cur.execute('''
            INSERT INTO equipamentos (nome, tipo, marca, modelo, descricao, foto, icone, sala_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            eq['nome'],
            eq.get('tipo'),
            eq.get('marca'),
            eq.get('modelo'),
            eq.get('descricao'),
            caminho_foto,
            eq.get('icone'),
            sala_id
        ))
        equipamento_id = cur.lastrowid
        # Salva dados extras
        for chave, valor in eq.get('dados', {}).items():
            if valor:
                cur.execute('''
                    INSERT INTO equipamento_dados (equipamento_id, chave, valor)
                    VALUES (%s, %s, %s)
                ''', (equipamento_id, chave, valor))
    # Vincular equipamentos já existentes (sem sala) à nova sala
    equipamentos_ids = request.form.getlist('equipamentos_ids[]')
    for eq_id in equipamentos_ids:
        cur.execute('UPDATE equipamentos SET sala_id=%s WHERE id=%s', (sala_id, eq_id))
    conn.commit()
    conn.close()
    # Log de criação de sala (formulário/adicionar-sala)
    detalhes = f"Sala criada: ID={sala_id}, Nome={nome} (via formulário)"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SALA', detalhes, 'sucesso')
    return jsonify({'status': 'ok', 'id': sala_id})

# --- API DE EQUIPAMENTOS (PROTEGIDA) ---

@app.route('/equipamentos', methods=['POST'])
@admin_required
def criar_equipamento():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    tipo = (dados.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    marca = (dados.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    modelo = (dados.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    caminho_foto = f'img/{tipo}-{marca}-{modelo}.png' if tipo and marca and modelo else None
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO equipamentos (nome, tipo, marca, modelo, descricao, foto, icone, sala_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        dados['nome'],
        dados.get('tipo'),
        dados.get('marca'),
        dados.get('modelo'),
        dados.get('descricao'),
        caminho_foto,
        dados.get('icone'),
        dados['sala_id']
    ))
    equipamento_id = cur.lastrowid
    for chave, valor in dados.get('dados', {}).items():
        if valor:
            cur.execute('''
                INSERT INTO equipamento_dados (equipamento_id, chave, valor)
                VALUES (%s, %s, %s)
            ''', (equipamento_id, chave, valor))
    conn.commit()
    conn.close()
    # Log de criação de equipamento
    detalhes = f"Equipamento criado: ID={equipamento_id}, Nome={dados['nome']}, Tipo={dados.get('tipo')}, Marca={dados.get('marca')}, Modelo={dados.get('modelo')}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_EQUIPAMENTO', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/equipamentos', methods=['GET'])
@login_required
def listar_equipamentos():
    sala_id = request.args.get('sala_id')
    conectaveis = request.args.get('conectaveis')
    disponiveis = request.args.get('disponiveis')
    conn = get_postgres_connection()
    cur = conn.cursor()
    if conectaveis == '1':
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, s.nome as sala_nome, e.defeito
            FROM equipamentos e
            JOIN salas s ON e.sala_id = s.id
            LEFT JOIN equipamento_dados d1 ON e.id = d1.equipamento_id AND d1.chave = 'ip1'
            LEFT JOIN equipamento_dados d2 ON e.id = d2.equipamento_id AND d2.chave = 'mac1'
            WHERE e.sala_id IS NOT NULL
              AND ((d1.valor IS NOT NULL AND d1.valor != '') OR (d2.valor IS NOT NULL AND d2.valor != ''))
              AND e.id NOT IN (SELECT equipamento_id FROM conexoes WHERE status = 'ativa')
              AND e.id NOT IN (SELECT equipamento_id FROM patch_panel_portas WHERE equipamento_id IS NOT NULL)
              AND (e.defeito IS NULL OR e.defeito = 0)
        ''')
    elif disponiveis == '1':
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, s.nome as sala_nome, e.defeito
            FROM equipamentos e
            JOIN salas s ON e.sala_id = s.id
            LEFT JOIN equipamento_dados d1 ON e.id = d1.equipamento_id AND d1.chave = 'ip1'
            LEFT JOIN equipamento_dados d2 ON e.id = d2.equipamento_id AND d2.chave = 'mac1'
            WHERE e.sala_id IS NOT NULL
              AND e.id NOT IN (SELECT equipamento_id FROM patch_panel_portas WHERE equipamento_id IS NOT NULL)
              AND e.id NOT IN (SELECT equipamento_id FROM conexoes WHERE status = 'ativa')
              AND ((d1.valor IS NOT NULL AND d1.valor != '') OR (d2.valor IS NOT NULL AND d2.valor != ''))
              AND (e.defeito IS NULL OR e.defeito = 0)
        ''')
    elif sala_id == 'null':
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, e.defeito, s.nome as sala_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
            WHERE e.sala_id IS NULL
        ''')
    elif sala_id:
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, e.defeito, s.nome as sala_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
            WHERE e.sala_id=%s
        ''', (sala_id,))
    else:
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, e.defeito, s.nome as sala_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
        ''')
    equipamentos = []
    for row in cur.fetchall():
        eq_id = row['id']
        cur.execute('SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s', (eq_id,))
        dados = {chave: valor for chave, valor in cur.fetchall()}
        defeito_val = int(row['defeito']) if row['defeito'] is not None else 0
        equipamentos.append({
            'id': eq_id,
            'nome': row['nome'],
            'tipo': row['tipo'],
            'marca': row['marca'],
            'modelo': row['modelo'],
            'descricao': row['descricao'],
            'foto': row['foto'],
            'icone': row['icone'],
            'sala_id': row['sala_id'],
            'sala_nome': row['sala_nome'],
            'defeito': defeito_val,
            'dados': dados
        })
    conn.close()
    return jsonify(equipamentos)

@app.route('/equipamentos/<int:id>', methods=['PUT'])
@admin_required
def atualizar_equipamento(id):
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    tipo = (dados.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    marca = (dados.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    modelo = (dados.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    caminho_foto = f'img/{tipo}-{marca}-{modelo}.png' if tipo and marca and modelo else None
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE equipamentos SET nome=%s, tipo=%s, marca=%s, modelo=%s, descricao=%s, foto=%s, icone=%s
        WHERE id=%s
    ''', (
        dados['nome'],
        dados.get('tipo'),
        dados.get('marca'),
        dados.get('modelo'),
        dados.get('descricao'),
        caminho_foto,
        dados.get('icone'),
        id
    ))
    for chave, valor in dados.get('dados', {}).items():
        cur.execute('SELECT id FROM equipamento_dados WHERE equipamento_id=%s AND chave=%s', (id, chave))
        row = cur.fetchone()
        if row:
            cur.execute('UPDATE equipamento_dados SET valor=%s WHERE id=%s', (valor, row[0]))
        else:
            cur.execute('INSERT INTO equipamento_dados (equipamento_id, chave, valor) VALUES (%s, %s, %s)', (id, chave, valor))
    conn.commit()
    conn.close()
    # Log de edição de equipamento
    detalhes = f"Equipamento atualizado: ID={id}, Nome={dados['nome']}, Tipo={dados.get('tipo')}, Marca={dados.get('marca')}, Modelo={dados.get('modelo')}"
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_EQUIPAMENTO', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/equipamentos/<int:id>', methods=['GET'])
@login_required
def get_equipamento(id):
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, marca, modelo, descricao, foto, icone, sala_id FROM equipamentos WHERE id=%s', (id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'erro': 'Equipamento não encontrado'}), 404
    cur.execute('SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s', (id,))
    dados = {chave: valor for chave, valor in cur.fetchall()}
    equipamento = {
        'id': row[0],
        'nome': row[1],
        'tipo': row[2],
        'marca': row[3],
        'modelo': row[4],
        'descricao': row[5],
        'foto': row[6],
        'icone': row[7],
        'sala_id': row[8],
        'dados': dados
    }
    conn.close()
    return jsonify(equipamento)

@app.route('/equipamentos/<int:id>', methods=['DELETE'])
@admin_required
def excluir_equipamento(id):
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT nome, tipo, marca, modelo FROM equipamentos WHERE id=%s', (id,))
    row = cur.fetchone()
    nome, tipo, marca, modelo = row if row else ('', '', '', '')
    cur.execute('DELETE FROM equipamento_dados WHERE equipamento_id=%s', (id,))
    cur.execute('DELETE FROM equipamentos WHERE id=%s', (id,))
    conn.commit()
    conn.close()
    # Log de exclusão de equipamento
    detalhes = f"Equipamento excluído: ID={id}, Nome={nome}, Tipo={tipo}, Marca={marca}, Modelo={modelo}"
    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_EQUIPAMENTO', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/tipos-equipamento')
@login_required
def tipos_equipamento():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT tipo FROM equipamentos WHERE tipo IS NOT NULL AND tipo != ""')
    tipos = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(tipos)

@app.route('/marcas-equipamento')
@login_required
def marcas_equipamento():
    tipo = request.args.get('tipo')
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT marca FROM equipamentos WHERE tipo=%s AND marca IS NOT NULL AND marca != ""', (tipo,))
    marcas = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(marcas)

@app.route('/modelos-equipamento')
@login_required
def modelos_equipamento():
    tipo = request.args.get('tipo')
    marca = request.args.get('marca')
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT modelo FROM equipamentos WHERE tipo=%s AND marca=%s AND modelo IS NOT NULL AND modelo != ""', (tipo, marca))
    modelos = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(modelos)

# --- ARQUIVOS ESTÁTICOS ---

# --- ROTAS DE SWITCHES ---

@app.route('/adicionar-switch.html')
@admin_required
def adicionar_switch_html():
    return send_from_directory(os.path.dirname(__file__), 'adicionar-switch.html')

@app.route('/gerenciar-portas-switch.html')
@login_required
def gerenciar_portas_switch_html():
    return send_from_directory(os.path.dirname(__file__), 'gerenciar-portas-switch.html')

@app.route('/editar-switch.html')
@login_required
def editar_switch_html():
    return send_from_directory(os.path.dirname(__file__), 'editar-switch.html')

@app.route('/switches', methods=['POST'])
@admin_required
def criar_switch():
    dados = request.json
    if not dados:
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SWITCH', 'Dados JSON inválidos', 'erro')
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS switches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        INSERT INTO switches (nome, marca, modelo)
        VALUES (%s, %s, %s)
    ''', (
        dados['nome'],
        dados['marca'],
        dados['modelo']
    ))
    switch_id = cur.lastrowid
    conn.commit()
    conn.close()
    # Log de criação de switch
    detalhes = f"Switch criado: ID={switch_id}, Nome={dados['nome']}, Marca={dados['marca']}, Modelo={dados['modelo']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SWITCH', detalhes, 'sucesso')
    return jsonify({'status': 'ok', 'id': switch_id})

@app.route('/switches', methods=['GET'])
@login_required
def listar_switches():            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Verificar se a tabela switches existe, se não, criar
    cur.execute('''
        CREATE TABLE IF NOT EXISTS switches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('SELECT id, nome, marca, modelo, data_criacao FROM switches ORDER BY data_criacao DESC')
    switches = [
        dict(id=row[0], nome=row[1], marca=row[2], modelo=row[3], data_criacao=row[4])
        for row in cur.fetchall()
    ]
    conn.close()
    return jsonify(switches)

@app.route('/switches/<int:id>', methods=['GET'])
@login_required
def get_switch(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT id, nome, marca, modelo, data_criacao FROM switches WHERE id=%s', (id,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
    
    switch = {
        'id': row[0],
        'nome': row[1],
        'marca': row[2],
        'modelo': row[3],
        'data_criacao': row[4]
    }
    
    conn.close()
    return jsonify(switch)

@app.route('/switches/<int:id>', methods=['PUT'])
@admin_required
def atualizar_switch(id):
    dados = request.json
    if not dados:
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', f'Switch ID={id}: Dados JSON inválidos', 'erro')
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Verificar se o switch existe
    cur.execute('SELECT id FROM switches WHERE id=%s', (id,))
    if not cur.fetchone():
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', f'Switch ID={id}: Não encontrado', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
    
    # Atualizar o switch
    cur.execute('''
        UPDATE switches SET nome=%s, marca=%s, modelo=%s
        WHERE id=%s
    ''', (
        dados['nome'],
        dados['marca'],
        dados['modelo'],
        id
    ))
    
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Switch atualizado: ID={id}, Nome={dados['nome']}, Marca={dados['marca']}, Modelo={dados['modelo']}"
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok'})

@app.route('/css/<path:filename>')
def css_static(filename):
    return send_from_directory('css', filename)

# --- ROTAS DE PORTAS DE SWITCHES ---

@app.route('/switch-portas', methods=['POST'])
@admin_required
def criar_porta_switch():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Criar tabela de portas se não existir
    cur.execute('''
        CREATE TABLE IF NOT EXISTS switch_portas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            switch_id INTEGER NOT NULL,
            numero_porta INTEGER NOT NULL,
            descricao TEXT,
            status TEXT DEFAULT 'livre',
            FOREIGN KEY (switch_id) REFERENCES switches (id)
        )
    ''')
    
    # Verificar se a porta já existe para este switch
    cur.execute('SELECT id FROM switch_portas WHERE switch_id=%s AND numero_porta=%s', 
                (dados['switch_id'], dados['numero_porta']))
    
    if cur.fetchone():
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Porta já existe para este switch'}), 400
    
    cur.execute('''
        INSERT INTO switch_portas (switch_id, numero_porta, descricao, status)
        VALUES (%s, %s, %s, %s)
    ''', (
        dados['switch_id'],
        dados['numero_porta'],
        dados.get('descricao', ''),
        dados.get('status', 'livre')
    ))
    
    porta_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok', 'id': porta_id})

@app.route('/switch-portas/<int:switch_id>', methods=['GET'])
@login_required
def listar_portas_switch(switch_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Criar tabela se não existir
    cur.execute('''
        CREATE TABLE IF NOT EXISTS switch_portas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            switch_id INTEGER NOT NULL,
            numero_porta INTEGER NOT NULL,
            descricao TEXT,
            status TEXT DEFAULT 'livre',
            FOREIGN KEY (switch_id) REFERENCES switches (id)
        )
    ''')
    
    cur.execute('''
        SELECT sp.id, sp.numero_porta, sp.descricao, 
               CASE 
                   WHEN c.id IS NOT NULL THEN 'ocupada'
                   WHEN ppp.equipamento_id IS NOT NULL THEN 'ocupada'
                   ELSE 'livre' 
               END as status,
               e.nome as equipamento_nome, e.tipo as equipamento_tipo, s.nome as sala_nome,
               pp.nome as patch_panel_nome, ppp.numero_porta as porta_patch_panel, ppp.id as patch_panel_porta_id,
               ppp.equipamento_id as patch_panel_equipamento_id
        FROM switch_portas sp
        LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
        LEFT JOIN equipamentos e ON c.equipamento_id = e.id
        LEFT JOIN salas s ON e.sala_id = s.id
        LEFT JOIN patch_panel_portas ppp ON ppp.switch_id = sp.switch_id AND ppp.porta_switch = sp.numero_porta
        LEFT JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
        WHERE sp.switch_id = %s
        ORDER BY sp.numero_porta
    ''', (switch_id,))
    
    portas = []
    for row in cur.fetchall():
        equipamento_info = None
        patch_panel_info = None
        
        if row[4]:  # Equipamento conectado diretamente
            # Buscar dados extras do equipamento
            cur.execute("SELECT id FROM equipamentos WHERE nome=%s AND tipo=%s", (row[4], row[5]))
            eq_row = cur.fetchone()
            eq_id = eq_row[0] if eq_row else None
            dados = {}
            if eq_id:
                cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('ip1','ip2','mac1','mac2')", (eq_id,))
                dados = {chave: valor for chave, valor in cur.fetchall()}
            equipamento_info = {
                'nome': row[4],
                'tipo': row[5],
                'sala_nome': row[6],
                'ip1': dados.get('ip1',''),
                'ip2': dados.get('ip2',''),
                'mac1': dados.get('mac1',''),
                'mac2': dados.get('mac2','')
            }
        
        if row[7]:  # Patch panel mapeado
            # Gerar keystone usando o prefixo personalizado
            cur.execute("SELECT prefixo_keystone, andar FROM patch_panels WHERE nome = %s", (row[7],))
            prefixo_result = cur.fetchone()
            prefixo = prefixo_result[0] if prefixo_result and prefixo_result[0] else f"PT{20 + (prefixo_result[1] if prefixo_result else 0)}"
            keystone = f"{prefixo}-{row[8]:04d}"
            
            # Buscar equipamento conectado no patch panel
            equipamento_patch = None
            if row[10]:  # Se há equipamento_id no patch panel
                cur.execute("""
                    SELECT e.nome, e.tipo, sal.nome as sala_nome, e.id
                    FROM equipamentos e
                    LEFT JOIN salas sal ON e.sala_id = sal.id
                    WHERE e.id = %s
                """, (row[10],))
                
                equip_result = cur.fetchone()
                if equip_result and equip_result[0]:
                    # Buscar dados extras do equipamento (IP, MAC)
                    dados = {}
                    cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('ip1','ip2','mac1','mac2')", (equip_result[3],))
                    dados = {chave: valor for chave, valor in cur.fetchall()}
                    
                    equipamento_patch = {
                        'nome': equip_result[0],
                        'tipo': equip_result[1],
                        'sala': equip_result[2],
                        'ip1': dados.get('ip1',''),
                        'ip2': dados.get('ip2',''),
                        'mac1': dados.get('mac1',''),
                        'mac2': dados.get('mac2','')
                    }
            
            patch_panel_info = {
                'nome': row[7],
                'porta_patch_panel': row[8],
                'keystone': keystone,
                'equipamento': equipamento_patch
            }
        
        porta = {
            'id': row[0],
            'numero_porta': row[1],
            'descricao': row[2],
            'status': row[3],
            'equipamento_info': equipamento_info,
            'patch_panel_info': patch_panel_info
        }
        portas.append(porta)
    
    conn.close()
    return jsonify(portas)

# --- ROTAS DE CONEXÕES ---

@app.route('/conexoes', methods=['POST'])
@admin_required
def criar_conexao():
    dados = request.json
    if not dados:
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', 'Dados JSON inválidos', 'erro')
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Criar tabela de conexões se não existir
    cur.execute('''
        CREATE TABLE IF NOT EXISTS conexoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            porta_id INTEGER NOT NULL,
            equipamento_id INTEGER NOT NULL,
            data_conexao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ativa',
            FOREIGN KEY (porta_id) REFERENCES switch_portas (id),
            FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id)
        )
    ''')
    
    # Verificar se a porta está livre
    cur.execute('SELECT status FROM switch_portas WHERE id=%s', (dados['porta_id'],))
    porta = cur.fetchone()
    
    if not porta:
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Porta ID={dados["porta_id"]}: Não encontrada', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
    
    if porta[0] != 'livre':
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Porta ID={dados["porta_id"]}: Já ocupada', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Porta já está ocupada'}), 400
    
    # Verificar se o equipamento já está conectado
    cur.execute('SELECT id FROM conexoes WHERE equipamento_id=%s AND status="ativa"', (dados['equipamento_id'],))
    if cur.fetchone():
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Equipamento ID={dados["equipamento_id"]}: Já conectado', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Equipamento já está conectado a outra porta'}), 400
    
    # Criar a conexão
    cur.execute('''
        INSERT INTO conexoes (porta_id, equipamento_id, status)
        VALUES (%s, %s, 'ativa')
    ''', (dados['porta_id'], dados['equipamento_id']))
    
    # Atualizar status da porta
    cur.execute('UPDATE switch_portas SET status="ocupada" WHERE id=%s', (dados['porta_id'],))
    
    conexao_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Conexão criada: ID={conexao_id}, Porta ID={dados['porta_id']}, Equipamento ID={dados['equipamento_id']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok', 'id': conexao_id})

@app.route('/conexoes/<int:conexao_id>', methods=['DELETE'])
@admin_required
def remover_conexao(conexao_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Buscar a conexão
    cur.execute('SELECT porta_id, equipamento_id FROM conexoes WHERE id=%s AND status="ativa"', (conexao_id,))
    conexao = cur.fetchone()
    
    if not conexao:
        registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', f'Conexão ID={conexao_id}: Não encontrada', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
    
    porta_id, equipamento_id = conexao
    
    # Marcar conexão como inativa
    cur.execute('UPDATE conexoes SET status="inativa" WHERE id=%s', (conexao_id,))
    
    # Marcar porta como livre
    cur.execute('UPDATE switch_portas SET status="livre" WHERE id=%s', (porta_id,))
    
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Conexão removida: ID={conexao_id}, Porta ID={porta_id}, Equipamento ID={equipamento_id}"
    registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok'})

@app.route('/conexoes', methods=['GET'])
@login_required
def listar_conexoes():            conn = get_postgres_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT c.id, c.data_conexao, c.status,
               sp.id as porta_id, sp.numero_porta, s.nome as switch_nome, s.marca as switch_marca,
               e.id as equipamento_id, e.nome as equipamento_nome, e.tipo as equipamento_tipo
        FROM conexoes c
        JOIN switch_portas sp ON c.porta_id = sp.id
        JOIN switches s ON sp.switch_id = s.id
        JOIN equipamentos e ON c.equipamento_id = e.id
        WHERE c.status = 'ativa'
        ORDER BY s.nome, sp.numero_porta
    ''')
    
    conexoes = [
        dict(
            id=row[0], data_conexao=row[1], status=row[2],
            porta_id=row[3], porta=row[4], switch=row[5], switch_marca=row[6],
            equipamento_id=row[7], equipamento=row[8], equipamento_tipo=row[9]
        )
        for row in cur.fetchall()
    ]
    
    conn.close()
    return jsonify(conexoes)

@app.route('/logs', methods=['GET'])
@admin_required
def visualizar_logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # Retornar os últimos 100 logs (mais recentes primeiro)
        logs_recentes = logs[-100:] if len(logs) > 100 else logs
        logs_recentes.reverse()  # Mais recentes primeiro
        
        return jsonify({
            'status': 'ok',
            'logs': logs_recentes,
            'total_logs': len(logs)
        })
    except FileNotFoundError:
        return jsonify({
            'status': 'ok',
            'logs': [],
            'total_logs': 0
        })
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro ao ler logs: {str(e)}'
        }), 500

@app.route('/logs', methods=['DELETE'])
@admin_required
def limpar_logs():
    try:
        # Limpar o arquivo de log
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        registrar_log(session.get('username', 'desconhecido'), 'LIMPAR_LOGS', 'Todos os logs foram limpos', 'sucesso')
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro ao limpar logs: {str(e)}'
        }), 500

@app.route('/visualizar-logs.html')
@admin_required
def visualizar_logs_html():
    return send_from_directory(os.path.dirname(__file__), 'visualizar-logs.html')

@app.route('/excluir-switch.html')
@admin_required
def excluir_switch_html():
    return send_from_directory(os.path.dirname(__file__), 'excluir-switch.html')

@app.route('/ver-switch.html')
@login_required
def ver_switch_html():
    return send_from_directory(os.path.dirname(__file__), 'ver-switch.html')

@app.route('/switches/<int:id>', methods=['DELETE'])
@admin_required
def excluir_switch(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    # Buscar dados do switch
    cur.execute('SELECT nome, marca, modelo FROM switches WHERE id=%s', (id,))
    row = cur.fetchone()
    nome, marca, modelo = row if row else ('', '', '')
    # Buscar portas do switch
    cur.execute('SELECT id FROM switch_portas WHERE switch_id=%s', (id,))
    portas = [r[0] for r in cur.fetchall()]
    # Para cada porta, marcar conexões como inativas e liberar porta
    for porta_id in portas:
        # Marcar conexões como inativas
        cur.execute('UPDATE conexoes SET status="inativa" WHERE porta_id=%s AND status="ativa"', (porta_id,))
        # Marcar porta como livre
        cur.execute('UPDATE switch_portas SET status="livre" WHERE id=%s', (porta_id,))
    # Excluir portas do switch
    cur.execute('DELETE FROM switch_portas WHERE switch_id=%s', (id,))
    # Excluir switch
    cur.execute('DELETE FROM switches WHERE id=%s', (id,))
    conn.commit()
    conn.close()
    # Log de exclusão de switch
    detalhes = f"Switch excluído: ID={id}, Nome={nome}, Marca={marca}, Modelo={modelo} (todas as conexões liberadas)"
    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_SWITCH', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/equipamento-defeito/<int:id>', methods=['POST'])
@admin_required
def atualizar_defeito_equipamento(id):
    dados = request.get_json()
    defeito = 1 if dados.get('defeito') else 0            conn = get_postgres_connection()
    cur = conn.cursor()
    # Se marcar como defeito, desvincula da sala
    if defeito:
        cur.execute('UPDATE equipamentos SET defeito=%s, sala_id=NULL WHERE id=%s', (defeito, id))
    else:
        cur.execute('UPDATE equipamentos SET defeito=%s WHERE id=%s', (defeito, id))
    conn.commit()
    # Verifica valor salvo imediatamente após o update
    cur.execute('SELECT defeito, sala_id FROM equipamentos WHERE id=%s', (id,))
    row = cur.fetchone()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/gerenciar-equipamentos.html')
@login_required
def gerenciar_equipamentos_html():
    return send_from_directory(os.path.dirname(__file__), 'gerenciar-equipamentos.html')

@app.route('/estoque-equipamentos.html')
@login_required
def estoque_equipamentos_html():
    return send_from_directory(os.path.dirname(__file__), 'estoque-equipamentos.html')

@app.route('/adicionar-cabo.html')
@tecnico_required
def adicionar_cabo_html():
    return send_from_directory(os.path.dirname(__file__), 'adicionar-cabo.html')

@app.route('/ver-cabos.html')
@login_required
def ver_cabos_html():
    return send_from_directory(os.path.dirname(__file__), 'ver-cabos.html')

@app.route('/cabos-estoque.html')
@login_required
def cabos_estoque_html():
    return send_file('cabos-estoque.html')

@app.route('/editar-cabo.html')
@tecnico_required
def editar_cabo_html():
    return send_from_directory(os.path.dirname(__file__), 'editar-cabo.html')

@app.route('/excluir-cabo.html')
@admin_required
def excluir_cabo_html():
    return send_from_directory(os.path.dirname(__file__), 'excluir-cabo.html')

@app.route('/conexoes-cabos.html')
@tecnico_required
def conexoes_cabos_html():
    return send_from_directory(os.path.dirname(__file__), 'conexoes-cabos.html')

@app.route('/detalhes-cabos-sala.html')
@login_required
def detalhes_cabos_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'detalhes-cabos-sala.html')

@app.route('/config-usuario.html')
@login_required
def config_usuario_html():
    return send_from_directory(os.path.dirname(__file__), 'config-usuario.html')

@app.route('/config-tecnico.html')
@login_required
def config_tecnico_html():
    return send_from_directory(os.path.dirname(__file__), 'config-tecnico.html')

@app.route('/patch-panels.html')
@tecnico_required
def patch_panels_html():
    return send_from_directory(os.path.dirname(__file__), 'patch-panels.html')

@app.route('/adicionar-patch-panel.html')
@admin_required
def adicionar_patch_panel_html():
    return send_from_directory(os.path.dirname(__file__), 'adicionar-patch-panel.html')

@app.route('/editar-patch-panel.html')
@admin_required
def editar_patch_panel_html():
    return send_from_directory(os.path.dirname(__file__), 'editar-patch-panel.html')

@app.route('/excluir-patch-panel.html')
@admin_required
def excluir_patch_panel_html():
    return send_from_directory(os.path.dirname(__file__), 'excluir-patch-panel.html')

@app.route('/ver-patch-panel.html')
@tecnico_required
def ver_patch_panel_html():
    return send_from_directory(os.path.dirname(__file__), 'ver-patch-panel.html')

@app.route('/gerenciar-portas-patch-panel.html')
@tecnico_required
def gerenciar_portas_patch_panel_html():
    return send_from_directory(os.path.dirname(__file__), 'gerenciar-portas-patch-panel.html')

@app.route('/ping-equipamentos', methods=['POST'])
@login_required
def ping_equipamentos():            conn = get_postgres_connection()
    cur = conn.cursor()
    # Busca todos os equipamentos com IP cadastrado
    cur.execute("""
        SELECT e.id, e.nome, d.valor as ip
        FROM equipamentos e
        JOIN equipamento_dados d ON e.id = d.equipamento_id
        WHERE d.chave = 'ip1' AND d.valor IS NOT NULL AND d.valor != ''
    """)
    equipamentos = cur.fetchall()
    resultados = []
    for eq_id, nome, ip in equipamentos:
        try:
            result = subprocess.run(['ping', '-n', '1', ip], capture_output=True, text=True, timeout=5)
            saida = result.stdout
            sucesso = int('TTL=' in saida or 'ttl=' in saida)
        except Exception as e:
            saida = str(e)
            sucesso = 0
        # Salva no log
        cur.execute(
            'INSERT INTO ping_logs (equipamento_id, nome_equipamento, ip, resultado, sucesso) VALUES (%s, %s, %s, %s, %s)',
            (eq_id, nome, ip, saida, sucesso)
        )
        resultados.append({'id': eq_id, 'nome': nome, 'ip': ip, 'sucesso': bool(sucesso), 'saida': saida})
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'resultados': resultados})

@app.route('/ping-logs')
@login_required
def ping_logs():            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.nome_equipamento, p.ip, p.sucesso, p.timestamp, s.nome as sala_nome, e.id as equipamento_id
        FROM ping_logs p
        LEFT JOIN equipamentos e ON p.equipamento_id = e.id
        LEFT JOIN salas s ON e.sala_id = s.id
        ORDER BY p.timestamp DESC
        LIMIT 100
    ''')
    logs = []
    for row in cur.fetchall():
        eq_id = row[5]
        # Busca MAC
        cur.execute("SELECT valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('mac', 'mac1') LIMIT 1", (eq_id,))
        mac_row = cur.fetchone()
        mac = mac_row[0] if mac_row else ''
        # Busca switch e porta (se houver conexão ativa)
        cur.execute('''
            SELECT s.nome, sp.numero_porta
            FROM conexoes c
            JOIN switch_portas sp ON c.porta_id = sp.id
            JOIN switches s ON sp.switch_id = s.id
            WHERE c.equipamento_id=%s AND c.status='ativa' LIMIT 1
        ''', (eq_id,))
        sw_row = cur.fetchone()
        switch = sw_row[0] if sw_row else ''
        porta = sw_row[1] if sw_row else ''
        logs.append(dict(
            nome=row[0], ip=row[1], sucesso=row[2], timestamp=row[3], sala=row[4] or 'Sem sala', mac=mac, switch=switch, porta=porta
        ))
    conn.close()
    return jsonify(logs)

@app.route('/ping-equipamentos.html')
@login_required
def ping_equipamentos_html():
    return send_from_directory(os.path.dirname(__file__), 'ping-equipamentos.html')

@app.route('/ping-logs', methods=['DELETE'])
@admin_required
def limpar_ping_logs():            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM ping_logs')
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/empresa_atual')
@login_required
def empresa_atual():            conn = get_postgres_connection()
    cur = conn.cursor()
    # Removido - tabela empresas não existe mais no banco unificado
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify({'nome': row[0], 'logo': row[1]})
    return jsonify({'erro': 'Empresa não encontrada!'}), 404

@app.route('/upload-foto-sala', methods=['POST'])
def upload_foto_sala():
    if 'foto' not in request.files:
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum arquivo enviado'})
    file = request.files['foto']
    if not file.filename:
    # Removido - não necessário no banco unificado
    pasta = os.path.join('static', 'img', 'fotos-salas', empresa_dir)
    os.makedirs(pasta, exist_ok=True)
    filename = cast(str, file.filename)
    caminho = os.path.join(pasta, filename)
    file.save(caminho)
    return jsonify({'status': 'ok', 'caminho': f'static/img/fotos-salas/{empresa_dir}/{filename}'})

@app.route('/fotos-salas')
def fotos_salas():        return jsonify({'imagens': []})
    # Removido - não necessário no banco unificado
    pasta = os.path.join('static', 'img', 'fotos-salas', empresa_dir)
    if not os.path.exists(pasta):
        return jsonify({'imagens': []})
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return jsonify({'imagens': [f'/static/img/fotos-salas/{empresa_dir}/{arq}' for arq in arquivos]})

@app.route('/upload-fotos-salas.html')
def upload_fotos_salas_html():
    return send_from_directory(os.path.dirname(__file__), 'upload-fotos-salas.html')

@app.route('/conexoes-equipamentos.html')
@tecnico_required
def conexoes_equipamentos_html():
    return send_from_directory(os.path.dirname(__file__), 'conexoes-equipamentos.html')

@app.route('/api/equipamentos-imagens')
@login_required
def equipamentos_imagens():
    pasta = os.path.join(os.path.dirname(__file__), 'static', 'img', 'equipamentos')
    extensoes = ('*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg')
    arquivos = []
    for ext in extensoes:
        arquivos.extend(glob.glob(os.path.join(pasta, ext)))
    # Caminhos relativos para uso no frontend, sempre começando com /static/
    imagens = ['/static/img/equipamentos/' + os.path.basename(a) for a in arquivos]
    return jsonify(sorted(imagens))

@app.route('/api/salas', methods=['GET'])
@login_required
def api_salas():            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nome FROM salas')
    salas = [{'id': row[0], 'nome': row[1]} for row in cur.fetchall()]
    conn.close()
    return jsonify(salas)

@app.route('/api/salas/<int:sala_id>/layout', methods=['POST'])
@login_required
def salvar_layout_sala(sala_id):            layout = request.get_json()
    if not layout:
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    # Cria a tabela se não existir
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sala_layouts (
            sala_id INTEGER PRIMARY KEY,
            layout_json TEXT,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Salva ou atualiza o layout
    cur.execute('''
        INSERT INTO sala_layouts (sala_id, layout_json, atualizado_em)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT(sala_id) DO UPDATE SET
            layout_json=excluded.layout_json,
            atualizado_em=CURRENT_TIMESTAMP
    ''', (sala_id, json.dumps(layout)))
    conn.commit()
    conn.close()
    # Adiciona log da ação
    usuario = session.get('username', 'desconhecido')
    registrar_log(usuario, 'salvar_layout', f'sala_id={sala_id}', 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/api/salas/<int:sala_id>/layout', methods=['GET'])
@login_required
def obter_layout_sala(sala_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT layout_json FROM sala_layouts WHERE sala_id=%s', (sala_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return jsonify(json.loads(row[0]))
    return jsonify({'erro': 'Nenhum layout salvo para esta sala.'}), 404

@app.route('/api/salas/<int:sala_id>/conexoes-reais', methods=['GET'])
@login_required
def obter_conexoes_reais_sala(sala_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Buscar conexões de cabos ativas na sala
    cur.execute('''
        SELECT cc.id, cc.cabo_id, cc.equipamento_origem_id, cc.equipamento_destino_id,
               cc.porta_origem, cc.porta_destino, cc.sala_id, cc.observacao,
               c.codigo_unico as codigo_cabo, c.tipo as tipo_cabo, c.comprimento, c.marca, c.modelo,
               eo.nome as equipamento_origem, ed.nome as equipamento_destino,
               CASE WHEN cc.data_desconexao IS NULL THEN 1 ELSE 0 END as ativo
        FROM conexoes_cabos cc
        JOIN cabos c ON cc.cabo_id = c.id
        LEFT JOIN equipamentos eo ON cc.equipamento_origem_id = eo.id
        LEFT JOIN equipamentos ed ON cc.equipamento_destino_id = ed.id
        WHERE cc.sala_id = %s AND cc.data_desconexao IS NULL
        ORDER BY cc.data_conexao DESC
    ''', (sala_id,))
    
    rows = cur.fetchall()
    conn.close()
    
    conexoes = []
    for row in rows:
        conexao = {
            'id': row[0],
            'cabo_id': row[1],
            'equipamento_origem_id': row[2],
            'equipamento_destino_id': row[3],
            'porta_origem': row[4],
            'porta_destino': row[5],
            'sala_id': row[6],
            'observacao': row[7],
            'codigo_cabo': row[8],
            'tipo_cabo': row[9],
            'comprimento': row[10],
            'marca': row[11],
            'modelo': row[12],
            'equipamento_origem': row[13],
            'equipamento_destino': row[14],
            'ativo': bool(row[15])
        }
        conexoes.append(conexao)
    
    return jsonify(conexoes)

@app.route('/api/salas/<int:sala_id>/layout-hibrido', methods=['GET'])
@login_required
def obter_layout_hibrido_sala(sala_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Buscar layout manual
    cur.execute('SELECT layout_json FROM sala_layouts WHERE sala_id=%s', (sala_id,))
    layout_row = cur.fetchone()
    
    # Buscar conexões reais
    cur.execute('''
        SELECT cc.id, cc.cabo_id, cc.equipamento_origem_id, cc.equipamento_destino_id,
               cc.porta_origem, cc.porta_destino, cc.sala_id, cc.observacao,
               c.codigo_unico as codigo_cabo, c.tipo as tipo_cabo, c.comprimento, c.marca, c.modelo,
               eo.nome as equipamento_origem, ed.nome as equipamento_destino,
               CASE WHEN cc.data_desconexao IS NULL THEN 1 ELSE 0 END as ativo
        FROM conexoes_cabos cc
        JOIN cabos c ON cc.cabo_id = c.id
        LEFT JOIN equipamentos eo ON cc.equipamento_origem_id = eo.id
        LEFT JOIN equipamentos ed ON cc.equipamento_destino_id = ed.id
        WHERE cc.sala_id = %s AND cc.data_desconexao IS NULL
        ORDER BY cc.data_conexao DESC
    ''', (sala_id,))
    
    conexoes_rows = cur.fetchall()
    conn.close()
    
    # Preparar resultado
    resultado = {
        'items': [],
        'conns': []
    }
    
    # Adicionar layout manual se existir
    if layout_row and layout_row[0]:
        layout_manual = json.loads(layout_row[0])
        resultado['items'] = layout_manual.get('items', [])
        # Não incluir conexões manuais no híbrido
        # resultado['conns'] = layout_manual.get('conns', [])
    
    # Função para definir cor baseada no tipo de cabo
    def get_cor_por_tipo_cabo(tipo_cabo):
        cores = {
            'HDMI': '#e74c3c',      # Vermelho
            'VGA': '#3498db',       # Azul
            'USB': '#f39c12',       # Laranja
            'RJ45': '#27ae60',      # Verde
            'Audio': '#9b59b6',     # Roxo
            'Power': '#e67e22',     # Laranja escuro
            'Dante': '#1abc9c',     # Verde água
            'Serial': '#34495e',    # Cinza escuro
            'Fiber': '#f1c40f',     # Amarelo
            'Coaxial': '#95a5a6'    # Cinza
        }
        return cores.get(tipo_cabo.upper(), '#e74c3c')  # Vermelho como padrão
    
    # Adicionar conexões reais
    conexoes_reais = []
    for row in conexoes_rows:
        tipo_cabo = row[9] or 'Desconhecido'
        cor_cabo = get_cor_por_tipo_cabo(tipo_cabo)
        
        conexao = {
            'id': f"real_{row[0]}",
            'fromId': f"equip_{row[2]}" if row[2] else None,
            'toId': f"equip_{row[3]}" if row[3] else None,
            'name': f"{row[8]} ({tipo_cabo})",
            'label': f"{row[8]} ({tipo_cabo})",
            'color': cor_cabo,
            'fontSize': 12,
            'tipo_cabo': tipo_cabo,
            'codigo_cabo': row[8],
            'equipamento_origem': row[13],
            'equipamento_destino': row[14],
            'porta_origem': row[4],
            'porta_destino': row[5],
            'is_real': True
        }
        conexoes_reais.append(conexao)
    
    resultado['conns'] = conexoes_reais
    
    return jsonify(resultado)

@app.route('/visualizar-layout-sala.html')
@login_required
def visualizar_layout_html():
    return send_from_directory('.', 'visualizar-layout-sala.html')

@app.route('/api/salas-com-layout', methods=['GET'])
@login_required
def salas_com_layout():            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT s.id, s.nome
        FROM salas s
        JOIN sala_layouts l ON l.sala_id = s.id
    ''')
    salas = [{'id': row[0], 'nome': row[1]} for row in cur.fetchall()]
    conn.close()
    return jsonify(salas)

@app.route('/visualizar-switch-sala.html')
@login_required
def visualizar_switch_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'visualizar-switch-sala.html')

@app.route('/api/salas/<int:sala_id>/switches-usados')
@login_required
def switches_usados_sala(sala_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Buscar switches que têm conexão com equipamentos da sala específica
    # Incluindo tanto conexões via patch panel quanto conexões diretas
    cur.execute('''
        SELECT DISTINCT s.id as switch_id, s.nome as switch_nome, s.marca as switch_marca, s.modelo as switch_modelo
        FROM switches s
        JOIN switch_portas sp ON s.id = sp.switch_id
        LEFT JOIN patch_panel_portas ppp ON sp.switch_id = ppp.switch_id AND sp.numero_porta = ppp.porta_switch
        LEFT JOIN equipamentos e1 ON ppp.equipamento_id = e1.id
        LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
        LEFT JOIN equipamentos e2 ON c.equipamento_id = e2.id
        WHERE (e1.sala_id = %s OR e2.sala_id = %s)
        ORDER BY s.id
    ''', (sala_id, sala_id))
    
    switches_rows = cur.fetchall()
    switches = {}
    
    def extrair_numero_switch(nome):
        import re
        match = re.search(r'Switch\s*(\d+)', nome, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    for switch_id, switch_nome, switch_marca, switch_modelo in switches_rows:
        numero_logico = extrair_numero_switch(switch_nome)
        if numero_logico is None:
            numero_logico = switch_id
        
        # Buscar todas as portas do switch (sem duplicatas)
        cur.execute('''
            SELECT DISTINCT sp.numero_porta, sp.descricao
            FROM switch_portas sp
            WHERE sp.switch_id = %s
            ORDER BY sp.numero_porta
        ''', (switch_id,))
        
        portas_data = []
        for porta_row in cur.fetchall():
            numero_porta, descricao = porta_row
            
            # Verificar se a porta está mapeada para patch panel
            cur.execute('''
                SELECT pp.nome, ppp.numero_porta, ppp.equipamento_id
                FROM patch_panel_portas ppp
                JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
                LEFT JOIN equipamentos e ON ppp.equipamento_id = e.id
                WHERE ppp.switch_id = %s AND ppp.porta_switch = %s
            ''', (switch_id, numero_porta))
            
            patch_panel_row = cur.fetchone()
            
            # Verificar se a porta tem conexão direta
            cur.execute('''
                SELECT c.equipamento_id
                FROM conexoes c
                JOIN switch_portas sp ON c.porta_id = sp.id
                WHERE sp.switch_id = %s AND sp.numero_porta = %s AND c.status = 'ativa'
            ''', (switch_id, numero_porta))
            
            conexao_direta_row = cur.fetchone()
            
            if patch_panel_row:
                # Porta mapeada para patch panel
                patch_panel_nome, porta_patch_panel, equipamento_id = patch_panel_row
                
                if equipamento_id:
                    # Verificar se o equipamento é da sala específica
                    cur.execute('''
                        SELECT e.nome, e.tipo, e.marca, s.nome as sala_nome
                        FROM equipamentos e
                        LEFT JOIN salas s ON e.sala_id = s.id
                        WHERE e.id = %s AND e.sala_id = %s
                    ''', (equipamento_id, sala_id))
                    
                    equip_row = cur.fetchone()
                    if equip_row:
                        # Equipamento da sala específica - OCUPADA com destaque
                        cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('ip1','ip2','mac1','mac2')", (equipamento_id,))
                        dados = {chave: valor for chave, valor in cur.fetchall()}
                        
                        equipamento_info = {
                            'nome': equip_row[0],
                            'tipo': equip_row[1],
                            'marca': equip_row[2],
                            'sala_nome': equip_row[3],
                            'ip1': dados.get('ip1', ''),
                            'ip2': dados.get('ip2', ''),
                            'mac1': dados.get('mac1', ''),
                            'mac2': dados.get('mac2', '')
                        }
                        
                        porta_info = {
                            'numero': numero_porta,
                            'status': 'ocupada',
                            'sala_especifica': True,
                            'patch_panel_info': {
                                'nome': patch_panel_nome,
                                'porta_patch_panel': porta_patch_panel,
                                'equipamento': equipamento_info
                            }
                        }
                    else:
                        # Equipamento de outra sala - OCUPADA sem destaque
                        cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('ip1','ip2','mac1','mac2')", (equipamento_id,))
                        dados = {chave: valor for chave, valor in cur.fetchall()}
                        
                        cur.execute('''
                            SELECT e.nome, e.tipo, e.marca, s.nome as sala_nome
                            FROM equipamentos e
                            LEFT JOIN salas s ON e.sala_id = s.id
                            WHERE e.id = %s
                        ''', (equipamento_id,))
                        
                        equip_row = cur.fetchone()
                        equipamento_info = {
                            'nome': equip_row[0],
                            'tipo': equip_row[1],
                            'marca': equip_row[2],
                            'sala_nome': equip_row[3],
                            'ip1': dados.get('ip1', ''),
                            'ip2': dados.get('ip2', ''),
                            'mac1': dados.get('mac1', ''),
                            'mac2': dados.get('mac2', '')
                        }
                        
                        porta_info = {
                            'numero': numero_porta,
                            'status': 'ocupada',
                            'sala_especifica': False,
                            'patch_panel_info': {
                                'nome': patch_panel_nome,
                                'porta_patch_panel': porta_patch_panel,
                                'equipamento': equipamento_info
                            }
                        }
                else:
                    # Mapeada sem equipamento - MAPEADA
                    porta_info = {
                        'numero': numero_porta,
                        'status': 'mapeada',
                        'sala_especifica': False,
                        'patch_panel_info': {
                            'nome': patch_panel_nome,
                            'porta_patch_panel': porta_patch_panel
                        }
                    }
            elif conexao_direta_row:
                # Porta com conexão direta
                equipamento_id = conexao_direta_row[0]
                
                # Verificar se o equipamento é da sala específica
                cur.execute('''
                    SELECT e.nome, e.tipo, e.marca, s.nome as sala_nome
                    FROM equipamentos e
                    LEFT JOIN salas s ON e.sala_id = s.id
                    WHERE e.id = %s AND e.sala_id = %s
                ''', (equipamento_id, sala_id))
                
                equip_row = cur.fetchone()
                if equip_row:
                    # Equipamento da sala específica - OCUPADA com destaque
                    cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('ip1','ip2','mac1','mac2')", (equipamento_id,))
                    dados = {chave: valor for chave, valor in cur.fetchall()}
                    
                    equipamento_info = {
                        'nome': equip_row[0],
                        'tipo': equip_row[1],
                        'marca': equip_row[2],
                        'sala_nome': equip_row[3],
                        'ip1': dados.get('ip1', ''),
                        'ip2': dados.get('ip2', ''),
                        'mac1': dados.get('mac1', ''),
                        'mac2': dados.get('mac2', '')
                    }
                    
                    porta_info = {
                        'numero': numero_porta,
                        'status': 'ocupada',
                        'sala_especifica': True,
                        'equipamento_info': equipamento_info
                    }
                else:
                    # Equipamento de outra sala - OCUPADA sem destaque
                    cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=%s AND chave IN ('ip1','ip2','mac1','mac2')", (equipamento_id,))
                    dados = {chave: valor for chave, valor in cur.fetchall()}
                    
                    cur.execute('''
                        SELECT e.nome, e.tipo, e.marca, s.nome as sala_nome
                        FROM equipamentos e
                        LEFT JOIN salas s ON e.sala_id = s.id
                        WHERE e.id = %s
                    ''', (equipamento_id,))
                    
                    equip_row = cur.fetchone()
                    equipamento_info = {
                        'nome': equip_row[0],
                        'tipo': equip_row[1],
                        'marca': equip_row[2],
                        'sala_nome': equip_row[3],
                        'ip1': dados.get('ip1', ''),
                        'ip2': dados.get('ip2', ''),
                        'mac1': dados.get('mac1', ''),
                        'mac2': dados.get('mac2', '')
                    }
                    
                    porta_info = {
                        'numero': numero_porta,
                        'status': 'ocupada',
                        'sala_especifica': False,
                        'equipamento_info': equipamento_info
                    }
            else:
                # Porta livre
                porta_info = {
                    'numero': numero_porta,
                    'status': 'livre',
                    'sala_especifica': False
                }
            
            portas_data.append(porta_info)
        
        switches[numero_logico] = {
            'id': switch_id,
            'nome': switch_nome,
            'marca': switch_marca,
            'modelo': switch_modelo,
            'portas': portas_data
        }
    
    conn.close()
    result = list(switches.values())
    return jsonify(result)

def master_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('nivel') != 'master':
            return jsonify({'erro': 'Acesso restrito ao master'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/usuarios', methods=['POST'])
@master_required
def admin_criar_usuario():
    data = request.json
    if not data:
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    nome = data.get('nome','').strip()
    username = data.get('username','').strip()
    senha = data.get('senha','')
    nivel = data.get('nivel','usuario')
    if not nome or not username or not senha or not nivel:
        return jsonify({'erro': 'Todos os campos são obrigatórios!'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM usuarios WHERE username=%s', (username,))
    if cur.fetchone():
        conn.close()
        return jsonify({'erro': 'Usuário já existe!'}), 400
    cur.execute('INSERT INTO usuarios (nome, username, senha, nivel) VALUES (%s, %s, %s, %s)', (nome, username, senha, nivel))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/usuarios', methods=['GET'])
@master_required
def admin_listar_usuarios():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, nome, nivel FROM usuarios')
    usuarios = [dict(id=row[0], username=row[1], nome=row[2], nivel=row[3]) for row in cur.fetchall()]
    conn.close()
    return jsonify(usuarios)

@app.route('/admin/empresas', methods=['GET'])
@master_required
def admin_listar_empresas():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nome FROM empresas')
    empresas = [dict(id=row[0], nome=row[1]) for row in cur.fetchall()]
    conn.close()
    return jsonify(empresas)

@app.route('/admin/vinculos', methods=['GET'])
@master_required
def admin_listar_vinculos():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT usuario_id, empresa_id FROM usuario_empresas')
    vinculos = [dict(usuario_id=row[0], empresa_id=row[1]) for row in cur.fetchall()]
    conn.close()
    return jsonify(vinculos)

@app.route('/admin/vinculos', methods=['POST'])
@master_required
def admin_adicionar_vinculo():
    data = request.json
    if not data:
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    usuario_id = data.get('usuario_id')
    empresa_id = data.get('empresa_id')
    if not usuario_id or not empresa_id:
        return jsonify({'erro': 'usuario_id e empresa_id são obrigatórios'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (%s, %s)', (usuario_id, empresa_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/vinculos', methods=['DELETE'])
@master_required
def admin_remover_vinculo():
    data = request.json
    if not data:
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    usuario_id = data.get('usuario_id')
    empresa_id = data.get('empresa_id')
    if not usuario_id or not empresa_id:
        return jsonify({'erro': 'usuario_id e empresa_id são obrigatórios'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM usuario_empresas WHERE usuario_id=%s AND empresa_id=%s', (usuario_id, empresa_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/usuarios/<int:usuario_id>/nivel', methods=['PUT'])
@master_required
def admin_alterar_nivel_usuario(usuario_id):
    data = request.json
    if not data:
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    novo_nivel = data.get('nivel')
    if not novo_nivel:
        return jsonify({'erro': 'nivel é obrigatório'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('UPDATE usuarios SET nivel=%s WHERE id=%s', (novo_nivel, usuario_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/config-master.html')
@master_required
def config_master_html():
    return send_from_directory(os.path.dirname(__file__), 'config-master.html')

@app.route('/api/salas/<int:id>', methods=['GET'])
@login_required
def api_get_sala(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, descricao, foto, fotos, andar_id FROM salas WHERE id=%s', (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(dict(id=row[0], nome=row[1], tipo=row[2], descricao=row[3], foto=row[4], fotos=row[5], andar_id=row[6]))
    return jsonify({'erro': 'Sala não encontrada'}), 404

@app.route('/dashboard.html')
@login_required
def dashboard_html():
    return send_from_directory(os.path.dirname(__file__), 'dashboard.html')

# --- API DE CABOS ---

@app.route('/cabos', methods=['POST'])
@tecnico_required
def criar_cabo():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    # Validar campos obrigatórios
    if not dados.get('codigo_unico') or not dados.get('tipo'):
        return jsonify({'status': 'erro', 'mensagem': 'Código único e tipo são obrigatórios'}), 400
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO cabos (codigo_unico, tipo, comprimento, marca, modelo, descricao, foto, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            dados['codigo_unico'],
            dados['tipo'],
            dados.get('comprimento'),
            dados.get('marca'),
            dados.get('modelo'),
            dados.get('descricao'),
            dados.get('foto'),
            dados.get('status', 'funcionando')
        ))
        
        cabo_id = cur.lastrowid
        conn.commit()
        
        registrar_log(session.get('username'), 'criar_cabo', f'Cabo {dados["codigo_unico"]} criado', 'sucesso')
        return jsonify({'status': 'ok', 'cabo_id': cabo_id})
        
    except sqlite3.IntegrityError:
        return jsonify({'status': 'erro', 'mensagem': 'Código único já existe'}), 400
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500
    finally:
        conn.close()

@app.route('/cabos', methods=['GET'])
@login_required
def listar_cabos():            # Parâmetros de filtro
    status = request.args.get('status')
    tipo = request.args.get('tipo')
    conectado = request.args.get('conectado')  # 'true' para conectados, 'false' para em estoque
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    query = '''
        SELECT c.id, c.codigo_unico, c.tipo, c.comprimento, c.marca, c.modelo, 
               c.descricao, c.foto, c.status, c.data_criacao, c.data_modificacao,
               tc.descricao as tipo_descricao, tc.icone as tipo_icone,
               CASE WHEN EXISTS (SELECT 1 FROM conexoes_cabos cc WHERE cc.cabo_id = c.id AND cc.data_desconexao IS NULL) THEN 1 ELSE 0 END as conectado
        FROM cabos c
        LEFT JOIN tipos_cabos tc ON c.tipo = tc.nome
        WHERE 1=1
    '''
    params = []
    
    if status:
        query += ' AND c.status = %s'
        params.append(status)
    
    if tipo:
        query += ' AND c.tipo = %s'
        params.append(tipo)
    
    if conectado == 'true':
        query += ' AND EXISTS (SELECT 1 FROM conexoes_cabos cc WHERE cc.cabo_id = c.id AND cc.data_desconexao IS NULL)'
    elif conectado == 'false':
        query += ' AND NOT EXISTS (SELECT 1 FROM conexoes_cabos cc WHERE cc.cabo_id = c.id AND cc.data_desconexao IS NULL)'
    
    query += ' ORDER BY c.codigo_unico'
    
    cur.execute(query, params)
    rows = cur.fetchall()
    
    cabos = []
    for row in rows:
        cabo = {
            'id': row[0],
            'codigo_unico': row[1],
            'tipo': row[2],
            'comprimento': row[3],
            'marca': row[4],
            'modelo': row[5],
            'descricao': row[6],
            'foto': row[7],
            'status': row[8],
            'data_criacao': row[9],
            'data_modificacao': row[10],
            'tipo_descricao': row[11],
            'tipo_icone': row[12],
            'conectado': bool(row[13])
        }
        cabos.append(cabo)
    
    conn.close()
    return jsonify(cabos)

@app.route('/cabos/<int:id>', methods=['GET'])
@login_required
def get_cabo(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT c.id, c.codigo_unico, c.tipo, c.comprimento, c.marca, c.modelo, 
               c.descricao, c.foto, c.status, c.data_criacao, c.data_modificacao,
               tc.descricao as tipo_descricao, tc.icone as tipo_icone
        FROM cabos c
        LEFT JOIN tipos_cabos tc ON c.tipo = tc.nome
        WHERE c.id = %s
    ''', (id,))
    
    row = cur.fetchone()
    conn.close()
    
    if row:
        cabo = {
            'id': row[0],
            'codigo_unico': row[1],
            'tipo': row[2],
            'comprimento': row[3],
            'marca': row[4],
            'modelo': row[5],
            'descricao': row[6],
            'foto': row[7],
            'status': row[8],
            'data_criacao': row[9],
            'data_modificacao': row[10],
            'tipo_descricao': row[11],
            'tipo_icone': row[12]
        }
        return jsonify(cabo)
    
    return jsonify({'erro': 'Cabo não encontrado'}), 404

@app.route('/cabos/<int:id>', methods=['PUT'])
@tecnico_required
def atualizar_cabo(id):
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE cabos 
            SET codigo_unico = %s, tipo = %s, comprimento = %s, marca = %s, modelo = %s, 
                descricao = %s, foto = %s, status = %s
            WHERE id = %s
        ''', (
            dados.get('codigo_unico'),
            dados.get('tipo'),
            dados.get('comprimento'),
            dados.get('marca'),
            dados.get('modelo'),
            dados.get('descricao'),
            dados.get('foto'),
            dados.get('status'),
            id
        ))
        
        if cur.rowcount == 0:
            return jsonify({'status': 'erro', 'mensagem': 'Cabo não encontrado'}), 404
        
        conn.commit()
        registrar_log(session.get('username'), 'atualizar_cabo', f'Cabo ID {id} atualizado', 'sucesso')
        return jsonify({'status': 'ok'})
        
    except sqlite3.IntegrityError:
        return jsonify({'status': 'erro', 'mensagem': 'Código único já existe'}), 400
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500
    finally:
        conn.close()

@app.route('/cabos/<int:id>', methods=['DELETE'])
@admin_required
def excluir_cabo(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Verificar se o cabo está conectado
    cur.execute('SELECT COUNT(*) FROM conexoes_cabos WHERE cabo_id = %s AND data_desconexao IS NULL', (id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Não é possível excluir um cabo que está conectado'}), 400
    
    cur.execute('DELETE FROM cabos WHERE id = %s', (id,))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Cabo não encontrado'}), 404
    
    conn.commit()
    conn.close()
    
    registrar_log(session.get('username'), 'excluir_cabo', f'Cabo ID {id} excluído', 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/tipos-cabos', methods=['GET'])
@login_required
def tipos_cabos():            conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('SELECT nome, descricao, icone FROM tipos_cabos ORDER BY nome')
    rows = cur.fetchall()
    conn.close()
    
    tipos = [{'nome': row[0], 'descricao': row[1], 'icone': row[2]} for row in rows]
    return jsonify(tipos)

@app.route('/conexoes-cabos', methods=['POST'])
@tecnico_required
def criar_conexao_cabo():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    # Validar campos obrigatórios
    if not dados.get('cabo_id') or not dados.get('equipamento_origem_id'):
        return jsonify({'status': 'erro', 'mensagem': 'cabo_id e equipamento_origem_id são obrigatórios'}), 400
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se o cabo já está conectado
        cur.execute('SELECT COUNT(*) FROM conexoes_cabos WHERE cabo_id = %s AND data_desconexao IS NULL', (dados['cabo_id'],))
        if cur.fetchone()[0] > 0:
            return jsonify({'status': 'erro', 'mensagem': 'Cabo já está conectado a outro equipamento'}), 400
        
        cur.execute('''
            INSERT INTO conexoes_cabos (cabo_id, equipamento_origem_id, equipamento_destino_id, 
                                      porta_origem, porta_destino, sala_id, observacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            dados['cabo_id'],
            dados['equipamento_origem_id'],
            dados['equipamento_destino_id'],
            dados.get('porta_origem'),
            dados.get('porta_destino'),
            dados.get('sala_id'),
            dados.get('observacao')
        ))
        
        conexao_id = cur.lastrowid
        conn.commit()
        
        registrar_log(session.get('username'), 'criar_conexao_cabo', f'Conexão de cabo {dados["cabo_id"]} criada', 'sucesso')
        return jsonify({'status': 'ok', 'id': conexao_id})
        
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500
    finally:
        conn.close()

@app.route('/conexoes-cabos', methods=['GET'])
@login_required
def listar_conexoes_cabos():            conn = get_postgres_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT cc.id, cc.cabo_id, cc.equipamento_origem_id, cc.equipamento_destino_id,
               cc.porta_origem, cc.porta_destino, cc.sala_id, cc.observacao,
               cc.data_conexao, cc.data_desconexao,
               c.codigo_unico, c.tipo, c.comprimento, c.marca, c.modelo,
               eo.nome as equipamento_origem_nome, ed.nome as equipamento_destino_nome,
               s.nome as sala_nome
        FROM conexoes_cabos cc
        JOIN cabos c ON cc.cabo_id = c.id
        LEFT JOIN equipamentos eo ON cc.equipamento_origem_id = eo.id
        LEFT JOIN equipamentos ed ON cc.equipamento_destino_id = ed.id
        LEFT JOIN salas s ON cc.sala_id = s.id
        WHERE cc.data_desconexao IS NULL
        ORDER BY cc.data_conexao DESC
    ''')
    
    rows = cur.fetchall()
    conn.close()
    
    conexoes = []
    for row in rows:
        conexao = {
            'id': row[0],
            'cabo_id': row[1],
            'equipamento_origem_id': row[2],
            'equipamento_destino_id': row[3],
            'porta_origem': row[4],
            'porta_destino': row[5],
            'sala_id': row[6],
            'observacao': row[7],
            'data_conexao': row[8],
            'data_desconexao': row[9],
            'codigo_unico': row[10],
            'tipo': row[11],
            'comprimento': row[12],
            'marca': row[13],
            'modelo': row[14],
            'equipamento_origem_nome': row[15],
            'equipamento_destino_nome': row[16],
            'sala_nome': row[17]
        }
        conexoes.append(conexao)
    
    return jsonify(conexoes)

@app.route('/conexoes-cabos/<int:id>', methods=['DELETE'])
@tecnico_required
def desconectar_cabo(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    cur.execute('UPDATE conexoes_cabos SET data_desconexao = CURRENT_TIMESTAMP WHERE id = %s', (id,))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
    
    conn.commit()
    conn.close()
    
    registrar_log(session.get('username'), 'desconectar_cabo', f'Conexão de cabo {id} desconectada', 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/conexoes-cabos/sala/<int:sala_id>', methods=['GET'])
@login_required
def cabos_por_sala(sala_id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Buscar conexões diretas de cabos (excluindo conexões que vão para patch panels)
    cur.execute('''
        SELECT cc.id, cc.cabo_id, cc.equipamento_origem_id, cc.equipamento_destino_id,
               cc.porta_origem, cc.porta_destino, cc.sala_id, cc.observacao,
               cc.data_conexao, cc.data_desconexao,
               c.codigo_unico as codigo_cabo, c.tipo as tipo_cabo, c.comprimento, c.marca, c.modelo,
               eo.nome as equipamento_origem, ed.nome as equipamento_destino,
               s.nome as sala_nome,
               CASE WHEN cc.data_desconexao IS NULL THEN 1 ELSE 0 END as ativo,
               'cabo_direto' as tipo_conexao
        FROM conexoes_cabos cc
        LEFT JOIN cabos c ON cc.cabo_id = c.id
        LEFT JOIN equipamentos eo ON cc.equipamento_origem_id = eo.id
        LEFT JOIN equipamentos ed ON cc.equipamento_destino_id = ed.id
        LEFT JOIN salas s ON cc.sala_id = s.id
        WHERE cc.sala_id = %s 
        AND cc.data_desconexao IS NULL 
        AND c.id IS NOT NULL
        AND (ed.nome IS NULL OR ed.nome NOT LIKE '%Patch Panel%')
        AND NOT EXISTS (
            SELECT 1 FROM patch_panel_portas ppp 
            JOIN patch_panels pp ON ppp.patch_panel_id = pp.id 
            WHERE ppp.equipamento_id = cc.equipamento_origem_id 
            AND ppp.numero_porta = cc.porta_destino
        )
    ''', (sala_id,))
    
    conexoes_diretas = cur.fetchall()
    
    # Buscar conexões via patch panel (apenas se houver conexão real de cabo)
    cur.execute('''
        SELECT 
            ppp.id as id,
            cc.cabo_id,
            e.id as equipamento_origem_id,
            cc.equipamento_destino_id,
            cc.porta_origem,
            ppp.numero_porta as porta_destino,
            e.sala_id,
            cc.observacao,
            cc.data_conexao,
            cc.data_desconexao,
            c.codigo_unico as codigo_cabo,
            c.tipo as tipo_cabo,
            c.comprimento,
            c.marca,
            c.modelo,
            e.nome as equipamento_origem,
            pp.nome as equipamento_destino,
            s.nome as sala_nome,
            CASE WHEN cc.data_desconexao IS NULL THEN 1 ELSE 0 END as ativo,
            'patch_panel' as tipo_conexao
        FROM patch_panel_portas ppp
        JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
        JOIN equipamentos e ON ppp.equipamento_id = e.id
        LEFT JOIN salas s ON e.sala_id = s.id
        INNER JOIN conexoes_cabos cc ON cc.equipamento_origem_id = e.id AND cc.equipamento_destino_id = pp.id AND cc.porta_destino = ppp.numero_porta AND cc.data_desconexao IS NULL
        INNER JOIN cabos c ON cc.cabo_id = c.id
        WHERE e.sala_id = %s AND ppp.status = 'ocupada'
    ''', (sala_id,))
    
    conexoes_patch_panel = cur.fetchall()
    
    conn.close()
    
    # Combinar os resultados
    todas_conexoes = conexoes_diretas + conexoes_patch_panel
    
    cabos = []
    for row in todas_conexoes:
        cabo = {
            'id': row[0],
            'cabo_id': row[1],
            'equipamento_origem_id': row[2],
            'equipamento_destino_id': row[3],
            'porta_origem': row[4],
            'porta_destino': row[5],
            'sala_id': row[6],
            'observacao': row[7],
            'data_conexao': row[8],
            'data_desconexao': row[9],
            'codigo_cabo': row[10],
            'tipo_cabo': row[11],
            'comprimento': row[12],
            'marca': row[13],
            'modelo': row[14],
            'equipamento_origem': row[15],
            'equipamento_destino': row[16],
            'sala_nome': row[17],
            'ativo': bool(row[18]),
            'tipo_conexao': row[19] if len(row) > 19 else 'cabo_direto'
        }
        cabos.append(cabo)
    
    # Ordenar por data de conexão (conexões diretas primeiro, depois patch panel)
    cabos.sort(key=lambda x: (x['tipo_conexao'] == 'patch_panel', x.get('data_conexao', '')))
    
    return jsonify(cabos)

@app.route('/logs/sala/<int:sala_id>', methods=['GET'])
@login_required
def logs_por_sala(sala_id):
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        # Filtra logs que mencionam a sala pelo ID ("ID=<sala_id>" ou "sala_id=<sala_id>")
        sala_id_str = f"ID={sala_id}"
        sala_id_alt = f"sala_id={sala_id}"
        logs_sala = [l for l in logs if sala_id_str in l or sala_id_alt in l]
        logs_sala = logs_sala[-100:] if len(logs_sala) > 100 else logs_sala
        logs_sala.reverse()  # Mais recentes primeiro
        return jsonify({'status': 'ok', 'logs': logs_sala, 'total_logs': len(logs_sala)})
    except FileNotFoundError:
        return jsonify({'status': 'ok', 'logs': [], 'total_logs': 0})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': f'Erro ao ler logs: {str(e)}'}), 500

@app.route('/historico-sala.html')
@login_required
def historico_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'historico-sala.html')

@app.route('/dashboard-sala.html')
@login_required
def dashboard_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'dashboard-sala.html')

@app.route('/exportar-dados.html')
@login_required
def exportar_dados_html():
    return send_from_directory(os.path.dirname(__file__), 'exportar-dados.html')

@app.route('/cabos/<int:id>/defeito', methods=['POST'])
@admin_required
def marcar_cabo_defeito(id):            dados = request.json or {}
    motivo = dados.get('motivo', 'Substituição automática')
    conn = get_postgres_connection()
    cur = conn.cursor()
    # Buscar descricao atual
    cur.execute('SELECT descricao FROM cabos WHERE id=%s', (id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Cabo não encontrado'}), 404
    descricao_atual = row[0] or ''
    nova_obs = f"[DEF. {motivo} em {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}] "
    nova_descricao = (descricao_atual + '\n' + nova_obs).strip()
    cur.execute('UPDATE cabos SET status=%s, descricao=%s WHERE id=%s', ('defeito', nova_descricao, id))
    conn.commit()
    conn.close()
    registrar_log(session.get('username'), 'marcar_cabo_defeito', f'Cabo ID {id} marcado como defeito', 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/cabos/<int:id>/reparar', methods=['POST'])
@admin_required
def reparar_cabo(id):            dados = request.json or {}
    novo_status = dados.get('status', 'funcionando')
    justificativa = dados.get('justificativa', 'Reparação realizada')
    if novo_status not in ['funcionando', 'em_estoque']:
        return jsonify({'status': 'erro', 'mensagem': 'Status inválido. Use "funcionando" ou "em_estoque"'}), 400
    conn = get_postgres_connection()
    cur = conn.cursor()
    # Verificar se o cabo existe e está com defeito
    cur.execute('SELECT status, descricao FROM cabos WHERE id=%s', (id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Cabo não encontrado'}), 404
    if row[0] != 'defeito':
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Cabo não está com defeito'}), 400
    descricao_atual = row[1] or ''
    nova_obs = f"[REP. {justificativa} em {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}] "
    nova_descricao = (descricao_atual + '\n' + nova_obs).strip()
    cur.execute('UPDATE cabos SET status=%s, descricao=%s WHERE id=%s', (novo_status, nova_descricao, id))
    conn.commit()
    conn.close()
    registrar_log(session.get('username'), 'reparar_cabo', f'Cabo ID {id} reparado - Status: {novo_status}', 'sucesso')
    return jsonify({'status': 'ok'})

# --- ROTAS DE PATCH PANELS ---

@app.route('/patch-panels', methods=['POST'])
@admin_required
def criar_patch_panel():
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se já existe patch panel com o mesmo nome no andar
        cur.execute('SELECT id FROM patch_panels WHERE andar = %s AND nome = %s', (dados['andar'], dados['nome']))
        if cur.fetchone():
            return jsonify({'erro': f'Já existe um patch panel com o nome "{dados["nome"]}" no {dados["andar"]}º andar!'}), 400
        
        # Criar tabela se não existir
        cur.execute('''
            CREATE TABLE IF NOT EXISTS patch_panels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                andar INTEGER NOT NULL,
                prefixo_keystone TEXT NOT NULL,
                porta_inicial INTEGER NOT NULL DEFAULT 1,
                num_portas INTEGER NOT NULL DEFAULT 500,
                status TEXT DEFAULT 'ativo',
                descricao TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Gerar código único (múltiplos patch panels por andar)
        andar_base = 20 + dados['andar']
        
        # Contar quantos patch panels já existem no andar
        cur.execute('SELECT COUNT(*) FROM patch_panels WHERE andar = %s', (dados['andar'],))
        count = cur.fetchone()[0]
        
        # Gerar código sequencial
        codigo = f"PP{andar_base}-{(count + 1):02d}"
        
        # Inserir patch panel
        cur.execute('''
            INSERT INTO patch_panels (codigo, nome, andar, prefixo_keystone, porta_inicial, num_portas, status, descricao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (codigo, dados['nome'], dados['andar'], dados['prefixo_keystone'], 1, dados.get('num_portas', 500), dados.get('status', 'ativo'), dados.get('descricao')))
        
        patch_panel_id = cur.lastrowid
        
        # Criar portas do patch panel
        cur.execute('''
            CREATE TABLE IF NOT EXISTS patch_panel_portas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patch_panel_id INTEGER NOT NULL,
                numero_porta INTEGER NOT NULL,
                switch_id INTEGER,
                porta_switch INTEGER,
                status TEXT DEFAULT 'livre',
                equipamento_id INTEGER,
                data_conexao TIMESTAMP,
                FOREIGN KEY (patch_panel_id) REFERENCES patch_panels (id),
                FOREIGN KEY (switch_id) REFERENCES switches (id),
                FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id),
                UNIQUE(patch_panel_id, numero_porta)
            )
        ''')
        
        # Inserir portas sempre começando do 1
        for i in range(dados.get('num_portas', 500)):
            numero_porta = i + 1
            cur.execute('''
                INSERT INTO patch_panel_portas (patch_panel_id, numero_porta)
                VALUES (%s, %s)
            ''', (patch_panel_id, numero_porta))
        
        conn.commit()
        
        # Registrar log
        detalhes = f"Patch Panel criado: {dados['nome']} - {dados.get('num_portas', 500)} portas (1-{dados.get('num_portas', 500)})"
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_PATCH_PANEL', detalhes, 'sucesso')
        
        return jsonify({'status': 'ok', 'patch_panel_id': patch_panel_id})
        
    except Exception as e:
        conn.rollback()
        detalhes = f"Erro ao criar patch panel: {str(e)}"
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_PATCH_PANEL', detalhes, 'erro')
        return jsonify({'status': 'erro', 'mensagem': f'Erro ao criar patch panel: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels', methods=['GET'])
@login_required
def listar_patch_panels():            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT pp.id, pp.codigo, pp.nome, pp.andar, pp.porta_inicial, pp.num_portas, pp.status, pp.descricao, pp.data_criacao, pp.prefixo_keystone
            FROM patch_panels pp
            ORDER BY pp.andar, pp.nome
        ''')
        
        patch_panels = []
        for row in cur.fetchall():
            andar_nome = f"{row[3]}º Andar" if row[3] > 0 else "Térreo"
            porta_final = row[4] + row[5] - 1  # porta_inicial + num_portas - 1
            patch_panels.append({
                'id': row[0],
                'codigo': row[1],
                'nome': row[2],
                'andar': row[3],
                'andar_nome': andar_nome,
                'porta_inicial': row[4],
                'porta_final': porta_final,
                'num_portas': row[5],
                'status': row[6],
                'descricao': row[7],
                'data_criacao': row[8]
            })
        
        return jsonify(patch_panels)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar patch panels: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels/validar-portas', methods=['GET'])
@login_required
def validar_portas_patch_panel():            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Buscar todas as portas existentes em patch panels
        cur.execute('''
            SELECT pp.porta_inicial, pp.num_portas
            FROM patch_panels pp
        ''')
        
        portas_existentes = []
        for row in cur.fetchall():
            porta_inicial = row[0]
            num_portas = row[1]
            # Adicionar todas as portas deste patch panel
            for i in range(num_portas):
                portas_existentes.append(porta_inicial + i)
        
        return jsonify({
            'status': 'ok', 
            'portas_existentes': portas_existentes
        })
        
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': f'Erro ao validar portas: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels/andar/<int:andar>', methods=['GET'])
@login_required
def listar_patch_panels_por_andar(andar):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT pp.id, pp.codigo, pp.nome, pp.andar, pp.porta_inicial, pp.num_portas, pp.status, pp.descricao, pp.data_criacao
            FROM patch_panels pp
            WHERE pp.andar = %s
            ORDER BY pp.nome
        ''', (andar,))
        
        patch_panels = []
        for row in cur.fetchall():
            andar_nome = f"{row[3]}º Andar" if row[3] > 0 else "Térreo"
            porta_final = row[4] + row[5] - 1  # porta_inicial + num_portas - 1
            patch_panels.append({
                'id': row[0],
                'codigo': row[1],
                'nome': row[2],
                'andar': row[3],
                'andar_nome': andar_nome,
                'porta_inicial': row[4],
                'porta_final': porta_final,
                'num_portas': row[5],
                'status': row[6],
                'descricao': row[7],
                'data_criacao': row[8]
            })
        
        return jsonify(patch_panels)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar patch panels do andar: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels/<int:id>', methods=['PUT'])
@login_required
def atualizar_patch_panel(id):            dados = request.get_json()
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se já existe outro patch panel com o mesmo nome no andar
        cur.execute('SELECT id FROM patch_panels WHERE andar = %s AND nome = %s AND id != %s', (dados['andar'], dados['nome'], id))
        if cur.fetchone():
            return jsonify({'erro': f'Já existe um patch panel com o nome "{dados["nome"]}" no {dados["andar"]}º andar!'}), 400
        
        # Buscar dados atuais do patch panel
        cur.execute('SELECT porta_inicial, num_portas FROM patch_panels WHERE id = %s', (id,))
        dados_atuais = cur.fetchone()
        
        if not dados_atuais:
            return jsonify({'erro': 'Patch Panel não encontrado'}), 404
        
        porta_inicial_atual = dados_atuais[0]
        num_portas_atual = dados_atuais[1]
        porta_inicial_nova = dados.get('porta_inicial', 1)
        num_portas_nova = dados['num_portas']
        
        # Verificar se houve mudança na porta inicial ou número de portas
        recriar_portas = (porta_inicial_atual != porta_inicial_nova) or (num_portas_atual != num_portas_nova)
        
        # Atualizar patch panel
        cur.execute('''
            UPDATE patch_panels 
            SET nome = %s, andar = %s, porta_inicial = %s, num_portas = %s, status = %s, descricao = %s
            WHERE id = %s
        ''', (dados['nome'], dados['andar'], porta_inicial_nova, num_portas_nova, dados.get('status', 'ativo'), dados.get('descricao'), id))
        
        # Se houve mudança na numeração, recriar as portas
        if recriar_portas:
            # Verificar se há conexões ativas
            cur.execute('SELECT COUNT(*) FROM patch_panel_portas WHERE patch_panel_id = %s AND equipamento_id IS NOT NULL', (id,))
            conexoes_ativas = cur.fetchone()[0]
            
            if conexoes_ativas > 0:
                return jsonify({'erro': f'Não é possível alterar a numeração. Existem {conexoes_ativas} conexões ativas.'}), 400
            
            # Excluir portas existentes
            cur.execute('DELETE FROM patch_panel_portas WHERE patch_panel_id = %s', (id,))
            
            # Criar novas portas com a nova numeração
            for i in range(num_portas_nova):
                numero_porta = porta_inicial_nova + i
                cur.execute('''
                    INSERT INTO patch_panel_portas (patch_panel_id, numero_porta)
                    VALUES (%s, %s)
                ''', (id, numero_porta))
        
        conn.commit()
        
        # Registrar log
        detalhes = f"Patch Panel atualizado: {dados['nome']}"
        if recriar_portas:
            detalhes += f" - Portas recriadas: {porta_inicial_nova} a {porta_inicial_nova + num_portas_nova - 1}"
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_PATCH_PANEL', detalhes, 'sucesso')
        
        return jsonify({'status': 'ok', 'mensagem': 'Patch Panel atualizado com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        detalhes = f"Erro ao atualizar patch panel {id}: {str(e)}"
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_PATCH_PANEL', detalhes, 'erro')
        return jsonify({'erro': f'Erro ao atualizar patch panel: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels/<int:id>', methods=['DELETE'])
@login_required
def excluir_patch_panel(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se há conexões ativas
        cur.execute('SELECT COUNT(*) FROM patch_panel_portas WHERE patch_panel_id = %s AND equipamento_id IS NOT NULL', (id,))
        conexoes_ativas = cur.fetchone()[0]
        
        if conexoes_ativas > 0:
            return jsonify({'mensagem': f'Não é possível excluir o patch panel. Existem {conexoes_ativas} conexões ativas.'}), 400
        
        # Excluir portas do patch panel
        cur.execute('DELETE FROM patch_panel_portas WHERE patch_panel_id = %s', (id,))
        
        # Excluir patch panel
        cur.execute('DELETE FROM patch_panels WHERE id = %s', (id,))
        
        conn.commit()
        
        # Registrar log
        registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_PATCH_PANEL', f'Patch Panel ID {id} excluído', 'sucesso')
        
        return jsonify({'status': 'ok', 'mensagem': 'Patch Panel excluído com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'mensagem': f'Erro ao excluir patch panel: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panel-portas/<int:id>', methods=['PUT'])
@login_required
def atualizar_mapeamento_porta(id):            dados = request.get_json()
    
    # Validar dados
    switch_id = dados.get('switch_id')
    porta_switch = dados.get('porta_switch')
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    # Se ambos os valores são None ou vazios, limpar o mapeamento
    if not switch_id and not porta_switch:
        switch_id = None
        porta_switch = None
        # Manter o status atual se tem equipamento conectado, senão 'livre'
        cur.execute('SELECT equipamento_id FROM patch_panel_portas WHERE id = %s', (id,))
        result = cur.fetchone()
        if result and result[0]:
            status = 'ocupada'  # Mantém ocupada se tem equipamento
        else:
            status = 'livre'
    else:
        # Validar se ambos os valores estão presentes
        if not switch_id or not porta_switch:
            return jsonify({'erro': 'Switch ID e Porta Switch são obrigatórios para mapeamento'}), 400
        
        # Verificar se a porta tem equipamento conectado
        cur.execute('SELECT equipamento_id FROM patch_panel_portas WHERE id = %s', (id,))
        result = cur.fetchone()
        if result and result[0]:
            status = 'ocupada'  # Se tem equipamento, fica ocupada
        else:
            status = 'mapeada'  # Se não tem equipamento, fica mapeada
    
    try:
        # Verificar se a porta existe
        cur.execute('SELECT id FROM patch_panel_portas WHERE id = %s', (id,))
        if not cur.fetchone():
            return jsonify({'erro': 'Porta do patch panel não encontrada'}), 404
        
        # Atualizar mapeamento
        cur.execute('''
            UPDATE patch_panel_portas 
            SET switch_id = %s, porta_switch = %s, status = %s
            WHERE id = %s
        ''', (switch_id, porta_switch, status, id))
        
        # Atualizar status da porta do switch
        if switch_id and porta_switch:
            cur.execute('''
                UPDATE switch_portas 
                SET status = 'mapeada'
                WHERE switch_id = %s AND numero_porta = %s
            ''', (switch_id, porta_switch))
        else:
            # Se está removendo o mapeamento, buscar o switch_id e porta_switch antigos
            cur.execute('''
                SELECT switch_id, porta_switch FROM patch_panel_portas WHERE id = %s
            ''', (id,))
            old_mapping = cur.fetchone()
            
            if old_mapping and old_mapping[0] and old_mapping[1]:
                # Verificar se a porta do switch não tem equipamento conectado
                cur.execute('''
                    UPDATE switch_portas 
                    SET status = 'livre'
                    WHERE switch_id = %s AND numero_porta = %s AND id NOT IN (
                        SELECT porta_id FROM conexoes WHERE porta_id IS NOT NULL
                    )
                ''', (old_mapping[0], old_mapping[1]))
        
        conn.commit()
        
        # Registrar log
        detalhes = f"Porta {id} mapeada para Switch {switch_id}, Porta {porta_switch}" if switch_id else f"Mapeamento removido da porta {id}"
        registrar_log(session.get('username', 'desconhecido'), 'MAPEAR_PORTA_PATCH_PANEL', detalhes, 'sucesso')
        
        return jsonify({'status': 'ok', 'mensagem': 'Mapeamento atualizado com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        detalhes = f"Erro ao atualizar mapeamento da porta {id}: {str(e)}"
        registrar_log(session.get('username', 'desconhecido'), 'MAPEAR_PORTA_PATCH_PANEL', detalhes, 'erro')
        return jsonify({'erro': f'Erro ao atualizar mapeamento: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels/<int:id>/portas', methods=['GET'])
@login_required
def listar_portas_patch_panel(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT ppp.id, ppp.numero_porta, ppp.status, ppp.equipamento_id, ppp.switch_id, ppp.porta_switch,
                   e.nome as equipamento_nome, e.tipo as equipamento_tipo, e.sala_id as equipamento_sala_id,
                   pp.andar as patch_panel_andar, s.nome as switch_nome, sal.nome as equipamento_sala, 
                   pp.prefixo_keystone
            FROM patch_panel_portas ppp
            LEFT JOIN equipamentos e ON ppp.equipamento_id = e.id
            LEFT JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
            LEFT JOIN switches s ON ppp.switch_id = s.id
            LEFT JOIN salas sal ON e.sala_id = sal.id
            WHERE ppp.patch_panel_id = %s
            ORDER BY ppp.numero_porta
        ''', (id,))
        
        portas = []
        for row in cur.fetchall():
            portas.append({
                'id': row[0],
                'numero_porta': row[1],
                'status': row[2],
                'equipamento_id': row[3],
                'switch_id': row[4],
                'porta_switch': row[5],
                'equipamento_nome': row[6],
                'equipamento_tipo': row[7],
                'equipamento_sala_id': row[8],
                'switch_nome': row[10],
                'sala_nome': row[11],
                'prefixo_keystone': row[12]
            })
        
        return jsonify(portas)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar portas do patch panel: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panel-portas/<int:id>/conectar-equipamento', methods=['PUT'])
@login_required
def conectar_equipamento_patch_panel(id):            dados = request.get_json()
    equipamento_id = dados.get('equipamento_id')
    
    if not equipamento_id:
        return jsonify({'erro': 'ID do equipamento é obrigatório'}), 400
    
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se a porta existe e está livre
        cur.execute('SELECT id, status FROM patch_panel_portas WHERE id = %s', (id,))
        porta = cur.fetchone()
        if not porta:
            return jsonify({'erro': 'Porta do patch panel não encontrada'}), 404
        
        if porta[1] == 'ocupada':
            return jsonify({'erro': 'Porta já tem equipamento conectado'}), 400
        
        # Verificar se o equipamento existe
        cur.execute('SELECT id, nome FROM equipamentos WHERE id = %s', (equipamento_id,))
        equipamento = cur.fetchone()
        if not equipamento:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        # Conectar equipamento à porta
        cur.execute('''
            UPDATE patch_panel_portas 
            SET equipamento_id = %s, status = 'ocupada'
            WHERE id = %s
        ''', (equipamento_id, id))
        
        # Atualizar keystone no equipamento
        cur.execute('''
            UPDATE equipamentos 
            SET keystone = (
                SELECT pp.prefixo_keystone || '-' || printf('%04d', ppp.numero_porta)
                FROM patch_panel_portas ppp
                JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
                WHERE ppp.id = %s
            )
            WHERE id = %s
        ''', (id, equipamento_id))
        
        conn.commit()
        
        # Registrar log
        detalhes = f"Equipamento {equipamento[1]} conectado à porta {id} do patch panel"
        registrar_log(session.get('username', 'desconhecido'), 'CONECTAR_EQUIPAMENTO_PATCH_PANEL', detalhes, 'sucesso')
        
        return jsonify({'status': 'ok', 'mensagem': 'Equipamento conectado com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        detalhes = f"Erro ao conectar equipamento à porta {id}: {str(e)}"
        registrar_log(session.get('username', 'desconhecido'), 'CONECTAR_EQUIPAMENTO_PATCH_PANEL', detalhes, 'erro')
        return jsonify({'erro': f'Erro ao conectar equipamento: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panel-portas/<int:id>/desconectar-equipamento', methods=['PUT'])
@login_required
def desconectar_equipamento_patch_panel(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se a porta existe e tem equipamento conectado
        cur.execute('SELECT id, equipamento_id, status FROM patch_panel_portas WHERE id = %s', (id,))
        porta = cur.fetchone()
        if not porta:
            return jsonify({'erro': 'Porta do patch panel não encontrada'}), 404
        
        if not porta[1]:
            return jsonify({'erro': 'Nenhum equipamento conectado a esta porta'}), 400
        
        # Obter nome do equipamento para o log
        cur.execute('SELECT nome FROM equipamentos WHERE id = %s', (porta[1],))
        equipamento_result = cur.fetchone()
        equipamento_nome = equipamento_result[0] if equipamento_result else 'Desconhecido'
        
        # Desconectar equipamento da porta
        # Verificar se a porta ainda está mapeada para um switch
        cur.execute('SELECT switch_id FROM patch_panel_portas WHERE id = %s', (id,))
        switch_result = cur.fetchone()
        
        if switch_result and switch_result[0]:
            # Se ainda está mapeada para switch, status = 'mapeada'
            novo_status = 'mapeada'
        else:
            # Se não está mapeada, status = 'livre'
            novo_status = 'livre'
        
        cur.execute('''
            UPDATE patch_panel_portas 
            SET equipamento_id = NULL, status = %s
            WHERE id = %s
        ''', (novo_status, id))
        
        # Limpar keystone do equipamento
        cur.execute('UPDATE equipamentos SET keystone = NULL WHERE id = %s', (porta[1],))
        
        conn.commit()
        
        # Registrar log
        detalhes = f"Equipamento {equipamento_nome} desconectado da porta {id} do patch panel"
        registrar_log(session.get('username', 'desconhecido'), 'DESCONECTAR_EQUIPAMENTO_PATCH_PANEL', detalhes, 'sucesso')
        
        return jsonify({'status': 'ok', 'mensagem': 'Equipamento desconectado com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        detalhes = f"Erro ao desconectar equipamento da porta {id}: {str(e)}"
        registrar_log(session.get('username', 'desconhecido'), 'DESCONECTAR_EQUIPAMENTO_PATCH_PANEL', detalhes, 'erro')
        return jsonify({'erro': f'Erro ao desconectar equipamento: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/switch-portas/<int:id>/desconectar', methods=['PUT'])
@login_required
def desconectar_porta_switch(id):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Verificar se a porta existe
        cur.execute('SELECT id, status FROM switch_portas WHERE id = %s', (id,))
        porta = cur.fetchone()
        if not porta:
            return jsonify({'erro': 'Porta do switch não encontrada'}), 404
        
        # Se a porta está mapeada para um patch panel, desmapear
        if porta[1] == 'mapeada':
            # Buscar qual porta do patch panel está mapeada para esta porta do switch
            cur.execute('''
                SELECT id, equipamento_id FROM patch_panel_portas 
                WHERE switch_id = (SELECT switch_id FROM switch_portas WHERE id = %s)
                AND porta_switch = (SELECT numero_porta FROM switch_portas WHERE id = %s)
            ''', (id, id))
            
            patch_panel_porta = cur.fetchone()
            if patch_panel_porta:
                porta_patch_id, equipamento_id = patch_panel_porta
                
                # Determinar o status correto da porta do patch panel
                if equipamento_id:
                    # Se tem equipamento conectado, status deve ser 'ocupada'
                    novo_status = 'ocupada'
                else:
                    # Se não tem equipamento, status deve ser 'livre'
                    novo_status = 'livre'
                
                # Desmapear a porta do patch panel (remover apenas o mapeamento com switch)
                cur.execute('''
                    UPDATE patch_panel_portas 
                    SET switch_id = NULL, porta_switch = NULL, status = %s
                    WHERE id = %s
                ''', (novo_status, porta_patch_id))
        
        # Se a porta tem equipamento conectado diretamente, desconectar
        elif porta[1] == 'ocupada':
            # Buscar e remover conexão
            cur.execute('DELETE FROM conexoes WHERE porta_id = %s', (id,))
        
        # Marcar porta como livre
        cur.execute('UPDATE switch_portas SET status = %s WHERE id = %s', ('livre', id))
        
        conn.commit()
        
        # Registrar log
        detalhes = f"Porta {id} do switch desconectada"
        registrar_log(session.get('username', 'desconhecido'), 'DESCONECTAR_PORTA_SWITCH', detalhes, 'sucesso')
        
        return jsonify({'status': 'ok', 'mensagem': 'Porta desconectada com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        detalhes = f"Erro ao desconectar porta {id} do switch: {str(e)}"
        registrar_log(session.get('username', 'desconhecido'), 'DESCONECTAR_PORTA_SWITCH', detalhes, 'erro')
        return jsonify({'erro': f'Erro ao desconectar porta: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/salas/andar/<int:andar>', methods=['GET'])
@login_required
def listar_salas_por_andar(andar):            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        # Assumindo que as salas têm um campo 'andar' ou podem ser identificadas por nome
        # Você pode ajustar esta query conforme sua estrutura de dados
        cur.execute('''
            SELECT id, nome
            FROM salas
            WHERE nome LIKE %s OR nome LIKE %s
            ORDER BY nome
        ''', (f'%{andar}%', f'%{andar}º%'))
        
        salas = []
        for row in cur.fetchall():
            salas.append({
                'id': row[0],
                'nome': row[1]
            })
        
        return jsonify(salas)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar salas do andar: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/patch-panels/<int:id>', methods=['GET'])
@login_required
def get_patch_panel(id):
    try:            return jsonify({'status': 'erro', 'mensagem': 'Banco de dados não selecionado'}), 400
        
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, codigo, nome, andar, porta_inicial, num_portas, status, descricao, data_criacao
            FROM patch_panels 
            WHERE id = %s
        """, (id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'status': 'erro', 'mensagem': 'Patch panel não encontrado'}), 404
        
        patch_panel = {
            'id': row[0],
            'codigo': row[1],
            'nome': row[2],
            'andar': row[3],
            'porta_inicial': row[4],
            'num_portas': row[5],
            'status': row[6],
            'descricao': row[7],
            'data_criacao': row[8],
            'porta_final': row[4] + row[5] - 1
        }
        
        conn.close()
        return jsonify(patch_panel)
        
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500            conn = get_postgres_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT pp.id, pp.nome, pp.sala_id, pp.num_portas, pp.descricao, pp.data_criacao,
                   s.nome as sala_nome
            FROM patch_panels pp
            LEFT JOIN salas s ON pp.sala_id = s.id
            WHERE pp.id = %s
        ''', (id,))
        
        row = cur.fetchone()
        if not row:
            return jsonify({'erro': 'Patch panel não encontrado'}), 404
        
        patch_panel = {
            'id': row[0],
            'nome': row[1],
            'sala_id': row[2],
            'num_portas': row[3],
            'descricao': row[4],
            'data_criacao': row[5],
            'sala_nome': row[6] or 'Sem sala'
        }
        
        # Buscar portas do patch panel
        cur.execute('''
            SELECT ppp.id, ppp.numero_porta, ppp.status, ppp.equipamento_id,
                   e.nome as equipamento_nome
            FROM patch_panel_portas ppp
            LEFT JOIN equipamentos e ON ppp.equipamento_id = e.id
            WHERE ppp.patch_panel_id = %s
            ORDER BY ppp.numero_porta
        ''', (id,))
        
        portas = []
        for porta_row in cur.fetchall():
            portas.append({
                'id': porta_row[0],
                'numero_porta': porta_row[1],
                'status': porta_row[2],
                'equipamento_id': porta_row[3],
                'equipamento_nome': porta_row[4] or 'Livre'
            })
        
        patch_panel['portas'] = portas
        
        return jsonify(patch_panel)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar patch panel: {str(e)}'}), 500
    
    finally:
        conn.close()

@app.route('/equipamentos/<int:equipamento_id>/patch-panel-info', methods=['GET'])
@login_required
def get_equipamento_patch_panel_info(equipamento_id):
    try:        conn = get_postgres_connection()
        cur = conn.cursor()
        
        # Buscar informações do equipamento e sua conexão com patch panel
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.sala_id,
                   s.nome as sala_nome,
                   ppp.patch_panel_id, ppp.numero_porta,
                   pp.andar, pp.nome as patch_panel_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
            LEFT JOIN patch_panel_portas ppp ON e.id = ppp.equipamento_id
            LEFT JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
            WHERE e.id = %s
        ''', (equipamento_id,))
        
        row = cur.fetchone()
        if not row:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        # Se o equipamento está conectado a um patch panel
        if row[5]:  # patch_panel_id não é None
            patch_panel_info = {
                'andar': row[7],
                'patch_panel_id': row[5],
                'patch_panel_nome': row[8],
                'porta_numero': row[6]
            }
        else:
            patch_panel_info = None
        
        equipamento_info = {
            'id': row[0],
            'nome': row[1],
            'tipo': row[2],
            'sala_id': row[3],
            'sala_nome': row[4] or 'Sem sala',
            'patch_panel_info': patch_panel_info
        }
        
        conn.close()
        return jsonify(equipamento_info)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar informações do equipamento: {str(e)}'}), 500



@app.route('/debug/equipamento/<int:equipamento_id>', methods=['GET'])
@login_required
def debug_equipamento(equipamento_id):
    """Endpoint para debug de equipamento"""
    try:        conn = get_postgres_connection()
        cur = conn.cursor()
        
        # Buscar informações detalhadas do equipamento
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.sala_id, s.nome as sala_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
            WHERE e.id = %s
        ''', (equipamento_id,))
        
        row = cur.fetchone()
        if not row:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        # Buscar informações do patch panel
        cur.execute('''
            SELECT ppp.id, ppp.numero_porta, ppp.status, pp.nome as patch_panel_nome
            FROM patch_panel_portas ppp
            LEFT JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
            WHERE ppp.equipamento_id = %s
        ''', (equipamento_id,))
        
        patch_panel_info = cur.fetchone()
        
        debug_info = {
            'equipamento': {
                'id': row[0],
                'nome': row[1],
                'tipo': row[2],
                'sala_id': row[3],
                'sala_nome': row[4]
            },
            'patch_panel': patch_panel_info
        }
        
        conn.close()
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar debug: {str(e)}'}), 500

@app.route('/conectar-cabo-estoque.html')
@tecnico_required
def conectar_cabo_estoque_html():
    return send_file('conectar-cabo-estoque.html')

@app.route('/editar-cabo-especifico.html')
@tecnico_required
def editar_cabo_especifico_html():
    return send_file('editar-cabo-especifico.html')



if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)