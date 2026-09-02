"""Auth endpoints — register, verify, login, Google OAuth, forgot password."""
from __future__ import annotations

import json
import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.rate_limiter import check_rate_limit
from app.redis_client import get_redis
from app.schemas.auth import (
    AuthRedirectExchangeRequest,
    ForgotPasswordOTPVerifyRequest,
    ForgotPasswordOTPVerifyResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    OnboardingRequest,
    OnboardingResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserResponse,
)
from app.services import auth_service
from app.services.oauth_service import google_oauth
from app.utils.dependencies import get_current_user
from app.utils.security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
log    = logging.getLogger(__name__)



@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):

    await check_rate_limit(f"ip:{request.client.host}", window_seconds=60, limit=5)
    await auth_service.register_email(db, body.email, body.password)
    return RegisterResponse(message="Registration successful. Check your email for a verification code.")



@router.post("/verify-email/otp", response_model=OTPVerifyResponse)
async def verify_email_otp(body: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    user  = await auth_service.verify_email_otp(db, body.email, body.otp_code)
    token = create_access_token(
        {"sub": str(user.id), "role": user.role, "scope": "onboarding"},
        expire_minutes=30,
    )
    return OTPVerifyResponse(message="Email verified.", access_token=token)



@router.get("/verify-email/link")
async def verify_email_link(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.verify_email_link(db, token)
    except HTTPException:
        return RedirectResponse(f"{settings.FRONTEND_URL}/verify-email?error=invalid_token")

    access = create_access_token(
        {"sub": str(user.id), "role": user.role, "scope": "onboarding"},
        expire_minutes=30,
    )
    redis = await get_redis()
    exchange_code = secrets.token_urlsafe(32)
    await redis.setex(
        f"auth_exchange:{exchange_code}",
        120,
        json.dumps({"access_token": access, "refresh_token": None, "next": "onboarding"}),
    )
    return RedirectResponse(f"{settings.FRONTEND_URL}/onboarding?code={exchange_code}")



@router.post("/verify-email/resend", status_code=200)
async def resend_verification(body: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.resend_verification(db, body.email)
    return {"message": "If the account exists and is unverified, a new code has been sent."}



@router.post("/onboarding", response_model=OnboardingResponse)
async def onboarding(
    body: OnboardingRequest,
    response: Response,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user, access, refresh = await auth_service.complete_onboarding(db, current_user, body.display_name)
    _set_refresh_cookie(response, refresh)
    return OnboardingResponse(
        access_token=access,
        refresh_token=None,
        user=UserResponse.model_validate(user),
    )



@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):

    await check_rate_limit(f"ip:{request.client.host}", window_seconds=60, limit=10)
    user, access, refresh = await auth_service.login_email(db, body.email, body.password)
    _set_refresh_cookie(response, refresh)
    # Body no longer carries the refresh token (XSS cannot read httpOnly
    # cookies); the schema keeps the field optional for non-browser clients.
    return LoginResponse(
        access_token=access,
        refresh_token=None,
        user=UserResponse.model_validate(user),
    )



@router.get("/google/authorize")
async def google_authorize():
    redis = await get_redis()
    url, state = google_oauth.create_authorization_url()
    await redis.setex(f"oauth_state:{state}", 300, "1")
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code:  str       = Query(...),
    state: str       = Query(...),
    error: str|None  = Query(None),
    db:    AsyncSession = Depends(get_db),
):
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=google_cancelled")

    redis  = await get_redis()
    cached = await redis.get(f"oauth_state:{state}")
    if not cached:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=invalid_state")
    await redis.delete(f"oauth_state:{state}")

    try:
        info = await google_oauth.exchange_code(code)
    except Exception as e:
        log.error("Google exchange failed", extra={"error": str(e)})
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=google_failed")

    try:
        user = await auth_service.find_or_create_google_user(db, info)
    except HTTPException as e:
        if e.status_code == 409:
            return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=email_already_registered")
        raise

    expire_min = 30 if not user.onboarding_done else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    scope      = "onboarding" if not user.onboarding_done else "full"
    access     = create_access_token({"sub": str(user.id), "role": user.role, "scope": scope},
                                      expire_minutes=expire_min)
    refresh    = None if not user.onboarding_done else await auth_service._create_refresh(user.id)
    dest       = "/onboarding" if not user.onboarding_done else "/chat"
    exchange_code = secrets.token_urlsafe(32)
    await redis.setex(
        f"auth_exchange:{exchange_code}",
        120,
        json.dumps({"access_token": access, "refresh_token": refresh, "next": dest.lstrip("/")}),
    )
    return RedirectResponse(f"{settings.FRONTEND_URL}{dest}?code={exchange_code}")


@router.post("/exchange-code")
async def exchange_auth_code(body: AuthRedirectExchangeRequest):
    redis = await get_redis()
    payload = await redis.get(f"auth_exchange:{body.code}")
    if not payload:
        raise HTTPException(400, detail="Authorization code invalid or expired.")
    await redis.delete(f"auth_exchange:{body.code}")
    return json.loads(payload)



# Refresh token lives in an httpOnly cookie so XSS cannot exfiltrate a
# long-lived credential. Path is scoped to the auth surface; SameSite=strict
# keeps it off cross-site requests (frontend and API are same-site: ports do
# not affect site origin).
REFRESH_COOKIE = "orivory_refresh"


def _refresh_cookie_max_age() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=_refresh_cookie_max_age(),
        httponly=True,
        secure=settings.ENVIRONMENT.lower() in ("production", "prod", "staging"),
        samesite="strict",
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")


def _extract_refresh_token(body: "RefreshTokenRequest | None", request: Request) -> str | None:
    """Prefer the httpOnly cookie; fall back to body for non-cookie clients."""
    cookie = request.cookies.get(REFRESH_COOKIE)
    if cookie:
        return cookie
    if body is not None and body.refresh_token:
        return body.refresh_token
    return None


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
):
    token = _extract_refresh_token(body, request)
    if not token or len(token) < 32:
        raise HTTPException(401, detail="Refresh token invalid or expired.")
    redis = await get_redis()
    token_hash = auth_service._hash_refresh_token(token)
    user_id_b = await redis.get(f"refresh:{token_hash}")
    if not user_id_b:
        raise HTTPException(401, detail="Refresh token invalid or expired.")

    user_id = user_id_b.decode("utf-8") if isinstance(user_id_b, bytes) else user_id_b
    # Remove the old (now-hashed) token before issuing a new one. The
    # rotation also drops the entry from the per-user index on the
    # ``_create_refresh`` side via SADD overwrite semantics — the old
    # hash simply expires with the old key.
    await redis.delete(f"refresh:{token_hash}")
    await redis.srem(f"refresh_user:{user_id}", token_hash)

    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.user import User
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.id == user_id))

    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(401, detail="Account not found.")

    new_access  = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh = await auth_service._create_refresh(user.id)
    # Rotate the cookie: the response body intentionally omits the refresh
    # token so a script-injected XSS cannot read a long-lived credential.
    _set_refresh_cookie(response, new_refresh)
    return {"access_token": new_access, "token_type": "bearer"}



