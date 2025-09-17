import os
import sqlite3
import json
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
LOG_DIR = 'logs_empresas'

# ----------------- MODO JSON (Datastore de exemplo) -----------------
# Este projeto pode operar em modo somente JSON quando session['db'] começar com
# 'json:'. Nesse modo, salvamos dados em arquivos em static/data/empresas/<empresa_dir>/
# mantendo entidades como 'salas.json' e 'equipamentos.json'.

def _is_json_mode(db_file):
    return isinstance(db_file, str) and db_file.startswith('json:')

def _empresa_dir_from_db(db_file):
    # db_file pode ser 'json:empresa_<id>' ou um nome livre
    raw = os.path.splitext(os.path.basename(str(db_file)))[0]
    if _is_json_mode(db_file):
        try:
            emp_id = int(str(db_file).split('_')[-1])
            return f'empresa_{emp_id}'
        except Exception:
            pass
    # fallback: sanitiza o nome base
    return re.sub(r'[^A-Za-z0-9_-]+', '_', raw)

def _empresa_data_dir(db_file):
    base = os.path.join(os.path.dirname(__file__), 'static', 'data', 'empresas')
    empresa_dir = _empresa_dir_from_db(db_file)
    path = os.path.join(base, empresa_dir)
    os.makedirs(path, exist_ok=True)
    return path

def _json_table_path(db_file, table_name):
    return os.path.join(_empresa_data_dir(db_file), f'{table_name}.json')

def _json_read_table(db_file, table_name):
    path = _json_table_path(db_file, table_name)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def is_patch_panel(equipamento):
    """Verifica se um equipamento é um patch panel baseado no tipo ou nome"""
    tipo = (equipamento.get('tipo') or '').lower()
    nome = (equipamento.get('nome') or '').lower()
    
    # Palavras-chave que indicam patch panel
    patch_panel_keywords = [
        'patch panel', 'patch-panel', 'patchpanel', 'patch_panel',
        'keystone', 'rack', 'distribuidor', 'distribuição'
    ]
    
    return any(keyword in tipo or keyword in nome for keyword in patch_panel_keywords)

def _json_write_table(db_file, table_name, rows):
    path = _json_table_path(db_file, table_name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

def _json_next_id(rows):
    max_id = 0
    for r in rows:
        try:
            rid = int(r.get('id', 0))
            if rid > max_id:
                max_id = rid
        except Exception:
            continue
    return max_id + 1

def get_log_file(empresa_db=None):
    """
    Retorna o caminho do arquivo de log para uma empresa específica
    """
    if not empresa_db:
        # Para logs do sistema (login, logout, etc.)
        return os.path.join(LOG_DIR, 'sistema_logs.txt')
    
    # Para logs de empresas específicas
    empresa_nome = os.path.splitext(os.path.basename(empresa_db))[0]
    return os.path.join(LOG_DIR, f'{empresa_nome}_logs.txt')

def registrar_log(usuario, acao, detalhes, status='sucesso', empresa_db=None):
    """
    Registra uma ação no arquivo de log da empresa específica
    """
    try:
        # Criar diretório de logs se não existir
        os.makedirs(LOG_DIR, exist_ok=True)
        
        log_file = get_log_file(empresa_db)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Usuario: {usuario} | Acao: {acao} | Detalhes: {detalhes} | Status: {status}\n"
        
        print(f"DEBUG: Tentando registrar log: {log_entry.strip()}")  # Debug
        print(f"DEBUG: Arquivo de log: {log_file}")  # Debug
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"DEBUG: Log registrado com sucesso no arquivo: {log_file}")  # Debug
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
        print(f"DEBUG: Arquivo de log: {log_file}")  # Debug
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
        registrar_log('sistema', 'LOGIN', f'Tentativa de login com dados JSON inválidos', 'erro')
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    username = dados.get('username', 'desconhecido')

    # Autenticação exclusivamente via JSON
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'static', 'data')

        with open(os.path.join(data_dir, 'usuarios.json'), 'r', encoding='utf-8') as f:
            usuarios = json.load(f)

        user = next((u for u in usuarios if u.get('username') == dados.get('username') and u.get('senha') == dados.get('senha')), None)
        if not user:
            registrar_log('sistema', 'LOGIN', f'Tentativa de login falhou para usuário: {username}', 'erro')
            return jsonify({'status': 'erro', 'mensagem': 'Usuário ou senha inválidos'}), 401

        try:
            with open(os.path.join(data_dir, 'empresas.json'), 'r', encoding='utf-8') as f:
                empresas_all = json.load(f)
        except FileNotFoundError:
            empresas_all = []

        try:
            with open(os.path.join(data_dir, 'usuario_empresas.json'), 'r', encoding='utf-8') as f:
                ues = json.load(f)
        except FileNotFoundError:
            ues = []

        empresa_ids = {ue.get('empresa_id') for ue in ues if ue.get('usuario_id') == user.get('id')}
        empresas = []
        for e in empresas_all:
            if not empresa_ids or e.get('id') in empresa_ids:
                e2 = dict(e)
                if 'db_file' not in e2:
                    e2['db_file'] = f"json:empresa_{e2.get('id','')}"
                empresas.append({'id': e2.get('id'), 'nome': e2.get('nome'), 'db_file': e2.get('db_file')})

        session['user_id'] = user.get('id')
        session['nivel'] = user.get('nivel')
        session['username'] = user.get('username')
        session['nome'] = user.get('nome')

        registrar_log(username, 'LOGIN', f'Login realizado com sucesso - Nível: {user.get("nivel")}, Nome: {user.get("nome")}', 'sucesso')

        if user.get('nivel') == 'master':
            return jsonify({'status': 'ok', 'redirect': '/config-master.html'})
        return jsonify({'status': 'ok', 'empresas': empresas})
    except Exception as e:
        registrar_log('sistema', 'LOGIN', f'Erro no modo JSON: {str(e)}', 'erro')
        return jsonify({'status': 'erro', 'mensagem': 'Falha ao autenticar (JSON). Verifique os arquivos em static/data.'}), 500

@app.route('/escolher_empresa', methods=['POST'])
def escolher_empresa():
    dados = request.json
    if not dados or 'db_file' not in dados:
        username = session.get('username', 'desconhecido')
        registrar_log(username, 'ESCOLHER_EMPRESA', 'Tentativa de escolher empresa com dados inválidos', 'erro')
        return jsonify({'erro': 'Dados ausentes ou inválidos!'}), 400
    
    db_file = dados.get('db_file')
    username = session.get('username', 'desconhecido')
    
    # Log da escolha de empresa (log do sistema, não de empresa específica)
    registrar_log(username, 'ESCOLHER_EMPRESA', f'Empresa selecionada: {db_file}', 'sucesso')
    
    session['db'] = db_file
    return jsonify({'status': 'ok', 'redirect': '/painel.html'})

@app.route('/logout')
def logout():
    username = session.get('username', 'desconhecido')
    nivel = session.get('nivel', 'desconhecido')
    nome = session.get('nome', 'desconhecido')
    
    # Log de logout antes de limpar a sessão (log do sistema, não de empresa específica)
    registrar_log(username, 'LOGOUT', f'Logout realizado - Nível: {nivel}, Nome: {nome}', 'sucesso')
    
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
        if 'user_id' not in session or session.get('nivel') not in ['admin', 'master']:
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
@tecnico_required
def editar_equipamento_html():
    return send_from_directory(os.path.dirname(__file__), 'editar-equipamento.html')

@app.route('/excluir-equipamento.html')
@login_required
def excluir_equipamento_html():
    return send_from_directory(os.path.dirname(__file__), 'excluir-equipamento.html')

@app.route('/dashboard-sala.html')
@login_required
def dashboard_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'dashboard-sala.html')

@app.route('/historico-sala.html')
@login_required
def historico_sala_html():
    return send_from_directory(os.path.dirname(__file__), 'historico-sala.html')

# --- API HISTÓRICO SALA ---

@app.route('/logs/sala/<int:sala_id>', methods=['GET'])
@login_required
def logs_por_sala(sala_id: int):
    """Retorna o histórico básico (placeholder) da sala. 
    Em modo JSON, ainda não há armazenamento dedicado por sala, então retornamos lista vazia.
    Mantém compatibilidade de frontend (evita 404)."""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    # Estrutura de retorno esperada: lista de eventos
    # Cada item pode conter: timestamp, acao, detalhes
    return jsonify([])

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
    if _is_json_mode(db_file):
        salas = _json_read_table(db_file, 'salas')
        andares = {a.get('id'): a for a in _json_read_table(db_file, 'andares')}
        result = []
        for s in salas:
            result.append({
                'id': s.get('id'),
                'nome': s.get('nome'),
                'tipo': s.get('tipo'),
                'descricao': s.get('descricao'),
                'foto': s.get('foto'),
                'fotos': s.get('fotos'),
                'andar_id': s.get('andar_id'),
                'andar': (andares.get(s.get('andar_id')) or {}).get('titulo') if s.get('andar_id') is not None else None
            })
        return jsonify(result)
    else:
        conn = sqlite3.connect(db_file)
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        salas = _json_read_table(db_file, 'salas')
        # duplicidade por nome (case-insensitive)
        nome = dados.get('nome')
        if nome and any((s.get('nome') or '').lower() == nome.lower() for s in salas):
            return jsonify({'status': 'erro', 'mensagem': 'Já existe uma sala com esse nome!'}), 400

        sala_id = _json_next_id(salas)
        nova_sala = {
            'id': sala_id,
            'nome': dados.get('nome'),
            'tipo': dados.get('tipo'),
            'descricao': dados.get('descricao'),
            'foto': dados.get('foto'),
            'fotos': dados.get('fotos'),
            'andar_id': dados.get('andar_id')
        }
        salas.append(nova_sala)
        _json_write_table(db_file, 'salas', salas)

        equipamentos_ids = dados.get('equipamentos_ids', [])
        if equipamentos_ids:
            equipamentos = _json_read_table(db_file, 'equipamentos')
            ids_set = set(str(x) for x in equipamentos_ids)
            for e in equipamentos:
                if str(e.get('id')) in ids_set:
                    e['sala_id'] = sala_id
            _json_write_table(db_file, 'equipamentos', equipamentos)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        # Verificação de nome duplicado (case-insensitive)
        nome = dados['nome']
        cur.execute('SELECT 1 FROM salas WHERE LOWER(nome) = LOWER(?)', (nome,))
        if cur.fetchone():
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Já existe uma sala com esse nome!'}), 400
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
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SALA', detalhes, 'sucesso', db_file)
    return jsonify({'status': 'ok', 'id': sala_id})

@app.route('/salas/<int:id>', methods=['GET'])
@login_required
def get_sala(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        salas = _json_read_table(db_file, 'salas')
        sala = next((s for s in salas if s.get('id') == id), None)
        if sala:
            return jsonify({
                'id': sala.get('id'),
                'nome': sala.get('nome'),
                'tipo': sala.get('tipo'),
                'descricao': sala.get('descricao'),
                'foto': sala.get('foto'),
                'fotos': sala.get('fotos'),
                'andar_id': sala.get('andar_id')
            })
        return jsonify({'erro': 'Sala não encontrada'}), 404
    else:
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
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SALA', f'Sala ID={id}: Dados JSON inválidos', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        salas = _json_read_table(db_file, 'salas')
        sala = next((s for s in salas if s.get('id') == id), None)
        if not sala:
            return jsonify({'status': 'erro', 'mensagem': 'Sala não encontrada'}), 404
        sala['nome'] = dados.get('nome')
        sala['tipo'] = dados.get('tipo')
        sala['descricao'] = dados.get('descricao')
        sala['foto'] = dados.get('foto')
        sala['fotos'] = dados.get('fotos')
        sala['andar_id'] = dados.get('andar_id')
        _json_write_table(db_file, 'salas', salas)

        equipamentos_ids = [str(x) for x in dados.get('equipamentos_ids', [])]
        equipamentos = _json_read_table(db_file, 'equipamentos')
        equipamentos_atuais = [e.get('id') for e in equipamentos if e.get('sala_id') == id]
        equipamentos_desatrelados = [eq for eq in equipamentos_atuais if str(eq) not in equipamentos_ids]
        for e in equipamentos:
            if str(e.get('id')) in equipamentos_ids:
                e['sala_id'] = id
            elif e.get('sala_id') == id and str(e.get('id')) not in equipamentos_ids:
                e['sala_id'] = None
        _json_write_table(db_file, 'equipamentos', equipamentos)

        detalhes = f"Sala atualizada: ID={id}, Nome={dados.get('nome')}, Equipamentos desatrelados={len(equipamentos_desatrelados)}, Equipamentos vinculados={len(equipamentos_ids)}"
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SALA', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok'})
    else:
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
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SALA', detalhes, 'sucesso', db_file)
        
        return jsonify({'status': 'ok'})

