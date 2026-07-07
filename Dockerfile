FROM python:3.14-slim

WORKDIR /question_place

# ---- ENVS ----

ENV ENV=local
ENV DATABASE_URL=sqlite:///./question_place.db

ENV JWT_SECRET_KEY=dev-secret
ENV JWT_ALGORITHM=HS256
ENV JWT_EXPIRE_MINUTES=120

ENV AWS_REGION=us-east-1
ENV AWS_S3_BUCKET_NAME=""
ENV AWS_S3_MEDIA_PREFIX=media
ENV AWS_S3_USE_PRESIGNED_URLS=true
ENV AWS_S3_PRESIGNED_EXPIRES_SECONDS=3600
ENV MEDIA_TEMP_PATH=/tmp/question_place_media

# --------

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
