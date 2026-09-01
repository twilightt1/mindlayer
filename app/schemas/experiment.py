"""
A/B Testing Framework for user-facing feature experiments.

This module provides infrastructure for:
- Defining experiments with variants
- Random user assignment to variants
- Tracking experiment metrics
- Querying experiment results
"""
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    """Status of an experiment."""
    DRAFT = "draft"           # Not yet active
    RUNNING = "running"       # Active and assigning users
    PAUSED = "paused"         # Temporarily stopped
    COMPLETED = "completed"    # Finished, results final
    ARCHIVED = "archived"     # Archived, no longer used


class VariantType(str, Enum):
    """Type of variant."""
    CONTROL = "control"       # Baseline/control group
    TREATMENT = "treatment"    # Variant being tested


class ExperimentVariant(BaseModel):
    """A single variant in an experiment."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=100)
    description: str | None = None
    variant_type: VariantType = VariantType.TREATMENT
    weight: int = Field(default=50, ge=1, le=100)  # Percentage weight
    config: dict[str, Any] = Field(default_factory=dict)  # Feature flags, etc.
    is_default: bool = False  # Used if no assignment exists

    class Config:
        from_attributes = True


class MetricDefinition(BaseModel):
    """Definition of a metric to track in an experiment."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=100)
    description: str | None = None
    metric_type: str = "counter"  # counter, gauge, histogram
    aggregation: str = "sum"  # sum, avg, count, p95


class Experiment(BaseModel):
    """An A/B test experiment."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=200)
    description: str | None = None
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: list[ExperimentVariant] = Field(default_factory=list)
    metrics: list[MetricDefinition] = Field(default_factory=list)
    targeting: dict[str, Any] = Field(default_factory=dict)  # User segment rules
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class UserAssignment(BaseModel):
    """Record of a user's assignment to an experiment variant."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    experiment_id: UUID
    variant_id: UUID
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    # Denormalized for easy querying
    experiment_name: str
    variant_name: str

    class Config:
        from_attributes = True


class MetricEvent(BaseModel):
    """A metric event to record."""
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    user_id: UUID | None = None  # None for anonymous events
    variant_id: UUID
    metric_name: str
    value: float = 1.0  # For counters, always 1
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class MetricStats(BaseModel):
    """Statistics for a metric."""
    total: float
    mean: float
    count: int
    p95: float | None = None
    control_mean: float | None = None
    lift: float | None = None  # % change vs control
    p_value: float | None = None  # Statistical significance


class VariantResult(BaseModel):
    """Results for a single variant."""
    variant_id: UUID
    variant_name: str
    variant_type: VariantType
    user_count: int
    metric_results: dict[str, MetricStats]


class ExperimentResults(BaseModel):
    """Results of an experiment."""
    experiment_id: UUID
    experiment_name: str
    status: ExperimentStatus
    total_users: int
    variant_results: list[VariantResult]
    start_date: datetime | None = None
    end_date: datetime | None = None
    statistical_significance: dict[str, float] = Field(default_factory=dict)


# Request/Response schemas

class CreateExperimentRequest(BaseModel):
    """Request to create a new experiment."""
    name: str = Field(..., max_length=200)
    description: str | None = None
    variants: list[ExperimentVariant] = Field(default_factory=list)
    metrics: list[MetricDefinition] = Field(default_factory=list)
    targeting: dict[str, Any] = Field(default_factory=dict)
    start_date: datetime | None = None
    end_date: datetime | None = None


class UpdateExperimentRequest(BaseModel):
    """Request to update an experiment."""
    name: str | None = None
    description: str | None = None
    status: ExperimentStatus | None = None
    targeting: dict[str, Any] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class AddVariantRequest(BaseModel):
    """Request to add a variant to an experiment."""
    name: str = Field(..., max_length=100)
    description: str | None = None
    variant_type: VariantType = VariantType.TREATMENT
    weight: int = Field(default=50, ge=1, le=100)
    config: dict[str, Any] = Field(default_factory=dict)


class RecordMetricRequest(BaseModel):
    """Request to record a metric event."""
    metric_name: str
    value: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None  # UUID as string


class ExperimentListResponse(BaseModel):
    """List of experiments."""
    experiments: list[Experiment]
    total: int


class UserVariantResponse(BaseModel):
    """User's variant assignment for an experiment."""
    experiment_name: str
    variant_name: str
    variant_config: dict[str, Any] = Field(default_factory=dict)