@app.route('/salas/<int:id>', methods=['DELETE'])
@admin_required
def excluir_sala(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        salas = _json_read_table(db_file, 'salas')
        sala = next((s for s in salas if s.get('id') == id), None)
        nome_sala = sala.get('nome') if sala else ''
        salas = [s for s in salas if s.get('id') != id]
        _json_write_table(db_file, 'salas', salas)

        equipamentos = _json_read_table(db_file, 'equipamentos')
        for e in equipamentos:
            if e.get('sala_id') == id:
                e['sala_id'] = None
        _json_write_table(db_file, 'equipamentos', equipamentos)

        detalhes = f"Sala excluída: ID={id}, Nome={nome_sala}"
        registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_SALA', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok'})
    else:
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
        registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_SALA', detalhes, 'sucesso', db_file)
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
    if _is_json_mode(db_file):
        # Verificação de nome duplicado (case-insensitive)
        salas = _json_read_table(db_file, 'salas')
        if any((s.get('nome') or '').lower() == (nome or '').lower() for s in salas):
            return jsonify({'status': 'erro', 'mensagem': 'Já existe uma sala com esse nome!'}), 400
        # Cria a sala
        sala_id = _json_next_id(salas)
        salas.append({
            'id': sala_id,
            'nome': nome,
            'tipo': tipo,
            'descricao': descricao,
            'foto': caminho_foto,
            'fotos': fotos_str,
            'andar_id': andar_id,
            'data_criacao': datetime.now().isoformat()
        })
        _json_write_table(db_file, 'salas', salas)
        
        # Cria os equipamentos
        equipamentos_data = _json_read_table(db_file, 'equipamentos')
        for eq in equipamentos:
            # Gera caminho da foto automaticamente
            tipo_eq = (eq.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
            marca = (eq.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
            modelo = (eq.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
            caminho_foto_eq = f'img/{tipo_eq}-{marca}-{modelo}.png' if tipo_eq and marca and modelo else None
            equipamento_id = _json_next_id(equipamentos_data)
            equipamentos_data.append({
                'id': equipamento_id,
                'nome': eq.get('nome'),
                'tipo': eq.get('tipo'),
                'marca': eq.get('marca'),
                'modelo': eq.get('modelo'),
                'descricao': eq.get('descricao'),
                'foto': caminho_foto_eq,
                'icone': eq.get('icone'),
                'sala_id': sala_id,
                'defeito': 0,
                'dados': eq.get('dados', {})
            })
        _json_write_table(db_file, 'equipamentos', equipamentos_data)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        # Verificação de nome duplicado (case-insensitive)
        cur.execute('SELECT 1 FROM salas WHERE LOWER(nome) = LOWER(?)', (nome,))
        if cur.fetchone():
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Já existe uma sala com esse nome!'}), 400
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
            modelo = (eq.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
            caminho_foto = f'img/{tipo}-{marca}-{modelo}.png' if tipo and marca and modelo else None
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
            for eq in equipamentos_data:
                if eq.get('id') == int(eq_id):
                    eq['sala_id'] = sala_id
                    break
        _json_write_table(db_file, 'equipamentos', equipamentos_data)
    
    # Vincular equipamentos já existentes (sem sala) à nova sala (modo SQLite)
    if not _is_json_mode(db_file):
        equipamentos_ids = request.form.getlist('equipamentos_ids[]')
        for eq_id in equipamentos_ids:
            cur.execute('UPDATE equipamentos SET sala_id=? WHERE id=?', (sala_id, eq_id))
        conn.commit()
        conn.close()
    # Log de criação de sala (formulário/adicionar-sala)
    detalhes = f"Sala criada: ID={sala_id}, Nome={nome} (via formulário)"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SALA', detalhes, 'sucesso', db_file)
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
    modelo = (dados.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    caminho_foto = f'img/{tipo}-{marca}-{modelo}.png' if tipo and marca and modelo else None
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        equipamento_id = _json_next_id(equipamentos)
        registro = {
            'id': equipamento_id,
            'nome': dados.get('nome'),
            'tipo': dados.get('tipo'),
            'marca': dados.get('marca'),
            'modelo': dados.get('modelo'),
            'descricao': dados.get('descricao'),
            'foto': caminho_foto,
            'icone': dados.get('icone'),
            'sala_id': dados.get('sala_id'),
            'defeito': dados.get('defeito', 0),
            'dados': dados.get('dados', {})
        }
        equipamentos.append(registro)
        _json_write_table(db_file, 'equipamentos', equipamentos)
    else:
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
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_EQUIPAMENTO', detalhes, 'sucesso', db_file)
    return jsonify({'status': 'ok'})

@app.route('/equipamentos', methods=['GET'])
@login_required
def listar_equipamentos():
    sala_id = request.args.get('sala_id')
    conectaveis = request.args.get('conectaveis')
    disponiveis = request.args.get('disponiveis')
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        salas_map = {s.get('id'): s for s in _json_read_table(db_file, 'salas')}
        def tem_ip_ou_mac(d):
            if not isinstance(d, dict):
                return False
            return bool((d.get('ip1') or '').strip()) or bool((d.get('mac1') or '').strip())

        lista = []
        for e in equipamentos:
            registro = {
                'id': e.get('id'),
                'nome': e.get('nome'),
                'tipo': e.get('tipo'),
                'marca': e.get('marca'),
                'modelo': e.get('modelo'),
                'descricao': e.get('descricao'),
                'foto': e.get('foto'),
                'icone': e.get('icone'),
                'sala_id': e.get('sala_id'),
                'sala_nome': (salas_map.get(e.get('sala_id')) or {}).get('nome') if e.get('sala_id') else None,
                'defeito': int(e.get('defeito') or 0),
                'dados': e.get('dados') or {}
            }
            lista.append(registro)

        if conectaveis == '1':
            lista = [r for r in lista if r['sala_id'] is not None and tem_ip_ou_mac(r['dados']) and (r['defeito'] == 0) and not is_patch_panel(r)]
        elif disponiveis == '1':
            # Filtrar equipamentos que não estão conectados a switches ou patch panels
            conexoes = _json_read_table(db_file, 'conexoes')
            patch_panel_portas = _json_read_table(db_file, 'patch_panel_portas')
            
            # IDs de equipamentos já conectados
            equipamentos_conectados_switches = {c.get('equipamento_id') for c in conexoes if c.get('status') == 'ativa'}
            equipamentos_conectados_patch_panels = {p.get('equipamento_id') for p in patch_panel_portas if p.get('equipamento_id')}
            
            # Filtrar equipamentos disponíveis (não conectados e não patch panels)
            lista = [r for r in lista if 
                    r['sala_id'] is not None and 
                    tem_ip_ou_mac(r['dados']) and 
                    (r['defeito'] == 0) and
                    not is_patch_panel(r) and
                    r['id'] not in equipamentos_conectados_switches and
                    r['id'] not in equipamentos_conectados_patch_panels]
        elif sala_id == 'null':
            lista = [r for r in lista if r['sala_id'] is None and ('ponto' not in (r['tipo'] or '').lower()) and ('ponto' not in (r['nome'] or '').lower()) and not is_patch_panel(r)]
        elif sala_id:
            try:
                sala_id_int = int(sala_id)
                lista = [r for r in lista if r['sala_id'] == sala_id_int]
            except Exception:
                lista = [r for r in lista if False]
        # Filtrar patch panels de todas as listas
        lista = [r for r in lista if not is_patch_panel(r)]
        return jsonify(lista)
    else:
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
                  AND e.id NOT IN (SELECT equipamento_id FROM patch_panel_portas WHERE equipamento_id IS NOT NULL)
                  AND (e.defeito IS NULL OR e.defeito = 0)
                  AND LOWER(e.tipo) NOT LIKE '%patch panel%'
                  AND LOWER(e.tipo) NOT LIKE '%patch-panel%'
                  AND LOWER(e.tipo) NOT LIKE '%patchpanel%'
                  AND LOWER(e.tipo) NOT LIKE '%keystone%'
                  AND LOWER(e.nome) NOT LIKE '%patch panel%'
                  AND LOWER(e.nome) NOT LIKE '%patch-panel%'
                  AND LOWER(e.nome) NOT LIKE '%patchpanel%'
                  AND LOWER(e.nome) NOT LIKE '%keystone%'
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
                  AND LOWER(e.tipo) NOT LIKE '%patch panel%'
                  AND LOWER(e.tipo) NOT LIKE '%patch-panel%'
                  AND LOWER(e.tipo) NOT LIKE '%patchpanel%'
                  AND LOWER(e.tipo) NOT LIKE '%keystone%'
                  AND LOWER(e.nome) NOT LIKE '%patch panel%'
                  AND LOWER(e.nome) NOT LIKE '%patch-panel%'
                  AND LOWER(e.nome) NOT LIKE '%patchpanel%'
                  AND LOWER(e.nome) NOT LIKE '%keystone%'
            ''')
        elif sala_id == 'null':
            cur.execute('''
                SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, e.defeito, s.nome as sala_nome
                FROM equipamentos e
                LEFT JOIN salas s ON e.sala_id = s.id
                WHERE e.sala_id IS NULL
                  AND LOWER(e.tipo) NOT LIKE '%ponto%'
                  AND LOWER(e.nome) NOT LIKE '%ponto usuário%'
                  AND LOWER(e.nome) NOT LIKE '%ponto usuario%'
                  AND LOWER(e.tipo) NOT LIKE '%patch panel%'
                  AND LOWER(e.tipo) NOT LIKE '%patch-panel%'
                  AND LOWER(e.tipo) NOT LIKE '%patchpanel%'
                  AND LOWER(e.tipo) NOT LIKE '%keystone%'
                  AND LOWER(e.nome) NOT LIKE '%patch panel%'
                  AND LOWER(e.nome) NOT LIKE '%patch-panel%'
                  AND LOWER(e.nome) NOT LIKE '%patchpanel%'
                  AND LOWER(e.nome) NOT LIKE '%keystone%'
            ''')
        elif sala_id:
            cur.execute('''
                SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, e.defeito, s.nome as sala_nome
                FROM equipamentos e
                LEFT JOIN salas s ON e.sala_id = s.id
                WHERE e.sala_id=?
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
                'sala_nome': row['sala_nome'],
                'defeito': defeito_val,
                'dados': dados
            })
        conn.close()
        return jsonify(equipamentos)

@app.route('/equipamentos-disponiveis', methods=['GET'])
@login_required
def listar_equipamentos_disponiveis():
    """Lista apenas equipamentos funcionando (defeito = 0) para adicionar às salas"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        resultado = []
        for e in equipamentos:
            if e.get('sala_id') is None and ('ponto' not in (e.get('tipo') or '').lower()) and ('ponto' not in (e.get('nome') or '').lower()) and int(e.get('defeito') or 0) == 0 and not is_patch_panel(e):
                resultado.append({
                    'id': e.get('id'),
                    'nome': e.get('nome'),
                    'tipo': e.get('tipo'),
                    'marca': e.get('marca'),
                    'modelo': e.get('modelo'),
                    'descricao': e.get('descricao'),
                    'foto': e.get('foto'),
                    'icone': e.get('icone'),
                    'sala_id': e.get('sala_id'),
                    'sala_nome': None,
                    'defeito': int(e.get('defeito') or 0),
                    'dados': e.get('dados') or {}
                })
        return jsonify(resultado)
    else:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.descricao, e.foto, e.icone, e.sala_id, e.defeito, s.nome as sala_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
            WHERE e.sala_id IS NULL
              AND LOWER(e.tipo) NOT LIKE '%ponto%'
              AND LOWER(e.nome) NOT LIKE '%ponto usuário%'
              AND LOWER(e.nome) NOT LIKE '%ponto usuario%'
              AND (e.defeito IS NULL OR e.defeito = 0)
              AND LOWER(e.tipo) NOT LIKE '%patch panel%'
              AND LOWER(e.tipo) NOT LIKE '%patch-panel%'
              AND LOWER(e.tipo) NOT LIKE '%patchpanel%'
              AND LOWER(e.tipo) NOT LIKE '%keystone%'
              AND LOWER(e.nome) NOT LIKE '%patch panel%'
              AND LOWER(e.nome) NOT LIKE '%patch-panel%'
              AND LOWER(e.nome) NOT LIKE '%patchpanel%'
              AND LOWER(e.nome) NOT LIKE '%keystone%'
        ''')
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
                'sala_nome': row['sala_nome'],
                'defeito': defeito_val,
                'dados': dados
            })
        conn.close()
        return jsonify(equipamentos)

@app.route('/equipamentos/<int:id>', methods=['PUT'])
@tecnico_required
def atualizar_equipamento(id):
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    tipo = (dados.get('tipo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    marca = (dados.get('marca') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    modelo = (dados.get('modelo') or '').strip().lower().replace(' ', '-').replace('ç','c').replace('ã','a').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('â','a').replace('ê','e').replace('ô','o').replace('õ','o').replace('ü','u').replace('ñ','n')
    caminho_foto = f'img/{tipo}-{marca}-{modelo}.png' if tipo and marca and modelo else None
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        alvo = next((e for e in equipamentos if e.get('id') == id), None)
        if not alvo:
            return jsonify({'status': 'erro', 'mensagem': 'Equipamento não encontrado'}), 404
        alvo['nome'] = dados.get('nome')
        alvo['tipo'] = dados.get('tipo')
        alvo['marca'] = dados.get('marca')
        alvo['modelo'] = dados.get('modelo')
        alvo['descricao'] = dados.get('descricao')
        alvo['foto'] = caminho_foto
        alvo['icone'] = dados.get('icone')
        alvo['defeito'] = dados.get('defeito', 0)
        # mescla dados
        existentes = alvo.get('dados') or {}
        novos = dados.get('dados', {}) or {}
        for k, v in novos.items():
            existentes[k] = v
        alvo['dados'] = existentes
        _json_write_table(db_file, 'equipamentos', equipamentos)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute('''
            UPDATE equipamentos SET nome=?, tipo=?, marca=?, modelo=?, descricao=?, foto=?, icone=?, defeito=?
            WHERE id=?
        ''', (
            dados['nome'],
            dados.get('tipo'),
            dados.get('marca'),
            dados.get('modelo'),
            dados.get('descricao'),
            caminho_foto,
            dados.get('icone'),
            dados.get('defeito', 0),
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
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_EQUIPAMENTO', detalhes, 'sucesso', db_file)
    return jsonify({'status': 'ok'})

@app.route('/equipamentos/<int:id>', methods=['GET'])
@login_required
def get_equipamento(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        e = next((x for x in equipamentos if x.get('id') == id), None)
        if not e:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        return jsonify({
            'id': e.get('id'),
            'nome': e.get('nome'),
            'tipo': e.get('tipo'),
            'marca': e.get('marca'),
            'modelo': e.get('modelo'),
            'descricao': e.get('descricao'),
            'foto': e.get('foto'),
            'icone': e.get('icone'),
            'sala_id': e.get('sala_id'),
            'dados': e.get('dados') or {}
        })
    else:
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
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        alvo = next((e for e in equipamentos if e.get('id') == id), None)
        nome = alvo.get('nome') if alvo else ''
        tipo = alvo.get('tipo') if alvo else ''
        marca = alvo.get('marca') if alvo else ''
        modelo = alvo.get('modelo') if alvo else ''
        equipamentos = [e for e in equipamentos if e.get('id') != id]
        _json_write_table(db_file, 'equipamentos', equipamentos)
    else:
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
    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_EQUIPAMENTO', detalhes, 'sucesso', db_file)
    return jsonify({'status': 'ok'})

@app.route('/tipos-equipamento')
@login_required
def tipos_equipamento():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        tipos_cadastrados = sorted({(e.get('tipo') or '') for e in equipamentos if (e.get('tipo') or '') != ''})
        
        # Sempre incluir tipos padrão para permitir criação de novos equipamentos
        try:
            with open('static/data/tipos-equipamentos.json', 'r', encoding='utf-8') as f:
                tipos_padrao = json.load(f)
        except Exception:
            # Fallback para tipos básicos se o arquivo não existir
            tipos_padrao = ['TV', 'Monitor', 'Projetor', 'Notebook', 'Desktop', 'Roteador', 'Switch', 'Servidor', 'Impressora', 'Outro']
        
        # Combinar tipos cadastrados com tipos padrão
        todos_tipos = set(tipos_cadastrados + tipos_padrao)
        tipos = sorted(list(todos_tipos))
        
        return jsonify(tipos)
    else:
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
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        marcas = sorted({(e.get('marca') or '') for e in equipamentos if (e.get('tipo') or '') == (tipo or '') and (e.get('marca') or '') != ''})
        return jsonify(list(marcas))
    else:
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
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        modelos = sorted({(e.get('modelo') or '') for e in equipamentos if (e.get('tipo') or '') == (tipo or '') and (e.get('marca') or '') == (marca or '') and (e.get('modelo') or '') != ''})
        return jsonify(list(modelos))
    else:
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
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SWITCH', 'Dados JSON inválidos', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        switch_id = _json_next_id(switches)
        registro = {
            'id': switch_id,
            'nome': dados.get('nome'),
            'marca': dados.get('marca'),
            'modelo': dados.get('modelo'),
            'data_criacao': datetime.now().isoformat()
        }
        switches.append(registro)
        _json_write_table(db_file, 'switches', switches)

        # criar portas padrão
        modelo = (dados.get('modelo') or '').lower()
        # Sempre criar 48 portas para novos switches
        num_portas = 48
        portas = _json_read_table(db_file, 'switch_portas')
        for porta_num in range(1, num_portas + 1):
            descricao = f"Porta {porta_num}"
            if porta_num <= 4:
                descricao += " (Uplink/Gerenciamento)"
            elif porta_num <= 8:
                descricao += " (PoE)"
            else:
                descricao += " (Acesso)"
            portas.append({
                'id': _json_next_id(portas),
                'switch_id': switch_id,
                'numero_porta': porta_num,
                'descricao': descricao,
                'status': 'livre'
            })
        _json_write_table(db_file, 'switch_portas', portas)

        # vínculo opcional com andar/idf
        andar_id = dados.get('andar_id')
        idf_responsavel_id = dados.get('idf_responsavel_id')
        if andar_id is not None and str(andar_id) != '':
            andar_switches = _json_read_table(db_file, 'andar_switches')
            # remove duplicados do mesmo switch
            andar_switches = [x for x in andar_switches if x.get('switch_id') != switch_id]
            andar_switches.append({
                'id': _json_next_id(andar_switches),
                'andar_id': andar_id,
                'switch_id': switch_id,
                'idf_responsavel_id': idf_responsavel_id
            })
            _json_write_table(db_file, 'andar_switches', andar_switches)
        num_portas = num_portas
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Criar tabela de switches se não existir
        cur.execute('''
            CREATE TABLE IF NOT EXISTS switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de portas de switches se não existir
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
            INSERT INTO switches (nome, marca, modelo)
            VALUES (?, ?, ?)
        ''', (
            dados['nome'],
            dados['marca'],
            dados['modelo']
        ))
        switch_id = cur.lastrowid
        
        # Criar portas padrão
        modelo = dados['modelo'].lower()
        # Sempre criar 48 portas para novos switches
        num_portas = 48
        for porta_num in range(1, num_portas + 1):
            descricao = f"Porta {porta_num}"
            if porta_num <= 4:
                descricao += " (Uplink/Gerenciamento)"
            elif porta_num <= 8:
                descricao += " (PoE)"
            else:
                descricao += " (Acesso)"
            cur.execute('''
                INSERT INTO switch_portas (switch_id, numero_porta, descricao, status)
                VALUES (?, ?, ?, ?)
            ''', (switch_id, porta_num, descricao, 'livre'))
        
        # Vincular ao andar/IDF se informado
        andar_id = dados.get('andar_id')
        idf_responsavel_id = dados.get('idf_responsavel_id')
        if andar_id is not None and str(andar_id) != '':
            # Garantir tabela
            cur.execute('''
                CREATE TABLE IF NOT EXISTS andar_switches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    andar_id INTEGER NOT NULL,
                    switch_id INTEGER NOT NULL,
                    idf_responsavel_id INTEGER,
                    UNIQUE(andar_id, switch_id)
                )
            ''')
            try:
                cur.execute('''
                    INSERT INTO andar_switches (andar_id, switch_id, idf_responsavel_id)
                    VALUES (?, ?, ?)
                ''', (andar_id, switch_id, idf_responsavel_id))
            except sqlite3.IntegrityError:
                cur.execute('''
                    UPDATE andar_switches SET idf_responsavel_id=?
                    WHERE andar_id=? AND switch_id=?
                ''', (idf_responsavel_id, andar_id, switch_id))

        conn.commit()
        conn.close()
    
    # Log de criação de switch e portas
    detalhes = f"Switch criado: ID={switch_id}, Nome={dados['nome']}, Marca={dados['marca']}, Modelo={dados['modelo']}, Portas criadas: {num_portas}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_SWITCH', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok', 'id': switch_id, 'portas_criadas': num_portas})

@app.route('/switches', methods=['GET'])
@login_required
def listar_switches():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        andar_links = _json_read_table(db_file, 'andar_switches')
        idfs = {i.get('id'): i for i in _json_read_table(db_file, 'idfs')}
        resultado = []
        for s in switches:
            link = next((l for l in andar_links if l.get('switch_id') == s.get('id')), None)
            andar_id = link.get('andar_id') if link else None
            idf_responsavel_id = link.get('idf_responsavel_id') if link else None
            if andar_id == 0:
                andar_titulo = 'Térreo'
            elif andar_id is not None:
                andar_titulo = f"{andar_id}º Andar"
            else:
                andar_titulo = None
            resultado.append({
                'id': s.get('id'),
                'nome': s.get('nome'),
                'marca': s.get('marca'),
                'modelo': s.get('modelo'),
                'data_criacao': s.get('data_criacao'),
                'andar_id': andar_id,
                'idf_responsavel_id': idf_responsavel_id,
                'andar_titulo': andar_titulo,
                'idf_nome': (idfs.get(idf_responsavel_id) or {}).get('nome') if idf_responsavel_id else None
            })
        # ordenar por data_criacao desc
        resultado.sort(key=lambda x: x.get('data_criacao') or '', reverse=True)
        return jsonify(resultado)
    else:
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
        
        cur.execute('''
            SELECT s.id, s.nome, s.marca, s.modelo, s.data_criacao,
                   asw.andar_id, asw.idf_responsavel_id,
                   CASE 
                       WHEN asw.andar_id = 0 THEN 'Térreo'
                       WHEN asw.andar_id IS NOT NULL THEN asw.andar_id || 'º Andar'
                       ELSE NULL
                   END as andar_titulo,
                   i.nome as idf_nome
            FROM switches s
            LEFT JOIN andar_switches asw ON s.id = asw.switch_id
            LEFT JOIN idfs i ON asw.idf_responsavel_id = i.id
            ORDER BY s.data_criacao DESC
        ''')
        switches = []
        for row in cur.fetchall():
            switch = {
                'id': row[0],
                'nome': row[1],
                'marca': row[2],
                'modelo': row[3],
                'data_criacao': row[4],
                'andar_id': row[5],
                'idf_responsavel_id': row[6],
                'andar_titulo': row[7],
                'idf_nome': row[8]
            }
            switches.append(switch)
        conn.close()
        return jsonify(switches)

@app.route('/switches/<int:id>', methods=['GET'])
@login_required
def get_switch(id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        s = next((x for x in switches if x.get('id') == id), None)
        if not s:
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        links = _json_read_table(db_file, 'andar_switches')
        link = next((l for l in links if l.get('switch_id') == id), None)
        andar_id = link.get('andar_id') if link else None
        idf_responsavel_id = link.get('idf_responsavel_id') if link else None
        if andar_id == 0:
            andar_titulo = 'Térreo'
        elif andar_id is not None:
            andar_titulo = f"{andar_id}º Andar"
        else:
            andar_titulo = None
        idfs = {i.get('id'): i for i in _json_read_table(db_file, 'idfs')}
        retorno = {
            'id': s.get('id'),
            'nome': s.get('nome'),
            'marca': s.get('marca'),
            'modelo': s.get('modelo'),
            'data_criacao': s.get('data_criacao'),
            'andar_id': andar_id,
            'idf_responsavel_id': idf_responsavel_id,
            'andar_titulo': andar_titulo,
            'idf_nome': (idfs.get(idf_responsavel_id) or {}).get('nome') if idf_responsavel_id else None
        }
        return jsonify(retorno)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        cur.execute('''
            SELECT s.id, s.nome, s.marca, s.modelo, s.data_criacao,
                   asw.andar_id, asw.idf_responsavel_id,
                   CASE 
                       WHEN asw.andar_id = 0 THEN 'Térreo'
                       WHEN asw.andar_id IS NOT NULL THEN asw.andar_id || 'º Andar'
                       ELSE NULL
                   END as andar_titulo,
                   i.nome as idf_nome
            FROM switches s
            LEFT JOIN andar_switches asw ON s.id = asw.switch_id
            LEFT JOIN idfs i ON asw.idf_responsavel_id = i.id
            WHERE s.id = ?
        ''', (id,))
        row = cur.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        
        switch = {
            'id': row[0],
            'nome': row[1],
            'marca': row[2],
            'modelo': row[3],
            'data_criacao': row[4],
            'andar_id': row[5],
            'idf_responsavel_id': row[6],
            'andar_titulo': row[7],
            'idf_nome': row[8]
        }
        
        conn.close()
        return jsonify(switch)

@app.route('/switches/<int:id>', methods=['PUT'])
@admin_required
def atualizar_switch(id):
    dados = request.json
    if not dados:
        registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', f'Switch ID={id}: Dados JSON inválidos', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        s = next((x for x in switches if x.get('id') == id), None)
        if not s:
            registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', f'Switch ID={id}: Não encontrado', 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        s['nome'] = dados.get('nome')
        s['marca'] = dados.get('marca')
        s['modelo'] = dados.get('modelo')
        _json_write_table(db_file, 'switches', switches)

        andar_id = dados.get('andar_id')
        idf_responsavel_id = dados.get('idf_responsavel_id')
        links = _json_read_table(db_file, 'andar_switches')
        links = [l for l in links if l.get('switch_id') != id]
        if andar_id is not None and str(andar_id) != '':
            links.append({
                'id': _json_next_id(links),
                'andar_id': andar_id,
                'switch_id': id,
                'idf_responsavel_id': idf_responsavel_id
            })
        _json_write_table(db_file, 'andar_switches', links)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Verificar se o switch existe
        cur.execute('SELECT id FROM switches WHERE id=?', (id,))
        if not cur.fetchone():
            registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', f'Switch ID={id}: Não encontrado', 'erro', db_file)
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
        
        # Gerenciar vínculos de andar/IDF
        andar_id = dados.get('andar_id')
        idf_responsavel_id = dados.get('idf_responsavel_id')
        
        # Garantir que a tabela andar_switches existe
        cur.execute('''
            CREATE TABLE IF NOT EXISTS andar_switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                andar_id INTEGER NOT NULL,
                switch_id INTEGER NOT NULL,
                idf_responsavel_id INTEGER,
                UNIQUE(andar_id, switch_id)
            )
        ''')
        
        # Remover vínculos existentes
        cur.execute('DELETE FROM andar_switches WHERE switch_id = ?', (id,))
        
        # Adicionar novo vínculo se andar_id foi fornecido
        if andar_id is not None and str(andar_id) != '':
            try:
                cur.execute('''
                    INSERT INTO andar_switches (andar_id, switch_id, idf_responsavel_id)
                    VALUES (?, ?, ?)
                ''', (andar_id, id, idf_responsavel_id))
            except sqlite3.IntegrityError:
                # Se já existe, atualizar
                cur.execute('''
                    UPDATE andar_switches SET idf_responsavel_id=?
                    WHERE andar_id=? AND switch_id=?
                ''', (idf_responsavel_id, andar_id, id))
        
        conn.commit()
        conn.close()
    
    # Registrar log de sucesso
    detalhes = f"Switch atualizado: ID={id}, Nome={dados['nome']}, Marca={dados['marca']}, Modelo={dados['modelo']}"
    if andar_id is not None:
        detalhes += f", Andar={andar_id}, IDF={idf_responsavel_id or 'Nenhum'}"
    registrar_log(session.get('username', 'desconhecido'), 'ATUALIZAR_SWITCH', detalhes, 'sucesso', db_file)
    
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
    if _is_json_mode(db_file):
        portas = _json_read_table(db_file, 'switch_portas')
        # checar duplicidade
        if any(p.get('switch_id') == dados.get('switch_id') and int(p.get('numero_porta')) == int(dados.get('numero_porta')) for p in portas):
            return jsonify({'status': 'erro', 'mensagem': 'Porta já existe para este switch'}), 400
        porta = {
            'id': _json_next_id(portas),
            'switch_id': dados.get('switch_id'),
            'numero_porta': dados.get('numero_porta'),
            'descricao': dados.get('descricao', ''),
            'status': dados.get('status', 'livre')
        }
        portas.append(porta)
        _json_write_table(db_file, 'switch_portas', portas)
        return jsonify({'status': 'ok', 'id': porta['id']})
    else:
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

@app.route('/switch-portas/<int:switch_id>/criar-portas-padrao', methods=['POST'])
@admin_required
def criar_portas_padrao_switch(switch_id):
    """Criar portas padrão para um switch existente que não tem portas"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        s = next((x for x in switches if x.get('id') == switch_id), None)
        if not s:
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        portas = _json_read_table(db_file, 'switch_portas')
        if any(p.get('switch_id') == switch_id for p in portas):
            return jsonify({'status': 'erro', 'mensagem': 'Switch já possui portas configuradas'}), 400
        modelo = (s.get('modelo') or '').lower()
        # Sempre criar 48 portas para switches sem portas
        num_portas = 48
        for porta_num in range(1, num_portas + 1):
            descricao = f"Porta {porta_num}"
            if porta_num <= 4:
                descricao += " (Uplink/Gerenciamento)"
            elif porta_num <= 8:
                descricao += " (PoE)"
            else:
                descricao += " (Acesso)"
            portas.append({
                'id': _json_next_id(portas),
                'switch_id': switch_id,
                'numero_porta': porta_num,
                'descricao': descricao,
                'status': 'livre'
            })
        _json_write_table(db_file, 'switch_portas', portas)
        detalhes = f"Portas padrão criadas para switch ID={switch_id}, Nome={s.get('nome')}, Portas criadas: {num_portas}"
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_PORTAS_PADRAO_SWITCH', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok', 'portas_criadas': num_portas, 'mensagem': f'{num_portas} portas criadas com sucesso para o switch {s.get("nome")}'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Verificar se o switch existe
        cur.execute('SELECT nome, modelo FROM switches WHERE id = ?', (switch_id,))
        switch = cur.fetchone()
        if not switch:
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        
        # Verificar se já existem portas para este switch
        cur.execute('SELECT COUNT(*) FROM switch_portas WHERE switch_id = ?', (switch_id,))
        if cur.fetchone()[0] > 0:
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Switch já possui portas configuradas'}), 400
        
        # Determinar número de portas baseado no modelo
        modelo = switch[1].lower()
        # Sempre recriar 48 portas
        num_portas = 48
        
        # Criar portas automaticamente
        for porta_num in range(1, num_portas + 1):
            descricao = f"Porta {porta_num}"
            if porta_num <= 4:
                descricao += " (Uplink/Gerenciamento)"
            elif porta_num <= 8:
                descricao += " (PoE)"
            else:
                descricao += " (Acesso)"
                
            cur.execute('''
                INSERT INTO switch_portas (switch_id, numero_porta, descricao, status)
                VALUES (?, ?, ?, ?)
            ''', (switch_id, porta_num, descricao, 'livre'))
        
        conn.commit()
        conn.close()
    
    # Log da criação de portas
    detalhes = f"Portas padrão criadas para switch ID={switch_id}, Nome={switch[0]}, Portas criadas: {num_portas}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_PORTAS_PADRAO_SWITCH', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok', 'portas_criadas': num_portas, 'mensagem': f'{num_portas} portas criadas com sucesso para o switch {switch[0]}'})

@app.route('/switch-portas/<int:switch_id>/recriar-portas', methods=['POST'])
@admin_required
def recriar_portas_switch(switch_id):
    """Recriar todas as portas de um switch (remover existentes e criar novas)"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        s = next((x for x in switches if x.get('id') == switch_id), None)
        if not s:
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        numero_portas = dados.get('numero_portas', 24)
        if numero_portas < 1 or numero_portas > 100:
            return jsonify({'status': 'erro', 'mensagem': 'Número de portas deve estar entre 1 e 100'}), 400
        portas = _json_read_table(db_file, 'switch_portas')
        # remover portas existentes
        portas = [p for p in portas if p.get('switch_id') != switch_id]
        _json_write_table(db_file, 'switch_portas', portas)
        # remover mapeamentos de patch panel
        ppp = _json_read_table(db_file, 'patch_panel_portas')
        ppp = [m for m in ppp if m.get('switch_id') != switch_id]
        _json_write_table(db_file, 'patch_panel_portas', ppp)
        # remover conexões das portas deste switch
        conexoes = _json_read_table(db_file, 'conexoes')
        # precisamos conhecer as portas antigas; já removidas, então nenhuma ativa. Garantimos limpando conexoes por switch_id não trivial, então mantemos apenas conexoes que não referem esse switch
        # Como conexoes referem porta_id, vamos simplesmente descartar conexões cujas porta_id não existam mais (todas desse switch)
        portas_ids_restantes = {p.get('id') for p in portas}
        conexoes = [c for c in conexoes if c.get('porta_id') in portas_ids_restantes]
        _json_write_table(db_file, 'conexoes', conexoes)
        # criar novas portas
        portas = _json_read_table(db_file, 'switch_portas')
        for porta_num in range(1, numero_portas + 1):
            descricao = f"Porta {porta_num}"
            if porta_num <= 4:
                descricao += " (Uplink/Gerenciamento)"
            elif porta_num <= 8:
                descricao += " (PoE)"
            else:
                descricao += " (Acesso)"
            portas.append({
                'id': _json_next_id(portas),
                'switch_id': switch_id,
                'numero_porta': porta_num,
                'descricao': descricao,
                'status': 'livre'
            })
        _json_write_table(db_file, 'switch_portas', portas)
        detalhes = f"Portas recriadas para switch ID={switch_id}, Nome={s.get('nome')}, Portas criadas: {numero_portas}"
        registrar_log(session.get('username', 'desconhecido'), 'RECRIAR_PORTAS_SWITCH', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok', 'portas_criadas': numero_portas, 'mensagem': f'{numero_portas} portas recriadas com sucesso para o switch {s.get("nome")}'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        try:
            # Verificar se o switch existe
            cur.execute('SELECT nome, modelo FROM switches WHERE id = ?', (switch_id,))
            switch = cur.fetchone()
            if not switch:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
            
            numero_portas = dados.get('numero_portas', 24)
            if numero_portas < 1 or numero_portas > 100:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Número de portas deve estar entre 1 e 100'}), 400
            
            # Remover todas as portas existentes (isso também remove conexões e mapeamentos)
            cur.execute('DELETE FROM switch_portas WHERE switch_id = ?', (switch_id,))
            
            # Remover mapeamentos de patch panel para este switch
            cur.execute('DELETE FROM patch_panel_portas WHERE switch_id = ?', (switch_id,))
            
            # Remover conexões diretas para este switch
            cur.execute('''
                DELETE FROM conexoes 
                WHERE porta_id IN (SELECT id FROM switch_portas WHERE switch_id = ?)
            ''', (switch_id,))
            
            # Criar novas portas
            for porta_num in range(1, numero_portas + 1):
                descricao = f"Porta {porta_num}"
                if porta_num <= 4:
                    descricao += " (Uplink/Gerenciamento)"
                elif porta_num <= 8:
                    descricao += " (PoE)"
                else:
                    descricao += " (Acesso)"
                
                cur.execute('''
                    INSERT INTO switch_portas (switch_id, numero_porta, descricao, status)
                    VALUES (?, ?, ?, ?)
                ''', (switch_id, porta_num, descricao, 'livre'))
            
            conn.commit()
            
            # Log da recriação de portas
            detalhes = f"Portas recriadas para switch ID={switch_id}, Nome={switch[0]}, Portas criadas: {numero_portas}"
            registrar_log(session.get('username', 'desconhecido'), 'RECRIAR_PORTAS_SWITCH', detalhes, 'sucesso', db_file)
            
            return jsonify({
                'status': 'ok', 
                'portas_criadas': numero_portas, 
                'mensagem': f'{numero_portas} portas recriadas com sucesso para o switch {switch[0]}'
            })
            
        except Exception as e:
            conn.rollback()
            detalhes = f"Erro ao recriar portas para switch ID={switch_id}: {str(e)}"
            registrar_log(session.get('username', 'desconhecido'), 'RECRIAR_PORTAS_SWITCH', detalhes, 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': f'Erro ao recriar portas: {str(e)}'}), 500
        
        finally:
            conn.close()

@app.route('/switch-portas/<int:switch_id>/adicionar-portas', methods=['POST'])
@admin_required
def adicionar_portas_switch(switch_id):
    """Adicionar mais portas a um switch existente"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        s = next((x for x in switches if x.get('id') == switch_id), None)
        if not s:
            return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
        numero_portas = dados.get('numero_portas', 1)
        if numero_portas < 1 or numero_portas > 50:
            return jsonify({'status': 'erro', 'mensagem': 'Número de portas deve estar entre 1 e 50'}), 400
        portas = _json_read_table(db_file, 'switch_portas')
        existentes = [p for p in portas if p.get('switch_id') == switch_id]
        max_porta = max([p.get('numero_porta') for p in existentes], default=0)
        portas_criadas = 0
        for i in range(1, numero_portas + 1):
            porta_num = max_porta + i
            descricao = f"Porta {porta_num}"
            if porta_num <= 4:
                descricao += " (Uplink/Gerenciamento)"
            elif porta_num <= 8:
                descricao += " (PoE)"
            else:
                descricao += " (Acesso)"
            portas.append({
                'id': _json_next_id(portas),
                'switch_id': switch_id,
                'numero_porta': porta_num,
                'descricao': descricao,
                'status': 'livre'
            })
            portas_criadas += 1
        _json_write_table(db_file, 'switch_portas', portas)
        detalhes = f"Portas adicionadas ao switch ID={switch_id}, Nome={s.get('nome')}, Portas adicionadas: {portas_criadas}"
        registrar_log(session.get('username', 'desconhecido'), 'ADICIONAR_PORTAS_SWITCH', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok', 'portas_adicionadas': portas_criadas, 'mensagem': f'{portas_criadas} portas adicionadas com sucesso ao switch {s.get("nome")}'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        try:
            # Verificar se o switch existe
            cur.execute('SELECT nome, modelo FROM switches WHERE id = ?', (switch_id,))
            switch = cur.fetchone()
            if not switch:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Switch não encontrado'}), 404
            
            numero_portas = dados.get('numero_portas', 1)
            if numero_portas < 1 or numero_portas > 50:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Número de portas deve estar entre 1 e 50'}), 400
            
            # Obter o maior número de porta existente
            cur.execute('SELECT MAX(numero_porta) FROM switch_portas WHERE switch_id = ?', (switch_id,))
            max_porta = cur.fetchone()[0] or 0
            
            # Criar novas portas a partir do próximo número
            portas_criadas = 0
            for i in range(1, numero_portas + 1):
                porta_num = max_porta + i
                descricao = f"Porta {porta_num}"
                if porta_num <= 4:
                    descricao += " (Uplink/Gerenciamento)"
                elif porta_num <= 8:
                    descricao += " (PoE)"
                else:
                    descricao += " (Acesso)"
                    
                cur.execute('''
                    INSERT INTO switch_portas (switch_id, numero_porta, descricao, status)
                    VALUES (?, ?, ?, ?)
                ''', (switch_id, porta_num, descricao, 'livre'))
                portas_criadas += 1
            
            conn.commit()
            
            # Log da adição de portas
            detalhes = f"Portas adicionadas ao switch ID={switch_id}, Nome={switch[0]}, Portas adicionadas: {portas_criadas}"
            registrar_log(session.get('username', 'desconhecido'), 'ADICIONAR_PORTAS_SWITCH', detalhes, 'sucesso', db_file)
            
            return jsonify({
                'status': 'ok', 
                'portas_adicionadas': portas_criadas, 
                'mensagem': f'{portas_criadas} portas adicionadas com sucesso ao switch {switch[0]}'
            })
            
        except Exception as e:
            conn.rollback()
            detalhes = f"Erro ao adicionar portas ao switch ID={switch_id}: {str(e)}"
            registrar_log(session.get('username', 'desconhecido'), 'ADICIONAR_PORTAS_SWITCH', detalhes, 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': f'Erro ao adicionar portas: {str(e)}'}), 500
        
        finally:
            conn.close()

@app.route('/switch-portas/<int:switch_id>', methods=['GET'])
@login_required
def listar_portas_switch(switch_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        portas = [p for p in _json_read_table(db_file, 'switch_portas') if p.get('switch_id') == switch_id]
        portas.sort(key=lambda x: int(x.get('numero_porta') or 0))
        conexoes = [c for c in _json_read_table(db_file, 'conexoes') if c.get('status') == 'ativa']
        equipamentos = {e.get('id'): e for e in _json_read_table(db_file, 'equipamentos')}
        salas = {s.get('id'): s for s in _json_read_table(db_file, 'salas')}
        ppp = [m for m in _json_read_table(db_file, 'patch_panel_portas') if m.get('switch_id') == switch_id]
        patch_panels = {p.get('id'): p for p in _json_read_table(db_file, 'patch_panels')}
        resposta = []
        for p in portas:
            porta_id = p.get('id')
            numero_porta = p.get('numero_porta')
            descricao = p.get('descricao')
            status = 'livre'
            equipamento_info = None
            patch_panel_info = None
            cx = next((c for c in conexoes if c.get('porta_id') == porta_id), None)
            if cx:
                status = 'ocupada'
                eq = equipamentos.get(cx.get('equipamento_id'))
                if eq:
                    sala_nome = (salas.get(eq.get('sala_id')) or {}).get('nome') if eq.get('sala_id') else None
                    dados = eq.get('dados') or {}
                    equipamento_info = {
                        'nome': eq.get('nome'),
                        'tipo': eq.get('tipo'),
                        'sala_nome': sala_nome,
                        'ip1': (dados.get('ip1') or ''),
                        'ip2': (dados.get('ip2') or ''),
                        'mac1': (dados.get('mac1') or ''),
                        'mac2': (dados.get('mac2') or '')
                    }
            mapeamento = next((m for m in ppp if int(m.get('porta_switch') or 0) == int(numero_porta)), None)
            if mapeamento:
                status = 'ocupada'
                pp = patch_panels.get(mapeamento.get('patch_panel_id'))
                prefixo = (pp or {}).get('prefixo_keystone')
                andar = (pp or {}).get('andar')
                if not prefixo:
                    prefixo = f"PT{20 + (andar or 0)}"
                keystone = f"{prefixo}-{int(mapeamento.get('numero_porta') or 0):04d}"
                equipamento_patch = None
                eqp = equipamentos.get(mapeamento.get('equipamento_id')) if mapeamento.get('equipamento_id') else None
                if eqp:
                    dados = eqp.get('dados') or {}
                    equipamento_patch = {
                        'nome': eqp.get('nome'),
                        'tipo': eqp.get('tipo'),
                        'sala': (salas.get(eqp.get('sala_id')) or {}).get('nome') if eqp.get('sala_id') else None,
                        'ip1': (dados.get('ip1') or ''),
                        'ip2': (dados.get('ip2') or ''),
                        'mac1': (dados.get('mac1') or ''),
                        'mac2': (dados.get('mac2') or '')
                    }
                patch_panel_info = {
                    'nome': (pp or {}).get('nome'),
                    'porta_patch_panel': mapeamento.get('numero_porta'),
                    'keystone': keystone,
                    'equipamento': equipamento_patch
                }
            resposta.append({
                'id': porta_id,
                'numero_porta': numero_porta,
                'descricao': descricao,
                'status': status,
                'equipamento_info': equipamento_info,
                'patch_panel_info': patch_panel_info
            })
        return jsonify(resposta)
    else:
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
            WHERE sp.switch_id = ?
            ORDER BY sp.numero_porta
        ''', (switch_id,))
        
        portas = []
        for row in cur.fetchall():
            equipamento_info = None
            patch_panel_info = None
            
            if row[4]:  # Equipamento conectado diretamente
                # Buscar dados extras do equipamento
                cur.execute("SELECT id FROM equipamentos WHERE nome=? AND tipo= ?", (row[4], row[5]))
                eq_row = cur.fetchone()
                eq_id = eq_row[0] if eq_row else None
                dados = {}
                if eq_id:
                    cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=? AND chave IN ('ip1','ip2','mac1','mac2')", (eq_id,))
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
                cur.execute("SELECT prefixo_keystone, andar FROM patch_panels WHERE nome = ?", (row[7],))
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
                        WHERE e.id = ?
                    """, (row[10],))
                    
                    equip_result = cur.fetchone()
                    if equip_result and equip_result[0]:
                        # Buscar dados extras do equipamento (IP, MAC)
                        dados = {}
                        cur.execute("SELECT chave, valor FROM equipamento_dados WHERE equipamento_id=? AND chave IN ('ip1','ip2','mac1','mac2')", (equip_result[3],))
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

@app.route('/switch-portas/<int:porta_id>', methods=['PUT'])
@admin_required
def editar_porta_switch(porta_id):
    """Editar uma porta específica do switch"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        portas = _json_read_table(db_file, 'switch_portas')
        p = next((x for x in portas if x.get('id') == porta_id), None)
        if not p:
            return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
        if 'descricao' in dados:
            p['descricao'] = dados.get('descricao')
        _json_write_table(db_file, 'switch_portas', portas)
        detalhes = f"Porta editada: ID={porta_id}, Switch ID={p.get('switch_id')}, Porta {p.get('numero_porta')}"
        registrar_log(session.get('username', 'desconhecido'), 'EDITAR_PORTA_SWITCH', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok', 'mensagem': 'Porta editada com sucesso!'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        try:
            # Verificar se a porta existe
            cur.execute('SELECT id, switch_id, numero_porta FROM switch_portas WHERE id = ?', (porta_id,))
            porta = cur.fetchone()
            if not porta:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
            
            # Atualizar a porta
            if 'descricao' in dados:
                cur.execute('UPDATE switch_portas SET descricao = ? WHERE id = ?', (dados['descricao'], porta_id))
            
            conn.commit()
            
            # Log da edição da porta
            detalhes = f"Porta editada: ID={porta_id}, Switch ID={porta[1]}, Porta {porta[2]}"
            registrar_log(session.get('username', 'desconhecido'), 'EDITAR_PORTA_SWITCH', detalhes, 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Porta editada com sucesso!'})
            
        except Exception as e:
            conn.rollback()
            detalhes = f"Erro ao editar porta ID={porta_id}: {str(e)}"
            registrar_log(session.get('username', 'desconhecido'), 'EDITAR_PORTA_SWITCH', detalhes, 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': f'Erro ao editar porta: {str(e)}'}), 500
        
        finally:
            conn.close()

@app.route('/switch-portas/<int:porta_id>', methods=['DELETE'])
@admin_required
def deletar_porta_switch(porta_id):
    """Deletar uma porta específica do switch"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        portas = _json_read_table(db_file, 'switch_portas')
        porta = next((p for p in portas if p.get('id') == porta_id), None)
        if not porta:
            return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
        # ocupada?
        conexoes = _json_read_table(db_file, 'conexoes')
        if any(c.get('porta_id') == porta_id and c.get('status') == 'ativa' for c in conexoes):
            return jsonify({'status': 'erro', 'mensagem': 'Não é possível deletar uma porta que está ocupada'}), 400
        # mapeada com patch panel?
        ppp = _json_read_table(db_file, 'patch_panel_portas')
        if any(m.get('switch_id') == porta.get('switch_id') and int(m.get('porta_switch') or 0) == int(porta.get('numero_porta') or 0) for m in ppp):
            return jsonify({'status': 'erro', 'mensagem': 'Não é possível deletar uma porta que está mapeada para patch panel'}), 400
        portas = [p for p in portas if p.get('id') != porta_id]
        _json_write_table(db_file, 'switch_portas', portas)
        detalhes = f"Porta deletada: ID={porta_id}, Switch ID={porta.get('switch_id')}, Porta {porta.get('numero_porta')}"
        registrar_log(session.get('username', 'desconhecido'), 'DELETAR_PORTA_SWITCH', detalhes, 'sucesso', db_file)
        return jsonify({'status': 'ok', 'mensagem': 'Porta deletada com sucesso!'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        try:
            # Verificar se a porta existe
            cur.execute('SELECT id, switch_id, numero_porta FROM switch_portas WHERE id = ?', (porta_id,))
            porta = cur.fetchone()
            if not porta:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
            
            # Verificar se a porta está ocupada
            cur.execute('SELECT COUNT(*) FROM conexoes WHERE porta_id = ? AND status = "ativa"', (porta_id,))
            if cur.fetchone()[0] > 0:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Não é possível deletar uma porta que está ocupada'}), 400
            
            # Verificar se a porta está mapeada para patch panel
            cur.execute('''
                SELECT COUNT(*) FROM patch_panel_portas 
                WHERE switch_id = (SELECT switch_id FROM switch_portas WHERE id = ?)
                AND porta_switch = (SELECT numero_porta FROM switch_portas WHERE id = ?)
            ''', (porta_id, porta_id))
            if cur.fetchone()[0] > 0:
                conn.close()
                return jsonify({'status': 'erro', 'mensagem': 'Não é possível deletar uma porta que está mapeada para patch panel'}), 400
            
            # Deletar a porta
            cur.execute('DELETE FROM switch_portas WHERE id = ?', (porta_id,))
            conn.commit()
            
            # Log da deleção da porta
            detalhes = f"Porta deletada: ID={porta_id}, Switch ID={porta[1]}, Porta {porta[2]}"
            registrar_log(session.get('username', 'desconhecido'), 'DELETAR_PORTA_SWITCH', detalhes, 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Porta deletada com sucesso!'})
            
        except Exception as e:
            conn.rollback()
            detalhes = f"Erro ao deletar porta ID={porta_id}: {str(e)}"
            registrar_log(session.get('username', 'desconhecido'), 'DELETAR_PORTA_SWITCH', detalhes, 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': f'Erro ao deletar porta: {str(e)}'}), 500
        
        finally:
            conn.close()

# --- ROTAS DE CONEXÕES ---

@app.route('/conexoes', methods=['POST'])
@admin_required
def criar_conexao():
    dados = request.json
    if not dados:
        registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', 'Dados JSON inválidos', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        portas = _json_read_table(db_file, 'switch_portas')
        porta = next((p for p in portas if p.get('id') == dados.get('porta_id')), None)
        if not porta:
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f"Porta ID={dados.get('porta_id')}: Não encontrada", 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
        if (porta.get('status') or 'livre') != 'livre':
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f"Porta ID={dados.get('porta_id')}: Já ocupada", 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': 'Porta já está ocupada'}), 400
        conexoes = _json_read_table(db_file, 'conexoes')
        if any(c.get('equipamento_id') == dados.get('equipamento_id') and c.get('status') == 'ativa' for c in conexoes):
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f"Equipamento ID={dados.get('equipamento_id')}: Já conectado", 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': 'Equipamento já está conectado a outra porta'}), 400
        
        # Verificar se o equipamento já está conectado a algum patch panel
        patch_panel_portas = _json_read_table(db_file, 'patch_panel_portas')
        equipamento_ja_conectado_pp = next((p for p in patch_panel_portas 
                                           if p.get('equipamento_id') == dados.get('equipamento_id')), None)
        if equipamento_ja_conectado_pp:
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f"Equipamento ID={dados.get('equipamento_id')}: Já conectado a patch panel", 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': 'Este equipamento já está conectado a um patch panel'}), 400
        conexao = {
            'id': _json_next_id(conexoes),
            'porta_id': dados.get('porta_id'),
            'equipamento_id': dados.get('equipamento_id'),
            'data_conexao': datetime.now().isoformat(),
            'status': 'ativa'
        }
        conexoes.append(conexao)
        _json_write_table(db_file, 'conexoes', conexoes)
        # atualizar status porta
        porta['status'] = 'ocupada'
        _json_write_table(db_file, 'switch_portas', portas)
        conexao_id = conexao['id']
    else:
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
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Porta ID={dados["porta_id"]}: Não encontrada', 'erro', db_file)
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
        
        if porta[0] != 'livre':
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Porta ID={dados["porta_id"]}: Já ocupada', 'erro', db_file)
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Porta já está ocupada'}), 400
        
        # Verificar se o equipamento já está conectado
        cur.execute('SELECT id FROM conexoes WHERE equipamento_id=? AND status="ativa"', (dados['equipamento_id'],))
        if cur.fetchone():
            registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', f'Equipamento ID={dados["equipamento_id"]}: Já conectado', 'erro', db_file)
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
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok', 'id': conexao_id})

@app.route('/conexoes/<int:conexao_id>', methods=['DELETE'])
@admin_required
def remover_conexao(conexao_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        conexoes = _json_read_table(db_file, 'conexoes')
        cx = next((c for c in conexoes if c.get('id') == conexao_id and c.get('status') == 'ativa'), None)
        if not cx:
            registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', f'Conexão ID={conexao_id}: Não encontrada', 'erro', db_file)
            return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
        porta_id = cx.get('porta_id')
        equipamento_id = cx.get('equipamento_id')
        cx['status'] = 'inativa'
        _json_write_table(db_file, 'conexoes', conexoes)
        portas = _json_read_table(db_file, 'switch_portas')
        p = next((x for x in portas if x.get('id') == porta_id), None)
        if p:
            p['status'] = 'livre'
            _json_write_table(db_file, 'switch_portas', portas)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Buscar a conexão
        cur.execute('SELECT porta_id, equipamento_id FROM conexoes WHERE id=? AND status="ativa"', (conexao_id,))
        conexao = cur.fetchone()
        
        if not conexao:
            registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', f'Conexão ID={conexao_id}: Não encontrada', 'erro', db_file)
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
    registrar_log(session.get('username', 'desconhecido'), 'REMOVER_CONEXAO', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok'})

@app.route('/conexoes', methods=['GET'])
@login_required
def listar_conexoes():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        conexoes = [c for c in _json_read_table(db_file, 'conexoes') if c.get('status') == 'ativa']
        portas = {p.get('id'): p for p in _json_read_table(db_file, 'switch_portas')}
        switches = {s.get('id'): s for s in _json_read_table(db_file, 'switches')}
        equipamentos = {e.get('id'): e for e in _json_read_table(db_file, 'equipamentos')}
        itens = []
        for c in conexoes:
            p = portas.get(c.get('porta_id')) or {}
            s = switches.get(p.get('switch_id')) or {}
            e = equipamentos.get(c.get('equipamento_id')) or {}
            itens.append({
                'id': c.get('id'),
                'data_conexao': c.get('data_conexao'),
                'status': c.get('status'),
                'porta_id': p.get('id'),
                'porta': p.get('numero_porta'),
                'switch': s.get('nome'),
                'switch_marca': s.get('marca'),
                'equipamento_id': e.get('id'),
                'equipamento': e.get('nome'),
                'equipamento_tipo': e.get('tipo')
            })
        itens.sort(key=lambda x: (x.get('switch') or '', int(x.get('porta') or 0)))
        return jsonify(itens)
    else:
        conn = sqlite3.connect(db_file)
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    try:
        log_file = get_log_file(db_file)
        with open(log_file, 'r', encoding='utf-8') as f:
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
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    try:
        # Limpar o arquivo de log da empresa
        log_file = get_log_file(db_file)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        registrar_log(session.get('username', 'desconhecido'), 'LIMPAR_LOGS', 'Todos os logs foram limpos', 'sucesso', db_file)
        
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
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        s = next((x for x in switches if x.get('id') == id), None)
        nome, marca, modelo = (s.get('nome') if s else ''), (s.get('marca') if s else ''), (s.get('modelo') if s else '')
        switches = [x for x in switches if x.get('id') != id]
        _json_write_table(db_file, 'switches', switches)
        portas = _json_read_table(db_file, 'switch_portas')
        portas_ids = {p.get('id') for p in portas if p.get('switch_id') == id}
        portas = [p for p in portas if p.get('switch_id') != id]
        _json_write_table(db_file, 'switch_portas', portas)
        # inativar conexoes dessas portas
        conexoes = _json_read_table(db_file, 'conexoes')
        for c in conexoes:
            if c.get('porta_id') in portas_ids and c.get('status') == 'ativa':
                c['status'] = 'inativa'
        _json_write_table(db_file, 'conexoes', conexoes)
    else:
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
    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_SWITCH', detalhes, 'sucesso', db_file)
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

# --- API PATCH PANELS ---

@app.route('/patch-panels', methods=['GET'])
@login_required
def listar_patch_panels():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400

    if _is_json_mode(db_file):
        patch_panels = _json_read_table(db_file, 'patch_panels')
        andares = {a.get('id'): a for a in _json_read_table(db_file, 'andares')}
        resultado = []
        for pp in patch_panels:
            porta_inicial = int(pp.get('porta_inicial') or 1)
            num_portas = int(pp.get('num_portas') or 0)
            andar_id = pp.get('andar')
            andar_nome = None
            if andar_id == 0:
                andar_nome = 'Térreo'
            elif andar_id is not None:
                # fallback se não existir em andares.json
                andar_nome = (andares.get(andar_id) or {}).get('titulo') or f"{andar_id}º Andar"
            resultado.append({
                'id': pp.get('id'),
                'codigo': pp.get('codigo'),
                'nome': pp.get('nome'),
                'andar': andar_id,
                'andar_nome': andar_nome,
                'num_portas': num_portas,
                'porta_inicial': porta_inicial,
                'porta_final': porta_inicial + num_portas - 1 if num_portas else porta_inicial,
                'status': pp.get('status') or 'ativo',
                'descricao': pp.get('descricao'),
                'data_criacao': pp.get('data_criacao'),
            })
        # ordenar por id
        resultado.sort(key=lambda x: int(x.get('id') or 0))
        return jsonify(resultado)
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501


@app.route('/patch-panels/andar/<int:andar>', methods=['GET'])
@login_required
def listar_patch_panels_por_andar(andar):
    """Lista patch panels de um andar específico"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            patch_panels = _json_read_table(db_file, 'patch_panels')
            andares = {a.get('id'): a for a in _json_read_table(db_file, 'andares')}
            
            # Filtrar patch panels do andar
            patch_panels_andar = []
            for pp in patch_panels:
                if pp.get('andar') == andar:
                    andar_info = andares.get(pp.get('andar'))
                    patch_panels_andar.append({
                        'id': pp.get('id'),
                        'nome': pp.get('nome'),
                        'andar': pp.get('andar'),
                        'andar_nome': andar_info.get('nome') if andar_info else f'Andar {andar}',
                        'num_portas': pp.get('num_portas', 0),
                        'prefixo_keystone': pp.get('prefixo_keystone'),
                        'descricao': pp.get('descricao')
                    })
            
            return jsonify(patch_panels_andar)
        except Exception as e:
            print(f"Erro ao listar patch panels do andar {andar}: {e}")
            return jsonify([])
    else:
        return jsonify({'erro': 'Modo SQLite não implementado'}), 501

@app.route('/patch-panels/validar-portas', methods=['GET'])
@login_required
def validar_portas_patch_panels():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        portas = _json_read_table(db_file, 'patch_panel_portas')
        numeros = sorted({int(p.get('numero_porta') or 0) for p in portas if p.get('numero_porta') is not None})
        return jsonify({'status': 'ok', 'portas_existentes': numeros})
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501


@app.route('/patch-panels', methods=['POST'])
@admin_required
def criar_patch_panel():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    dados = request.get_json() or {}
    if _is_json_mode(db_file):
        patch_panels = _json_read_table(db_file, 'patch_panels')
        portas = _json_read_table(db_file, 'patch_panel_portas')

        novo = {
            'id': _json_next_id(patch_panels),
            'codigo': dados.get('codigo') or f"PP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'nome': dados.get('nome'),
            'andar': dados.get('andar'),
            'num_portas': int(dados.get('num_portas') or 0),
            'porta_inicial': int(dados.get('porta_inicial') or 1),
            'status': dados.get('status') or 'ativo',
            'descricao': dados.get('descricao'),
            'data_criacao': datetime.now().isoformat()
        }
        patch_panels.append(novo)

        # criar portas
        inicio = int(novo['porta_inicial'])
        fim = inicio + int(novo['num_portas'] or 0) - 1
        for numero in range(inicio, fim + 1):
            portas.append({
                'id': _json_next_id(portas),
                'patch_panel_id': novo['id'],
                'numero_porta': numero,
                'switch_id': None,
                'porta_switch': None,
                'status': 'livre',
                'equipamento_id': None,
                'data_conexao': None
            })

        _json_write_table(db_file, 'patch_panels', patch_panels)
        _json_write_table(db_file, 'patch_panel_portas', portas)
        registrar_log(session.get('username','desconhecido'), 'CRIAR_PATCH_PANEL', f"Patch panel {novo['nome']} criado", 'sucesso', db_file)
        return jsonify({'status': 'ok', 'id': novo['id']})
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501


@app.route('/patch-panels/<int:id>', methods=['PUT'])
@admin_required
def atualizar_patch_panel(id: int):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    dados = request.get_json() or {}
    if _is_json_mode(db_file):
        patch_panels = _json_read_table(db_file, 'patch_panels')
        alvo = next((pp for pp in patch_panels if pp.get('id') == id), None)
        if not alvo:
            return jsonify({'status': 'erro', 'mensagem': 'Patch panel não encontrado'}), 404
        for campo in ['nome','andar','num_portas','porta_inicial','status','descricao']:
            if campo in dados and dados.get(campo) is not None:
                alvo[campo] = int(dados[campo]) if campo in ['andar','num_portas','porta_inicial'] else dados[campo]
        _json_write_table(db_file, 'patch_panels', patch_panels)
        registrar_log(session.get('username','desconhecido'), 'ATUALIZAR_PATCH_PANEL', f'Patch panel {id} atualizado', 'sucesso', db_file)
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501


@app.route('/patch-panels/<int:id>', methods=['DELETE'])
@admin_required
def excluir_patch_panel(id: int):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        patch_panels = _json_read_table(db_file, 'patch_panels')
        portas = _json_read_table(db_file, 'patch_panel_portas')
        if not any(pp.get('id') == id for pp in patch_panels):
            return jsonify({'status': 'erro', 'mensagem': 'Patch panel não encontrado'}), 404
        patch_panels = [pp for pp in patch_panels if pp.get('id') != id]
        portas = [p for p in portas if p.get('patch_panel_id') != id]
        _json_write_table(db_file, 'patch_panels', patch_panels)
        _json_write_table(db_file, 'patch_panel_portas', portas)
        registrar_log(session.get('username','desconhecido'), 'EXCLUIR_PATCH_PANEL', f'Patch panel {id} excluído', 'sucesso', db_file)
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501


@app.route('/patch-panels/<int:id>/portas', methods=['GET'])
@login_required
def listar_portas_patch_panel(id: int):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        portas = [p for p in _json_read_table(db_file, 'patch_panel_portas') if p.get('patch_panel_id') == id]
        equipamentos = {e.get('id'): e for e in _json_read_table(db_file, 'equipamentos')}
        salas = {s.get('id'): s for s in _json_read_table(db_file, 'salas')}
        switches = {sw.get('id'): sw for sw in _json_read_table(db_file, 'switches')}
        patch_panel = next((pp for pp in _json_read_table(db_file, 'patch_panels') if pp.get('id') == id), {})
        prefixo_keystone = patch_panel.get('prefixo_keystone') or 'KST'

        resultado = []
        for p in sorted(portas, key=lambda x: int(x.get('numero_porta') or 0)):
            equip = equipamentos.get(p.get('equipamento_id')) if p.get('equipamento_id') else None
            sala_nome = (salas.get((equip or {}).get('sala_id')) or {}).get('nome') if equip else None
            switch_obj = switches.get(p.get('switch_id')) if p.get('switch_id') else None
            resultado.append({
                'id': p.get('id'),
                'numero_porta': p.get('numero_porta'),
                'prefixo_keystone': prefixo_keystone,
                'switch_id': p.get('switch_id'),
                'switch_nome': (switch_obj or {}).get('nome'),
                'porta_switch': p.get('porta_switch'),
                'status': p.get('status') or 'livre',
                'equipamento_nome': (equip or {}).get('nome'),
                'equipamento_tipo': (equip or {}).get('tipo'),
                'equipamento_sala': sala_nome,
                'sala_nome': sala_nome,
            })
        return jsonify(resultado)
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501


@app.route('/patch-panel-portas/<int:porta_id>/conectar-equipamento', methods=['PUT'])
@admin_required
def conectar_equipamento_patch_panel(porta_id):
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        patch_panel_portas = _json_read_table(db_file, 'patch_panel_portas')
        
        porta_pp = next((p for p in patch_panel_portas if p.get('id') == porta_id), None)
        if not porta_pp:
            return jsonify({'status': 'erro', 'mensagem': 'Porta do patch panel não encontrada'}), 404
        
        if porta_pp.get('status') != 'livre' and porta_pp.get('status') != 'mapeada':
            return jsonify({'status': 'erro', 'mensagem': 'Porta não está disponível para conexão'}), 400
        
        equipamento_id = dados.get('equipamento_id')
        if not equipamento_id:
            return jsonify({'status': 'erro', 'mensagem': 'ID do equipamento é obrigatório'}), 400
        
        # Verificar se o equipamento existe
        equipamentos = _json_read_table(db_file, 'equipamentos')
        equipamento = next((e for e in equipamentos if e.get('id') == equipamento_id), None)
        if not equipamento:
            return jsonify({'status': 'erro', 'mensagem': 'Equipamento não encontrado'}), 404
        
        # Verificar se o equipamento já está conectado a qualquer patch panel
        equipamento_ja_conectado_pp = next((p for p in patch_panel_portas 
                                           if p.get('equipamento_id') == equipamento_id and p.get('id') != porta_id), None)
        if equipamento_ja_conectado_pp:
            return jsonify({'status': 'erro', 'mensagem': 'Este equipamento já está conectado a outro patch panel'}), 400
        
        # Verificar se o equipamento já está conectado a algum switch
        conexoes = _json_read_table(db_file, 'conexoes')
        equipamento_ja_conectado_switch = next((c for c in conexoes 
                                              if c.get('equipamento_id') == equipamento_id and c.get('status') == 'ativa'), None)
        if equipamento_ja_conectado_switch:
            return jsonify({'status': 'erro', 'mensagem': 'Este equipamento já está conectado a um switch'}), 400
        
        # Conectar equipamento
        porta_pp['equipamento_id'] = equipamento_id
        porta_pp['status'] = 'ocupada'
        porta_pp['data_conexao'] = datetime.now().isoformat()
        
        _json_write_table(db_file, 'patch_panel_portas', patch_panel_portas)
        
        registrar_log(session.get('username'), 'CONECTAR_EQUIPAMENTO_PATCH_PANEL', 
                     f'Equipamento {equipamento_id} conectado à porta {porta_id}', 'sucesso', db_file)
        
        return jsonify({'status': 'ok', 'mensagem': 'Equipamento conectado com sucesso!'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/patch-panel-portas/<int:porta_id>/desconectar-equipamento', methods=['PUT'])
@admin_required
def desconectar_equipamento_patch_panel(porta_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        patch_panel_portas = _json_read_table(db_file, 'patch_panel_portas')
        
        porta_pp = next((p for p in patch_panel_portas if p.get('id') == porta_id), None)
        if not porta_pp:
            return jsonify({'status': 'erro', 'mensagem': 'Porta do patch panel não encontrada'}), 404
        
        if porta_pp.get('status') != 'ocupada':
            return jsonify({'status': 'erro', 'mensagem': 'Porta não está ocupada'}), 400
        
        equipamento_id = porta_pp.get('equipamento_id')
        
        # Desconectar equipamento
        porta_pp['equipamento_id'] = None
        porta_pp['data_conexao'] = None
        
        # Se a porta estava mapeada para um switch, voltar para mapeada
        if porta_pp.get('switch_id'):
            porta_pp['status'] = 'mapeada'
        else:
            porta_pp['status'] = 'livre'
        
        _json_write_table(db_file, 'patch_panel_portas', patch_panel_portas)
        
        registrar_log(session.get('username'), 'DESCONECTAR_EQUIPAMENTO_PATCH_PANEL', 
                     f'Equipamento {equipamento_id} desconectado da porta {porta_id}', 'sucesso', db_file)
        
        return jsonify({'status': 'ok', 'mensagem': 'Equipamento desconectado com sucesso!'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/patch-panel-portas/<int:porta_id>', methods=['PUT'])
@tecnico_required
def atualizar_patch_panel_porta(porta_id: int):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    dados = request.get_json() or {}
    if _is_json_mode(db_file):
        portas = _json_read_table(db_file, 'patch_panel_portas')
        porta = next((p for p in portas if p.get('id') == porta_id), None)
        if not porta:
            return jsonify({'status': 'erro', 'mensagem': 'Porta não encontrada'}), 404
        if 'switch_id' in dados:
            porta['switch_id'] = dados.get('switch_id') if dados.get('switch_id') not in ['', None] else None
        if 'porta_switch' in dados:
            valor = dados.get('porta_switch')
            porta['porta_switch'] = int(valor) if str(valor).isdigit() else None
        _json_write_table(db_file, 'patch_panel_portas', portas)
        registrar_log(session.get('username','desconhecido'), 'ATUALIZAR_PATCH_PANEL_PORTA', f'Porta {porta_id} atualizada', 'sucesso', db_file)
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'erro': 'Modo SQLite não suportado nesta rota no ambiente atual'}), 501

@app.route('/ping-equipamentos', methods=['POST'])
@login_required
def ping_equipamentos():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        equipamentos = _json_read_table(db_file, 'equipamentos')
        # Buscar equipamentos com IP cadastrado
        equipamentos_com_ip = []
        for eq in equipamentos:
            dados = eq.get('dados', {})
            ip = dados.get('ip1') or dados.get('ip')
            if ip and ip.strip():
                equipamentos_com_ip.append({
                    'id': eq.get('id'),
                    'nome': eq.get('nome'),
                    'ip': ip
                })
        
        resultados = []
        equipamentos_online = 0
        equipamentos_offline = 0
        
        for eq in equipamentos_com_ip:
            eq_id = eq['id']
            nome = eq['nome']
            ip = eq['ip']
            
            try:
                result = subprocess.run(['ping', '-n', '1', ip], capture_output=True, text=True, timeout=5)
                saida = result.stdout
                sucesso = int('TTL=' in saida or 'ttl=' in saida)
                if sucesso:
                    equipamentos_online += 1
                else:
                    equipamentos_offline += 1
            except Exception as e:
                saida = str(e)
                sucesso = 0
                equipamentos_offline += 1
            
            # Salva no log
            ping_logs = _json_read_table(db_file, 'ping_logs')
            novo_log = {
                'id': _json_next_id(ping_logs),
                'equipamento_id': eq_id,
                'nome_equipamento': nome,
                'ip': ip,
                'resultado': saida,
                'sucesso': sucesso,
                'timestamp': datetime.now().isoformat()
            }
            ping_logs.append(novo_log)
            _json_write_table(db_file, 'ping_logs', ping_logs)
            
            resultados.append({'id': eq_id, 'nome': nome, 'ip': ip, 'sucesso': bool(sucesso), 'saida': saida})
        
        # Log da execução do ping
        total_equipamentos = len(equipamentos_com_ip)
        detalhes = f'Ping executado em {total_equipamentos} equipamentos: {equipamentos_online} online, {equipamentos_offline} offline'
        registrar_log(session.get('username', 'desconhecido'), 'EXECUTAR_PING', detalhes, 'sucesso', db_file)
        
        return jsonify({'status': 'ok', 'resultados': resultados})
    else:
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
        equipamentos_online = 0
        equipamentos_offline = 0
        
        for eq_id, nome, ip in equipamentos:
            try:
                result = subprocess.run(['ping', '-n', '1', ip], capture_output=True, text=True, timeout=5)
                saida = result.stdout
                sucesso = int('TTL=' in saida or 'ttl=' in saida)
                if sucesso:
                    equipamentos_online += 1
                else:
                    equipamentos_offline += 1
            except Exception as e:
                saida = str(e)
                sucesso = 0
                equipamentos_offline += 1
            # Salva no log
            cur.execute(
                'INSERT INTO ping_logs (equipamento_id, nome_equipamento, ip, resultado, sucesso) VALUES (?, ?, ?, ?, ?)',
                (eq_id, nome, ip, saida, sucesso)
            )
            resultados.append({'id': eq_id, 'nome': nome, 'ip': ip, 'sucesso': bool(sucesso), 'saida': saida})
        
        conn.commit()
        conn.close()
        
        # Log da execução do ping
        total_equipamentos = len(equipamentos)
        detalhes = f'Ping executado em {total_equipamentos} equipamentos: {equipamentos_online} online, {equipamentos_offline} offline'
        registrar_log(session.get('username', 'desconhecido'), 'EXECUTAR_PING', detalhes, 'sucesso', db_file)
        
        return jsonify({'status': 'ok', 'resultados': resultados})

@app.route('/ping-logs')
@login_required
def ping_logs():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        ping_logs = _json_read_table(db_file, 'ping_logs')
        equipamentos = _json_read_table(db_file, 'equipamentos')
        salas = _json_read_table(db_file, 'salas')
        conexoes = _json_read_table(db_file, 'conexoes')
        switch_portas = _json_read_table(db_file, 'switch_portas')
        switches = _json_read_table(db_file, 'switches')
        
        # Criar dicionários para lookup
        equipamentos_dict = {e.get('id'): e for e in equipamentos}
        salas_dict = {s.get('id'): s for s in salas}
        switch_portas_dict = {sp.get('id'): sp for sp in switch_portas}
        switches_dict = {s.get('id'): s for s in switches}
        
        logs = []
        # Ordenar por timestamp (mais recentes primeiro) e limitar a 100
        ping_logs_ordenados = sorted(ping_logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:100]
        
        for p in ping_logs_ordenados:
            eq_id = p.get('equipamento_id')
            equipamento = equipamentos_dict.get(eq_id) if eq_id else None
            sala = salas_dict.get(equipamento.get('sala_id')) if equipamento else None
            
            # Buscar MAC do equipamento
            mac = ''
            if equipamento and equipamento.get('dados'):
                dados = equipamento.get('dados', {})
                mac = dados.get('mac') or dados.get('mac1') or ''
            
            # Buscar switch e porta (se houver conexão ativa)
            switch = ''
            porta = ''
            if eq_id:
                conexao_ativa = next((c for c in conexoes if c.get('equipamento_id') == eq_id and c.get('status') == 'ativa'), None)
                if conexao_ativa:
                    porta_switch = switch_portas_dict.get(conexao_ativa.get('porta_id'))
                    if porta_switch:
                        switch_obj = switches_dict.get(porta_switch.get('switch_id'))
                        if switch_obj:
                            switch = switch_obj.get('nome', '')
                            porta = porta_switch.get('numero_porta', '')
            
            logs.append(dict(
                nome=p.get('nome_equipamento'), 
                ip=p.get('ip'), 
                sucesso=p.get('sucesso'), 
                timestamp=p.get('timestamp'), 
                sala=sala.get('nome') if sala else 'Sem sala', 
                mac=mac, 
                switch=switch, 
                porta=porta
            ))
        
        return jsonify(logs)
    else:
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
    
    if _is_json_mode(db_file):
        # Limpar todos os logs de ping
        _json_write_table(db_file, 'ping_logs', [])
        
        # Log da limpeza dos logs de ping
        registrar_log(session.get('username', 'desconhecido'), 'LIMPAR_PING_LOGS', 'Todos os logs de ping foram limpos', 'sucesso', db_file)
        
        return jsonify({'status': 'ok'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute('DELETE FROM ping_logs')
        conn.commit()
        conn.close()
        
        # Log da limpeza dos logs de ping
        registrar_log(session.get('username', 'desconhecido'), 'LIMPAR_PING_LOGS', 'Todos os logs de ping foram limpos', 'sucesso', db_file)
        
        return jsonify({'status': 'ok'})

@app.route('/empresa_atual')
@login_required
def empresa_atual():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400

    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'static', 'data')
        with open(os.path.join(data_dir, 'empresas.json'), 'r', encoding='utf-8') as f:
            empresas_all = json.load(f)
    except Exception:
        empresas_all = []

    # Heurística: se a empresa do JSON tiver 'db_file', casamos por ele;
    # senão, casamos por id inferido do "json:empresa_<id>" salvo na sessão.
    empresa = None
    for e in empresas_all:
        if e.get('db_file') == db_file:
            empresa = e
            break
    if not empresa:
        # tentar extrair id do placeholder "json:empresa_<id>"
        if isinstance(db_file, str) and db_file.startswith('json:empresa_'):
            try:
                emp_id = int(db_file.split('_')[-1])
                empresa = next((e for e in empresas_all if e.get('id') == emp_id), None)
            except Exception:
                empresa = None

    if empresa:
        return jsonify({'nome': empresa.get('nome'), 'logo': empresa.get('logo')})

    return jsonify({'erro': 'Empresa não encontrada!'}), 404

@app.route('/upload-foto-sala', methods=['POST'])
def upload_foto_sala():
    if 'foto' not in request.files:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_FOTO_SALA', 'Tentativa de upload sem arquivo', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum arquivo enviado'})
    
    file = request.files['foto']
    if not file.filename:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_FOTO_SALA', 'Tentativa de upload com nome de arquivo vazio', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Nome de arquivo vazio'})
    
    db_file = session.get('db')
    if not db_file:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_FOTO_SALA', 'Tentativa de upload sem empresa selecionada', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Nenhuma empresa selecionada!'})
    
    if _is_json_mode(db_file):
        empresa_dir = _empresa_dir_from_db(db_file)
    else:
        empresa_dir = os.path.splitext(os.path.basename(db_file))[0]
    
    pasta = os.path.join('static', 'img', 'fotos-salas', empresa_dir)
    os.makedirs(pasta, exist_ok=True)
    filename = cast(str, file.filename)
    caminho = os.path.join(pasta, filename)
    file.save(caminho)
    
    # Log do upload bem-sucedido
    registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_FOTO_SALA', f'Foto {filename} enviada para empresa {empresa_dir}', 'sucesso', db_file)
    
    return jsonify({'status': 'ok', 'caminho': f'static/img/fotos-salas/{empresa_dir}/{filename}'})

@app.route('/fotos-salas')
def fotos_salas():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'imagens': []})
    if _is_json_mode(db_file):
        empresa_dir = _empresa_dir_from_db(db_file)
    else:
        empresa_dir = os.path.splitext(os.path.basename(db_file))[0]
    pasta = os.path.join('static', 'img', 'fotos-salas', empresa_dir)
    if not os.path.exists(pasta):
        return jsonify({'imagens': []})
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return jsonify({'imagens': [f'/static/img/fotos-salas/{empresa_dir}/{arq}' for arq in arquivos]})

@app.route('/excluir-foto-sala', methods=['DELETE'])
@login_required
def excluir_foto_sala():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'status': 'erro', 'mensagem': 'Nenhuma empresa selecionada!'})
    
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'URL da imagem não fornecida'})
    
    url = data['url']
    if _is_json_mode(db_file):
        empresa_dir = _empresa_dir_from_db(db_file)
    else:
        empresa_dir = os.path.splitext(os.path.basename(db_file))[0]
    
    # Extrair o nome do arquivo da URL
    if url.startswith('/static/img/fotos-salas/'):
        caminho_relativo = url.replace('/static/img/fotos-salas/', '')
        if caminho_relativo.startswith(empresa_dir + '/'):
            nome_arquivo = caminho_relativo.replace(empresa_dir + '/', '')
            caminho_completo = os.path.join('static', 'img', 'fotos-salas', empresa_dir, nome_arquivo)
            
            try:
                if os.path.exists(caminho_completo):
                    os.remove(caminho_completo)
                    registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_FOTO_SALA', f'Foto {nome_arquivo} excluída da empresa {empresa_dir}', 'sucesso', db_file)
                    return jsonify({'status': 'ok', 'mensagem': 'Imagem excluída com sucesso'})
                else:
                    return jsonify({'status': 'erro', 'mensagem': 'Arquivo não encontrado'})
            except Exception as e:
                registrar_log(session.get('username', 'desconhecido'), 'EXCLUIR_FOTO_SALA', f'Erro ao excluir foto {nome_arquivo}: {str(e)}', 'erro', db_file)
                return jsonify({'status': 'erro', 'mensagem': f'Erro ao excluir arquivo: {str(e)}'})
        else:
            return jsonify({'status': 'erro', 'mensagem': 'Acesso negado a arquivo de outra empresa'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'URL inválida'})

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
    print(f"DEBUG: salvar_layout_sala chamada para sala_id={sala_id}")
    db_file = session.get('db')
    print(f"DEBUG: db_file da sessão: {db_file}")
    if not db_file:
        print("DEBUG: Nenhuma empresa selecionada na sessão!")
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    layout = request.get_json()
    if not layout:
        print("DEBUG: JSON ausente ou inválido")
        return jsonify({'erro': 'JSON ausente ou inválido'}), 400
    print(f"DEBUG: Layout recebido: {layout}")
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
    print(f"DEBUG: Layout salvo no banco de dados")
    # Adiciona log da ação
    usuario = session.get('username', 'desconhecido')
    print(f"DEBUG: Usuário da sessão: {usuario}")
    print(f"DEBUG: Chamando registrar_log com db_file: {db_file}")
    registrar_log(usuario, 'salvar_layout', f'sala_id={sala_id}', 'sucesso', db_file)
    print(f"DEBUG: Log registrado com sucesso")
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

@app.route('/api/salas/<int:sala_id>/conexoes-reais', methods=['GET'])
@login_required
def obter_conexoes_reais_sala(sala_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
        cabos = _json_read_table(db_file, 'cabos')
        equipamentos = _json_read_table(db_file, 'equipamentos')
        
        # Criar dicionários para lookup
        cabos_dict = {c.get('id'): c for c in cabos}
        equipamentos_dict = {e.get('id'): e for e in equipamentos}
        
        # Buscar conexões de cabos ativas na sala
        conexoes_ativas = [cc for cc in conexoes_cabos if cc.get('sala_id') == sala_id and not cc.get('data_desconexao')]
        
        conexoes = []
        for cc in conexoes_ativas:
            cabo = cabos_dict.get(cc.get('cabo_id'))
            equipamento_origem = equipamentos_dict.get(cc.get('equipamento_origem_id'))
            equipamento_destino = equipamentos_dict.get(cc.get('equipamento_destino_id'))
            
            if not cabo:
                continue
            
            conexao = {
                'id': cc.get('id'),
                'cabo_id': cc.get('cabo_id'),
                'equipamento_origem_id': cc.get('equipamento_origem_id'),
                'equipamento_destino_id': cc.get('equipamento_destino_id'),
                'porta_origem': cc.get('porta_origem'),
                'porta_destino': cc.get('porta_destino'),
                'sala_id': cc.get('sala_id'),
                'observacao': cc.get('observacao'),
                'codigo_cabo': cabo.get('codigo_unico'),
                'tipo_cabo': cabo.get('tipo'),
                'comprimento': cabo.get('comprimento'),
                'marca': cabo.get('marca'),
                'modelo': cabo.get('modelo'),
                'equipamento_origem': equipamento_origem.get('nome') if equipamento_origem else None,
                'equipamento_destino': equipamento_destino.get('nome') if equipamento_destino else None,
                'ativo': True
            }
            conexoes.append(conexao)
        
        # Ordenar por data de conexão (mais recentes primeiro)
        conexoes.sort(key=lambda x: x.get('data_conexao', ''), reverse=True)
        return jsonify(conexoes)
    else:
        conn = sqlite3.connect(db_file)
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
            WHERE cc.sala_id = ? AND cc.data_desconexao IS NULL
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
def obter_layout_hibrido_sala(sala_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    # Buscar layout manual
    cur.execute('SELECT layout_json FROM sala_layouts WHERE sala_id=?', (sala_id,))
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
        WHERE cc.sala_id = ? AND cc.data_desconexao IS NULL
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

# --- API CABOS (TELA DETALHES-CABOS-SALA) ---

@app.route('/conexoes-cabos', methods=['POST'])
@admin_required
def criar_conexao_cabo():
    """Criar uma nova conexão de cabo"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
            
            # Validar dados obrigatórios
            if not dados.get('cabo_id'):
                return jsonify({'status': 'erro', 'mensagem': 'ID do cabo é obrigatório'}), 400
            
            if not dados.get('equipamento_origem_id') and not dados.get('equipamento_destino_id'):
                return jsonify({'status': 'erro', 'mensagem': 'Pelo menos um equipamento deve ser especificado'}), 400
            
            # Verificar se o cabo existe
            cabos = _json_read_table(db_file, 'cabos')
            cabo = next((c for c in cabos if c.get('id') == dados.get('cabo_id')), None)
            if not cabo:
                return jsonify({'status': 'erro', 'mensagem': 'Cabo não encontrado'}), 404
            
            # Criar nova conexão
            nova_conexao = {
                'id': _json_next_id(conexoes_cabos),
                'cabo_id': dados.get('cabo_id'),
                'equipamento_origem_id': dados.get('equipamento_origem_id'),
                'equipamento_destino_id': dados.get('equipamento_destino_id'),
                'porta_origem': dados.get('porta_origem'),
                'porta_destino': dados.get('porta_destino'),
                'sala_id': dados.get('sala_id'),
                'observacao': dados.get('observacao', ''),
                'data_conexao': datetime.now().isoformat(),
                'data_desconexao': None
            }
            
            conexoes_cabos.append(nova_conexao)
            _json_write_table(db_file, 'conexoes_cabos', conexoes_cabos)
            
            registrar_log(session.get('username'), 'CRIAR_CONEXAO_CABO', 
                         f'Conexão de cabo criada: ID={nova_conexao["id"]}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Conexão de cabo criada com sucesso!', 'conexao_id': nova_conexao['id']})
            
        except Exception as e:
            print(f"Erro ao criar conexão de cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/conexoes-cabos/sala/<int:sala_id>', methods=['GET'])
@login_required
def api_conexoes_cabos_por_sala(sala_id: int):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
        cabos = {c.get('id'): c for c in _json_read_table(db_file, 'cabos')}
        equipamentos = {e.get('id'): e for e in _json_read_table(db_file, 'equipamentos')}
        patch_panels = {pp.get('id'): pp for pp in _json_read_table(db_file, 'patch_panels')}
        resultado = []
        for cc in conexoes_cabos:
            if cc.get('sala_id') != sala_id or cc.get('data_desconexao'):
                continue
            cabo = cabos.get(cc.get('cabo_id'))
            if not cabo:
                continue
            
            # Buscar equipamento de origem
            eq_o = equipamentos.get(cc.get('equipamento_origem_id'))
            
            # Buscar equipamento de destino (pode ser equipamento ou patch panel)
            # Primeiro tentar patch panel, depois equipamento
            eq_d = patch_panels.get(cc.get('equipamento_destino_id'))
            if not eq_d:
                eq_d = equipamentos.get(cc.get('equipamento_destino_id'))
            
            resultado.append({
                'id': cc.get('id'),
                'cabo_id': cc.get('cabo_id'),
                'codigo_cabo': (cabo or {}).get('codigo_unico'),
                'tipo_cabo': (cabo or {}).get('tipo'),
                'equipamento_origem': (eq_o or {}).get('nome'),
                'equipamento_destino': (eq_d or {}).get('nome'),
                'porta_origem': cc.get('porta_origem'),
                'porta_destino': cc.get('porta_destino'),
                'observacao': cc.get('observacao'),
                'data_conexao': cc.get('data_conexao'),
                'data_desconexao': cc.get('data_desconexao'),
                'ativo': True,
                # IDs úteis para edições posteriores
                'equipamento_origem_id': cc.get('equipamento_origem_id'),
                'equipamento_destino_id': cc.get('equipamento_destino_id')
            })
        return jsonify(resultado)
    else:
        return jsonify([])

@app.route('/conexoes-cabos/<int:conexao_id>', methods=['PUT'])
@admin_required
def atualizar_conexao_cabo(conexao_id):
    """Atualizar uma conexão de cabo existente"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
            
            # Encontrar a conexão
            conexao = next((c for c in conexoes_cabos if c.get('id') == conexao_id), None)
            if not conexao:
                return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
            
            # Atualizar campos permitidos
            if 'observacao' in dados:
                conexao['observacao'] = dados['observacao']
            if 'porta_origem' in dados:
                conexao['porta_origem'] = dados['porta_origem']
            if 'porta_destino' in dados:
                conexao['porta_destino'] = dados['porta_destino']
            
            _json_write_table(db_file, 'conexoes_cabos', conexoes_cabos)
            
            registrar_log(session.get('username'), 'ATUALIZAR_CONEXAO_CABO', 
                         f'Conexão de cabo atualizada: ID={conexao_id}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Conexão atualizada com sucesso!'})
            
        except Exception as e:
            print(f"Erro ao atualizar conexão de cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/conexoes-cabos/<int:conexao_id>', methods=['DELETE'])
@admin_required
def excluir_conexao_cabo(conexao_id):
    """Excluir uma conexão de cabo"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
            
            # Encontrar e remover a conexão
            conexao_original = next((c for c in conexoes_cabos if c.get('id') == conexao_id), None)
            if not conexao_original:
                return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
            
            conexoes_cabos = [c for c in conexoes_cabos if c.get('id') != conexao_id]
            _json_write_table(db_file, 'conexoes_cabos', conexoes_cabos)
            
            registrar_log(session.get('username'), 'EXCLUIR_CONEXAO_CABO', 
                         f'Conexão de cabo excluída: ID={conexao_id}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Conexão excluída com sucesso!'})
            
        except Exception as e:
            print(f"Erro ao excluir conexão de cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/conexoes-cabos/<int:conexao_id>/desconectar', methods=['PUT'])
@admin_required
def desconectar_cabo(conexao_id):
    """Desconectar um cabo (marcar como desconectado)"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
            
            # Encontrar a conexão
            conexao = next((c for c in conexoes_cabos if c.get('id') == conexao_id), None)
            if not conexao:
                return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
            
            # Marcar como desconectada
            conexao['data_desconexao'] = datetime.now().isoformat()
            
            _json_write_table(db_file, 'conexoes_cabos', conexoes_cabos)
            
            registrar_log(session.get('username'), 'DESCONECTAR_CABO', 
                         f'Cabo desconectado: ID={conexao_id}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Cabo desconectado com sucesso!'})
            
        except Exception as e:
            print(f"Erro ao desconectar cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/conexoes-cabos/<int:conexao_id>/substituir', methods=['POST'])
@admin_required
def substituir_cabo(conexao_id):
    """Substituir um cabo por outro"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
            cabos = _json_read_table(db_file, 'cabos')
            
            # Encontrar a conexão original
            conexao_original = next((c for c in conexoes_cabos if c.get('id') == conexao_id), None)
            if not conexao_original:
                return jsonify({'status': 'erro', 'mensagem': 'Conexão não encontrada'}), 404
            
            # Verificar se o novo cabo existe
            novo_cabo = next((c for c in cabos if c.get('id') == dados.get('novo_cabo_id')), None)
            if not novo_cabo:
                return jsonify({'status': 'erro', 'mensagem': 'Novo cabo não encontrado'}), 404
            
            # Desconectar cabo antigo
            conexao_original['data_desconexao'] = datetime.now().isoformat()
            
            # Criar nova conexão com o novo cabo
            nova_conexao = {
                'id': _json_next_id(conexoes_cabos),
                'cabo_id': dados.get('novo_cabo_id'),
                'equipamento_origem_id': conexao_original.get('equipamento_origem_id'),
                'equipamento_destino_id': conexao_original.get('equipamento_destino_id'),
                'porta_origem': conexao_original.get('porta_origem'),
                'porta_destino': conexao_original.get('porta_destino'),
                'sala_id': conexao_original.get('sala_id'),
                'observacao': f"Substituição de cabo - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                'data_conexao': datetime.now().isoformat(),
                'data_desconexao': None
            }
            
            conexoes_cabos.append(nova_conexao)
            _json_write_table(db_file, 'conexoes_cabos', conexoes_cabos)
            
            registrar_log(session.get('username'), 'SUBSTITUIR_CABO', 
                         f'Cabo substituído: Conexão {conexao_id} -> Cabo {dados.get("novo_cabo_id")}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Cabo substituído com sucesso!', 'nova_conexao_id': nova_conexao['id']})
            
        except Exception as e:
            print(f"Erro ao substituir cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/conexoes-cabos', methods=['GET'])
@login_required
def listar_conexoes_cabos():
    """Lista conexões de cabos com filtros opcionais"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    cabo_id = request.args.get('cabo_id')
    
    if _is_json_mode(db_file):
        try:
            conexoes_cabos = _json_read_table(db_file, 'conexoes_cabos')
            cabos = {c.get('id'): c for c in _json_read_table(db_file, 'cabos')}
            equipamentos = {e.get('id'): e for e in _json_read_table(db_file, 'equipamentos')}
            patch_panels = {pp.get('id'): pp for pp in _json_read_table(db_file, 'patch_panels')}
            
            resultado = []
            for cc in conexoes_cabos:
                # Filtrar por cabo_id se especificado
                if cabo_id and cc.get('cabo_id') != int(cabo_id):
                    continue
                
                # Pular conexões desconectadas
                if cc.get('data_desconexao'):
                    continue
                
                cabo = cabos.get(cc.get('cabo_id'))
                if not cabo:
                    continue
                
                # Buscar equipamento de origem
                eq_o = equipamentos.get(cc.get('equipamento_origem_id'))
                
                # Buscar equipamento de destino (pode ser equipamento ou patch panel)
                # Primeiro tentar patch panel, depois equipamento
                eq_d = patch_panels.get(cc.get('equipamento_destino_id'))
                if not eq_d:
                    eq_d = equipamentos.get(cc.get('equipamento_destino_id'))
                
                resultado.append({
                    'id': cc.get('id'),
                    'cabo_id': cc.get('cabo_id'),
                    'codigo_cabo': (cabo or {}).get('codigo_unico'),
                    'tipo_cabo': (cabo or {}).get('tipo'),
                    'equipamento_origem': (eq_o or {}).get('nome'),
                    'equipamento_destino': (eq_d or {}).get('nome'),
                    'porta_origem': cc.get('porta_origem'),
                    'porta_destino': cc.get('porta_destino'),
                    'observacao': cc.get('observacao'),
                    'data_conexao': cc.get('data_conexao'),
                    'data_desconexao': cc.get('data_desconexao'),
                    'ativo': True,
                    'equipamento_origem_id': cc.get('equipamento_origem_id'),
                    'equipamento_destino_id': cc.get('equipamento_destino_id')
                })
            
            return jsonify(resultado)
        except Exception as e:
            print(f"Erro ao listar conexões de cabos: {e}")
            return jsonify([])
    else:
        return jsonify([])

@app.route('/tipos-cabos', methods=['GET'])
@login_required
def api_tipos_cabos():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    try:
        # Ler arquivo global de tipos de cabos
        tipos_path = os.path.join('static', 'data', 'tipos-cabos.json')
        if not os.path.exists(tipos_path):
            return jsonify(['HDMI', 'VGA', 'RJ45', 'USB', 'Audio'])
        
        with open(tipos_path, 'r', encoding='utf-8') as f:
            tipos = json.load(f)
        
        # Se arquivo for dicionário/objeto, transformar em lista de nomes
        if isinstance(tipos, dict):
            tipos = [{'nome': k, 'descricao': v} for k, v in tipos.items()]
        elif tipos and isinstance(tipos[0], dict):
            # Manter objetos originais com nome e descrição
            tipos = [t for t in tipos if t.get('nome') or t.get('tipo')]
        
        # Ordenar por nome
        tipos_ordenados = sorted(tipos, key=lambda x: x.get('nome', '') or x.get('tipo', ''))
        return jsonify(tipos_ordenados)
    except Exception as e:
        print(f"Erro ao carregar tipos de cabos: {e}")
        return jsonify(['HDMI', 'VGA', 'RJ45', 'USB', 'Audio'])

@app.route('/cabos', methods=['POST'])
@admin_required
def criar_cabo():
    """Criar um novo cabo"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            cabos = _json_read_table(db_file, 'cabos')
            
            # Validar dados obrigatórios
            if not dados.get('codigo_unico'):
                return jsonify({'status': 'erro', 'mensagem': 'Código único é obrigatório'}), 400
            
            if not dados.get('tipo'):
                return jsonify({'status': 'erro', 'mensagem': 'Tipo do cabo é obrigatório'}), 400
            
            # Verificar se código único já existe
            if any(c.get('codigo_unico') == dados.get('codigo_unico') for c in cabos):
                return jsonify({'status': 'erro', 'mensagem': 'Código único já existe'}), 400
            
            # Criar novo cabo
            novo_cabo = {
                'id': _json_next_id(cabos),
                'codigo_unico': dados.get('codigo_unico'),
                'tipo': dados.get('tipo'),
                'comprimento': dados.get('comprimento'),
                'marca': dados.get('marca', ''),
                'modelo': dados.get('modelo', ''),
                'descricao': dados.get('descricao', ''),
                'status': dados.get('status', 'funcionando'),
                'data_criacao': datetime.now().isoformat()
            }
            
            cabos.append(novo_cabo)
            _json_write_table(db_file, 'cabos', cabos)
            
            registrar_log(session.get('username'), 'CRIAR_CABO', 
                         f'Cabo criado: {novo_cabo["codigo_unico"]}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Cabo criado com sucesso!', 'cabo_id': novo_cabo['id']})
            
        except Exception as e:
            print(f"Erro ao criar cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/cabos/<int:cabo_id>', methods=['PUT'])
@admin_required
def atualizar_cabo(cabo_id):
    """Atualizar um cabo existente"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            cabos = _json_read_table(db_file, 'cabos')
            
            # Encontrar o cabo
            cabo = next((c for c in cabos if c.get('id') == cabo_id), None)
            if not cabo:
                return jsonify({'status': 'erro', 'mensagem': 'Cabo não encontrado'}), 404
            
            # Verificar se código único já existe (se foi alterado)
            if dados.get('codigo_unico') and dados.get('codigo_unico') != cabo.get('codigo_unico'):
                if any(c.get('codigo_unico') == dados.get('codigo_unico') for c in cabos if c.get('id') != cabo_id):
                    return jsonify({'status': 'erro', 'mensagem': 'Código único já existe'}), 400
            
            # Atualizar campos permitidos
            if 'codigo_unico' in dados:
                cabo['codigo_unico'] = dados['codigo_unico']
            if 'tipo' in dados:
                cabo['tipo'] = dados['tipo']
            if 'comprimento' in dados:
                cabo['comprimento'] = dados['comprimento']
            if 'marca' in dados:
                cabo['marca'] = dados['marca']
            if 'modelo' in dados:
                cabo['modelo'] = dados['modelo']
            if 'descricao' in dados:
                cabo['descricao'] = dados['descricao']
            if 'status' in dados:
                cabo['status'] = dados['status']
            
            _json_write_table(db_file, 'cabos', cabos)
            
            registrar_log(session.get('username'), 'ATUALIZAR_CABO', 
                         f'Cabo atualizado: {cabo["codigo_unico"]}', 'sucesso', db_file)
            
            return jsonify({'status': 'ok', 'mensagem': 'Cabo atualizado com sucesso!'})
            
        except Exception as e:
            print(f"Erro ao atualizar cabo: {e}")
            return jsonify({'status': 'erro', 'mensagem': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Modo SQLite não implementado'}), 501

@app.route('/cabos/<int:cabo_id>', methods=['GET'])
@login_required
def obter_cabo(cabo_id):
    """Obter dados de um cabo específico"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        try:
            cabos = _json_read_table(db_file, 'cabos')
            cabo = next((c for c in cabos if c.get('id') == cabo_id), None)
            
            if not cabo:
                return jsonify({'erro': 'Cabo não encontrado'}), 404
            
            return jsonify(cabo)
        except Exception as e:
            print(f"Erro ao obter cabo {cabo_id}: {e}")
            return jsonify({'erro': 'Erro interno do servidor'}), 500
    else:
        return jsonify({'erro': 'Modo SQLite não implementado'}), 501

@app.route('/cabos', methods=['GET'])
@login_required
def api_listar_cabos():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    if _is_json_mode(db_file):
        return jsonify(_json_read_table(db_file, 'cabos'))
    return jsonify([])
@app.route('/api/salas/<int:sala_id>/switches-usados')
@login_required
def switches_usados_sala(sala_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        switches = _json_read_table(db_file, 'switches')
        switch_portas = _json_read_table(db_file, 'switch_portas')
        patch_panel_portas = _json_read_table(db_file, 'patch_panel_portas')
        patch_panels = _json_read_table(db_file, 'patch_panels')
        equipamentos = _json_read_table(db_file, 'equipamentos')
        salas = _json_read_table(db_file, 'salas')
        conexoes = _json_read_table(db_file, 'conexoes')

        # Dicionários de apoio
        equipamentos_dict = {e.get('id'): e for e in equipamentos}
        salas_dict = {s.get('id'): s for s in salas}
        patch_panels_dict = {pp.get('id'): pp for pp in patch_panels}
        switch_portas_by_id = {sp.get('id'): sp for sp in switch_portas}
        switch_portas_by_switch = {}
        for sp in switch_portas:
            switch_portas_by_switch.setdefault(sp.get('switch_id'), []).append(sp)

        # índices rápidos
        ppp_index = {}
        for m in patch_panel_portas:
            key = (m.get('switch_id'), m.get('porta_switch'))
            ppp_index[key] = m
        conexao_por_porta = {c.get('porta_id'): c for c in conexoes if c.get('status') == 'ativa'}

        # Identificar switches relevantes pela sala
        switch_ids_usados = set()
        # via conexões diretas
        for c in conexoes:
            if c.get('status') == 'ativa':
                eq = equipamentos_dict.get(c.get('equipamento_id'))
                sp = switch_portas_by_id.get(c.get('porta_id'))
                if eq and sp and eq.get('sala_id') == sala_id:
                    switch_ids_usados.add(sp.get('switch_id'))
        # via patch panel
        for m in patch_panel_portas:
            eq = equipamentos_dict.get(m.get('equipamento_id')) if m.get('equipamento_id') else None
            if eq and eq.get('sala_id') == sala_id and m.get('switch_id'):
                switch_ids_usados.add(m.get('switch_id'))

        resultado = []
        for switch_id in sorted(switch_ids_usados):
            sw = next((s for s in switches if s.get('id') == switch_id), None)
            if not sw:
                continue
            portas_sw = sorted(switch_portas_by_switch.get(switch_id, []), key=lambda x: int(x.get('numero_porta') or 0))
            portas_render = []
            for porta in portas_sw:
                numero = porta.get('numero_porta')
                status = 'livre'
                equipamento_info = None
                patch_panel_info = None
                sala_especifica = False

                # Primeiro, verificar mapeamento com patch panel
                mapping = ppp_index.get((switch_id, numero))
                if mapping:
                    pp = patch_panels_dict.get(mapping.get('patch_panel_id')) if mapping.get('patch_panel_id') else None
                    patch_panel_info = {
                        'nome': (pp or {}).get('nome'),
                        'porta_patch_panel': mapping.get('numero_porta'),
                        'prefixo_keystone': (pp or {}).get('prefixo_keystone')
                    }
                    if mapping.get('equipamento_id'):
                        eq = equipamentos_dict.get(mapping.get('equipamento_id'))
                        if eq:
                            status = 'ocupada'
                            sala = salas_dict.get(eq.get('sala_id'))
                            equipamento_info = {
                                'nome': eq.get('nome'),
                                'tipo': eq.get('tipo'),
                                'marca': eq.get('marca'),
                                'sala_nome': (sala or {}).get('nome'),
                                'ip1': (eq.get('dados') or {}).get('ip1') or (eq.get('dados') or {}).get('ip') or '',
                                'ip2': (eq.get('dados') or {}).get('ip2') or '',
                                'mac1': (eq.get('dados') or {}).get('mac1') or (eq.get('dados') or {}).get('mac') or '',
                                'mac2': (eq.get('dados') or {}).get('mac2') or ''
                            }
                            sala_especifica = (eq.get('sala_id') == sala_id)
                    else:
                        status = 'mapeada'
                else:
                    # Verificar conexão direta
                    c = conexao_por_porta.get(porta.get('id'))
                    if c:
                        eq = equipamentos_dict.get(c.get('equipamento_id')) if c.get('equipamento_id') else None
                        if eq:
                            status = 'ocupada'
                            sala = salas_dict.get(eq.get('sala_id'))
                            equipamento_info = {
                                'nome': eq.get('nome'),
                                'tipo': eq.get('tipo'),
                                'marca': eq.get('marca'),
                                'sala_nome': (sala or {}).get('nome'),
                                'ip1': (eq.get('dados') or {}).get('ip1') or (eq.get('dados') or {}).get('ip') or '',
                                'ip2': (eq.get('dados') or {}).get('ip2') or '',
                                'mac1': (eq.get('dados') or {}).get('mac1') or (eq.get('dados') or {}).get('mac') or '',
                                'mac2': (eq.get('dados') or {}).get('mac2') or ''
                            }
                            sala_especifica = (eq.get('sala_id') == sala_id)

                portas_render.append({
                    'numero': numero,
                    'status': status,
                    'equipamento_info': equipamento_info,
                    'patch_panel_info': patch_panel_info,
                    'sala_especifica': sala_especifica
                })

            resultado.append({
                'id': sw.get('id'),
                'nome': sw.get('nome'),
                'marca': sw.get('marca'),
                'modelo': sw.get('modelo'),
                'portas': portas_render
            })

        return jsonify(resultado)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Buscar switches que têm conexão com equipamentos da sala específica
        cur.execute('''
            SELECT DISTINCT s.id as switch_id, s.nome as switch_nome, s.marca as switch_marca, s.modelo as switch_modelo
            FROM switches s
            JOIN switch_portas sp ON s.id = sp.switch_id
            LEFT JOIN patch_panel_portas ppp ON sp.switch_id = ppp.switch_id AND sp.numero_porta = ppp.porta_switch
            LEFT JOIN equipamentos e1 ON ppp.equipamento_id = e1.id
            LEFT JOIN conexoes c ON sp.id = c.porta_id AND c.status = 'ativa'
            LEFT JOIN equipamentos e2 ON c.equipamento_id = e2.id
            WHERE (e1.sala_id = ? OR e2.sala_id = ?)
            ORDER BY s.id
        ''', (sala_id, sala_id))
        
        switches_rows = cur.fetchall()
        conn.close()
        
        switches_list = []
        for switch_id, switch_nome, switch_marca, switch_modelo in switches_rows:
            switch_data = {
                'id': switch_id,
                'nome': switch_nome,
                'marca': switch_marca,
                'modelo': switch_modelo
            }
            switches_list.append(switch_data)
        
        return jsonify(switches_list)
@app.route('/salas/andar/<int:andar>', methods=['GET'])
@login_required
def listar_salas_por_andar(andar):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    try:
        # Assumindo que as salas têm um campo 'andar' ou podem ser identificadas por nome
        # Você pode ajustar esta query conforme sua estrutura de dados
        cur.execute('''
            SELECT id, nome
            FROM salas
            WHERE nome LIKE ? OR nome LIKE ?
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
    try:
        db_file = session.get('db')
        if not db_file:
            return jsonify({'status': 'erro', 'mensagem': 'Banco de dados não selecionado'}), 400
        
        if _is_json_mode(db_file):
            pps = _json_read_table(db_file, 'patch_panels')
            pp = next((x for x in pps if x.get('id') == id), None)
            if not pp:
                return jsonify({'status': 'erro', 'mensagem': 'Patch panel não encontrado'}), 404
            porta_inicial = int(pp.get('porta_inicial') or 1)
            num_portas = int(pp.get('num_portas') or 0)
            retorno = {
                'id': pp.get('id'),
                'codigo': pp.get('codigo'),
                'nome': pp.get('nome'),
                'andar': pp.get('andar'),
                'porta_inicial': porta_inicial,
                'num_portas': num_portas,
                'status': pp.get('status'),
                'descricao': pp.get('descricao'),
                'data_criacao': pp.get('data_criacao'),
                'porta_final': porta_inicial + num_portas - 1 if num_portas else porta_inicial
            }
            return jsonify(retorno)
        else:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, codigo, nome, andar, porta_inicial, num_portas, status, descricao, data_criacao
                FROM patch_panels 
                WHERE id = ?
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
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT pp.id, pp.nome, pp.sala_id, pp.num_portas, pp.descricao, pp.data_criacao,
                   s.nome as sala_nome
            FROM patch_panels pp
            LEFT JOIN salas s ON pp.sala_id = s.id
            WHERE pp.id = ?
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
            WHERE ppp.patch_panel_id = ?
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
    try:
        db_file = session.get('db')
        if not db_file:
            return jsonify({'erro': 'Banco de dados não selecionado'}), 400
        
        if _is_json_mode(db_file):
            equipamentos = _json_read_table(db_file, 'equipamentos')
            salas = _json_read_table(db_file, 'salas')
            patch_panel_portas = _json_read_table(db_file, 'patch_panel_portas')
            patch_panels = _json_read_table(db_file, 'patch_panels')
            
            # Buscar equipamento
            equipamento = next((e for e in equipamentos if e.get('id') == equipamento_id), None)
            if not equipamento:
                return jsonify({'erro': 'Equipamento não encontrado'}), 404
            
            # Buscar sala
            sala = next((s for s in salas if s.get('id') == equipamento.get('sala_id')), None)
            
            # Buscar conexão com patch panel
            porta_patch = next((ppp for ppp in patch_panel_portas if ppp.get('equipamento_id') == equipamento_id), None)
            
            # Se o equipamento está conectado a um patch panel
            if porta_patch:
                patch_panel = next((pp for pp in patch_panels if pp.get('id') == porta_patch.get('patch_panel_id')), None)
                if patch_panel:
                    patch_panel_info = {
                        'andar': patch_panel.get('andar'),
                        'patch_panel_id': porta_patch.get('patch_panel_id'),
                        'patch_panel_nome': patch_panel.get('nome'),
                        'porta_numero': porta_patch.get('numero_porta')
                    }
                else:
                    patch_panel_info = None
            else:
                patch_panel_info = None
            
            equipamento_info = {
                'id': equipamento.get('id'),
                'nome': equipamento.get('nome'),
                'tipo': equipamento.get('tipo'),
                'sala_id': equipamento.get('sala_id'),
                'sala_nome': sala.get('nome') if sala else 'Sem sala',
                'patch_panel_info': patch_panel_info
            }
            
            return jsonify(equipamento_info)
        else:
            conn = sqlite3.connect(db_file)
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
                WHERE e.id = ?
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
    try:
        db_file = session.get('db')
        if not db_file:
            return jsonify({'erro': 'Banco de dados não selecionado'}), 400
        
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Buscar informações detalhadas do equipamento
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.sala_id, s.nome as sala_nome
            FROM equipamentos e
            LEFT JOIN salas s ON e.sala_id = s.id
            WHERE e.id = ?
        ''', (equipamento_id,))
        
        row = cur.fetchone()
        if not row:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        # Buscar informações do patch panel
        cur.execute('''
            SELECT ppp.id, ppp.numero_porta, ppp.status, pp.nome as patch_panel_nome
            FROM patch_panel_portas ppp
            LEFT JOIN patch_panels pp ON ppp.patch_panel_id = pp.id
            WHERE ppp.equipamento_id = ?
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

@app.route('/upload-logo-empresa', methods=['POST'])
@admin_required
def upload_logo_empresa():
    if 'logo' not in request.files:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_LOGO_EMPRESA', 'Tentativa de upload sem arquivo', 'erro', session.get('db'))
        return jsonify({'status': 'erro', 'mensagem': 'Nenhum arquivo enviado'})
    
    file = request.files['logo']
    if not file.filename:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_LOGO_EMPRESA', 'Tentativa de upload com nome de arquivo vazio', 'erro', session.get('db'))
        return jsonify({'status': 'erro', 'mensagem': 'Nome de arquivo vazio'})
    
    db_file = session.get('db')
    if not db_file:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_LOGO_EMPRESA', 'Tentativa de upload sem empresa selecionada', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Nenhuma empresa selecionada!'})

    # Deriva diretório da empresa a partir do db_file (sanitizado p/ Windows)
    raw = os.path.splitext(os.path.basename(str(db_file)))[0]
    if isinstance(db_file, str) and db_file.startswith('json:empresa_'):
        try:
            emp_id = int(db_file.split('_')[-1])
            empresa_dir = f'empresa_{emp_id}'
        except Exception:
            empresa_dir = re.sub(r'[^A-Za-z0-9_-]+', '_', raw)
    else:
        empresa_dir = re.sub(r'[^A-Za-z0-9_-]+', '_', raw)

    pasta = os.path.join('static', 'img', 'logos-empresas', empresa_dir)
    os.makedirs(pasta, exist_ok=True)

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_LOGO_EMPRESA', f'Tentativa de upload com extensão inválida: {file.filename}', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Extensão de arquivo não permitida. Use: png, jpg, jpeg, gif, svg'})

    filename = secure_filename(file.filename)
    caminho = os.path.join(pasta, filename)
    file.save(caminho)

    # Atualiza empresas.json (sem SQLite)
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'static', 'data')
        empresas_path = os.path.join(data_dir, 'empresas.json')
        empresas = []
        if os.path.exists(empresas_path):
            with open(empresas_path, 'r', encoding='utf-8') as f:
                empresas = json.load(f)

        logo_path = f'/static/img/logos-empresas/{empresa_dir}/{filename}'

        # Encontrar empresa por db_file; se não tiver db_file no JSON, inferir pelo id do placeholder "json:empresa_<id>"
        empresa = None
        for e in empresas:
            if e.get('db_file') == db_file:
                empresa = e
                break
        if not empresa and isinstance(db_file, str) and db_file.startswith('json:empresa_'):
            try:
                emp_id = int(db_file.split('_')[-1])
                empresa = next((e for e in empresas if e.get('id') == emp_id), None)
            except Exception:
                empresa = None

        if empresa is None:
            # cria/garante entrada caso não exista
            empresa = {'id': None, 'nome': empresa_dir}
            empresas.append(empresa)

        empresa['logo'] = logo_path
        if 'db_file' not in empresa:
            empresa['db_file'] = db_file

        with open(empresas_path, 'w', encoding='utf-8') as f:
            json.dump(empresas, f, ensure_ascii=False, indent=2)
    except Exception as e:
        registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_LOGO_EMPRESA', f'Erro ao atualizar empresas.json: {str(e)}', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Falha ao atualizar empresas.json'}), 500

    registrar_log(session.get('username', 'desconhecido'), 'UPLOAD_LOGO_EMPRESA', f'Logo {filename} enviado para empresa {empresa_dir}', 'sucesso', db_file)
    return jsonify({'status': 'ok', 'caminho': logo_path})

