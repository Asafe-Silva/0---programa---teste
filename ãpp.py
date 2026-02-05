from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
import sqlite3
from datetime import datetime
import os
from flask_socketio import SocketIO, emit

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # fallback local
    psycopg2 = None
    RealDictCursor = None

app = Flask(__name__)

# SocketIO para tempo real
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DATABASE = 'database.db'
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()


def is_postgres():
    return DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')

# secret key para sessões (em produção usar var de ambiente)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'troque_esta_chave_para_producao')

# --- Função para criar/conectar banco ---
def get_db_connection():
    if is_postgres():
        if psycopg2 is None:
            raise RuntimeError('psycopg2 não está instalado. Instale psycopg2-binary.')
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def prepare_query(query):
    if is_postgres():
        return query.replace('?', '%s')
    return query


def execute_query(conn, query, params=None, fetchone=False, fetchall=False):
    query = prepare_query(query)
    params = params or ()
    if is_postgres():
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
            return None
    cur = conn.execute(query, params)
    if fetchone:
        return cur.fetchone()
    if fetchall:
        return cur.fetchall()
    return None


def row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)

def criar_tabela():
    conn = get_db_connection()
    if is_postgres():
        execute_query(conn, '''
            CREATE TABLE IF NOT EXISTS feedbacks (
                id SERIAL PRIMARY KEY,
                grau TEXT NOT NULL,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                dia_semana TEXT NOT NULL
            )
        ''')
        execute_query(conn, '''
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        ''')
    else:
        execute_query(conn, '''
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grau TEXT NOT NULL,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                dia_semana TEXT NOT NULL
            )
        ''')
        # tabela de administradores
        execute_query(conn, '''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        ''')
    # inserir administradores predefinidos (se não existirem)
    admins_pre = [
        ('admin_001', '1234'),
        ('admin_002', '2231'),
        ('admin_003', '4321'),
        ('admin_004', '3124'),
        ('admin_005', '3241'),
        ('admin_000', '0000')
    ]
    for u, p in admins_pre:
        try:
            if is_postgres():
                execute_query(
                    conn,
                    'INSERT INTO admins (username, senha) VALUES (?, ?) ON CONFLICT (username) DO NOTHING',
                    (u, p)
                )
            else:
                execute_query(conn, 'INSERT OR IGNORE INTO admins (username, senha) VALUES (?, ?)', (u, p))
        except Exception:
            pass
    conn.commit()
    conn.close()

criar_tabela()

# --- Interface Pública ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.get_json()
    grau = data.get('grau')

    agora = datetime.now()
    # formato solicitado: dd/mm/aaaa (dia/mês/ano com quatro dígitos)
    data_str = agora.strftime('%d/%m/%Y')
    hora_str = agora.strftime('%H:%M:%S')
    # dia da semana em português
    dias_pt = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    # weekday(): 0 = Monday
    dia_semana = dias_pt[agora.weekday()]

    conn = get_db_connection()
    execute_query(
        conn,
        'INSERT INTO feedbacks (grau, data, hora, dia_semana) VALUES (?, ?, ?, ?)',
        (grau, data_str, hora_str, dia_semana)
    )
    conn.commit()
    # obter dados recém-inseridos (último id)
    new_row = execute_query(conn, 'SELECT * FROM feedbacks ORDER BY id DESC LIMIT 1', fetchone=True)

    # atualizar contagens e emitir evento para clientes conectados
    total_muito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Muito satisfeito'",
        fetchone=True
    )['total']
    total_satisfeito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Satisfeito'",
        fetchone=True
    )['total']
    total_insatisfeito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Insatisfeito'",
        fetchone=True
    )['total']

    conn.close()

    # emitir evento de novo feedback e estatísticas atualizadas
    try:
        socketio.emit('new_feedback', row_to_dict(new_row), broadcast=True)
        socketio.emit('stats_update', {
            'total_muito': total_muito,
            'total_satisfeito': total_satisfeito,
            'total_insatisfeito': total_insatisfeito
        }, broadcast=True)
    except Exception:
        pass

    return jsonify({'mensagem': 'Obrigado pelo seu feedback!'})


# --- Área Administrativa (agora protegida por sessão) ---
@app.route('/admin')
def admin():
    # requer sessão de admin
    if 'admin_user' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    registros = execute_query(conn, 'SELECT * FROM feedbacks ORDER BY data DESC, hora DESC', fetchall=True)

    # contagem por grau
    total_muito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Muito satisfeito'",
        fetchone=True
    )['total']
    total_satisfeito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Satisfeito'",
        fetchone=True
    )['total']
    total_insatisfeito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Insatisfeito'",
        fetchone=True
    )['total']
    total = total_muito + total_satisfeito + total_insatisfeito
    percent_muito = round((total_muito / total) * 100, 2) if total else 0
    percent_satisfeito = round((total_satisfeito / total) * 100, 2) if total else 0
    percent_insatisfeito = round((total_insatisfeito / total) * 100, 2) if total else 0

    historico = [row_to_dict(r) for r in registros]
    dias_contagem = {}
    ultimo_registro = historico[0] if historico else None
    for reg in historico:
        dias_contagem[reg['dia_semana']] = dias_contagem.get(reg['dia_semana'], 0) + 1
    dia_top = max(dias_contagem, key=dias_contagem.get) if dias_contagem else 'Sem dados'
    ultimo_feedback = (
        f"{ultimo_registro['data']} {ultimo_registro['hora']}" if ultimo_registro else 'Sem registros'
    )

    conn.close()

    return render_template('admin.html', registros=registros,
                           total_muito=total_muito,
                           total_satisfeito=total_satisfeito,
                           total_insatisfeito=total_insatisfeito,
                           total=total,
                           percent_muito=percent_muito,
                           percent_satisfeito=percent_satisfeito,
                           percent_insatisfeito=percent_insatisfeito,
                           dia_top=dia_top,
                           ultimo_feedback=ultimo_feedback,
                           admin_user=session.get('admin_user'))


