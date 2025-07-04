import os
import sqlite3
import json
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
import subprocess
from typing import cast
import glob

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
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('SELECT id, nivel, nome FROM usuarios WHERE username=? AND senha=?', (dados['username'], dados['senha']))
    user = cur.fetchone()
    if not user:
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Usuário ou senha inválidos'}), 401
    user_id, nivel, nome = user
    cur.execute('''
        SELECT e.id, e.nome, e.db_file
        FROM empresas e
        JOIN usuario_empresas ue ON ue.empresa_id = e.id
        WHERE ue.usuario_id = ?
    ''', (user_id,))
    empresas = [{'id': row[0], 'nome': row[1], 'db_file': row[2]} for row in cur.fetchall()]
    conn.close()
    session['user_id'] = user_id
    session['nivel'] = nivel
    session['username'] = dados['username']
    session['nome'] = nome
    if nivel == 'master':
        return jsonify({'status': 'ok', 'redirect': '/config-master.html'})
    return jsonify({'status': 'ok', 'empresas': empresas})

@app.route('/escolher_empresa', methods=['POST'])
def escolher_empresa():
    dados = request.json
    if not dados or 'db_file' not in dados:
        return jsonify({'erro': 'Dados ausentes ou inválidos!'}), 400
    db_file = dados.get('db_file')
    session['db'] = db_file
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, descricao, foto, fotos, andar_id FROM salas')
    salas = [
        dict(id=row[0], nome=row[1], tipo=row[2], descricao=row[3], foto=row[4], fotos=row[5], andar_id=row[6])
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO salas (nome, tipo, descricao, foto, fotos, andar_id)
        VALUES (?, ?, ?, ?, ?, ?)
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
        cur.execute('UPDATE equipamentos SET sala_id=? WHERE id=?', (sala_id, eq_id))
    conn.commit()
    conn.close()
    # Log de criação de sala
    detalhes = f"Sala criada: ID={sala_id}, Nome={dados['nome']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SALA', detalhes, 'sucesso')
    return jsonify({'status': 'ok', 'id': sala_id})

@app.route('/salas/<int:id>', methods=['GET'])
@login_required
def get_sala(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, descricao, foto, fotos, andar_id FROM salas WHERE id=?', (id,))
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    # Busca equipamentos atualmente vinculados à sala
    cur.execute('SELECT id FROM equipamentos WHERE sala_id = ?', (id,))
    equipamentos_atuais = [row[0] for row in cur.fetchall()]
    
    # Atualiza dados da sala
    cur.execute('''
        UPDATE salas SET nome=?, tipo=?, descricao=?, foto=?, fotos=?, andar_id=?
        WHERE id=?
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
            WHERE equipamento_id = ? AND status = 'ativa'
        ''', (eq_id,))
        porta_result = cur.fetchone()
        
        if porta_result:
            porta_id = porta_result[0]
            # Marca a conexão como inativa
            cur.execute('''
                UPDATE conexoes SET status = 'inativa' 
                WHERE equipamento_id = ? AND status = 'ativa'
            ''', (eq_id,))
            
            # Marca a porta como livre
            cur.execute('''
                UPDATE switch_portas SET status = 'livre' 
                WHERE id = ?
            ''', (porta_id,))
    
    # Desvincula todos os equipamentos da sala
    cur.execute('UPDATE equipamentos SET sala_id=NULL WHERE sala_id=?', (id,))
    
    # Vincula os selecionados
    for eq_id in equipamentos_ids:
        cur.execute('UPDATE equipamentos SET sala_id=? WHERE id=?', (id, eq_id))
    
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Sala atualizada: ID={id}, Nome={dados['nome']}, Equipamentos desatrelados={len(equipamentos_desatrelados)}, Equipamentos vinculados={len(equipamentos_ids)}"
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SALA', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok'})

