import os

import boto3
from fastapi.templating import Jinja2Templates


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

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
    case "local":
        ENV_DOCS_URL = "/docs"
        ENV_REDOC_URL = "/redoc"
        ENV_OPENAPI_URL = "/openapi.json"

# DATABASE AND STORAGE

DATABASE_URL = os.getenv("DATABASE_URL", "")

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
MEDIA_TEMP_PATH = os.getenv("MEDIA_TEMP_PATH", "/tmp/question_place_media")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")
AWS_S3_MEDIA_PREFIX = os.getenv("AWS_S3_MEDIA_PREFIX", "media").strip("/")
AWS_S3_USE_PRESIGNED_URLS = env_bool("AWS_S3_USE_PRESIGNED_URLS", True)
AWS_S3_PRESIGNED_EXPIRES_SECONDS = int(os.getenv("AWS_S3_PRESIGNED_EXPIRES_SECONDS", "3600"))

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
