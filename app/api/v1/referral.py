"""
Referral API

Endpoints for referral system:
    GET  /api/v1/referral/code      - Get user's referral code
    GET  /api/v1/referral/stats    - Get user's referral stats
    POST /api/v1/referral/share    - Create share link for email
    GET  /api/v1/referral/leaderboard - Get top referrers
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.referral_service import (
    get_or_create_referral_code,
    get_referral_stats,
    create_referral_link,
    get_referral_leaderboard,
)
from app.utils.dependencies import get_current_verified_user

router = APIRouter(prefix="/referral", tags=["referral"])


class ReferralCodeResponse(BaseModel):
    code: str
    link: str


class ReferralStatsResponse(BaseModel):
    total_referrals: int
    pending_referrals: int
    unclaimed_rewards: int
    referral_code: str
    referral_link: str


class ShareReferralRequest(BaseModel):
    email: EmailStr


class ShareReferralResponse(BaseModel):
    success: bool
    message: str
    referral_link: str


class LeaderboardEntry(BaseModel):
    user_id: str
    referral_count: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]


@router.get("/code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReferralCodeResponse:
    """Get or create user's referral code."""
    code = await get_or_create_referral_code(db, current_user.id)
    return ReferralCodeResponse(
        code=code.code,
        link=f"https://Orivory.app/signup?ref={code.code}"
    )


@router.get("/stats", response_model=ReferralStatsResponse)
async def get_stats(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReferralStatsResponse:
    """Get user's referral statistics."""
    stats = await get_referral_stats(db, current_user.id)
    return ReferralStatsResponse(**stats)


@router.post("/share", response_model=ShareReferralResponse)
async def share_referral(
    body: ShareReferralRequest,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShareReferralResponse:
    """Create a share link for a specific email."""
    # Don't let users refer themselves
    if body.email.lower() == current_user.email.lower():
        raise HTTPException(status_code=400, detail="Cannot refer yourself")
    
    await create_referral_link(db, current_user.id, body.email)
    
    code = await get_or_create_referral_code(db, current_user.id)
    
    return ShareReferralResponse(
        success=True,
        message=f"Referral link created for {body.email}",
        referral_link=f"https://Orivory.app/signup?ref={code.code}"
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeaderboardResponse:
    """Get top referrers leaderboard."""
    entries = await get_referral_leaderboard(db)
    return LeaderboardResponse(
        entries=[LeaderboardEntry(**e) for e in entries]
    )
