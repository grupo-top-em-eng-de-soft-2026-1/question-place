from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

import app.config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(data: dict) -> str:
    payload = data.copy()

    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=app.config.JWT_EXPIRE_MINUTES
    )

    return jwt.encode(
        payload, app.config.JWT_SECRET_KEY, algorithm=app.config.JWT_ALGORITHM
    )