@app.route('/remover-logo-empresa', methods=['DELETE'])
@admin_required
def remover_logo_empresa():
    db_file = session.get('db')
    if not db_file:
        registrar_log(session.get('username', 'desconhecido'), 'REMOVER_LOGO_EMPRESA', 'Tentativa de remoção sem empresa selecionada', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': 'Nenhuma empresa selecionada!'})

    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'static', 'data')
        empresas_path = os.path.join(data_dir, 'empresas.json')
        if not os.path.exists(empresas_path):
            return jsonify({'status': 'ok', 'mensagem': 'Nenhum logo definido'})

        with open(empresas_path, 'r', encoding='utf-8') as f:
            empresas = json.load(f)

        empresa = next((e for e in empresas if e.get('db_file') == db_file), None)
        if not empresa and isinstance(db_file, str) and db_file.startswith('json:empresa_'):
            try:
                emp_id = int(db_file.split('_')[-1])
                empresa = next((e for e in empresas if e.get('id') == emp_id), None)
            except Exception:
                empresa = None

        if not empresa or not empresa.get('logo'):
            return jsonify({'status': 'ok', 'mensagem': 'Nenhum logo definido'})

        logo_path = empresa['logo']
        if logo_path.startswith('/static/'):
            file_path = logo_path[1:]
            if os.path.exists(file_path):
                os.remove(file_path)

        empresa['logo'] = None
        with open(empresas_path, 'w', encoding='utf-8') as f:
            json.dump(empresas, f, ensure_ascii=False, indent=2)

        registrar_log(session.get('username', 'desconhecido'), 'REMOVER_LOGO_EMPRESA', f'Logo removido da empresa {os.path.splitext(os.path.basename(db_file))[0]}', 'sucesso', db_file)
        return jsonify({'status': 'ok', 'mensagem': 'Logo removido com sucesso'})
    except Exception as e:
        registrar_log(session.get('username', 'desconhecido'), 'REMOVER_LOGO_EMPRESA', f'Erro ao remover logo: {str(e)}', 'erro', db_file)
        return jsonify({'status': 'erro', 'mensagem': f'Erro ao remover logo: {str(e)}'}), 500

