from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
import sqlite3
from datetime import datetime
import os
from flask_socketio import SocketIO, emit

app = Flask(__name__)

# SocketIO para tempo real
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DATABASE = 'database.db'

# secret key para sessões (em produção usar var de ambiente)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'troque_esta_chave_para_producao')

# --- Função para criar/conectar banco ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grau TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            dia_semana TEXT NOT NULL
        )
    ''')
    # tabela de administradores
    conn.execute('''
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
            conn.execute('INSERT OR IGNORE INTO admins (username, senha) VALUES (?, ?)', (u, p))
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
    conn.execute(
        'INSERT INTO feedbacks (grau, data, hora, dia_semana) VALUES (?, ?, ?, ?)',
        (grau, data_str, hora_str, dia_semana)
    )
    conn.commit()
    # obter dados recém-inseridos (último id)
    cur = conn.execute('SELECT * FROM feedbacks ORDER BY id DESC LIMIT 1')
    new_row = cur.fetchone()

    # atualizar contagens e emitir evento para clientes conectados
    total_muito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Muito satisfeito'").fetchone()[0]
    total_satisfeito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Satisfeito'").fetchone()[0]
    total_insatisfeito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Insatisfeito'").fetchone()[0]

    conn.close()

    # emitir evento de novo feedback e estatísticas atualizadas
    try:
        socketio.emit('new_feedback', dict(new_row), broadcast=True)
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
    registros = conn.execute('SELECT * FROM feedbacks ORDER BY data DESC, hora DESC').fetchall()

    # contagem por grau
    total_muito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Muito satisfeito'").fetchone()[0]
    total_satisfeito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Satisfeito'").fetchone()[0]
    total_insatisfeito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Insatisfeito'").fetchone()[0]
    total = total_muito + total_satisfeito + total_insatisfeito

    conn.close()

    return render_template('admin.html', registros=registros,
                           total_muito=total_muito,
                           total_satisfeito=total_satisfeito,
                           total_insatisfeito=total_insatisfeito,
                           total=total,
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
    row = conn.execute('SELECT * FROM admins WHERE username = ? AND senha = ?', (username, senha)).fetchone()
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
    dados = conn.execute('SELECT * FROM feedbacks').fetchall()
    conn.close()

    if formato == 'csv':
        # usar csv module para garantir colunas separadas corretamente e escape
        import io, csv
        sio = io.StringIO()
        writer = csv.writer(sio)
        writer.writerow(['id', 'grau', 'data', 'hora', 'dia_semana'])
        for row in dados:
            writer.writerow([row['id'], row['grau'], row['data'], row['hora'], row['dia_semana']])
        output = sio.getvalue()
        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=feedbacks.csv"})
    elif formato == 'txt':
        output = "\n".join([f"{row['id']} | {row['grau']} | {row['data']} {row['hora']} | {row['dia_semana']}" for row in dados])
        return Response(output, mimetype="text/plain",
                        headers={"Content-Disposition": "attachment;filename=feedbacks.txt"})
    else:
        return "Formato inválido.", 400


# enviar estado inicial quando um cliente conectar
@socketio.on('connect')
def handle_connect():
    try:
        conn = get_db_connection()
        total_muito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Muito satisfeito'").fetchone()[0]
        total_satisfeito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Satisfeito'").fetchone()[0]
        total_insatisfeito = conn.execute("SELECT COUNT(*) FROM feedbacks WHERE grau='Insatisfeito'").fetchone()[0]
        latest = conn.execute('SELECT * FROM feedbacks ORDER BY id DESC LIMIT 10').fetchall()
        conn.close()
        emit('init', {
            'total_muito': total_muito,
            'total_satisfeito': total_satisfeito,
            'total_insatisfeito': total_insatisfeito,
            'latest': [dict(r) for r in latest]
        })
    except Exception:
        pass


if __name__ == '__main__':
    socketio.run(app, debug=True)
