<div align="center">
  <img src="docs/assets/book-icon-with-background.png" width="300" alt="Ícone do Question Place" />
</div>

<h1 align="center">Question Place</h1>

Aplicação web em FastAPI para gerenciamento privado de imagens, áudios e vídeos.
Implementa autenticação JWT, perfis, upload, metadados, thumbnails, versões de
vídeo, busca, filtros e CRUD completo de objetos multimídia.

## Recursos do Question Place

- biblioteca isolada por usuário, com busca por nome, descrição e tags;
- imagens JPG, PNG, GIF, SVG e WebP, com thumbnail e metadados/EXIF;
- áudios MP3, WAV, OGG e FLAC, com metadados técnicos;
- vídeos MP4, AVI, MOV e WebM, com thumbnail e versões 1080p, 720p e 480p;
- reprodução protegida por JWT e escolha da qualidade do vídeo;
- edição, substituição do conteúdo e exclusão.

## Funcionamento

O FastAPI entrega as páginas HTML e também expõe a API consumida pelo
JavaScript dessas páginas. Os dados de usuário são persistidos com SQLAlchemy:

- localmente, em um banco SQLite criado no arquivo `question_place.db`;
- em produção, em um banco PostgreSQL no Amazon RDS;
- fotos de perfil e todos os objetos da biblioteca são enviados ao Amazon S3;
- o disco local é usado somente como área temporária durante validação,
  extração de metadados, criação de thumbnails e transcodificação;
- o token JWT é armazenado pelo navegador em `localStorage` e enviado como
  `Bearer Token` nas rotas protegidas.

No upload de mídia, a aplicação cria um diretório descartável em
`MEDIA_TEMP_PATH`, processa o arquivo com Pillow ou FFmpeg, envia original,
thumbnail e variantes ao S3 e remove o diretório mesmo se ocorrer erro. O banco
guarda apenas metadados e chaves S3. Downloads continuam protegidos pelas rotas
`/media`: depois de validar o proprietário, a API redireciona para uma URL S3
pré-assinada de curta duração (ou faz streaming quando essa opção é desativada).

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
- FFmpeg/ffprobe (instalado automaticamente pelo Docker)

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
repositório e permanece disponível após a remoção do container. O Compose
inicia somente a aplicação: ele **não cria nem emula AWS, S3 ou RDS**.

Para encerrar:

```bash
docker compose down
```

Ou:

```bash
sudo bash scripts/local-docker-down.sh
```

### S3 no ambiente local

As telas, o cadastro, o login e a edição dos dados do perfil funcionam
localmente com SQLite. Uploads de foto e da biblioteca exigem um bucket S3 e
credenciais AWS válidas dentro do container. Defina ao menos
`AWS_S3_BUCKET_NAME` antes de iniciar o Compose.

Sem credenciais AWS, somente a operação de upload falhará. Para testar essa
integração localmente, forneça credenciais ao container por um método seguro,
como um perfil AWS montado em modo somente leitura ou variáveis de ambiente
temporárias. Não grave chaves no `Dockerfile`, no Compose ou no repositório.

O bucket deve permitir CORS para a origem local quando
`AWS_S3_USE_PRESIGNED_URLS=true`, pois o navegador segue o redirect assinado
para carregar thumbnails e conteúdo. LocalStack e MinIO não fazem parte deste
Compose; podem ser adicionados futuramente como alternativa de desenvolvimento.

## Rodar na AWS

A arquitetura de produção executa o Uvicorn em instâncias EC2, acessa
PostgreSQL no RDS e armazena todos os binários no S3. As instâncias devem ficar
em um Auto Scaling Group atrás de um Application Load Balancer. Como banco e
objetos são compartilhados, qualquer instância pode atender uma requisição sem
depender do disco de outra instância.

### Requisitos na EC2

- código do projeto disponível na instância;
- Python 3 e suporte a ambientes virtuais;
- dependências instaladas em `venv`;
- acesso de rede da EC2 ao endpoint privado do RDS na porta `5432`;
- uma IAM Role associada às instâncias com permissões `s3:PutObject`,
  `s3:GetObject`, `s3:DeleteObject` e `s3:ListBucket` limitadas ao bucket/prefixo;
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
AWS_S3_MEDIA_PREFIX=media \
AWS_S3_USE_PRESIGNED_URLS=true \
AWS_S3_PRESIGNED_EXPIRES_SECONDS=3600 \
MEDIA_TEMP_PATH=/tmp/question_place_media \
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
termina. Para uma implantação permanente, use uma AMI/Launch Template e um
serviço como `systemd`, mantenha segredos no Secrets Manager ou Parameter Store,
e associe a IAM Role ao Launch Template. Não configure access key e secret key
nas instâncias.

O diretório em `MEDIA_TEMP_PATH` precisa apenas de espaço para processar uma
mídia e suas variantes. Ele não é persistente: todos os artefatos concluídos
ficam no S3 e os diretórios temporários são apagados após cada operação.

## Variáveis principais

| Variável | Uso |
| --- | --- |
| `ENV` | Controla a exposição da documentação da API |
| `DATABASE_URL` | URL de conexão usada pelo SQLAlchemy |
| `AWS_REGION` | Região do cliente S3 |
| `AWS_S3_BUCKET_NAME` | Bucket usado por fotos e mídias da biblioteca |
| `AWS_S3_PUBLIC_BASE_URL` | Base das fotos quando URLs pré-assinadas estão desativadas |
| `AWS_S3_MEDIA_PREFIX` | Prefixo das mídias da biblioteca no bucket |
| `AWS_S3_USE_PRESIGNED_URLS` | Usa redirects temporários para objetos privados |
| `AWS_S3_PRESIGNED_EXPIRES_SECONDS` | Validade das URLs pré-assinadas |
| `MEDIA_TEMP_PATH` | Diretório local descartável usado no processamento |
| `MAX_UPLOAD_SIZE_MB` | Limite de cada upload (padrão: 500 MB) |
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