@app.route('/logos-empresa')
@admin_required
def logos_empresa():
    db_file = session.get('db')
    if not db_file:
        return jsonify({'imagens': []})
    empresa_dir = os.path.splitext(os.path.basename(db_file))[0]
    pasta = os.path.join('static', 'img', 'logos-empresas', empresa_dir)
    if not os.path.exists(pasta):
        return jsonify({'imagens': []})
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
    return jsonify({'imagens': [f'/static/img/logos-empresas/{empresa_dir}/{arq}' for arq in arquivos]})

@app.route('/gerenciar-logo-empresa.html')
@admin_required
def gerenciar_logo_empresa_html():
    return send_file('gerenciar-logo-empresa.html')

# --- ROTAS DE IDFs (Intermediate Distribution Frames) ---

@app.route('/idfs', methods=['GET'])
@login_required
def listar_idfs():
    """Lista todos os IDFs da empresa"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        idfs = _json_read_table(db_file, 'idfs')
        andar_switches = _json_read_table(db_file, 'andar_switches')
        resultado = []
        for i in idfs:
            andar_id = i.get('andar_id')
            if andar_id == 0:
                andar_nome = 'Térreo'
            else:
                andar_nome = f"{andar_id}º Andar"
            switches_count = sum(1 for l in andar_switches if l.get('idf_responsavel_id') == i.get('id'))
            resultado.append({
                'id': i.get('id'),
                'nome': i.get('nome'),
                'andar_id': andar_id,
                'descricao': i.get('descricao'),
                'foto': i.get('foto'),
                'status': i.get('status'),
                'data_criacao': i.get('data_criacao'),
                'andar_nome': andar_nome,
                'switches_count': switches_count
            })
        resultado.sort(key=lambda x: (x.get('data_criacao') or ''), reverse=True)
        return jsonify(resultado)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Criar tabelas de IDFs se não existirem
        cur.execute('''
            CREATE TABLE IF NOT EXISTS idfs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                andar_id INTEGER NOT NULL,
                descricao TEXT,
                foto TEXT,
                status TEXT DEFAULT 'ativo',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (andar_id) REFERENCES andares (id)
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS idf_equipamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idf_id INTEGER NOT NULL,
                equipamento_id INTEGER NOT NULL,
                funcao TEXT,
                posicao_rack TEXT,
                tipo_alocacao TEXT DEFAULT 'exclusivo',
                sala_origem_id INTEGER,
                FOREIGN KEY (idf_id) REFERENCES idfs (id),
                FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id),
                FOREIGN KEY (sala_origem_id) REFERENCES salas (id)
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS idf_sala_conexoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idf_id INTEGER NOT NULL,
                sala_id INTEGER NOT NULL,
                tipo_conexao TEXT,
                capacidade TEXT,
                status TEXT DEFAULT 'ativo',
                FOREIGN KEY (idf_id) REFERENCES idfs (id),
                FOREIGN KEY (sala_id) REFERENCES salas (id)
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS andar_switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                andar_id INTEGER NOT NULL,
                switch_id INTEGER NOT NULL,
                idf_responsavel_id INTEGER,
                FOREIGN KEY (andar_id) REFERENCES andares (id),
                FOREIGN KEY (switch_id) REFERENCES switches (id),
                FOREIGN KEY (idf_responsavel_id) REFERENCES idfs (id)
            )
        ''')
        
        # Buscar IDFs com informações do andar
        cur.execute('''
            SELECT i.id,
                   i.nome,
                   i.andar_id,
                   i.descricao,
                   i.foto,
                   i.status,
                   i.data_criacao,
                   a.titulo as andar_nome,
                   (
                     SELECT COUNT(*)
                     FROM andar_switches asw
                     WHERE asw.idf_responsavel_id = i.id
                   ) as switches_count
            FROM idfs i
            LEFT JOIN andares a ON i.andar_id = a.id
            ORDER BY i.data_criacao DESC
        ''')
        
        idfs = []
        for row in cur.fetchall():
            idf = {
                'id': row[0],
                'nome': row[1],
                'andar_id': row[2],
                'descricao': row[3],
                'foto': row[4],
                'status': row[5],
                'data_criacao': row[6],
                'andar_nome': row[7],
                'switches_count': row[8]
            }
            idfs.append(idf)
        
        conn.close()
        return jsonify(idfs)

@app.route('/idfs', methods=['POST'])
@admin_required
def criar_idf():
    """Cria um novo IDF"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        idfs = _json_read_table(db_file, 'idfs')
        if any((i.get('andar_id') == dados.get('andar_id') and (i.get('nome') or '').lower() == (dados.get('nome') or '').lower()) for i in idfs):
            return jsonify({'status': 'erro', 'mensagem': 'Já existe um IDF com esse nome neste andar!'}), 400
        idf_id = _json_next_id(idfs)
        idfs.append({
            'id': idf_id,
            'nome': dados.get('nome'),
            'andar_id': dados.get('andar_id'),
            'descricao': dados.get('descricao'),
            'foto': dados.get('foto'),
            'status': dados.get('status', 'ativo'),
            'data_criacao': datetime.now().isoformat()
        })
        _json_write_table(db_file, 'idfs', idfs)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Verificar se já existe IDF com o mesmo nome no mesmo andar
        cur.execute('SELECT 1 FROM idfs WHERE LOWER(nome) = LOWER(?) AND andar_id = ?', 
                    (dados['nome'], dados['andar_id']))
        if cur.fetchone():
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Já existe um IDF com esse nome neste andar!'}), 400
        
        # Criar IDF
        cur.execute('''
            INSERT INTO idfs (nome, andar_id, descricao, foto, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            dados['nome'],
            dados['andar_id'],
            dados.get('descricao'),
            dados.get('foto'),
            dados.get('status', 'ativo')
        ))
        
        idf_id = cur.lastrowid
        conn.commit()
        conn.close()
    
    # Log de criação
    detalhes = f"IDF criado: ID={idf_id}, Nome={dados['nome']}, Andar={dados['andar_id']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_IDF', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok', 'id': idf_id})

@app.route('/idfs/<int:id>', methods=['GET'])
@login_required
def get_idf(id):
    """Obtém detalhes de um IDF específico"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        idfs = _json_read_table(db_file, 'idfs')
        idf = next((x for x in idfs if x.get('id') == id), None)
        if not idf:
            return jsonify({'status': 'erro', 'mensagem': 'IDF não encontrado'}), 404
        andar_id = idf.get('andar_id')
        andar_nome = 'Térreo' if andar_id == 0 else f"{andar_id}º Andar"
        equipamentos_map = {e.get('id'): e for e in _json_read_table(db_file, 'equipamentos')}
        salas_map = {s.get('id'): s for s in _json_read_table(db_file, 'salas')}
        ie = [x for x in _json_read_table(db_file, 'idf_equipamentos') if x.get('idf_id') == id]
        equipamentos = []
        for row in ie:
            e = equipamentos_map.get(row.get('equipamento_id')) or {}
            equipamentos.append({
                'id': e.get('id'),
                'nome': e.get('nome'),
                'tipo': e.get('tipo'),
                'marca': e.get('marca'),
                'modelo': e.get('modelo'),
                'funcao': row.get('funcao'),
                'posicao_rack': row.get('posicao_rack'),
                'tipo_alocacao': row.get('tipo_alocacao'),
                'sala_origem_id': row.get('sala_origem_id'),
                'sala_origem_nome': (salas_map.get(row.get('sala_origem_id')) or {}).get('nome') if row.get('sala_origem_id') else None
            })
        isc = [x for x in _json_read_table(db_file, 'idf_sala_conexoes') if x.get('idf_id') == id]
        conexoes_salas = []
        for c in isc:
            sala = salas_map.get(c.get('sala_id')) or {}
            conexoes_salas.append({
                'sala_id': c.get('sala_id'),
                'sala_nome': sala.get('nome'),
                'tipo_conexao': c.get('tipo_conexao'),
                'capacidade': c.get('capacidade'),
                'status': c.get('status')
            })
        retorno = {
            'id': idf.get('id'),
            'nome': idf.get('nome'),
            'andar_id': andar_id,
            'descricao': idf.get('descricao'),
            'foto': idf.get('foto'),
            'status': idf.get('status'),
            'data_criacao': idf.get('data_criacao'),
            'andar_nome': andar_nome,
            'equipamentos': equipamentos,
            'conexoes_salas': conexoes_salas
        }
        return jsonify(retorno)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Buscar IDF
        cur.execute('''
            SELECT i.id, i.nome, i.andar_id, i.descricao, i.foto, i.status, i.data_criacao, a.titulo as andar_nome
            FROM idfs i
            LEFT JOIN andares a ON i.andar_id = a.id
            WHERE i.id = ?
        ''', (id,))
        
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'IDF não encontrado'}), 404
        
        idf = {
            'id': row[0],
            'nome': row[1],
            'andar_id': row[2],
            'descricao': row[3],
            'foto': row[4],
            'status': row[5],
            'data_criacao': row[6],
            'andar_nome': row[7]
        }
        
        # Buscar equipamentos do IDF
        cur.execute('''
            SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, ie.funcao, ie.posicao_rack, 
                   ie.tipo_alocacao, ie.sala_origem_id, s.nome as sala_origem_nome
            FROM idf_equipamentos ie
            JOIN equipamentos e ON ie.equipamento_id = e.id
            LEFT JOIN salas s ON ie.sala_origem_id = s.id
            WHERE ie.idf_id = ?
            ORDER BY ie.posicao_rack
        ''', (id,))
        
        equipamentos = []
        for row in cur.fetchall():
            equipamento = {
                'id': row[0],
                'nome': row[1],
                'tipo': row[2],
                'marca': row[3],
                'modelo': row[4],
                'funcao': row[5],
                'posicao_rack': row[6],
                'tipo_alocacao': row[7],
                'sala_origem_id': row[8],
                'sala_origem_nome': row[9]
            }
            equipamentos.append(equipamento)
        
        idf['equipamentos'] = equipamentos
        
        # Buscar conexões com salas
        cur.execute('''
            SELECT s.id, s.nome, isc.tipo_conexao, isc.capacidade, isc.status
            FROM idf_sala_conexoes isc
            JOIN salas s ON isc.sala_id = s.id
            WHERE isc.idf_id = ?
        ''', (id,))
        
        conexoes_salas = []
        for row in cur.fetchall():
            conexao = {
                'sala_id': row[0],
                'sala_nome': row[1],
                'tipo_conexao': row[2],
                'capacidade': row[3],
                'status': row[4]
            }
            conexoes_salas.append(conexao)
        
        idf['conexoes_salas'] = conexoes_salas
        
        conn.close()
        return jsonify(idf)

@app.route('/idfs/<int:id>/switches-andar', methods=['GET'])
@login_required
def get_switches_andar_idf(id):
    """Obtém todos os switches do andar do IDF"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        idf = next((x for x in _json_read_table(db_file, 'idfs') if x.get('id') == id), None)
        if not idf:
            return jsonify({'status': 'erro', 'mensagem': 'IDF não encontrado'}), 404
        andar_id = idf.get('andar_id')
        links = [l for l in _json_read_table(db_file, 'andar_switches') if l.get('andar_id') == andar_id]
        switches_map = {s.get('id'): s for s in _json_read_table(db_file, 'switches')}
        portas = _json_read_table(db_file, 'switch_portas')
        resultado = []
        for l in links:
            s = switches_map.get(l.get('switch_id'))
            if not s:
                continue
            sp_do_switch = [p for p in portas if p.get('switch_id') == s.get('id')]
            total = len(sp_do_switch)
            ocupadas = sum(1 for p in sp_do_switch if (p.get('status') or 'livre') != 'livre')
            resultado.append({
                'id': s.get('id'),
                'nome': s.get('nome'),
                'marca': s.get('marca'),
                'modelo': s.get('modelo'),
                'data_criacao': s.get('data_criacao'),
                'total_portas': total,
                'portas_ocupadas': ocupadas,
                'portas_livres': total - ocupadas
            })
        resultado.sort(key=lambda x: x.get('nome') or '')
        return jsonify(resultado)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Buscar andar do IDF
        cur.execute('SELECT andar_id FROM idfs WHERE id = ?', (id,))
        result = cur.fetchone()
        if not result:
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'IDF não encontrado'}), 404
        
        andar_id = result[0]
        
        # Buscar apenas os switches vinculados explicitamente ao andar do IDF
        cur.execute('''
            WITH porta_ocupacao AS (
                SELECT sp2.id AS porta_id,
                       sp2.switch_id,
                       CASE 
                           WHEN EXISTS (
                               SELECT 1 FROM conexoes c 
                               WHERE c.porta_id = sp2.id AND c.status = 'ativa'
                           ) THEN 1
                           WHEN EXISTS (
                               SELECT 1 FROM patch_panel_portas ppp 
                               WHERE ppp.switch_id = sp2.switch_id 
                                 AND ppp.porta_switch = sp2.numero_porta 
                                 AND ppp.equipamento_id IS NOT NULL
                           ) THEN 1
                           ELSE 0
                       END AS ocupada
                FROM switch_portas sp2
            )
            SELECT s.id, s.nome, s.marca, s.modelo, s.data_criacao,
                   COUNT(sp.id) AS total_portas,
                   COALESCE(SUM(po.ocupada), 0) AS portas_ocupadas
            FROM switches s
            JOIN andar_switches asw ON s.id = asw.switch_id AND asw.andar_id = ?
            LEFT JOIN switch_portas sp ON s.id = sp.switch_id
            LEFT JOIN porta_ocupacao po ON po.porta_id = sp.id
            GROUP BY s.id, s.nome, s.marca, s.modelo, s.data_criacao
            ORDER BY s.nome
        ''', (andar_id,))
        
        switches = []
        for row in cur.fetchall():
            switch = {
                'id': row[0],
                'nome': row[1],
                'marca': row[2],
                'modelo': row[3],
                'data_criacao': row[4],
                'total_portas': row[5] or 0,
                'portas_ocupadas': row[6] or 0,
                'portas_livres': (row[5] or 0) - (row[6] or 0)
            }
            switches.append(switch)
        
        conn.close()
        return jsonify(switches)

# Vincular/desvincular switches a um andar (para controle fino por IDF)
@app.route('/andares/<int:andar_id>/switches', methods=['POST'])
@admin_required
def vincular_switch_a_andar(andar_id):
    dados = request.json or {}
    switch_id = dados.get('switch_id')
    idf_responsavel_id = dados.get('idf_responsavel_id')
    if not switch_id:
        return jsonify({'status': 'erro', 'mensagem': 'switch_id é obrigatório'}), 400

    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400

    if _is_json_mode(db_file):
        links = _json_read_table(db_file, 'andar_switches')
        # remover existente do mesmo andar_id e switch_id
        links = [l for l in links if not (l.get('andar_id') == andar_id and l.get('switch_id') == switch_id)]
        links.append({
            'id': _json_next_id(links),
            'andar_id': andar_id,
            'switch_id': switch_id,
            'idf_responsavel_id': idf_responsavel_id
        })
        _json_write_table(db_file, 'andar_switches', links)
        return jsonify({'status': 'ok'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Garantir tabela
        cur.execute('''
            CREATE TABLE IF NOT EXISTS andar_switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                andar_id INTEGER NOT NULL,
                switch_id INTEGER NOT NULL,
                idf_responsavel_id INTEGER,
                UNIQUE(andar_id, switch_id),
                FOREIGN KEY (andar_id) REFERENCES andares (id),
                FOREIGN KEY (switch_id) REFERENCES switches (id)
            )
        ''')
        
        # Upsert simples: tentar inserir, se já existir atualizar idf_responsavel
        try:
            cur.execute('''
                INSERT INTO andar_switches (andar_id, switch_id, idf_responsavel_id)
                VALUES (?, ?, ?)
            ''', (andar_id, switch_id, idf_responsavel_id))
        except sqlite3.IntegrityError:
            cur.execute('''
                UPDATE andar_switches SET idf_responsavel_id=?
                WHERE andar_id=? AND switch_id=?
            ''', (idf_responsavel_id, andar_id, switch_id))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

@app.route('/andares/<int:andar_id>/switches/<int:switch_id>', methods=['DELETE'])
@admin_required
def desvincular_switch_de_andar(andar_id, switch_id):
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400

    if _is_json_mode(db_file):
        links = _json_read_table(db_file, 'andar_switches')
        links = [l for l in links if not (l.get('andar_id') == andar_id and l.get('switch_id') == switch_id)]
        _json_write_table(db_file, 'andar_switches', links)
        return jsonify({'status': 'ok'})
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute('DELETE FROM andar_switches WHERE andar_id=? AND switch_id=?', (andar_id, switch_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

@app.route('/idfs/<int:id>/equipamentos', methods=['POST'])
@admin_required
def adicionar_equipamento_idf(id):
    """Adiciona um equipamento ao IDF"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        idfs = _json_read_table(db_file, 'idfs')
        if not any(i.get('id') == id for i in idfs):
            return jsonify({'status': 'erro', 'mensagem': 'IDF não encontrado'}), 404
        ie = _json_read_table(db_file, 'idf_equipamentos')
        if any(x.get('idf_id') == id and x.get('equipamento_id') == dados.get('equipamento_id') for x in ie):
            return jsonify({'status': 'erro', 'mensagem': 'Equipamento já está neste IDF!'}), 400
        ie.append({
            'id': _json_next_id(ie),
            'idf_id': id,
            'equipamento_id': dados.get('equipamento_id'),
            'funcao': dados.get('funcao'),
            'posicao_rack': dados.get('posicao_rack'),
            'tipo_alocacao': dados.get('tipo_alocacao', 'exclusivo'),
            'sala_origem_id': dados.get('sala_origem_id')
        })
        _json_write_table(db_file, 'idf_equipamentos', ie)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Verificar se o IDF existe
        cur.execute('SELECT 1 FROM idfs WHERE id = ?', (id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'IDF não encontrado'}), 404
        
        # Verificar se o equipamento já está no IDF
        cur.execute('SELECT 1 FROM idf_equipamentos WHERE idf_id = ? AND equipamento_id = ?', 
                    (id, dados['equipamento_id']))
        if cur.fetchone():
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Equipamento já está neste IDF!'}), 400
        
        # Adicionar equipamento ao IDF
        cur.execute('''
            INSERT INTO idf_equipamentos (idf_id, equipamento_id, funcao, posicao_rack, tipo_alocacao, sala_origem_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            id,
            dados['equipamento_id'],
            dados.get('funcao'),
            dados.get('posicao_rack'),
            dados.get('tipo_alocacao', 'exclusivo'),
            dados.get('sala_origem_id')
        ))
        
        conn.commit()
        conn.close()
    
    # Log
    detalhes = f"Equipamento adicionado ao IDF: IDF ID={id}, Equipamento ID={dados['equipamento_id']}"
    registrar_log(session.get('username', 'desconhecido'), 'ADICIONAR_EQUIPAMENTO_IDF', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok'})

@app.route('/idfs/<int:id>/equipamentos-disponiveis', methods=['GET'])
@login_required
def listar_equipamentos_disponiveis_idf(id):
    """Lista equipamentos disponíveis para adicionar ao IDF"""
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        ie = [x.get('equipamento_id') for x in _json_read_table(db_file, 'idf_equipamentos') if x.get('idf_id') == id]
        equipamentos = _json_read_table(db_file, 'equipamentos')
        salas = {s.get('id'): s for s in _json_read_table(db_file, 'salas')}
        disponiveis = []
        for e in equipamentos:
            if e.get('id') in ie:
                continue
            disponiveis.append({
                'id': e.get('id'),
                'nome': e.get('nome'),
                'tipo': e.get('tipo'),
                'marca': e.get('marca'),
                'modelo': e.get('modelo'),
                'sala_id': e.get('sala_id'),
                'sala_nome': (salas.get(e.get('sala_id')) or {}).get('nome') if e.get('sala_id') else None,
                'tipo_disponivel': 'exclusivo' if e.get('sala_id') is None else 'sala'
            })
        disponiveis.sort(key=lambda x: x.get('nome') or '')
        return jsonify(disponiveis)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        try:
            # Buscar equipamentos que já estão no IDF
            cur.execute('SELECT equipamento_id FROM idf_equipamentos WHERE idf_id = ?', (id,))
            equipamentos_no_idf = [row[0] for row in cur.fetchall()]
            
            # Buscar todos os equipamentos (exclusivos e de salas)
            cur.execute('''
                SELECT e.id, e.nome, e.tipo, e.marca, e.modelo, e.sala_id, s.nome as sala_nome
                FROM equipamentos e
                LEFT JOIN salas s ON e.sala_id = s.id
                WHERE e.id NOT IN ({})
                ORDER BY e.nome
            '''.format(','.join('?' * len(equipamentos_no_idf))), equipamentos_no_idf)
            
            equipamentos = []
            for row in cur.fetchall():
                equipamento = {
                    'id': row[0],
                    'nome': row[1],
                    'tipo': row[2],
                    'marca': row[3],
                    'modelo': row[4],
                    'sala_id': row[5],
                    'sala_nome': row[6],
                    'tipo_disponivel': 'exclusivo' if row[5] is None else 'sala'
                }
                equipamentos.append(equipamento)
            
            return jsonify(equipamentos)
            
        except Exception as e:
            return jsonify({'erro': f'Erro ao listar equipamentos disponíveis: {str(e)}'}), 500
        
        finally:
            conn.close()

@app.route('/idfs/<int:id>/conexoes-salas', methods=['POST'])
@admin_required
def adicionar_conexao_sala_idf(id):
    """Adiciona uma conexão entre IDF e sala"""
    dados = request.json
    if not dados:
        return jsonify({'status': 'erro', 'mensagem': 'JSON ausente ou inválido'}), 400
    
    db_file = session.get('db')
    if not db_file:
        return jsonify({'erro': 'Nenhuma empresa selecionada!'}), 400
    
    if _is_json_mode(db_file):
        isc = _json_read_table(db_file, 'idf_sala_conexoes')
        if any(x.get('idf_id') == id and x.get('sala_id') == dados.get('sala_id') for x in isc):
            return jsonify({'status': 'erro', 'mensagem': 'Já existe conexão entre este IDF e esta sala!'}), 400
        isc.append({
            'id': _json_next_id(isc),
            'idf_id': id,
            'sala_id': dados.get('sala_id'),
            'tipo_conexao': dados.get('tipo_conexao'),
            'capacidade': dados.get('capacidade'),
            'status': dados.get('status', 'ativo')
        })
        _json_write_table(db_file, 'idf_sala_conexoes', isc)
    else:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        
        # Verificar se já existe conexão
        cur.execute('SELECT 1 FROM idf_sala_conexoes WHERE idf_id = ? AND sala_id = ?', 
                    (id, dados['sala_id']))
        if cur.fetchone():
            conn.close()
            return jsonify({'status': 'erro', 'mensagem': 'Já existe conexão entre este IDF e esta sala!'}), 400
        
        # Criar conexão
        cur.execute('''
            INSERT INTO idf_sala_conexoes (idf_id, sala_id, tipo_conexao, capacidade, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            id,
            dados['sala_id'],
            dados.get('tipo_conexao'),
            dados.get('capacidade'),
            dados.get('status', 'ativo')
        ))
        
        conn.commit()
        conn.close()
    
    # Log
    detalhes = f"Conexão IDF-Sala criada: IDF ID={id}, Sala ID={dados['sala_id']}"
    registrar_log(session.get('username', 'desconhecido'), 'CRIAR_CONEXAO_IDF_SALA', detalhes, 'sucesso', db_file)
    
    return jsonify({'status': 'ok'})

# --- ROTAS PARA PÁGINAS HTML DOS IDFs ---

@app.route('/gerenciar-idfs.html')
@admin_required
def gerenciar_idfs_html():
    return send_file('gerenciar-idfs.html')

@app.route('/detalhes-idf.html')
@login_required
def detalhes_idf_html():
    return send_file('detalhes-idf.html')

@app.route('/gerenciar-equipamentos-idf.html')
@admin_required
def gerenciar_equipamentos_idf_html():
    return send_file('gerenciar-equipamentos-idf.html')

@app.route('/editar-idf.html')
@admin_required
def editar_idf_html():
    return send_file('editar-idf.html')

@app.route('/adicionar-idf.html')
@admin_required
def adicionar_idf_html():
    return send_file('adicionar-idf.html')

@app.route('/andares', methods=['GET'])
@login_required
def listar_andares():
    """Lista todos os andares (0 a 199)"""
    # Retornar lista simples de andares de 0 a 199
    andares = []
    for i in range(200):  # 0 a 199
        if i == 0:
            titulo = "Térreo"
        else:
            titulo = f"{i}º Andar"
        
        andar = {
            'id': i,
            'titulo': titulo
        }
        andares.append(andar)
    
    return jsonify(andares)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
