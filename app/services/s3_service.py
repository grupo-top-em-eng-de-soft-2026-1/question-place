from fastapi import UploadFile

import app.config


async def upload_profile_picture(file: UploadFile, user_id: int) -> str:
    extension = file.filename.split(".")[-1]

    s3_key = f"users/{user_id}/profile_picture.{extension}"

    content = await file.read()

    app.config.s3.put_object(
        Bucket=app.config.AWS_S3_BUCKET_NAME,
        Key=s3_key,
        Body=content,
        ContentType=file.content_type,
    )

    return s3_key