# rota de login para admins (usada pelo modal)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    senha = data.get('senha')
    if not username or not senha:
        return jsonify({'success': False, 'mensagem': 'Usuário ou senha ausente.'}), 400

    conn = get_db_connection()
    row = execute_query(
        conn,
        'SELECT * FROM admins WHERE username = ? AND senha = ?',
        (username, senha),
        fetchone=True
    )
    conn.close()

    if row:
        session['admin_user'] = username
        return jsonify({'success': True, 'mensagem': 'Login realizado.'})
    else:
        return jsonify({'success': False, 'mensagem': 'Usuário ou senha inválidos.'}), 401


@app.route('/logout')
def logout():
    session.pop('admin_user', None)
    return redirect(url_for('index'))


# --- Exportação ---
@app.route('/exportar/<formato>')
def exportar(formato):
    conn = get_db_connection()
    dados = execute_query(conn, 'SELECT * FROM feedbacks', fetchall=True)
    conn.close()

    if formato == 'csv':
        # usar csv module para garantir colunas separadas corretamente e escape
        import io, csv
        sio = io.StringIO()
        writer = csv.writer(sio)
        writer.writerow(['id', 'grau', 'data', 'hora', 'dia_semana'])
        for row in dados:
            row = row_to_dict(row)
            writer.writerow([row['id'], row['grau'], row['data'], row['hora'], row['dia_semana']])
        output = sio.getvalue()
        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=feedbacks.csv"})
    elif formato == 'json':
        return Response(
            jsonify([row_to_dict(r) for r in dados]).get_data(as_text=True),
            mimetype='application/json',
            headers={"Content-Disposition": "attachment;filename=feedbacks.json"}
        )
    elif formato == 'txt':
        linhas = []
        for row in dados:
            row = row_to_dict(row)
            linhas.append(
                f"{row['id']} | {row['grau']} | {row['data']} {row['hora']} | {row['dia_semana']}"
            )
        output = "\n".join(linhas)
        return Response(output, mimetype="text/plain",
                        headers={"Content-Disposition": "attachment;filename=feedbacks.txt"})
    else:
        return "Formato inválido.", 400


@app.route('/api/feedbacks')
def api_feedbacks():
    conn = get_db_connection()
    dados = execute_query(conn, 'SELECT * FROM feedbacks ORDER BY id DESC', fetchall=True)
    conn.close()
    return jsonify([row_to_dict(r) for r in dados])


@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()
    total_muito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Muito satisfeito'",
        fetchone=True
    )['total']
    total_satisfeito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Satisfeito'",
        fetchone=True
    )['total']
    total_insatisfeito = execute_query(
        conn,
        "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Insatisfeito'",
        fetchone=True
    )['total']
    registros = execute_query(conn, 'SELECT data, dia_semana FROM feedbacks', fetchall=True)
    conn.close()

    total = total_muito + total_satisfeito + total_insatisfeito
    dias_contagem = {}
    for reg in registros:
        reg = row_to_dict(reg)
        dias_contagem[reg['dia_semana']] = dias_contagem.get(reg['dia_semana'], 0) + 1
    dia_top = max(dias_contagem, key=dias_contagem.get) if dias_contagem else 'Sem dados'

    return jsonify({
        'total': total,
        'total_muito': total_muito,
        'total_satisfeito': total_satisfeito,
        'total_insatisfeito': total_insatisfeito,
        'dia_top': dia_top
    })


# enviar estado inicial quando um cliente conectar
@socketio.on('connect')
def handle_connect():
    try:
        conn = get_db_connection()
        total_muito = execute_query(
            conn,
            "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Muito satisfeito'",
            fetchone=True
        )['total']
        total_satisfeito = execute_query(
            conn,
            "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Satisfeito'",
            fetchone=True
        )['total']
        total_insatisfeito = execute_query(
            conn,
            "SELECT COUNT(*) AS total FROM feedbacks WHERE grau='Insatisfeito'",
            fetchone=True
        )['total']
        latest = execute_query(conn, 'SELECT * FROM feedbacks ORDER BY id DESC LIMIT 10', fetchall=True)
        conn.close()
        emit('init', {
            'total_muito': total_muito,
            'total_satisfeito': total_satisfeito,
            'total_insatisfeito': total_insatisfeito,
            'latest': [row_to_dict(r) for r in latest]
        })
    except Exception:
        pass


if __name__ == '__main__':
    socketio.run(app, debug=True)
