from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = Field(default="en", max_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    preferred_language: str
    phone_number: str | None = None

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    preferred_language: str | None = Field(default=None, max_length=10)
    phone_number: str | None = Field(default=None, max_length=20)
