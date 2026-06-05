from pydantic import BaseModel, EmailStr


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

    class Config:
        from_attributes = True
