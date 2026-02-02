
# Sistema de Feedback (Satisfação)

Este projeto é uma pequena aplicação web para coletar feedback de satisfação dos usuários e visualizar estatísticas em uma área administrativa.

**O que o programa faz**: - Coleta avaliações de usuários ("Muito satisfeito", "Satisfeito", "Insatisfeito") através da interface pública; - Armazena registros em um banco SQLite (`database.db`); - Exibe estatísticas e histórico na área administrativa protegida por senha simples; - Permite exportar os dados em `CSV` ou `TXT`.

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
- URL: `/admin_001`
- Acesso simples por query param: `?senha=1234`
- Exibe:
	- Contagem de cada nível de satisfação
	- Gráfico de barras (Chart.js)
	- Tabela com histórico (id, grau, data, hora, dia da semana)
	- Links para exportar: `/exportar/csv` e `/exportar/txt`

Segurança: atualmente a senha administrativa está definida em código em `ãpp.py` como `ADMIN_PASSWORD = '1234'`. Troque por uma senha mais forte ou implemente autenticação adequada antes de usar em produção.

**Rotas principais**
- `GET /` — página pública de coleta de feedback.
- `POST /registrar` — registra um feedback (JSON: `{ "grau": "..." }`).
- `GET /admin_001?senha=...` — painel administrativo (restrito por senha simples).
- `GET /exportar/csv` — baixa todos os registros em CSV.
- `GET /exportar/txt` — baixa todos os registros em TXT.

**Banco de dados**
- Arquivo: `database.db` (SQLite) na raiz do projeto.
- Tabela: `feedbacks` com colunas:
	- `id` INTEGER PRIMARY KEY AUTOINCREMENT
	- `grau` TEXT
	- `data` TEXT (YYYY-MM-DD)
	- `hora` TEXT (HH:MM:SS)
	- `dia_semana` TEXT

**Personalização rápida**
- Para mudar a URL administrativa altere a constante `ADMIN_URL` em `ãpp.py`.
- Para trocar a senha altere `ADMIN_PASSWORD` em `ãpp.py`.
- Para desativar `debug` edite o bloco `if __name__ == '__main__':` e passe `debug=False`.

**Arquivos importantes**
- [ãpp.py](ãpp.py) — backend principal (Flask + SQLite)
- [requirements.txt](requirements.txt) — dependências
- [templates/index.html](templates/index.html) — interface pública
- [templates/admin.html](templates/admin.html) — área administrativa
- [templates/layout.html](templates/layout.html) — layout comum
- [static/js/main.js](static/js/main.js) — scripts cliente
- [static/css/style.css](static/css/style.css) — estilos

**Próximos passos recomendados**
- Substituir a autenticação administrativa por um sistema baseado em sessões ou variáveis de ambiente.
- Mover a senha para variável de ambiente (ex.: `ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD')`).
- Proteger endpoints com HTTPS em produção.

---
Atualizado automaticamente com um resumo e manual de uso.
