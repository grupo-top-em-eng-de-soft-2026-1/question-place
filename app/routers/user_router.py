import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserResponse, UserUpdate
from app.services.jwt_service import get_current_user
from app.services.s3_service import delete_object, get_object_stream, upload_profile_picture
from app.services.security_service import hash_password

user_router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@user_router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.get("/me/profile-image")
def profile_image(current_user: User = Depends(get_current_user)):
    if not current_user.profile_picture_s3_key:
        raise HTTPException(404, "Foto de perfil não encontrada")

    obj = get_object_stream(current_user.profile_picture_s3_key)
    headers = {"Cache-Control": "private, no-store"}
    if obj.get("ContentLength") is not None:
        headers["Content-Length"] = str(obj["ContentLength"])
    return StreamingResponse(
        obj["Body"].iter_chunks(),
        media_type=obj.get("ContentType") or "application/octet-stream",
        headers=headers,
    )


@user_router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    changes = payload.model_dump(exclude_unset=True)

    required_fields = {"full_name", "username", "email"}

    if any(changes.get(field) is None for field in required_fields & changes.keys()):
        raise HTTPException(
            status_code=422,
            detail="Nome, username e email não podem ser nulos",
        )

    if "username" in changes:
        username_exists = (
            db.query(User)
            .filter(
                User.username == changes["username"],
                User.id != current_user.id,
            )
            .first()
        )

        if username_exists:
            raise HTTPException(status_code=400, detail="Username already exists")

    if "email" in changes:
        email_exists = (
            db.query(User)
            .filter(
                User.email == changes["email"],
                User.id != current_user.id,
            )
            .first()
        )

        if email_exists:
            raise HTTPException(status_code=400, detail="Email already exists")

    password = changes.pop("password", None)

    for field, value in changes.items():
        setattr(current_user, field, value)

    if password is not None:
        current_user.password_hash = hash_password(password)

    db.commit()
    db.refresh(current_user)

    return current_user


@user_router.post("/me/upload-profile-picture", response_model=UserResponse)
async def upload_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s3_key = await upload_profile_picture(file=file, user_id=current_user.id)
    old_key = current_user.profile_picture_s3_key
    current_user.profile_picture_s3_key = s3_key
    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        try:
            delete_object(s3_key)
        except HTTPException:
            logger.exception("Não foi possível limpar nova foto após falha no banco")
        raise
    if old_key:
        try:
            delete_object(old_key)
        except HTTPException:
            logger.exception("Não foi possível remover a foto de perfil anterior")

    return current_user
