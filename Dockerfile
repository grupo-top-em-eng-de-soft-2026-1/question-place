FROM python:3.14-slim

WORKDIR /question_place

# ---- ENVS ----

ENV ENV=local
ENV DATABASE_URL=sqlite:///./question_place.db

ENV JWT_SECRET_KEY=dev-secret
ENV JWT_ALGORITHM=HS256
ENV JWT_EXPIRE_MINUTES=120

ENV AWS_REGION=us-east-1
ENV AWS_S3_BUCKET_NAME=question-place-storage
ENV AWS_S3_PUBLIC_BASE_URL=https://question-place-storage.s3.us-east-1.amazonaws.com

# --------

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]