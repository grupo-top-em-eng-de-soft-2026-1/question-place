# Estrutura do projeto

```text
question-place/
├── app/
│   ├── models/
│   │   ├── media.py
│   │   └── user.py
│   ├── routers/
│   │   ├── auth_router.py
│   │   ├── main_router.py
│   │   ├── media_router.py
│   │   └── user_router.py
│   ├── schemas/
│   │   ├── media_schema.py
│   │   └── user_schema.py
│   ├── services/
│   │   ├── jwt_service.py
│   │   ├── media_service.py
│   │   ├── s3_service.py
│   │   └── security_service.py
│   ├── config.py
│   ├── database.py
│   └── server.py
├── docs/
├── scripts/
├── static/
│   └── css/
├── templates/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Inicialização

`app/server.py` é o ponto de entrada do ASGI:

1. importa a configuração;
2. cria as tabelas SQLAlchemy ausentes;
3. instancia o FastAPI;
4. monta arquivos estáticos em `/static`;
5. registra os routers de páginas, autenticação, usuários e mídia.

O alvo usado pelo Uvicorn é:

```text
app.server:app
```

## Camadas

### `app/config.py`

Lê variáveis de ambiente, configura as URLs da documentação, cria o renderizador
Jinja2 e inicializa o cliente S3.

### `app/database.py`

Cria o engine SQLAlchemy, a fábrica de sessões e a base declarativa dos
modelos.

### `app/models`

Define a estrutura persistida no banco: `User` e `MediaObject`. O segundo guarda
metadados e chaves S3, nunca o conteúdo binário.

### `app/schemas`

Define os contratos Pydantic de entrada e saída da API. Essa camada valida
e-mail, limites dos campos editáveis e calcula a URL pública da foto.

### `app/routers`

- `main_router.py`: entrega páginas HTML;
- `auth_router.py`: cadastro e login;
- `user_router.py`: consulta, edição e foto do usuário autenticado;
- `media_router.py`: CRUD e entrega protegida da biblioteca multimídia.

### `app/services`

Agrupa autenticação JWT, hash de senha, integração com o S3 e processamento
temporário de mídia com Pillow/FFmpeg.

### `templates`

Contém páginas Jinja2. O backend não injeta dados de usuário no HTML; o
JavaScript consulta a API depois que a página é carregada.

### `static`

Arquivos servidos diretamente pelo FastAPI. No estado atual, contém o CSS
compartilhado pelas telas de login e cadastro.

### `scripts`

Scripts auxiliares para criar o ambiente virtual na EC2 e controlar o ambiente
Docker local.

## Fluxo de uma requisição autenticada

1. O navegador lê `access_token` do `localStorage`.
2. O JavaScript envia `Authorization: Bearer <token>`.
3. `OAuth2PasswordBearer` extrai o token.
4. `get_current_user` valida assinatura e expiração.
5. O identificador presente em `sub` é consultado no banco.
6. A rota recebe o objeto `User` autenticado.

As páginas `/me` e `/me/edit` são públicas no nível HTTP. A proteção dos dados
ocorre nas chamadas à API; sem token válido, o JavaScript redireciona o
navegador para a página inicial.
