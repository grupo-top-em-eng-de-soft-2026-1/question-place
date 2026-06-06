from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserResponse, UserUpdate
from app.services.jwt_service import get_current_user
from app.services.s3_service import upload_profile_picture

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


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

    for field, value in changes.items():
        setattr(current_user, field, value)

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

    current_user.profile_picture_s3_key = s3_key

    db.commit()
    db.refresh(current_user)

    return current_user
