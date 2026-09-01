from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.redis_client import get_redis
from app.utils.security import decode_access_token

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT + blacklist check. No verified/onboarding requirement."""
    token   = credentials.credentials
    payload = decode_access_token(token)

    jti = payload.get("jti")
    if jti:
        redis = await get_redis()
        if await redis.get(f"blacklist:{jti}"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")

    user = await db.scalar(select(User).where(User.id == payload["sub"]))
    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Account not found.")
    return user


async def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Email not verified.")
    return current_user


async def get_current_active_user(current_user: User = Depends(get_current_verified_user)) -> User:
    if not current_user.onboarding_done:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Please complete account setup.")
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user


async def enforce_llm_quota(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Rate limit + quota guard for endpoints that trigger LLM/embedding spend.

    Without this, any verified user could loop /insights/generate or
    /memories/recall and run up unbounded LLM cost — the quota system was
    only enforced on the chat path. Use as ``Depends(enforce_llm_quota)``.
    """
    from app.middleware.rate_limiter import check_rate_limit
    from app.services.quota_service import check_and_increment

    await check_rate_limit(
        str(current_user.id), window_seconds=60, limit=getattr(settings, "RATE_LIMIT_PER_MINUTE", 60)
    )
    await check_and_increment(current_user.id, db)
