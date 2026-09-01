"""
Feature hint schemas for the discovery hints system.

This module defines the schemas for feature discovery hints that guide users
toward underutilized features based on their behavior patterns.
"""
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class HintTriggerType(str, Enum):
    """Types of triggers for showing hints."""
    TIME_ON_PAGE = "time_on_page"           # Show after X seconds on page
    ACTION_COUNT = "action_count"           # Show after X actions
    FEATURE_UNTouched = "feature_untouched" # Show if feature unused for X days
    RECURRING = "recurring"                 # Show periodically
    FIRST_VISIT = "first_visit"            # Show on first visit to section
    MANUAL = "manual"                        # Manually triggered by admin


class HintPriority(str, Enum):
    """Priority levels for hints."""
    HIGH = "high"      # Always show, cannot be permanently dismissed
    MEDIUM = "medium"  # Show once, can be snoozed
    LOW = "low"       # Show only if no other hints pending


class HintStatus(str, Enum):
    """Status of a hint interaction."""
    PENDING = "pending"     # Hint is queued to be shown
    SHOWN = "shown"        # Hint was displayed to user
    DISMISSED = "dismissed" # User dismissed the hint
    ACTIONED = "actioned"   # User took the suggested action
    EXPIRED = "expired"     # Hint expired before being shown


class HintTrigger(BaseModel):
    """Defines when a hint should be triggered."""
    type: HintTriggerType
    # For TIME_ON_PAGE
    seconds: int | None = None
    # For ACTION_COUNT
    action: str | None = None
    count: int | None = None
    # For FEATURE_UNTouched
    feature: str | None = None
    days: int | None = None
    # For RECURRING
    interval_days: int | None = None
    max_times: int | None = None


class HintContent(BaseModel):
    """Content of a hint to display to the user."""
    title: str = Field(..., max_length=100)
    body: str = Field(..., max_length=300)
    action_label: str | None = Field(None, max_length=50)
    action_url: str | None = None
    icon: str | None = None  # Emoji or icon identifier


class FeatureHint(BaseModel):
    """Definition of a feature hint."""
    id: UUID
    feature: str = Field(..., description="Feature identifier (e.g., 'discovery', 'insights')")
    trigger: HintTrigger
    content: HintContent
    priority: HintPriority = HintPriority.MEDIUM
    dismissible: bool = True
    snooze_days: int = 7  # Default snooze duration
    active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HintInteractionCreate(BaseModel):
    """Schema for recording a hint interaction."""
    hint_id: UUID
    user_id: UUID
    action: Literal["shown", "dismissed", "actioned", "snoozed"]


class HintInteraction(BaseModel):
    """Record of a user's interaction with a hint."""
    id: UUID
    hint_id: UUID
    user_id: UUID
    status: HintStatus
    created_at: datetime
    updated_at: datetime
    # For snoozed hints
    snooze_until: datetime | None = None

    class Config:
        from_attributes = True


class HintDismissal(BaseModel):
    """Record of a dismissed hint (for permanent dismissal tracking)."""
    id: UUID
    hint_id: UUID
    user_id: UUID
    dismissed_at: datetime
    reason: str | None = None  # "not_interested", "already_know", "not_relevant"

    class Config:
        from_attributes = True


class UserHintState(BaseModel):
    """Current state of hints for a user."""
    user_id: UUID
    # Hints that are currently snoozed
    snoozed_hints: dict[str, datetime] = Field(default_factory=dict)
    # Count of times each hint has been shown
    shown_counts: dict[str, int] = Field(default_factory=dict)
    # When each feature was last used
    last_feature_use: dict[str, datetime] = Field(default_factory=dict)


# Response schemas

class HintResponse(BaseModel):
    """Single hint to display to user."""
    id: UUID
    feature: str
    content: HintContent
    priority: HintPriority


class HintListResponse(BaseModel):
    """List of hints available for a user."""
    hints: list[HintResponse]
    total: int


class HintInteractionResponse(BaseModel):
    """Result of recording a hint interaction."""
    success: bool
    message: str | None = None


# Analytics schemas

class HintAnalytics(BaseModel):
    """Analytics for a hint or feature."""
    hint_id: UUID | None = None
    feature: str
    period_start: datetime
    period_end: datetime
    total_showns: int = 0
    total_dismissals: int = 0
    total_actioneds: int = 0
    dismissal_rate: float = 0.0
    action_rate: float = 0.0
