# Schemas da API

Os contratos Pydantic estão em `app/schemas/user_schema.py`.

## `UserCreate`

Entrada de `POST /auth/register`.

| Campo | Tipo | Obrigatório |
| --- | --- | --- |
| `full_name` | string | sim |
| `username` | string | sim |
| `email` | e-mail válido | sim |
| `password` | string | sim |
| `description` | string ou `null` | não |

No estado atual, esse schema não define tamanho mínimo para senha nem limites
de texto. A unicidade de `username` e `email` é verificada na rota e reforçada
pelo banco.

Exemplo:

```json
{
  "full_name": "Maria Silva",
  "username": "maria",
  "email": "maria@example.com",
  "password": "uma-senha",
  "description": "Estudante"
}
```

## `UserLogin`

Entrada de `POST /auth/login`.

```json
{
  "username": "maria",
  "password": "uma-senha"
}
```

O login usa `username`, não e-mail.

## `UserUpdate`

Entrada de `PATCH /users/me`. Todos os campos são opcionais, permitindo
atualização parcial.

| Campo | Regras |
| --- | --- |
| `full_name` | 1 a 255 caracteres após remover espaços externos |
| `username` | 1 a 50 caracteres após remover espaços externos |
| `email` | e-mail válido |
| `password` | string não vazia; é armazenada somente como hash |
| `description` | string ou `null` |

Quando enviados, `full_name`, `username` e `email` não podem ser `null`.
`description` pode ser removida com `null`.

Exemplo:

```json
{
  "full_name": "Maria de Souza",
  "description": null
}
```

## `UserResponse`

Resposta do cadastro e das rotas de usuário.

| Campo | Tipo |
| --- | --- |
| `id` | integer |
| `full_name` | string |
| `username` | string |
| `email` | e-mail |
| `description` | string ou `null` |
| `profile_picture_s3_key` | string ou `null` |
| `profile_picture_url` | string ou `null`, calculado |

Exemplo:

```json
{
  "id": 1,
  "full_name": "Maria Silva",
  "username": "maria",
  "email": "maria@example.com",
  "description": "Estudante",
  "profile_picture_s3_key": "profile-images/users/1/arquivo.jpg",
  "profile_picture_url": "https://question-place-storage.s3.us-east-1.amazonaws.com/profile-images/users/1/arquivo.jpg"
}
```

`password_hash` e `created_at` não são expostos por esse contrato.
