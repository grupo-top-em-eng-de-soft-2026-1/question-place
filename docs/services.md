# Serviços

Os serviços em `app/services` concentram regras que são usadas pelos routers.

## Segurança de senha e criação de token

Arquivo: `app/services/security_service.py`.

### `hash_password`

Recebe a senha em texto e retorna um hash bcrypt por meio do `passlib`. A senha
original não é armazenada.

### `verify_password`

Compara a senha informada no login com o hash persistido no banco.

### `create_access_token`

Copia os dados recebidos, inclui a claim `exp` e assina o JWT com:

- `JWT_SECRET_KEY`;
- `JWT_ALGORITHM`;
- validade definida por `JWT_EXPIRE_MINUTES`.

No login, o payload contém:

```json
{
  "sub": "1",
  "username": "maria",
  "exp": "definido durante a emissão"
}
```

O identificador em `sub` é gravado como string.

## Autenticação da requisição

Arquivo: `app/services/jwt_service.py`.

`OAuth2PasswordBearer` procura o token no cabeçalho:

```http
Authorization: Bearer <token>
```

A dependência `get_current_user`:

1. decodifica e valida o JWT;
2. lê a claim `sub`;
3. converte o identificador para inteiro;
4. consulta o usuário no banco;
5. retorna HTTP `401` quando o token ou o usuário não são válidos.

O `tokenUrl` informado ao OpenAPI é `/auth/login`. Apesar da convenção OAuth2,
essa rota recebe JSON, e não formulário `application/x-www-form-urlencoded`.

## Upload de foto

Arquivo: `app/services/s3_service.py`.

`upload_profile_picture` aceita:

| Content-Type | Extensão salva |
| --- | --- |
| `image/jpeg` | `.jpg` |
| `image/png` | `.png` |
| `image/webp` | `.webp` |

Outros tipos recebem HTTP `400`.

A chave segue o formato:

```text
profile-images/users/<user_id>/<uuid>.<extensão>
```

O arquivo inteiro é lido em memória e enviado com `put_object`. A versão atual
não impõe limite de tamanho, não inspeciona o conteúdo real do arquivo e não
remove a imagem anterior quando uma nova foto é enviada.

Depois do upload, a rota salva a chave no campo
`profile_picture_s3_key`. A URL pública é calculada pelo `UserResponse`.