@app.route('/salas/<int:id>', methods=['DELETE'])
@admin_required
def excluir_sala(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT nome FROM salas WHERE id=?', (id,))
    row = cur.fetchone()
    nome_sala = row[0] if row else ''
    cur.execute('UPDATE equipamentos SET sala_id=NULL WHERE sala_id=?', (id,))
    cur.execute('DELETE FROM salas WHERE id=?', (id,))
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    # Cria a sala
    cur.execute('''
        INSERT INTO salas (nome, tipo, descricao, foto, fotos, andar_id)
        VALUES (?, ?, ?, ?, ?, ?)
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
        caminho_foto = f'img/{tipo}-{marca}.png' if tipo and marca else None
        cur.execute('''
            INSERT INTO equipamentos (nome, tipo, marca, modelo, descricao, foto, icone, sala_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                    VALUES (?, ?, ?)
                ''', (equipamento_id, chave, valor))
    # Vincular equipamentos já existentes (sem sala) à nova sala
    equipamentos_ids = request.form.getlist('equipamentos_ids[]')
    for eq_id in equipamentos_ids:
        cur.execute('UPDATE equipamentos SET sala_id=? WHERE id=?', (sala_id, eq_id))
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    tipo = (dados.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    marca = (dados.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    caminho_foto = f'img/{tipo}-{marca}.png' if tipo and marca else None
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO equipamentos (nome, tipo, marca, modelo, descricao, foto, icone, sala_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                VALUES (?, ?, ?)
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
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
              AND (e.defeito IS NULL OR e.defeito = 0)
        ''')
    elif sala_id == 'null':
        cur.execute('SELECT id, nome, tipo, marca, modelo, descricao, foto, icone, sala_id, defeito FROM equipamentos WHERE sala_id IS NULL')
    elif sala_id:
        cur.execute('SELECT id, nome, tipo, marca, modelo, descricao, foto, icone, sala_id, defeito FROM equipamentos WHERE sala_id=?', (sala_id,))
    else:
        cur.execute('SELECT id, nome, tipo, marca, modelo, descricao, foto, icone, sala_id, defeito FROM equipamentos')
    equipamentos = []
    for row in cur.fetchall():
        eq_id = row['id']
        cur.execute('SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=?', (eq_id,))
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
            'sala_nome': row['sala_nome'] if conectaveis == '1' else None,
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    tipo = (dados.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    marca = (dados.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    caminho_foto = f'img/{tipo}-{marca}.png' if tipo and marca else None
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''
        UPDATE equipamentos SET nome=?, tipo=?, marca=?, modelo=?, descricao=?, foto=?, icone=?
        WHERE id=?
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
        cur.execute('SELECT id FROM equipamento_dados WHERE equipamento_id=? AND chave=?', (id, chave))
        row = cur.fetchone()
        if row:
            cur.execute('UPDATE equipamento_dados SET valor=? WHERE id=?', (valor, row[0]))
        else:
            cur.execute('INSERT INTO equipamento_dados (equipamento_id, chave, valor) VALUES (?, ?, ?)', (id, chave, valor))
    conn.commit()
    conn.close()
    # Log de edição de equipamento
    detalhes = f"Equipamento atualizado: ID={id}, Nome={dados['nome']}, Tipo={dados.get('tipo')}, Marca={dados.get('marca')}, Modelo={dados.get('modelo')}"
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_EQUIPAMENTO', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/equipamentos/<int:id>', methods=['GET'])
@login_required
def get_equipamento(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, marca, modelo, descricao, foto, icone, sala_id FROM equipamentos WHERE id=?', (id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'erro': 'Equipamento não encontrado'}), 404
    cur.execute('SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=?', (id,))
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT nome, tipo, marca, modelo FROM equipamentos WHERE id=?', (id,))
    row = cur.fetchone()
    nome, tipo, marca, modelo = row if row else ('', '', '', '')
    cur.execute('DELETE FROM equipamento_dados WHERE equipamento_id=?', (id,))
    cur.execute('DELETE FROM equipamentos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    # Log de exclusão de equipamento
    detalhes = f"Equipamento excluído: ID={id}, Nome={nome}, Tipo={tipo}, Marca={marca}, Modelo={modelo}"
    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_EQUIPAMENTO', detalhes, 'sucesso')
    return jsonify({'status': 'ok'})

@app.route('/tipos-equipamento')
@login_required
def tipos_equipamento():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT tipo FROM equipamentos WHERE tipo IS NOT NULL AND tipo != ""')
    tipos = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(tipos)

@app.route('/marcas-equipamento')
@login_required
def marcas_equipamento():
    tipo = request.args.get('tipo')
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT marca FROM equipamentos WHERE tipo=? AND marca IS NOT NULL AND marca != ""', (tipo,))
    marcas = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify(marcas)

@app.route('/modelos-equipamento')
@login_required
def modelos_equipamento():
    tipo = request.args.get('tipo')
    marca = request.args.get('marca')
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT modelo FROM equipamentos WHERE tipo=? AND marca=? AND modelo IS NOT NULL AND modelo != ""', (tipo, marca))
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
        VALUES (?, ?, ?)
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
def listar_switches():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
def get_switch(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    cur.execute('SELECT id, nome, marca, modelo, data_criacao FROM switches WHERE id=?', (id,))
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
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    # Verificar se o switch existe
    cur.execute('SELECT id FROM switches WHERE id=?', (id,))
    if not cur.fetchone():
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', f'Switch ID={id}: Não encontrado', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
    
    # Atualizar o switch
    cur.execute('''
        UPDATE switches SET nome=?, marca=?, modelo=?
        WHERE id=?
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
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
    cur.execute('SELECT id FROM switch_portas WHERE switch_id=? AND numero_porta=?', 
                (dados['switch_id'], dados['numero_porta']))
    
    if cur.fetchone():
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Porta já existe para este switch'}), 400
    
    cur.execute('''
        INSERT INTO switch_portas (switch_id, numero_porta, descricao, status)
        VALUES (?, ?, ?, ?)
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
def listar_portas_switch(switch_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
        SELECT sp.id, sp.numero_porta, sp.descricao, sp.status, 
               e.nome as equipamento_nome, e.tipo as equipamento_tipo, s.nome as sala_nome
        FROM switch_portas sp
        LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
        LEFT JOIN equipamentos e ON c.equipamento_id = e.id
        LEFT JOIN salas s ON e.sala_id = s.id
        WHERE sp.switch_id = ?
        ORDER BY sp.numero_porta
    ''', (switch_id,))
    
    portas = []
    for row in cur.fetchall():
        equipamento_conectado = None
        if row[4]:
            # Buscar dados extras do equipamento
            cur.execute("SELECT id FROM equipamentos WHERE nome=? AND tipo=?", (row[4], row[5]))
            eq_row = cur.fetchone()
            eq_id = eq_row[0] if eq_row else None
            dados = {}
            if eq_id:
                cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=? AND chave IN ('ip1','ip2','mac1','mac2')", (eq_id,))
                dados = {chave: valor for chave, valor in cur.fetchall()}
            equipamento_conectado = {
                'nome': row[4],
                'tipo': row[5],
                'sala_nome': row[6],
                'ip1': dados.get('ip1',''),
                'ip2': dados.get('ip2',''),
                'mac1': dados.get('mac1',''),
                'mac2': dados.get('mac2','')
            }
        porta = {
            'id': row[0],
            'numero_porta': row[1],
            'descricao': row[2],
            'status': row[3],
            'equipamento_conectado': equipamento_conectado
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
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
    cur.execute('SELECT status FROM switch_portas WHERE id=?', (dados['porta_id'],))
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
    cur.execute('SELECT id FROM conexoes WHERE equipamento_id=? AND status="ativa"', (dados['equipamento_id'],))
    if cur.fetchone():
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Equipamento ID={dados["equipamento_id"]}: Já conectado', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Equipamento já está conectado a outra porta'}), 400
    
    # Criar a conexão
    cur.execute('''
        INSERT INTO conexoes (porta_id, equipamento_id, status)
        VALUES (?, ?, 'ativa')
    ''', (dados['porta_id'], dados['equipamento_id']))
    
    # Atualizar status da porta
    cur.execute('UPDATE switch_portas SET status="ocupada" WHERE id=?', (dados['porta_id'],))
    
    conexao_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Conexão criada: ID={conexao_id}, Porta ID={dados['porta_id']}, Equipamento ID={dados['equipamento_id']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok', 'id': conexao_id})

@app.route('/conexoes/<int:conexao_id>', methods=['DELETE'])
@admin_required
def remover_conexao(conexao_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    # Buscar a conexão
    cur.execute('SELECT porta_id, equipamento_id FROM conexoes WHERE id=? AND status="ativa"', (conexao_id,))
    conexao = cur.fetchone()
    
    if not conexao:
        registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', f'Conexão ID={conexao_id}: Não encontrada', 'erro')
        conn.close()
        return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
    
    porta_id, equipamento_id = conexao
    
    # Marcar conexão como inativa
    cur.execute('UPDATE conexoes SET status="inativa" WHERE id=?', (conexao_id,))
    
    # Marcar porta como livre
    cur.execute('UPDATE switch_portas SET status="livre" WHERE id=?', (porta_id,))
    
    conn.commit()
    conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Conexão removida: ID={conexao_id}, Porta ID={porta_id}, Equipamento ID={equipamento_id}"
    registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', detalhes, 'sucesso')
    
    return jsonify({'status': 'ok'})

@app.route('/conexoes', methods=['GET'])
@login_required
def listar_conexoes():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT c.id, c.data_conexao, c.status,
               sp.numero_porta, s.nome as switch_nome, s.marca as switch_marca,
               e.nome as equipamento_nome, e.tipo as equipamento_tipo
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
            porta=row[3], switch=row[4], switch_marca=row[5],
            equipamento=row[6], equipamento_tipo=row[7]
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
def excluir_switch(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    # Buscar dados do switch
    cur.execute('SELECT nome, marca, modelo FROM switches WHERE id=?', (id,))
    row = cur.fetchone()
    nome, marca, modelo = row if row else ('', '', '')
    # Buscar portas do switch
    cur.execute('SELECT id FROM switch_portas WHERE switch_id=?', (id,))
    portas = [r[0] for r in cur.fetchall()]
    # Para cada porta, marcar conexões como inativas e liberar porta
    for porta_id in portas:
        # Marcar conexões como inativas
        cur.execute('UPDATE conexoes SET status="inativa" WHERE porta_id=? AND status="ativa"', (porta_id,))
        # Marcar porta como livre
        cur.execute('UPDATE switch_portas SET status="livre" WHERE id=?', (porta_id,))
    # Excluir portas do switch
    cur.execute('DELETE FROM switch_portas WHERE switch_id=?', (id,))
    # Excluir switch
    cur.execute('DELETE FROM switches WHERE id=?', (id,))
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
    defeito = 1 if dados.get('defeito') else 0
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    # Se marcar como defeito, desvincula da sala
    if defeito:
        cur.execute('UPDATE equipamentos SET defeito=?, sala_id=NULL WHERE id=?', (defeito, id))
    else:
        cur.execute('UPDATE equipamentos SET defeito=? WHERE id=?', (defeito, id))
    conn.commit()
    # Verifica valor salvo imediatamente após o update
    cur.execute('SELECT defeito, sala_id FROM equipamentos WHERE id=?', (id,))
    row = cur.fetchone()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/gerenciar-equipamentos.html')
@login_required
def gerenciar_equipamentos_html():
    return send_from_directory(os.path.dirname(__file__), 'gerenciar-equipamentos.html')

@app.route('/config-usuario.html')
@login_required
def config_usuario_html():
    return send_from_directory(os.path.dirname(__file__), 'config-usuario.html')

@app.route('/config-tecnico.html')
@login_required
def config_tecnico_html():
    return send_from_directory(os.path.dirname(__file__), 'config-tecnico.html')

@app.route('/ping-equipamentos', methods=['POST'])
@login_required
def ping_equipamentos():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
            'INSERT INTO ping_logs (equipamento_id, nome_equipamento, ip, resultado, sucesso) VALUES (?, ?, ?, ?, ?)',
            (eq_id, nome, ip, saida, sucesso)
        )
        resultados.append({'id': eq_id, 'nome': nome, 'ip': ip, 'sucesso': bool(sucesso), 'saida': saida})
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'resultados': resultados})

@app.route('/ping-logs')
@login_required
def ping_logs():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
        cur.execute("SELECT valor FROM equipamento_dados WHERE equipamento_id=? AND chave IN ('mac', 'mac1') LIMIT 1", (eq_id,))
        mac_row = cur.fetchone()
        mac = mac_row[0] if mac_row else ''
        # Busca switch e porta (se houver conexão ativa)
        cur.execute('''
            SELECT s.nome, sp.numero_porta
            FROM conexoes c
            JOIN switch_portas sp ON c.porta_id = sp.id
            JOIN switches s ON sp.switch_id = s.id
            WHERE c.equipamento_id=? AND c.status='ativa' LIMIT 1
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
def limpar_ping_logs():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('DELETE FROM ping_logs')
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/empresa_atual')
@login_required
def empresa_atual():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('SELECT nome, logo FROM empresas WHERE db_file=?', (db_file,))
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
        return jsonify({'status': 'erro', 'mensagem': 'Nome de arquivo vazio'})
    pasta = os.path.join('static', 'img', 'fotos-salas')
    os.makedirs(pasta, exist_ok=True)
    filename = cast(str, file.filename)
    caminho = os.path.join(pasta, filename)
    file.save(caminho)
    return jsonify({'status': 'ok', 'caminho': f'static/img/fotos-salas/{filename}'})

@app.route('/fotos-salas')
def fotos_salas():
    pasta = os.path.join('static', 'img', 'fotos-salas')
    if not os.path.exists(pasta):
        return jsonify({'imagens': []})
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return jsonify({'imagens': [f'/static/img/fotos-salas/{arq}' for arq in arquivos]})

@app.route('/upload-fotos-salas.html')
def upload_fotos_salas_html():
    return send_from_directory(os.path.dirname(__file__), 'upload-fotos-salas.html')

@app.route('/conexoes-equipamentos.html')
@admin_required
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
def api_salas():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT id, nome FROM salas')
    salas = [{'id': row[0], 'nome': row[1]} for row in cur.fetchall()]
    conn.close()
    return jsonify(salas)

@app.route('/api/salas/<int:sala_id>/layout', methods=['POST'])
@login_required
def salvar_layout_sala(sala_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    layout = request.get_json()
    if not layout:
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    conn = sqlite3.connect(db_file)
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
        VALUES (?, ?, CURRENT_TIMESTAMP)
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
def obter_layout_sala(sala_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT layout_json FROM sala_layouts WHERE sala_id=?', (sala_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return jsonify(json.loads(row[0]))
    return jsonify({'erro': 'Nenhum layout salvo para esta sala.'}), 404

@app.route('/visualizar-layout-sala.html')
@login_required
def visualizar_layout_html():
    return send_from_directory('.', 'visualizar-layout-sala.html')

@app.route('/api/salas-com-layout', methods=['GET'])
@login_required
def salas_com_layout():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
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
def switches_usados_sala(sala_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''
        SELECT s.id as switch_id, s.nome as switch_nome, sp.numero_porta, e.nome as equipamento_nome, e.tipo as equipamento_tipo, sala.nome as sala_nome, e.id as equipamento_id, e.marca as equipamento_marca, e.foto as equipamento_foto
        FROM equipamentos e
        JOIN conexoes c ON c.equipamento_id = e.id AND c.status = 'ativa'
        JOIN switch_portas sp ON c.porta_id = sp.id
        JOIN switches s ON sp.switch_id = s.id
        LEFT JOIN salas sala ON e.sala_id = sala.id
        WHERE e.sala_id = ?
        ORDER BY s.id, sp.numero_porta
    ''', (sala_id,))
    rows = cur.fetchall()
    switches = {}
    for switch_id, switch_nome, numero_porta, equipamento_nome, equipamento_tipo, sala_nome, equipamento_id, equipamento_marca, equipamento_foto in rows:
        # Buscar dados extras do equipamento
        cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=? AND chave IN ('ip1','ip2','mac1','mac2','serie','série')", (equipamento_id,))
        dados = {chave: valor for chave, valor in cur.fetchall()}
        serie = dados.get('serie') or dados.get('série') or ''
        # Ajustar caminho da foto
        let_foto = equipamento_foto or ''
        if let_foto and not let_foto.startswith('static/'):
            let_foto = 'static/' + let_foto
        if switch_id not in switches:
            switches[switch_id] = {'id': switch_id, 'nome': switch_nome, 'portas': []}
        switches[switch_id]['portas'].append({
            'numero': numero_porta,
            'equipamento': equipamento_nome,
            'tipo': equipamento_tipo,
            'sala': sala_nome,
            'marca': equipamento_marca,
            'serie': serie,
            'foto': let_foto,
            'ip1': dados.get('ip1',''),
            'ip2': dados.get('ip2',''),
            'mac1': dados.get('mac1',''),
            'mac2': dados.get('mac2','')
        })
    conn.close()
    return jsonify(list(switches.values()))

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
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM usuarios WHERE username=?', (username,))
    if cur.fetchone():
        conn.close()
        return jsonify({'erro': 'Usuário já existe!'}), 400
    cur.execute('INSERT INTO usuarios (nome, username, senha, nivel) VALUES (?, ?, ?, ?)', (nome, username, senha, nivel))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/usuarios', methods=['GET'])
@master_required
def admin_listar_usuarios():
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('SELECT id, username, nome, nivel FROM usuarios')
    usuarios = [dict(id=row[0], username=row[1], nome=row[2], nivel=row[3]) for row in cur.fetchall()]
    conn.close()
    return jsonify(usuarios)

@app.route('/admin/empresas', methods=['GET'])
@master_required
def admin_listar_empresas():
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('SELECT id, nome FROM empresas')
    empresas = [dict(id=row[0], nome=row[1]) for row in cur.fetchall()]
    conn.close()
    return jsonify(empresas)

@app.route('/admin/vinculos', methods=['GET'])
@master_required
def admin_listar_vinculos():
    conn = sqlite3.connect('usuarios_empresas.db')
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
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO usuario_empresas (usuario_id, empresa_id) VALUES (?, ?)', (usuario_id, empresa_id))
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
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM usuario_empresas WHERE usuario_id=? AND empresa_id=?', (usuario_id, empresa_id))
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
    conn = sqlite3.connect('usuarios_empresas.db')
    cur = conn.cursor()
    cur.execute('UPDATE usuarios SET nivel=? WHERE id=?', (novo_nivel, usuario_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/config-master.html')
@master_required
def config_master_html():
    return send_from_directory(os.path.dirname(__file__), 'config-master.html')

@app.route('/api/salas/<int:id>', methods=['GET'])
@login_required
def api_get_sala(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('SELECT id, nome, tipo, descricao, foto, fotos, andar_id FROM salas WHERE id=?', (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(dict(id=row[0], nome=row[1], tipo=row[2], descricao=row[3], foto=row[4], fotos=row[5], andar_id=row[6]))
    return jsonify({'erro': 'Sala não encontrada'}), 404

if __name__ == '__main__':
    app.run(debug=True)