import logging
from pathlib import Path
from uuid import uuid4

from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile

import app.config

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

logger = logging.getLogger(__name__)


def _bucket() -> str:
    if not app.config.AWS_S3_BUCKET_NAME:
        raise HTTPException(503, "Armazenamento de objetos não configurado")
    return app.config.AWS_S3_BUCKET_NAME


def _service_error(action: str, exc: Exception) -> HTTPException:
    logger.exception("Falha do S3 durante %s", action)
    return HTTPException(503, "O armazenamento de objetos está temporariamente indisponível")


def upload_file(local_path: str | Path, key: str, content_type: str | None = None) -> None:
    extra_args = {"ContentType": content_type} if content_type else None
    try:
        app.config.s3.upload_file(
            str(local_path), _bucket(), key,
            ExtraArgs=extra_args,
        )
    except (BotoCoreError, ClientError, S3UploadFailedError, OSError) as exc:
        raise _service_error("upload de arquivo", exc) from exc


def upload_bytes(data: bytes, key: str, content_type: str | None = None) -> None:
    kwargs = {"Bucket": _bucket(), "Key": key, "Body": data}
    if content_type:
        kwargs["ContentType"] = content_type
    try:
        app.config.s3.put_object(**kwargs)
    except (BotoCoreError, ClientError) as exc:
        raise _service_error("upload de bytes", exc) from exc


def download_file(key: str, local_path: str | Path) -> None:
    try:
        app.config.s3.download_file(_bucket(), key, str(local_path))
    except (BotoCoreError, ClientError, OSError) as exc:
        raise _service_error("download", exc) from exc


def get_object_stream(key: str) -> dict:
    try:
        return app.config.s3.get_object(Bucket=_bucket(), Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise _service_error("leitura", exc) from exc


def delete_object(key: str) -> None:
    try:
        app.config.s3.delete_object(Bucket=_bucket(), Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise _service_error("exclusão", exc) from exc


def delete_objects(keys: list[str]) -> None:
    unique_keys = list(dict.fromkeys(key for key in keys if key))
    if not unique_keys:
        return
    try:
        for start in range(0, len(unique_keys), 1000):
            response = app.config.s3.delete_objects(
                Bucket=_bucket(),
                Delete={"Objects": [{"Key": key} for key in unique_keys[start:start + 1000]], "Quiet": True},
            )
            if response.get("Errors"):
                raise RuntimeError("S3 retornou falha ao excluir um ou mais objetos")
    except (BotoCoreError, ClientError, RuntimeError) as exc:
        raise _service_error("exclusão em lote", exc) from exc


def create_presigned_url(key: str, expires_seconds: int | None = None) -> str:
    try:
        return app.config.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": _bucket(), "Key": key},
            ExpiresIn=expires_seconds or app.config.AWS_S3_PRESIGNED_EXPIRES_SECONDS,
        )
    except (BotoCoreError, ClientError) as exc:
        raise _service_error("geração de URL temporária", exc) from exc


def object_exists(key: str) -> bool:
    try:
        app.config.s3.head_object(Bucket=_bucket(), Key=key)
        return True
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = exc.response.get("Error", {}).get("Code")
        if status == 404 or code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise _service_error("verificação de objeto", exc) from exc
    except BotoCoreError as exc:
        raise _service_error("verificação de objeto", exc) from exc


async def upload_profile_picture(file: UploadFile, user_id: int) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Use JPG, PNG ou WEBP.",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]

    s3_key = f"profile-images/users/{user_id}/{uuid4()}{extension}"

    content = await file.read()

    upload_bytes(content, s3_key, file.content_type)

    return s3_key
