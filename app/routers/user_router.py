from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserResponse
from app.services.jwt_service import get_current_user
from app.services.s3_service import upload_profile_picture

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.post("/me/profile-picture", response_model=UserResponse)
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
