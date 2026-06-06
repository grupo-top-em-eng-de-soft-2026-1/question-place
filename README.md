<div align="center">
  <img src="docs/assets/book-icon-with-background.png" width="300" alt="Ícone do Question Place" />
</div>

<h1 align="center">Question Place</h1>

Aplicação web de aprendizagem ativa construída com FastAPI. A versão atual
implementa cadastro, autenticação JWT, consulta e edição de perfil e envio de
foto de perfil para o Amazon S3.

## Funcionamento

O FastAPI entrega as páginas HTML e também expõe a API consumida pelo
JavaScript dessas páginas. Os dados de usuário são persistidos com SQLAlchemy:

- localmente, em um banco SQLite criado no arquivo `question_place.db`;
- na AWS, em um banco PostgreSQL no Amazon RDS;
- as fotos de perfil são enviadas ao Amazon S3;
- o token JWT é armazenado pelo navegador em `localStorage` e enviado como
  `Bearer Token` nas rotas protegidas.

Mais detalhes:

- [Estrutura do projeto](docs/project-structure.md)
- [Configuração e variáveis de ambiente](docs/config.md)
- [Rotas e fluxo da aplicação](docs/routes.md)
- [Modelos do banco](docs/models.md)
- [Schemas da API](docs/schemas.md)
- [Serviços](docs/services.md)

## Rodar localmente com Docker

### Requisitos

- Docker Engine
- Docker Compose

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Ou use o script auxiliar:

```bash
sudo bash scripts/local-docker-up.sh
```

A aplicação ficará disponível em:

- aplicação: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

O container usa `ENV=local`, SQLite e a porta `8000`. O diretório do projeto é
montado em `/question_place`, portanto o banco local é criado na raiz do
repositório e permanece disponível após a remoção do container.

Para encerrar:

```bash
docker compose down
```

Ou:

```bash
sudo bash scripts/local-docker-down.sh
```

### Upload para o S3 no ambiente local

As telas, o cadastro, o login e a edição dos dados do perfil funcionam
localmente com SQLite. O envio de foto usa o bucket S3 configurado no
`Dockerfile` e exige credenciais AWS válidas dentro do container.

Sem credenciais AWS, somente a operação de upload falhará. Para testar essa
integração localmente, forneça credenciais ao container por um método seguro,
como um perfil AWS montado em modo somente leitura ou variáveis de ambiente
temporárias. Não grave chaves no `Dockerfile`, no Compose ou no repositório.

## Rodar na AWS

A implantação atual executa o Uvicorn em uma instância EC2, acessa PostgreSQL
no RDS e armazena imagens no S3.

### Requisitos na EC2

- código do projeto disponível na instância;
- Python 3 e suporte a ambientes virtuais;
- dependências instaladas em `venv`;
- acesso de rede da EC2 ao endpoint privado do RDS na porta `5432`;
- uma IAM Role associada à EC2 com permissão de `s3:PutObject` no bucket;
- entrada HTTP liberada para a instância, conforme a configuração de rede.

Para preparar o ambiente virtual:

```bash
bash scripts/aws-install-venv.sh
bash scripts/init-venv-and-install-requirements.sh
```

Na raiz do projeto, inicie a aplicação:

```bash
sudo ENV=test \
AWS_REGION=us-east-1 \
DATABASE_URL='postgresql://postgres:SENHA@ENDPOINT-RDS:5432/question_place_db' \
AWS_S3_BUCKET_NAME=question-place-storage \
JWT_SECRET_KEY='SEGREDO-FORTE-E-ALEATORIO' \
JWT_ALGORITHM=HS256 \
JWT_EXPIRE_MINUTES=120 \
AWS_S3_PUBLIC_BASE_URL='https://question-place-storage.s3.us-east-1.amazonaws.com' \
./venv/bin/uvicorn app.server:app --host 0.0.0.0 --port 80
```

O nome correto da variável do banco é `DATABASE_URL`. A aplicação não lê
`AWS_RDS_DATABASE_URL`.

O valor `ENV=test` mantém `/docs`, `/redoc` e `/openapi.json` desativados. No
código atual, essas rotas são habilitadas somente com `ENV=local`.

O comando acima ocupa o terminal e encerra quando a sessão ou o processo
termina. Para uma implantação permanente, o processo deve ser administrado por
um serviço da instância, como `systemd`, com os segredos fora do repositório.

## Variáveis principais

| Variável | Uso |
| --- | --- |
| `ENV` | Controla a exposição da documentação da API |
| `DATABASE_URL` | URL de conexão usada pelo SQLAlchemy |
| `AWS_REGION` | Região do cliente S3 |
| `AWS_S3_BUCKET_NAME` | Bucket usado para fotos de perfil |
| `AWS_S3_PUBLIC_BASE_URL` | Base da URL pública das imagens |
| `JWT_SECRET_KEY` | Segredo usado para assinar os tokens |
| `JWT_ALGORITHM` | Algoritmo de assinatura JWT |
| `JWT_EXPIRE_MINUTES` | Duração do token em minutos |

Consulte [docs/config.md](docs/config.md) para os padrões e os efeitos de cada
configuração.

## Tecnologias

- Python 3
- FastAPI e Uvicorn
- SQLAlchemy
- Pydantic
- Jinja2
- PostgreSQL e SQLite
- Amazon EC2, RDS e S3
- Docker e Docker Compose

## Desenvolvedores

- [Jaime Gabriel Alves Pereira](https://github.com/JaimeGAlves/)
- [João Gabriel Freitas Cavalcante](https://github.com/joeCavZero/)
- [João Victor Cruz Silva](https://github.com/joaocruzs/)
- [Leticia Lopes de Oliveira](https://github.com/oliveiraleticialopes/)
- [Rayanne Ellen Lopes Figueiredo](https://github.com/RayanneLps/)
