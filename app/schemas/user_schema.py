from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator

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


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
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
    profile_picture_s3_key: str | None

    @computed_field
    @property
    def profile_picture_url(self) -> str | None:
        if not self.profile_picture_s3_key:
            return None

        return f"{app.config.AWS_S3_PUBLIC_BASE_URL}/{self.profile_picture_s3_key}"

    class Config:
        from_attributes = True
