# Mais Que Café

Aplicação web acadêmica para consulta e cadastro de clientes e produtos, criação de pedidos com vários itens e relatórios de vendas.

## Tecnologias

- Python e Flask
- HTML e CSS
- PostgreSQL para a versão web
- SQL Server continua sendo usado pela versão desktop original

## Executar a versão web

Na pasta raiz do projeto, instale as dependências:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

Defina `DATABASE_URL` para apontar a um PostgreSQL e então execute:

~~~powershell
.\.venv\Scripts\python.exe .\web\app.py
~~~

Abra http://127.0.0.1:5000 no navegador.

## Estrutura PostgreSQL

- `web/schema_postgres.sql`: cria as tabelas e os relacionamentos.
- `web/criar_banco.py`: executa o script de criação no banco indicado por `DATABASE_URL`.
- `web/conexao.py`: abre a conexão PostgreSQL usando `DATABASE_URL`.

## Publicação acadêmica temporária

O `requirements.txt` fica na raiz do repositório. No Render, configure a raiz do serviço como a raiz do repositório, o comando de instalação como `pip install -r requirements.txt` e o comando de início como `gunicorn --chdir web app:app`. Cadastre a variável privada `DATABASE_URL` usando a URL interna do PostgreSQL do Render.

Os planos gratuitos do Render são adequados para demonstração, mas têm limites: o banco gratuito expira 30 dias após a criação e o serviço web pode dormir quando fica sem acesso. Planeje a data de criação do banco em relação ao prazo do tutor e exporte os dados antes do vencimento.

Não publique credenciais, `.env`, `.venv`, documentos da faculdade ou dados pessoais reais.
