# Twitter Clone

Clone simplificado do Twitter: uma rede social de microblog com API REST em
**Django + Django REST Framework** e um front-end em HTML, CSS e JavaScript
puro, servido pelo próprio Django (projeto monolítico).

## Funcionalidades

- **Cadastro e login** com senha validada e guardada com hash. A autenticação da API usa token.
- **Perfil:** o usuário pode alterar a foto, o nome e a senha. Nenhuma alteração é obrigatória: cada campo é opcional.
- **Seguir pessoas**, ver quem eu sigo (seguindo) e quem me segue (seguidores).
- **Feed de notícias** com os tweets apenas de quem o usuário segue, do mais novo ao mais antigo.
- **Tweets** de até 280 caracteres (criar, ver e apagar os próprios).
- **Curtidas e comentários** nos tweets.

## Tecnologias

- Python 3.12+ e Django 5.2+ (arquitetura REST com Django REST Framework)
- Banco de dados: SQLite (qualquer banco suportado pelo Django funciona)
- Front-end: HTML, CSS e JavaScript puro (arquivo `templates/index.html`)

## Como executar no seu computador

```bash
# 1. Crie e ative o ambiente virtual
python -m venv .venv
# Windows (PowerShell):  .\.venv\Scripts\Activate.ps1
# Linux/macOS:           source .venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Crie o banco de dados
python manage.py migrate

# 4. (opcional) Crie um administrador para usar o /admin/
python manage.py createsuperuser

# 5. Suba o servidor
python manage.py runserver
```

Abra http://127.0.0.1:8000/ no navegador, crie uma conta e use o app.
Para testar o feed, crie duas contas (uma em uma janela anônima), siga uma com a outra e tweete.

## Testes

```bash
python manage.py test
```

## Variáveis de ambiente (produção)

| Variável | Para que serve | Padrão |
|---|---|---|
| `SECRET_KEY` | chave secreta do Django | chave insegura de desenvolvimento |
| `DEBUG` | `1` liga o modo de desenvolvimento, `0` desliga | `1` |
| `ALLOWED_HOSTS` | domínios permitidos, separados por vírgula | `localhost,127.0.0.1` |

Em produção, rode também `python manage.py collectstatic` e sirva as pastas
`staticfiles/` (em `/static/`) e `media/` (em `/media/`, onde ficam as fotos de perfil).

## API

Todas as rotas ficam em `/api/`. Exceto o cadastro e o login, todas exigem o
cabeçalho `Authorization: Token <seu-token>`. As listas são paginadas (10 por página).

| Método | Rota | O que faz |
|---|---|---|
| POST | `/api/auth/register/` | Cria a conta (`username`, `password`, `name` opcional) e devolve o token |
| POST | `/api/auth/login/` | Entra (`username`, `password`) e devolve o token |
| POST | `/api/auth/logout/` | Sai (apaga o token) |
| GET | `/api/me/` | Dados do usuário logado |
| PATCH | `/api/me/` | Altera `name`, `avatar` (arquivo), `remove_avatar` e a senha (`current_password` + `new_password`). Tudo opcional |
| GET | `/api/users/?q=` | Lista e busca usuários |
| GET | `/api/users/<username>/` | Perfil de um usuário (com contagens e `is_following`) |
| POST / DELETE | `/api/users/<username>/follow/` | Seguir / deixar de seguir |
| GET | `/api/users/<username>/followers/` | Seguidores |
| GET | `/api/users/<username>/following/` | Quem o usuário segue |
| GET | `/api/users/<username>/tweets/` | Tweets de um usuário |
| GET | `/api/feed/` | Feed: tweets de quem eu sigo |
| POST | `/api/tweets/` | Cria um tweet (`content`, até 280 caracteres) |
| GET / DELETE | `/api/tweets/<id>/` | Vê / apaga o próprio tweet |
| POST / DELETE | `/api/tweets/<id>/like/` | Curtir / descurtir |
| GET / POST | `/api/tweets/<id>/comments/` | Lista / cria comentários |
| DELETE | `/api/comments/<id>/` | Apaga o próprio comentário |

Exemplo:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "maria", "password": "SuaSenha#2026"}'

curl http://127.0.0.1:8000/api/feed/ -H "Authorization: Token SEU_TOKEN"
```

## Estrutura

```
config/      configurações do projeto Django
accounts/    usuários, perfil (foto), cadastro, login e seguir
tweets/      tweets, curtidas, comentários e feed
templates/   front-end (index.html)
```

## Deploy

O projeto foi publicado no PythonAnywhere. Resumo: clonar o repositório,
criar o ambiente virtual, `pip install -r requirements.txt`, `python manage.py migrate`,
`python manage.py collectstatic`, configurar o arquivo WSGI com as variáveis de ambiente e
mapear `/static/` e `/media/` na aba **Web**.
