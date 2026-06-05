from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

import app.config

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def upload_profile_picture(file: UploadFile, user_id: int) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Use JPG, PNG ou WEBP.",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]

    s3_key = f"profile-images/users/{user_id}/{uuid4()}{extension}"

    content = await file.read()

    app.config.s3.put_object(
        Bucket=app.config.AWS_S3_BUCKET_NAME,
        Key=s3_key,
        Body=content,
        ContentType=file.content_type,
    )

    return s3_key
