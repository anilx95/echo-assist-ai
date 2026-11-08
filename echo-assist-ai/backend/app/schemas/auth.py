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


class ProfileResponse(UserResponse):
    role: str
    is_verified: bool
    profile_photo_url: str | None = None
    date_of_birth: str | None = None
    address: str | None = None
    medical_accessibility_preferences: str | None = None


class ProfileUpdateRequest(UserUpdateRequest):
    profile_photo_url: str | None = Field(default=None, max_length=500)
    date_of_birth: str | None = None
    address: str | None = Field(default=None, max_length=5000)
    medical_accessibility_preferences: str | None = Field(default=None, max_length=5000)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1)


class MessageResponse(BaseModel):
    detail: str
