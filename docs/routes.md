# Rotas e fluxos

## Páginas HTML

| Método | Rota | Template | Finalidade |
| --- | --- | --- | --- |
| GET | `/` | `index.html` | Página inicial |
| GET | `/login` | `login.html` | Formulário de login |
| GET | `/register` | `register.html` | Formulário de cadastro |
| GET | `/me` | `me.html` | Exibição do perfil |
| GET | `/me/edit` | `edit_profile.html` | Edição do perfil |
| GET | `/library` | `library.html` | Biblioteca multimídia privada |

As páginas são renderizadas sem dados de usuário. Login, cadastro e perfil usam
`fetch` no navegador para chamar a API.

## Autenticação

### `POST /auth/register`

Cria um usuário depois de verificar se `username` e `email` já existem. A senha
é armazenada como hash bcrypt.

Respostas principais:

- `200`: usuário criado;
- `400`: username ou e-mail já cadastrado;
- `422`: corpo inválido.

### `POST /auth/login`

Valida username e senha e retorna:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Credenciais inválidas recebem `401`. A tela salva o token em `localStorage`.

## Usuário autenticado

Todas as rotas abaixo exigem `Authorization: Bearer <token>`.

### `GET /users/me`

Retorna o perfil do usuário identificado pela claim `sub` do JWT.

### `PATCH /users/me`

Atualiza parcialmente nome, username, e-mail, senha e descrição. Username e
e-mail continuam sujeitos à unicidade. Quando enviada, a nova senha é
armazenada como hash bcrypt.

### `POST /users/me/upload-profile-picture`

Recebe `multipart/form-data` com um campo `file`, envia a imagem ao S3 e grava
a chave no usuário.

Formatos aceitos:

- JPEG;
- PNG;
- WEBP.

## Fluxo de cadastro e login

1. O navegador envia os dados para `/auth/register`.
2. A aplicação grava o usuário no banco.
3. O usuário acessa `/login`.
4. O navegador envia username e senha para `/auth/login`.
5. A API devolve um JWT.
6. O navegador salva o token em `localStorage` e abre `/me`.
7. A tela consulta `/users/me` com o cabeçalho de autorização.

## Biblioteca multimídia

As rotas `POST /media`, `GET /media`, `GET/PATCH/DELETE /media/{id}` e
`PUT /media/{id}/content` mantêm o CRUD privado por usuário. Original,
thumbnail e variantes ficam no S3; o banco recebe somente metadados e keys.

`GET /media/{id}/content` aceita `quality=1080p`, `720p` ou `480p`, e
`GET /media/{id}/thumbnail` entrega a miniatura. Ambas validam JWT e propriedade
antes de gerar redirect pré-assinado ou streaming. As respostas de listagem e
detalhe expõem essas rotas da API, nunca uma key ou URL pública direta do S3.

## Fluxo de edição e imagem

1. `/me/edit` carrega os dados com `GET /users/me`.
2. Ao salvar, a página chama `PATCH /users/me`.
3. Se um arquivo foi selecionado, chama também a rota de upload.
4. O backend envia o objeto ao S3 e persiste sua chave no banco.
5. A página `/me` recebe `profile_picture_url` e a usa no elemento de imagem.

## Documentação automática

Com `ENV=local`, o FastAPI também expõe:

| Rota | Conteúdo |
| --- | --- |
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | Especificação OpenAPI |

Nos demais ambientes, essas rotas ficam desativadas.
