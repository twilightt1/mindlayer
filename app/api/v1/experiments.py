"""
A/B Testing API endpoints.

Provides endpoints for:
- Experiment management (admin)
- User variant assignment
- Metric recording
- Experiment results
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.experiment import (
    AddVariantRequest,
    CreateExperimentRequest,
    Experiment,
    ExperimentListResponse,
    ExperimentResults,
    ExperimentStatus,
    RecordMetricRequest,
    UpdateExperimentRequest,
    UserVariantResponse,
)
from app.services.experiments_service import experiments_service
from app.utils.dependencies import get_current_verified_user

router = APIRouter(prefix="/experiments", tags=["experiments"])


# ── User-facing endpoints ────────────────────────────────────────────────────


@router.get("/{experiment_name}/variant", response_model=UserVariantResponse)
async def get_user_variant(
    experiment_name: str,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> UserVariantResponse:
    """
    Get the current user's assigned variant for an experiment.
    
    Uses deterministic hashing to ensure consistent assignment.
    """
    result = experiments_service.get_user_variant_by_name(
        current_user.id, experiment_name
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_name}' not found or not running"
        )

    variant, _ = result
    return UserVariantResponse(
        experiment_name=experiment_name,
        variant_name=variant.name,
        variant_config=variant.config,
    )


@router.post("/{experiment_name}/metrics")
async def record_experiment_metric(
    experiment_name: str,
    body: RecordMetricRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a metric event for an experiment."""
    experiment = experiments_service.get_experiment_by_name(experiment_name)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_name}' not found"
        )

    body.user_id = str(current_user.id)
    event = experiments_service.record_metric(body, experiment.id)

    return {"success": True, "event_id": str(event.id)}


# ── Admin endpoints ──────────────────────────────────────────────────────────


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    status: ExperimentStatus | None = None,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentListResponse:
    """List all experiments (admin only)."""
    experiments = experiments_service.list_experiments(status)
    return ExperimentListResponse(experiments=experiments, total=len(experiments))


@router.post("", response_model=Experiment)
async def create_experiment(
    body: CreateExperimentRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Create a new experiment (admin only)."""
    experiment = experiments_service.create_experiment(body)
    return experiment


@router.get("/{experiment_id}", response_model=Experiment)
async def get_experiment(
    experiment_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Get an experiment by ID (admin only)."""
    experiment = experiments_service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return experiment


@router.patch("/{experiment_id}", response_model=Experiment)
async def update_experiment(
    experiment_id: UUID,
    body: UpdateExperimentRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Update an experiment (admin only)."""
    experiment = experiments_service.update_experiment(experiment_id, body)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return experiment


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an experiment (admin only)."""
    success = experiments_service.delete_experiment(experiment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return {"success": True, "message": f"Experiment {experiment_id} deleted"}


@router.post("/{experiment_id}/variants", response_model=Experiment)
async def add_variant(
    experiment_id: UUID,
    body: AddVariantRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Add a variant to an experiment (admin only)."""
    experiment = experiments_service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )

    # Add variant
    from app.schemas.experiment import ExperimentVariant
    new_variant = ExperimentVariant(
        name=body.name,
        description=body.description,
        variant_type=body.variant_type,
        weight=body.weight,
        config=body.config,
    )
    experiment.variants.append(new_variant)

    return experiment


@router.post("/{experiment_id}/start", response_model=Experiment)
async def start_experiment(
    experiment_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Start an experiment (change status to RUNNING)."""
    from datetime import UTC, datetime

    experiment = experiments_service.update_experiment(
        experiment_id,
        UpdateExperimentRequest(
            status=ExperimentStatus.RUNNING,
            start_date=datetime.now(UTC),
        )
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return experiment


@router.post("/{experiment_id}/pause", response_model=Experiment)
async def pause_experiment(
    experiment_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Pause an experiment (change status to PAUSED)."""
    experiment = experiments_service.update_experiment(
        experiment_id,
        UpdateExperimentRequest(status=ExperimentStatus.PAUSED)
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return experiment


@router.post("/{experiment_id}/complete", response_model=Experiment)
async def complete_experiment(
    experiment_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    """Complete an experiment (change status to COMPLETED)."""
    from datetime import UTC, datetime

    experiment = experiments_service.update_experiment(
        experiment_id,
        UpdateExperimentRequest(
            status=ExperimentStatus.COMPLETED,
            end_date=datetime.now(UTC),
        )
    )
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return experiment


@router.get("/{experiment_id}/results", response_model=ExperimentResults)
async def get_experiment_results(
    experiment_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentResults:
    """Get aggregated results for an experiment."""
    results = experiments_service.get_experiment_results(experiment_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return results
