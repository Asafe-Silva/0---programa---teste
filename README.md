
# Sistema de Feedback (Satisfação)

Este projeto é uma pequena aplicação web para coletar feedback de satisfação dos usuários e visualizar estatísticas em uma área administrativa com atualizações em tempo real.

**O que o programa faz**: - Coleta avaliações de usuários ("Muito satisfeito", "Satisfeito", "Insatisfeito") através da interface pública; - Armazena registros em um banco SQLite (`database.db`) ou em um banco online via `DATABASE_URL` (PostgreSQL); - Exibe estatísticas, insights e histórico em uma área administrativa protegida por sessão; - Permite exportar os dados em `CSV`, `TXT` ou `JSON`.

**Requisitos**
- **Python 3.8+** (recomendado)
- Dependências listadas em `requirements.txt`

**Instalação**
1. Clone ou copie o projeto para sua máquina.
2. Crie e ative um ambiente virtual (opcional, recomendado):

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate    # Windows (PowerShell)
```

3. Instale dependências:

```bash
pip install -r requirements.txt
```

**Executando a aplicação**

```bash
python ãpp.py
```

Por padrão a aplicação roda em `http://127.0.0.1:5000` com `debug=True`.

**Interface pública**
- A página inicial (`/`) apresenta três botões com opções de satisfação.
- Quando o usuário clica num botão, o navegador envia uma requisição `POST` para `/registrar` com JSON `{ "grau": "Satisfeito" }`.
- O servidor salva o registro com data, hora e dia da semana.

Exemplo (curl):

```bash
curl -X POST http://127.0.0.1:5000/registrar \
	-H "Content-Type: application/json" \
	-d '{"grau":"Muito satisfeito"}'
```

**Área administrativa**
- URL: `/admin`
- Acesso via modal de login na página inicial (usuários predefinidos no banco).
- Exibe:
	- Contagem de cada nível de satisfação e percentuais
	- Gráfico de barras (Chart.js)
	- Insights rápidos (dia mais ativo e último feedback)
	- Tabela com histórico (id, grau, data, hora, dia da semana)
	- Links para exportar: `/exportar/csv`, `/exportar/txt` e `/exportar/json`

**Rotas principais**
- `GET /` — página pública de coleta de feedback.
- `POST /registrar` — registra um feedback (JSON: `{ "grau": "..." }`).
- `POST /login` — autenticação administrativa.
- `GET /admin` — painel administrativo (restrito por sessão).
- `GET /exportar/csv` — baixa todos os registros em CSV.
- `GET /exportar/txt` — baixa todos os registros em TXT.
- `GET /exportar/json` — baixa todos os registros em JSON.
- `GET /api/feedbacks` — lista registros em JSON para análises externas.
- `GET /api/stats` — resumo estatístico em JSON.

**Banco de dados**
- Local: `database.db` (SQLite) na raiz do projeto.
- Online: configure `DATABASE_URL` com uma URL PostgreSQL (ex.: `postgresql://usuario:senha@host:5432/db`).
- Tabela: `feedbacks` com colunas:
	- `id` INTEGER PRIMARY KEY AUTOINCREMENT
	- `grau` TEXT
	- `data` TEXT (DD/MM/AAAA)
	- `hora` TEXT (HH:MM:SS)
	- `dia_semana` TEXT

**Personalização rápida**
- Para trocar administradores, edite a lista `admins_pre` em `ãpp.py` ou crie usuários diretamente no banco.
- Para desativar `debug` edite o bloco `if __name__ == '__main__':` e passe `debug=False`.

**Arquivos importantes**
- [ãpp.py](ãpp.py) — backend principal (Flask + SQLite/PostgreSQL)
- [requirements.txt](requirements.txt) — dependências
- [templates/index.html](templates/index.html) — interface pública
- [templates/admin.html](templates/admin.html) — área administrativa
- [templates/layout.html](templates/layout.html) — layout comum
- [static/js/main.js](static/js/main.js) — scripts cliente
- [static/css/style.css](static/css/style.css) — estilos

**Próximos passos recomendados**
- Guardar senhas com hash (bcrypt/argon2) e permitir reset seguro.
- Proteger endpoints com HTTPS em produção.

---
Atualizado automaticamente com um resumo e manual de uso.
