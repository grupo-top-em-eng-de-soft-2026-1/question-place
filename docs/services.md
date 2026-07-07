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

## Amazon S3

Arquivo: `app/services/s3_service.py`.

Centraliza upload de arquivo/bytes, download, streaming, exclusão individual ou
em lote, verificação de existência e geração de URL pré-assinada. Erros do
Boto3 são registrados no servidor e convertidos em respostas controladas sem
expor detalhes do bucket ou das credenciais.

O cliente usa a cadeia padrão de credenciais da AWS; em produção, as
credenciais devem vir da IAM Role da EC2.

### Upload de foto

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
`profile_picture_s3_key`. Por padrão, `UserResponse` gera uma URL pré-assinada.

## Processamento de mídia

Arquivo: `app/services/media_service.py`.

Cada upload é salvo em um subdiretório temporário de `MEDIA_TEMP_PATH`. Pillow
valida imagens e cria thumbnails; FFmpeg/ffprobe extrai metadados, cria a
thumbnail de vídeo e gera variantes H.264/AAC em 1080p, 720p e 480p com
`faststart`. Em seguida, original e derivados são enviados ao prefixo
`AWS_S3_MEDIA_PREFIX` no S3.

O resultado contém somente metadados e chaves S3. O diretório temporário é
apagado automaticamente. Se um upload de múltiplos artefatos falhar no meio, o
serviço tenta excluir do S3 os objetos que já foram enviados.
