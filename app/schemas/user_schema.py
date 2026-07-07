from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str
    description: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=1)
    description: str | None = None

    @field_validator("full_name", "username")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be blank")

        return value


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr
    description: str | None
    profile_picture_url: str | None = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def protected_profile_picture_url(cls, value):
        if isinstance(value, dict):
            data = dict(value)
            if "profile_picture_s3_key" in data:
                key = data.pop("profile_picture_s3_key")
                data["profile_picture_url"] = "/users/me/profile-image" if key else None
            return data
        return {
            "id": value.id,
            "full_name": value.full_name,
            "username": value.username,
            "email": value.email,
            "description": value.description,
            "created_at": value.created_at,
            "profile_picture_url": "/users/me/profile-image"
            if value.profile_picture_s3_key else None,
        }

    class Config:
        from_attributes = True
