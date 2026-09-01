"""
A/B Testing Service for user-facing feature experiments.

This service provides:
- Experiment management (CRUD)
- User assignment to experiment variants
- Metric recording and aggregation
- Experiment results and analytics
"""
import hashlib
import random
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.schemas.experiment import (
    CreateExperimentRequest,
    Experiment,
    ExperimentResults,
    ExperimentStatus,
    ExperimentVariant,
    MetricEvent,
    MetricStats,
    RecordMetricRequest,
    UpdateExperimentRequest,
    UserAssignment,
    VariantResult,
    VariantType,
)


class ExperimentsService:
    """
    Service for managing A/B experiments and user assignments.
    
    In production, this would be backed by a database.
    Currently uses in-memory storage for demonstration.
    """

    def __init__(self) -> None:
        self._experiments: dict[UUID, Experiment] = {}
        self._assignments: dict[tuple[UUID, UUID], UserAssignment] = {}  # (user_id, experiment_id)
        self._metrics: list[MetricEvent] = []
        self._initialized = False

    def _init_defaults(self) -> None:
        """Initialize with some example experiments."""
        if self._initialized:
            return
        self._initialized = True
        
        # Example: Onboarding flow experiment
        onboarding_exp = Experiment(
            name="onboarding_flow_v2",
            description="Test new simplified 3-step onboarding vs current flow",
            status=ExperimentStatus.RUNNING,
            variants=[
                ExperimentVariant(
                    name="control",
                    description="Current multi-step onboarding",
                    variant_type=VariantType.CONTROL,
                    weight=50,
                    config={"steps": 5, "show_sources": True},
                ),
                ExperimentVariant(
                    name="treatment",
                    description="New simplified 3-step onboarding",
                    variant_type=VariantType.TREATMENT,
                    weight=50,
                    config={"steps": 3, "quick_demo": True, "optional_sources": True},
                ),
            ],
            start_date=datetime.now(UTC),
        )
        self._experiments[onboarding_exp.id] = onboarding_exp

        # Example: Search UX experiment
        search_exp = Experiment(
            name="search_ux_filters",
            description="Test filter chips vs dropdown for search refinement",
            status=ExperimentStatus.RUNNING,
            variants=[
                ExperimentVariant(
                    name="control",
                    description="Dropdown filters",
                    variant_type=VariantType.CONTROL,
                    weight=50,
                    config={"filter_ui": "dropdown"},
                ),
                ExperimentVariant(
                    name="treatment",
                    description="Chip-based filters",
                    variant_type=VariantType.TREATMENT,
                    weight=50,
                    config={"filter_ui": "chips"},
                ),
            ],
            start_date=datetime.now(UTC),
        )
        self._experiments[search_exp.id] = search_exp

    def _hash_user(self, user_id: UUID, experiment_id: UUID) -> int:
        """Generate deterministic hash for consistent user assignment."""
        seed = f"{user_id}:{experiment_id}".encode()
        return int(hashlib.sha256(seed).hexdigest(), 16)

    def _assign_variant(self, user_id: UUID, experiment: Experiment) -> ExperimentVariant:
        """Assign a user to a variant using deterministic hashing."""
        # If user already has an assignment, return it
        key = (user_id, experiment.id)
        if key in self._assignments:
            assigned = self._assignments[key]
            for v in experiment.variants:
                if v.id == assigned.variant_id:
                    return v
        
        # New assignment - use weighted random based on hash
        total_weight = sum(v.weight for v in experiment.variants)
        hash_val = self._hash_user(user_id, experiment.id)
        normalized = (hash_val % total_weight) / total_weight
        
        cumulative = 0
        for variant in experiment.variants:
            cumulative += variant.weight / total_weight
            if normalized <= cumulative:
                return variant
        
        # Fallback to first variant
        return experiment.variants[0]

    # CRUD Operations

    def create_experiment(self, request: CreateExperimentRequest) -> Experiment:
        """Create a new experiment."""
        # Ensure at least one control variant
        if not request.variants:
            request.variants = [
                ExperimentVariant(
                    name="control",
                    description="Control group",
                    variant_type=VariantType.CONTROL,
                    weight=100,
                ),
            ]

        experiment = Experiment(
            name=request.name,
            description=request.description,
            variants=request.variants,
            metrics=request.metrics,
            targeting=request.targeting,
            start_date=request.start_date,
            end_date=request.end_date,
            status=ExperimentStatus.DRAFT,
        )
        self._experiments[experiment.id] = experiment
        return experiment

    def get_experiment(self, experiment_id: UUID) -> Experiment | None:
        """Get an experiment by ID."""
        return self._experiments.get(experiment_id)

    def get_experiment_by_name(self, name: str) -> Experiment | None:
        """Get an experiment by name."""
        for exp in self._experiments.values():
            if exp.name == name:
                return exp
        return None

    def list_experiments(self, status: ExperimentStatus | None = None) -> list[Experiment]:
        """List all experiments, optionally filtered by status."""
        self._init_defaults()
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e.status == status]
        return experiments

    def update_experiment(
        self, experiment_id: UUID, request: UpdateExperimentRequest
    ) -> Experiment | None:
        """Update an experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return None

        if request.name is not None:
            experiment.name = request.name
        if request.description is not None:
            experiment.description = request.description
        if request.status is not None:
            experiment.status = request.status
        if request.targeting is not None:
            experiment.targeting = request.targeting
        if request.start_date is not None:
            experiment.start_date = request.start_date
        if request.end_date is not None:
            experiment.end_date = request.end_date
        experiment.updated_at = datetime.now(UTC)

        return experiment

    def delete_experiment(self, experiment_id: UUID) -> bool:
        """Delete an experiment."""
        if experiment_id in self._experiments:
            del self._experiments[experiment_id]
            return True
        return False

    # User Assignment

    def get_user_variant(
        self, user_id: UUID, experiment_id: UUID
    ) -> ExperimentVariant | None:
        """Get a user's assigned variant for an experiment."""
        self._init_defaults()
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None
        return self._assign_variant(user_id, experiment)

    def get_user_variant_by_name(
        self, user_id: UUID, experiment_name: str
    ) -> tuple[ExperimentVariant, Experiment] | None:
        """Get a user's assigned variant by experiment name."""
        self._init_defaults()
        experiment = self.get_experiment_by_name(experiment_name)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None
        variant = self._assign_variant(user_id, experiment)
        
        # Store assignment
        key = (user_id, experiment.id)
        self._assignments[key] = UserAssignment(
            user_id=user_id,
            experiment_id=experiment.id,
            variant_id=variant.id,
            experiment_name=experiment.name,
            variant_name=variant.name,
        )
        
        return variant, experiment

    def get_user_assignments(self, user_id: UUID) -> list[UserAssignment]:
        """Get all assignments for a user."""
        return [
            a for key, a in self._assignments.items()
            if key[0] == user_id
        ]

    # Metrics

    def record_metric(self, request: RecordMetricRequest, experiment_id: UUID) -> MetricEvent:
        """Record a metric event for an experiment."""
        self._init_defaults()
        
        # Get user's variant assignment
        user_uuid = UUID(request.user_id) if request.user_id else None
        variant = None
        if user_uuid:
            variant = self.get_user_variant(user_uuid, experiment_id)
        
        if not variant:
            # Try to get from request (if provided)
            return MetricEvent(
                experiment_id=experiment_id,
                user_id=user_uuid,
                variant_id=variant.id if variant else UUID("00000000-0000-0000-0000-000000000000"),
                metric_name=request.metric_name,
                value=request.value,
                properties=request.properties,
            )
        
        event = MetricEvent(
            experiment_id=experiment_id,
            user_id=user_uuid,
            variant_id=variant.id,
            metric_name=request.metric_name,
            value=request.value,
            properties=request.properties,
        )
        self._metrics.append(event)
        return event

    def get_experiment_results(self, experiment_id: UUID) -> ExperimentResults | None:
        """Get aggregated results for an experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return None

        # Count users per variant
        variant_users: dict[UUID, set[UUID]] = {
            v.id: set() for v in experiment.variants
        }
        for key in self._assignments:
            user_id, exp_id = key
            if exp_id == experiment_id:
                assignment = self._assignments[key]
                variant_users[assignment.variant_id].add(user_id)

        # Aggregate metrics per variant
        variant_results = []
        for variant in experiment.variants:
            variant_metrics = [
                m for m in self._metrics if m.variant_id == variant.id
            ]
            
            metric_results = {}
            for metric_name in set(m.metric_name for m in variant_metrics):
                values = [m.value for m in variant_metrics if m.metric_name == metric_name]
                if values:
                    metric_results[metric_name] = MetricStats(
                        total=sum(values),
                        mean=sum(values) / len(values),
                        count=len(values),
                        p95=None,
                    )
            
            variant_results.append(VariantResult(
                variant_id=variant.id,
                variant_name=variant.name,
                variant_type=variant.variant_type,
                user_count=len(variant_users[variant.id]),
                metric_results=metric_results,
            ))

        return ExperimentResults(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            status=experiment.status,
            total_users=len(set(a.user_id for a in self._assignments.values() if a.experiment_id == experiment_id)),
            variant_results=variant_results,
            start_date=experiment.start_date,
            end_date=experiment.end_date,
        )


# Singleton instance
experiments_service = ExperimentsService()
