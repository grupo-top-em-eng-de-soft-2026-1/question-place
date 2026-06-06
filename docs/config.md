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
| `AWS_S3_BUCKET_NAME` | vazio | Bucket que recebe as imagens |
| `AWS_S3_PUBLIC_BASE_URL` | URL calculada | Prefixo público retornado pela API |

Quando `AWS_S3_PUBLIC_BASE_URL` não é informada, o valor é montado como:

```text
https://<bucket>.s3.<região>.amazonaws.com
```

O cliente Boto3 usa a cadeia padrão de credenciais da AWS. Na EC2, o método
recomendado é associar uma IAM Role à instância. O processo precisa, no mínimo,
de permissão para executar `s3:PutObject` no prefixo
`profile-images/users/*`.

A aplicação não gera URLs assinadas. A URL da imagem é formada concatenando a
base pública e a chave armazenada no banco, portanto os objetos precisam ser
legíveis pelo navegador por meio da política adotada no bucket ou por uma
camada pública equivalente.

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
AWS_S3_BUCKET_NAME=question-place-storage
AWS_S3_PUBLIC_BASE_URL=https://question-place-storage.s3.us-east-1.amazonaws.com
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
