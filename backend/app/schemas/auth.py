from pydantic import EmailStr, Field

from app.schemas.common import APIModel, CountryCode, SupportedLanguage


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    preferred_language: SupportedLanguage = "ru"
    country_code: CountryCode | None = None


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class DemoLoginRequest(APIModel):
    preferred_language: SupportedLanguage = "ru"


class UserResponse(APIModel):
    id: str
    email: str
    preferred_language: SupportedLanguage
    country_code: str | None
    is_admin: bool


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
