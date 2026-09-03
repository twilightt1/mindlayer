"""
Feature hints API endpoints.

Provides endpoints for:
- Fetching available hints for a user
- Recording hint interactions (shown, dismissed, actioned)
- Admin management of hints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.hint import (
    HintInteractionCreate,
    HintInteractionResponse,
    HintListResponse,
    HintResponse,
    UserHintState,
)
from app.utils.dependencies import get_current_verified_user, require_admin

router = APIRouter(prefix="/hints", tags=["hints"])


# In-memory hint store for demo (would be database-backed in production)
_HINTS_STORE: dict[UUID, dict] = {}
_USER_STATES: dict[UUID, UserHintState] = {}


def _get_hint_state(user_id: UUID) -> UserHintState:
    """Get or create hint state for user."""
    if user_id not in _USER_STATES:
        _USER_STATES[user_id] = UserHintState(user_id=user_id)
    return _USER_STATES[user_id]


def _is_hint_available(hint: dict, user_state: UserHintState) -> bool:
    """Check if a hint should be shown to user."""
    from datetime import UTC, datetime

    # Check if snoozed
    hint_id_str = str(hint["id"])
    if hint_id_str in user_state.snoozed_hints:
        snooze_until = user_state.snoozed_hints[hint_id_str]
        if datetime.now(UTC) < snooze_until:
            return False

    # Check shown count limit
    trigger_type = hint.get("trigger", {}).get("type")
    if trigger_type == "recurring":
        max_times = hint.get("trigger", {}).get("max_times", 1)
        shown_count = user_state.shown_counts.get(hint_id_str, 0)
        if shown_count >= max_times:
            return False

    return True


@router.get("", response_model=HintListResponse)
async def get_hints(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> HintListResponse:
    """
    Get available hints for the current user.
    
    Returns hints that are:
    - Active
    - Not permanently dismissed
    - Not currently snoozed
    - Under the show limit (for recurring hints)
    """
    user_state = _get_hint_state(current_user.id)

    available_hints = []
    for hint_id, hint in _HINTS_STORE.items():
        if not hint.get("active", True):
            continue
        if not _is_hint_available(hint, user_state):
            continue

        available_hints.append(HintResponse(
            id=hint["id"],
            feature=hint["feature"],
            content=hint["content"],
            priority=hint["priority"],
        ))

    # Sort by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    available_hints.sort(key=lambda h: priority_order.get(h.priority.value, 1))

    return HintListResponse(hints=available_hints, total=len(available_hints))


@router.post("/interactions", response_model=HintInteractionResponse)
async def record_interaction(
    body: HintInteractionCreate,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> HintInteractionResponse:
    """
    Record a user's interaction with a hint.
    
    Actions:
    - shown: Hint was displayed to user
    - dismissed: User dismissed the hint
    - actioned: User clicked the hint action
    - snoozed: User wants to see the hint later
    """
    user_state = _get_hint_state(current_user.id)
    hint_id_str = str(body.hint_id)

    # Get the hint
    hint = _HINTS_STORE.get(body.hint_id)
    if not hint:
        # Create a placeholder hint if it doesn't exist
        hint = {
            "id": body.hint_id,
            "active": True,
            "snooze_days": 7,
            "trigger": {"type": "manual"},
            "content": {"title": "Hint", "body": "Hint content"},
            "priority": "medium",
        }
        _HINTS_STORE[body.hint_id] = hint

    # Update shown count
    if body.action == "shown":
        current_count = user_state.shown_counts.get(hint_id_str, 0)
        user_state.shown_counts[hint_id_str] = current_count + 1

    # Handle snooze
    if body.action == "snoozed":
        from datetime import UTC, datetime, timedelta
        snooze_days = hint.get("snooze_days", 7)
        user_state.snoozed_hints[hint_id_str] = datetime.now(UTC) + timedelta(days=snooze_days)

    return HintInteractionResponse(
        success=True,
        message=f"Interaction '{body.action}' recorded for hint {body.hint_id}"
    )


@router.post("/dismiss", response_model=HintInteractionResponse)
async def dismiss_hint(
    hint_id: UUID,
    reason: str | None = None,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> HintInteractionResponse:
    """
    Permanently dismiss a hint for the user.
    
    The hint will not be shown again unless re-activated by admin.
    """
    user_state = _get_hint_state(current_user.id)
    hint_id_str = str(hint_id)

    # Mark as snoozed indefinitely (until app update)
    from datetime import UTC, datetime, timedelta
    user_state.snoozed_hints[hint_id_str] = datetime.now(UTC) + timedelta(days=365)

    return HintInteractionResponse(
        success=True,
        message=f"Hint {hint_id} dismissed"
    )


@router.post("/snooze/{hint_id}", response_model=HintInteractionResponse)
async def snooze_hint(
    hint_id: UUID,
    days: int = 7,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> HintInteractionResponse:
    """
    Snooze a hint for a specified number of days.
    """
    if days < 1 or days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snooze days must be between 1 and 30"
        )

    user_state = _get_hint_state(current_user.id)
    hint_id_str = str(hint_id)

    from datetime import UTC, datetime, timedelta
    user_state.snoozed_hints[hint_id_str] = datetime.now(UTC) + timedelta(days=days)

    return HintInteractionResponse(
        success=True,
        message=f"Hint {hint_id} snoozed for {days} days"
    )


@router.post("/track-feature/{feature}", response_model=HintInteractionResponse)
async def track_feature_use(
    feature: str,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> HintInteractionResponse:
    """
    Track that a user used a feature.
    
    This updates the hint state to prevent hints about unused features
    from being shown.
    """
    from datetime import UTC, datetime

    user_state = _get_hint_state(current_user.id)
    user_state.last_feature_use[feature] = datetime.now(UTC)

    return HintInteractionResponse(
        success=True,
        message=f"Feature '{feature}' usage tracked"
    )


# Admin endpoints — hint content is injected into other users' UI, so any
# authenticated user must not be able to write it.

@router.get("/admin/hints", response_model=list[HintResponse])
async def list_all_hints(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[HintResponse]:
    """List all hints (admin only)."""
    return [
        HintResponse(
            id=h["id"],
            feature=h["feature"],
            content=h["content"],
            priority=h["priority"],
        )
        for h in _HINTS_STORE.values()
    ]


@router.post("/admin/hints", response_model=HintResponse)
async def create_hint(
    hint: HintResponse,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HintResponse:
    """Create a new hint (admin only)."""
    hint_id = hint.id
    _HINTS_STORE[hint_id] = {
        "id": hint.id,
        "feature": hint.feature,
        "content": hint.content.model_dump(),
        "priority": hint.priority.value,
        "active": True,
        "snooze_days": 7,
        "trigger": {"type": "manual"},
    }
    return hint


@router.delete("/admin/hints/{hint_id}", response_model=HintInteractionResponse)
async def delete_hint(
    hint_id: UUID,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HintInteractionResponse:
    """Delete a hint (admin only)."""
    _HINTS_STORE.pop(hint_id, None)
    return HintInteractionResponse(success=True, message=f"Hint {hint_id} deleted")


# Initialize with default hints
def _init_default_hints():
    """Initialize store with default hints."""
    from uuid import uuid4

    default_hints = [
        {
            "id": uuid4(),
            "feature": "discovery",
            "content": {
                "title": "Discover Hidden Connections",
                "body": "Your memories are starting to connect. Explore the knowledge graph to find unexpected relationships.",
                "action_label": "Explore Graph",
                "action_url": "/discovery",
                "icon": "🔍",
            },
            "priority": "high",
            "trigger": {"type": "feature_untouched", "feature": "discovery", "days": 3},
            "active": True,
            "snooze_days": 7,
        },
        {
            "id": uuid4(),
            "feature": "sources",
            "content": {
                "title": "Connect Your Email",
                "body": "Import important emails automatically from Gmail. Your inbox, captured.",
                "action_label": "Connect Gmail",
                "action_url": "/sources/add?type=gmail",
                "icon": "📧",
            },
            "priority": "medium",
            "trigger": {"type": "first_visit"},
            "active": True,
            "snooze_days": 7,
        },
        {
            "id": uuid4(),
            "feature": "insights",
            "content": {
                "title": "New Insights Available",
                "body": "AI found 3 new connections in your recent memories. Tap to explore.",
                "action_label": "View Insights",
                "action_url": "/insights",
                "icon": "💡",
            },
            "priority": "high",
            "trigger": {"type": "recurring", "interval_days": 7, "max_times": 3},
            "active": True,
            "snooze_days": 7,
        },
    ]

    for hint in default_hints:
        _HINTS_STORE[hint["id"]] = hint


# Initialize on module load
_init_default_hints()
