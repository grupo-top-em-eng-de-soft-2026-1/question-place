from pydantic import BaseModel, EmailStr, computed_field

import app.config


class UserCreate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str
    description: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr
    description: str | None
    profile_picture_s3_key: str | None

    @computed_field
    @property
    def profile_picture_url(self) -> str | None:
        if not self.profile_picture_s3_key:
            return None

        return f"{app.config.AWS_S3_PUBLIC_BASE_URL}/{self.profile_picture_s3_key}"

    class Config:
        from_attributes = True
