from flask import Flask, render_template, request, jsonify, Response
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = 'database.db'

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
    data_str = agora.strftime('%Y-%m-%d')
    hora_str = agora.strftime('%H:%M:%S')
    dia_semana = agora.strftime('%A')

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO feedbacks (grau, data, hora, dia_semana) VALUES (?, ?, ?, ?)',
        (grau, data_str, hora_str, dia_semana)
    )
    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Obrigado pelo seu feedback!'})


# --- Área Administrativa ---
ADMIN_URL = '/admin_001'
ADMIN_PASSWORD = '1234'  # opcional

@app.route(f'{ADMIN_URL}')
def admin():
    # opcional: senha simples
    senha = request.args.get('senha')
    if senha != ADMIN_PASSWORD:
        return "Acesso negado. Coloque ?senha=1234 na URL.", 401

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
                           total=total)


# --- Exportação ---
@app.route('/exportar/<formato>')
def exportar(formato):
    conn = get_db_connection()
    dados = conn.execute('SELECT * FROM feedbacks').fetchall()
    conn.close()

    if formato == 'csv':
        output = "id,grau,data,hora,dia_semana\n"
        for row in dados:
            output += f"{row['id']},{row['grau']},{row['data']},{row['hora']},{row['dia_semana']}\n"
        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=feedbacks.csv"})
    elif formato == 'txt':
        output = "\n".join([f"{row['id']} | {row['grau']} | {row['data']} {row['hora']} | {row['dia_semana']}" for row in dados])
        return Response(output, mimetype="text/plain",
                        headers={"Content-Disposition": "attachment;filename=feedbacks.txt"})
    else:
        return "Formato inválido.", 400


if __name__ == '__main__':
    app.run(debug=True)
