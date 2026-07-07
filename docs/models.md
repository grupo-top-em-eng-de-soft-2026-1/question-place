# Modelos do banco

Os modelos SQLAlchemy ficam em `app/models`.

## `users`

Representada pela classe `User` em `app/models/user.py`.

| Coluna | Tipo | Restrições | Uso |
| --- | --- | --- | --- |
| `id` | Integer | chave primária, índice | Identificador do usuário |
| `full_name` | String(255) | obrigatório | Nome completo |
| `username` | String(50) | único, índice, obrigatório | Identificação usada no login |
| `email` | String(255) | único, índice, obrigatório | E-mail do usuário |
| `password_hash` | String(255) | obrigatório | Hash bcrypt da senha |
| `description` | Text | opcional | Texto do perfil |
| `profile_picture_s3_key` | String(512) | opcional | Chave do objeto salvo no S3 |
| `created_at` | DateTime com timezone | obrigatório, padrão do servidor | Data de criação |

A senha original não é persistida. Durante o cadastro, ela passa pelo
`hash_password` antes da criação do registro.

`profile_picture_s3_key` armazena somente uma chave semelhante a:

```text
profile-images/users/42/550e8400-e29b-41d4-a716-446655440000.jpg
```

A URL é pré-assinada por padrão. Se esse recurso for desativado, a URL completa
é calculada usando `AWS_S3_PUBLIC_BASE_URL`.

## `media_objects`

Representada por `MediaObject` em `app/models/media.py`. Mantém proprietário,
nome, tipo, tamanho, descrição, tags, gênero e metadados técnicos. Os campos
`storage_key`, `thumbnail_key` e `versions_json` contêm somente chaves privadas
do S3, por exemplo:

```text
media/users/42/<uuid>/original.mp4
media/users/42/<uuid>/thumbnail.jpg
media/users/42/<uuid>/variants/720p.mp4
```

Nenhum caminho absoluto ou binário é salvo no banco.

## Criação das tabelas

Na inicialização, `app/server.py` executa:

```python
Base.metadata.create_all(bind=engine)
```

Isso cria tabelas ausentes tanto no SQLite quanto no PostgreSQL. O mecanismo
não substitui migrations: ele não renomeia colunas, não altera tipos e não
remove estruturas antigas.

## Sessões

`app/database.py` cria uma `SessionLocal` ligada ao engine. As rotas recebem
uma sessão por meio da dependência `get_db`, que garante o fechamento ao fim da
requisição.

Cadastro, atualização de perfil e gravação da chave do S3 executam `commit` e
`refresh` explicitamente.
