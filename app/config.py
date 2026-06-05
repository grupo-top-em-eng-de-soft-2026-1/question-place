import os

import boto3
import dotenv
from fastapi.templating import Jinja2Templates

dotenv.load_dotenv()

AWS_RDS_DATABASE_URL = os.getenv("AWS_RDS_DATABASE_URL")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

templater = Jinja2Templates(directory="templates")

s3 = boto3.client("s3", region_name="us-east-1")
