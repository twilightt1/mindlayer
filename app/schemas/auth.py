from __future__ import annotations
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


class _EmailNormalizingModel(BaseModel):
    """Base for requests carrying an ``email`` field.

    ``EmailStr`` only normalizes the domain part, so ``User@x.com`` and
    ``user@x.com`` would be treated as different accounts (the users table has
    a unique index on the raw string). We lowercase the whole address at the
    boundary so storage and lookups are consistent everywhere.
    """

    @field_validator("email", check_fields=False)
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v


class RegisterRequest(_EmailNormalizingModel):
    email:    EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    message: str


class OTPVerifyRequest(_EmailNormalizingModel):
    email:    EmailStr
    otp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class OTPVerifyResponse(BaseModel):
    message:      str
    access_token: str
    next:         str = "onboarding"


class ResendVerificationRequest(_EmailNormalizingModel):
    email: EmailStr


class OnboardingRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=50)


class OnboardingResponse(BaseModel):
    access_token:  str
    refresh_token: str
    user:          "UserResponse"


class LoginRequest(_EmailNormalizingModel):
    email:    EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          "UserResponse"


class ForgotPasswordRequest(_EmailNormalizingModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ForgotPasswordOTPVerifyRequest(_EmailNormalizingModel):
    email:    EmailStr
    otp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ForgotPasswordOTPVerifyResponse(BaseModel):
    reset_token: str
    message:     str


class ResetPasswordRequest(BaseModel):
    token:        str
    new_password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id:              UUID
    email:           str
    display_name:    str | None
    avatar_url:      str | None
    auth_provider:   str
    role:            str
    is_active:       bool = True
    is_deleted:      bool = False
    is_verified:     bool
    onboarding_done: bool
    created_at:      datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=50)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password:     str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_differ(self) -> "ChangePasswordRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must differ from current password.")
        return self


class ChangePasswordResponse(BaseModel):
    message: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=32)


class AuthRedirectExchangeRequest(BaseModel):
    code: str = Field(min_length=32)
