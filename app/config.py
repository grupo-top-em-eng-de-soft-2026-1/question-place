# app/config.py

import os

import boto3
import dotenv
from fastapi.templating import Jinja2Templates

dotenv.load_dotenv()

# AWS

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

AWS_RDS_DATABASE_URL = os.getenv("AWS_RDS_DATABASE_URL", "")

AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")

# JWT

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# TEMPLATER

templater = Jinja2Templates(directory="templates")

# S3

s3 = boto3.client("s3", region_name=AWS_REGION)
