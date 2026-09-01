"""
Demo Data API - Onboarding Support

Endpoints:
    POST   /api/v1/demo/seed    - Seed demo data for new users
    GET    /api/v1/demo/status  - Check if user has demo data
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.demo_data_service import check_user_has_memories, seed_user_demo_data
from app.utils.dependencies import get_current_verified_user

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoSeedResponse(BaseModel):
    """Response from demo data seeding."""
    success: bool
    memory_count: int | None = None
    memory_titles: list[str] | None = None
    message: str


class DemoStatusResponse(BaseModel):
    """Demo data status for current user."""
    has_memories: bool
    has_demo_data: bool


@router.post("/seed", response_model=DemoSeedResponse)
async def seed_demo_data(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DemoSeedResponse:
    """
    Seed demo memories for the current user.

    Creates sample memories to demonstrate Orivory features.
    Only works if user doesn't have any memories yet.
    """
    result = await seed_user_demo_data(current_user.id, db)

    if result["created"]:
        return DemoSeedResponse(
            success=True,
            memory_count=result["memory_count"],
            memory_titles=result["memory_titles"],
            message=f"Created {result['memory_count']} demo memories!",
        )
    else:
        return DemoSeedResponse(
            success=False,
            message="You already have memories. Demo data only available for new users.",
        )


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DemoStatusResponse:
    """
    Check if user has memories and demo data.
    """
    has_memories = await check_user_has_memories(current_user.id, db)

    return DemoStatusResponse(
        has_memories=has_memories,
        has_demo_data=False,  # We don't track this separately yet
    )
