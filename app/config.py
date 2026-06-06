import os

import boto3
from fastapi.templating import Jinja2Templates

# ENV

ENV = os.getenv("ENV", "prod")

ENV_DOCS_URL = None
ENV_REDOC_URL = None
ENV_OPENAPI_URL = None

match ENV:
    case "prod":
        ENV_DOCS_URL = None
        ENV_REDOC_URL = None
        ENV_OPENAPI_URL = None
    case "test":
        ENV_DOCS_URL = "/docs"
        ENV_REDOC_URL = "/redoc"
        ENV_OPENAPI_URL = "/openapi.json"

# AWS

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

AWS_RDS_DATABASE_URL = os.getenv("AWS_RDS_DATABASE_URL", "")

AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")

AWS_S3_PUBLIC_BASE_URL = os.getenv(
    "AWS_S3_PUBLIC_BASE_URL",
    f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com",
)

# JWT

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# TEMPLATER

templater = Jinja2Templates(directory="templates")

# S3

s3 = boto3.client("s3", region_name=AWS_REGION)
