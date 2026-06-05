from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse
from app.services.security_service import (
    create_access_token,
    hash_password,
    verify_password,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=UserResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    username_exists = db.query(User).filter(User.username == payload.username).first()

    if username_exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    email_exists = db.query(User).filter(User.email == payload.email).first()

    if email_exists:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        description=payload.description,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@auth_router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token({"sub": str(user.id), "username": user.username})

    return {"access_token": access_token, "token_type": "bearer"}
