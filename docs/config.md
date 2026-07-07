# Configuração

As configurações da aplicação são carregadas em `app/config.py` no momento em
que o processo Python é iniciado. Alterações nas variáveis de ambiente exigem
reiniciar o Uvicorn.

## Ambientes

A variável `ENV` controla somente a exposição da documentação automática do
FastAPI.

| Valor | Swagger `/docs` | ReDoc `/redoc` | OpenAPI |
| --- | --- | --- | --- |
| `local` | habilitado | habilitado | `/openapi.json` |
| `prod` | desabilitado | desabilitado | desabilitado |
| `test` | desabilitado | desabilitado | desabilitado |
| outro valor | desabilitado | desabilitado | desabilitado |

O valor padrão é `prod`. Embora `test` não apareça como um caso explícito no
`match`, ele conserva os valores iniciais, que deixam a documentação
desabilitada.

## Banco de dados

`DATABASE_URL` é repassada diretamente ao `create_engine` do SQLAlchemy.

Exemplo local:

```text
sqlite:///./question_place.db
```

Exemplo para PostgreSQL:

```text
postgresql://USUARIO:SENHA@HOST:5432/NOME_DO_BANCO
```

A variável é obrigatória fora da imagem Docker. Se estiver ausente, o valor
padrão é uma string vazia e a criação do engine falha durante a inicialização.

Ao iniciar a aplicação, `Base.metadata.create_all(bind=engine)` cria as tabelas
que ainda não existem. O projeto não possui ferramenta de migrations, portanto
alterações futuras em tabelas existentes não são aplicadas automaticamente.

## Amazon S3

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `AWS_REGION` | `us-east-1` | Região usada pelo cliente Boto3 |
| `AWS_S3_BUCKET_NAME` | vazio | Bucket que recebe fotos e mídias |
| `AWS_S3_PUBLIC_BASE_URL` | URL calculada | Configuração legada, não usada pela foto protegida |
| `AWS_S3_MEDIA_PREFIX` | `media` | Prefixo das mídias da biblioteca |
| `AWS_S3_USE_PRESIGNED_URLS` | `true` | Redireciona conteúdo para URL S3 temporária |
| `AWS_S3_PRESIGNED_EXPIRES_SECONDS` | `3600` | Validade da URL temporária, em segundos |
| `MEDIA_TEMP_PATH` | `/tmp/question_place_media` | Área local descartável de processamento |
| `MAX_UPLOAD_SIZE_MB` | `500` | Limite de upload por arquivo |
| `PROFILE_IMAGE_MAX_SIZE_MB` | `10` | Limite da foto de perfil |

Quando `AWS_S3_PUBLIC_BASE_URL` não é informada, o valor é montado como:

```text
https://<bucket>.s3.<região>.amazonaws.com
```

O cliente Boto3 usa a cadeia padrão de credenciais da AWS. Na EC2, o método
recomendado é associar uma IAM Role à instância. O processo precisa de
`s3:PutObject`, `s3:GetObject` e `s3:DeleteObject` nos prefixos usados e de
`s3:ListBucket` limitado ao bucket.

Os objetos da biblioteca permanecem privados. Suas respostas expõem somente
rotas protegidas da API. Por padrão, depois de validar o JWT e a propriedade da
mídia, essas rotas geram redirects para URLs pré-assinadas. Se essa opção for
desativada, a API faz streaming do objeto. O bucket deve ter CORS compatível
com a origem da aplicação para que o frontend use redirects pré-assinados.

A foto de perfil não usa URL pública nem redirect. A rota autenticada
`/users/me/profile-image` faz streaming do objeto S3, e o schema de usuário
expõe somente esse caminho interno.

`MEDIA_TEMP_PATH` não é armazenamento definitivo: recebe apenas arquivos em
processamento e cada diretório de upload é apagado ao final, inclusive em caso
de erro. Original, thumbnail e variantes concluídas ficam no S3.

## JWT

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `JWT_SECRET_KEY` | vazio | Assina e valida tokens |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT |
| `JWT_EXPIRE_MINUTES` | `60` | Tempo de validade do token |

`JWT_SECRET_KEY` deve ser longa, aleatória e diferente entre ambientes. Um
segredo vazio permite iniciar a aplicação, mas não é uma configuração aceitável
para um ambiente compartilhado ou público.

## Valores fornecidos pela imagem Docker

O `Dockerfile` define o ambiente local:

```text
ENV=local
DATABASE_URL=sqlite:///./question_place.db
JWT_SECRET_KEY=dev-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=
AWS_S3_MEDIA_PREFIX=media
AWS_S3_USE_PRESIGNED_URLS=true
AWS_S3_PRESIGNED_EXPIRES_SECONDS=3600
MEDIA_TEMP_PATH=/tmp/question_place_media
```

Esses valores são adequados apenas para desenvolvimento. Variáveis fornecidas
ao executar o container substituem os valores da imagem.

## Segredos

O arquivo `.env` não é copiado para a imagem e está ignorado pelo Git. Ainda
assim, a aplicação não carrega esse arquivo explicitamente; as variáveis devem
estar presentes no ambiente do processo.

Não registre no repositório:

- senha do RDS;
- `JWT_SECRET_KEY` de ambientes remotos;
- access key e secret key da AWS;
- tokens ou URLs que contenham credenciais.