@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    response: Response,
    body: LogoutRequest | None = None,
    current_user=Depends(get_current_user),
):
    redis = await get_redis()
    # Revoke the refresh token from the httpOnly cookie or the legacy body.
    refresh_to_revoke = _extract_refresh_token(body, request)
    if refresh_to_revoke:
        await auth_service._invalidate_one_refresh(refresh_to_revoke)
    _clear_refresh_cookie(response)


    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = decode_access_token(token)
            jti = payload.get("jti")
            if jti:
                # Blacklist for exactly the token's remaining lifetime. The
                # token scope ("onboarding" = 30 min) can outlive the default
                # ACCESS_TOKEN_EXPIRE_MINUTES, so deriving TTL from the
                # default would let a logged-out token come back to life.
                exp = int(payload.get("exp", 0))
                remaining = max(exp - int(datetime.now(UTC).timestamp()), 1)
                await redis.setex(f"blacklist:{jti}", remaining, "1")
        except Exception as e:
            log.warning(f"Failed to blacklist access token during logout: {e}")

    return {"message": "Logged out successfully."}



@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.create_password_reset_session(db, body.email)
    return ForgotPasswordResponse(
        message="If the account exists, you will receive password reset instructions."
    )


@router.post("/forgot-password/verify-otp", response_model=ForgotPasswordOTPVerifyResponse)
async def forgot_password_verify_otp(
    body: ForgotPasswordOTPVerifyRequest,
    db:   AsyncSession = Depends(get_db),
):
    reset_token = await auth_service.verify_reset_otp(db, body.email, body.otp_code)
    return ForgotPasswordOTPVerifyResponse(
        reset_token=reset_token,
        message="OTP verified. Please set your new password.",
    )


@router.get("/forgot-password/verify-link")
async def forgot_password_verify_link(
    token: str = Query(...),
    db:    AsyncSession = Depends(get_db),
):
    try:
        reset_token = await auth_service.verify_reset_link(db, token)
    except HTTPException:
        return RedirectResponse(f"{settings.FRONTEND_URL}/forgot-password?error=invalid_token")
    return RedirectResponse(f"{settings.FRONTEND_URL}/reset-password?token={reset_token}")


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, body.token, body.new_password)
    return ResetPasswordResponse(message="Password reset successfully. Please log in.")
