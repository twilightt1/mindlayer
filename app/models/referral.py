"""
Referral System Models

Tracks referral codes, referrals, and rewards.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._datetime_helpers import utc_now
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.user import User


class ReferralCode(Base):
    """Referral code for a user."""
    __tablename__ = "referral_codes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_uses: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    user: Mapped[User] = relationship("User", backref="referral_codes")
    referrals: Mapped[list[Referral]] = relationship("Referral", back_populates="referral_code", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_referral_codes_user_active", "user_id", "is_active"),
    )


class Referral(Base):
    """Tracks a referral from one user to another."""
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    referral_code_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("referral_codes.id", ondelete="CASCADE"), nullable=False)
    referrer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referee_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    referee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, completed, rewarded
    reward_tier: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    referral_code: Mapped[ReferralCode] = relationship("ReferralCode", back_populates="referrals")

    __table_args__ = (
        UniqueConstraint("referrer_id", "referee_email", name="uq_referrer_email"),
        Index("ix_referrals_status", "status"),
    )


class ReferralReward(Base):
    """Tracks rewards given to referrers."""
    __tablename__ = "referral_rewards"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    referral_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(20), nullable=False)  # free_months, increased_quota
    reward_value: Mapped[int] = mapped_column(Integer, default=1)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    claimed_at: Mapped[datetime | None] = mapped_column(default=None)
