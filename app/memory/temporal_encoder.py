"""
Temporal Memory System for Orivory v2.0

Implements time-aware retrieval using:
- Sinusoidal temporal encoding
- Time-range filtering
- Recency weighting

Reference: TimeR4 + EM-LLM research
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.state import AgentState

log = logging.getLogger(__name__)

# ─── Time Constants ───────────────────────────────────────────────────────────

# Reference epoch for absolute encoding
EPOCH = datetime(2020, 1, 1)

# Time granularity buckets for cyclical encoding
TIME_BUCKETS = [
    (timedelta(hours=1), "hour"),
    (timedelta(days=1), "day"),
    (timedelta(weeks=1), "week"),
    (timedelta(days=30), "month"),
    (timedelta(days=365), "year"),
]

# Temporal vector dimension
TEMPORAL_DIM = 64

# Default recency decay half-life (90 days)
DEFAULT_HALF_LIFE_DAYS = 90


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class TemporalQuery:
    """Parsed temporal information from a query."""
    has_temporal: bool
    time_range: tuple[datetime, datetime] | None = None
    recency_weight: float = 0.0  # 0.0 = no recency preference, 1.0 = prefer recent
    granularity: str | None = None  # "hour", "day", "week", "month", "quarter", "year"
    relative_reference: str | None = None  # "today", "this_week", "last_month", etc.


@dataclass
class TemporalFeatures:
    """Temporal features for a document."""
    timestamp: datetime
    temporal_vector: list[float]
    decay_weight: float
    cyclical_features: dict[str, float]


# ─── Temporal Encoder ─────────────────────────────────────────────────────────

class TemporalEncoder:
    """
    Encodes temporal information using sinusoidal positional encoding.

    Similar to transformer attention positional encoding, but adapted for
    1D temporal sequences with support for:
    - Absolute position (days since epoch)
    - Cyclical patterns (day of week, month, year)
    - Relative recency
    """

    def __init__(
        self,
        reference_date: datetime | None = None,
        dimension: int = TEMPORAL_DIM,
    ):
        self.reference_date = reference_date or datetime.utcnow()
        self.dimension = dimension

        # Generate angular frequencies for each time bucket
        # Use seconds as base unit for consistency
        self.frequencies = []
        for bucket, _ in TIME_BUCKETS:
            period_seconds = bucket.total_seconds()
            # Angular frequency = 2*pi / period
            # Use normalized period (e.g., 1 day = 1, 1 month = 30)
            normalized_period = period_seconds / (24 * 60 * 60)  # days
            freq = 2 * math.pi / max(1, normalized_period)
            self.frequencies.append(freq)

    def encode_absolute(self, timestamp: datetime) -> list[float]:
        """
        Encode absolute time as fixed-dimensional vector.

        Uses sinusoidal encoding with multiple frequencies to capture
        different time scales.
        """
        # Time offset in days from reference (normalized for numerical stability)
        time_diff_days = (timestamp - self.reference_date).total_seconds() / (24 * 60 * 60)

        vector = []
        for i in range(self.dimension):
            freq_idx = i % len(self.frequencies)
            # Decay amplitude with frequency (higher freq = lower amplitude)
            amplitude = 1.0 / (1 + i // len(self.frequencies))
            # Use days as time unit for better numerical stability
            value = amplitude * math.sin(
                self.frequencies[freq_idx] * time_diff_days / (i / 10 + 1)
            )
            vector.append(value)

        return vector

    def encode_relative(
        self,
        doc_timestamp: datetime,
        query_timestamp: datetime | None = None,
    ) -> list[float]:
        """
        Encode relative time difference for queries like
        "documents from the last month".
        """
        query_time = query_timestamp or datetime.utcnow()
        time_diff = (query_time - doc_timestamp).total_seconds()

        # Compress large differences (logarithmic)
        compressed_diff = math.copysign(math.log1p(abs(time_diff)), time_diff)

        vector = []
        for i in range(self.dimension):
            freq_idx = i % len(self.frequencies)
            value = math.cos(
                self.frequencies[freq_idx] * compressed_diff / (i + 1)
            )
            vector.append(value)

        return vector

    def encode_cyclical(self, timestamp: datetime) -> dict[str, list[float]]:
        """
        Encode cyclical patterns in time (day of week, month, etc.).

        Returns a dict with feature names and their sin/cos encodings.
        """
        features = {}

        # Day of week (0-6)
        dow = timestamp.weekday()
        features["day_of_week"] = self._periodic(dow, 7)

        # Day of year (0-365)
        doy = timestamp.timetuple().tm_yday
        features["day_of_year"] = self._periodic(doy, 365)

        # Month (1-12)
        month = timestamp.month
        features["month"] = self._periodic(month, 12)

        # Hour of day (0-23)
        hour = timestamp.hour
        features["hour"] = self._periodic(hour, 24)

        # Quarter (1-4)
        quarter = (timestamp.month - 1) // 3 + 1
        features["quarter"] = self._periodic(quarter, 4)

        return features

    @staticmethod
    def _periodic(value: float, period: float) -> list[float]:
        """Generate sin/cos pair for cyclical encoding."""
        normalized = 2 * math.pi * value / period
        return [math.sin(normalized), math.cos(normalized)]

    def encode_document(self, timestamp: datetime) -> TemporalFeatures:
        """
        Generate all temporal features for a document.

        Args:
            timestamp: Document creation/modification time

        Returns:
            TemporalFeatures with vector, decay weight, and cyclical features
        """
        # Calculate decay weight (exponential decay)
        days_old = (datetime.utcnow() - timestamp).days
        decay_weight = math.exp(-0.693 * days_old / DEFAULT_HALF_LIFE_DAYS)

        return TemporalFeatures(
            timestamp=timestamp,
            temporal_vector=self.encode_absolute(timestamp),
            decay_weight=decay_weight,
            cyclical_features=self.encode_cyclical(timestamp),
        )


# ─── Temporal Query Parser ─────────────────────────────────────────────────────

class TemporalQueryParser:
    """
    Parses temporal information from natural language queries.

    Extracts:
    - Explicit time ranges ("between 2024-01 and 2024-06")
    - Relative references ("last month", "recently", "this quarter")
    - Recency preferences
    """

    # Patterns for temporal extraction
    TIME_RANGE_PATTERNS = [
        # Explicit ranges
        (r"between\s+(\d{4}-\d{2})\s+and\s+(\d{4}-\d{2})", "explicit_range"),
        (r"from\s+(\w+\s+\d{4})\s+to\s+(\w+\s+\d{4})", "explicit_range"),
        (r"(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4})", "explicit_range"),

        # Relative periods
        (r"last\s+(hour|day|week|month|quarter|year)s?", "relative_period"),
        (r"past\s+(\d+)\s+(hours?|days?|weeks?|months?)", "relative_count"),
        (r"this\s+(hour|day|week|month|quarter|year)", "current_period"),
        (r"recently", "recent"),
        (r"ago", "past"),
    ]

    GRANULARITY_MAP = {
        "hour": timedelta(hours=1),
        "day": timedelta(days=1),
        "week": timedelta(weeks=1),
        "month": timedelta(days=30),
        "quarter": timedelta(days=90),
        "year": timedelta(days=365),
    }

    def parse(self, query: str) -> TemporalQuery:
        """
        Parse temporal information from query.

        Args:
            query: Natural language query

        Returns:
            TemporalQuery with extracted temporal information
        """
        import re

        query_lower = query.lower()

        # Check for explicit time ranges
        for pattern, pattern_type in self.TIME_RANGE_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                return self._handle_match(match, pattern_type, query)

        # No temporal pattern found
        return TemporalQuery(has_temporal=False)

    def _handle_match(self, match: re.Match, pattern_type: str, query: str) -> TemporalQuery:
        """Handle matched temporal pattern."""
        now = datetime.utcnow()

        if pattern_type == "explicit_range":
            # Parse year-month dates
            try:
                start_str, end_str = match.groups()
                # Try to parse "YYYY-MM" format
                start = datetime.strptime(start_str, "%Y-%m")
                end = datetime.strptime(end_str, "%Y-%m")
                end = end + timedelta(days=31)  # Go to end of month

                return TemporalQuery(
                    has_temporal=True,
                    time_range=(start, end),
                    recency_weight=0.5,
                    granularity="month",
                )
            except ValueError:
                pass

        if pattern_type == "relative_period":
            period = match.group(1)
            return self._get_relative_period(period, now)

        if pattern_type == "relative_count":
            count = int(match.group(1))
            unit = match.group(2).rstrip("s")  # Remove plural
            delta = self.GRANULARITY_MAP.get(unit, timedelta(days=1))

            start = now - (delta * count)
            return TemporalQuery(
                has_temporal=True,
                time_range=(start, now),
                recency_weight=1.0,
                granularity=unit,
            )

        if pattern_type == "current_period":
            period = match.group(1)
            return self._get_current_period(period, now)

        if pattern_type in ("recent", "past"):
            # Default to last 30 days for "recently"
            start = now - timedelta(days=30)
            return TemporalQuery(
                has_temporal=True,
                time_range=(start, now),
                recency_weight=1.0,
                granularity="day",
                relative_reference="recent",
            )

        return TemporalQuery(has_temporal=False)

    def _get_relative_period(self, period: str, now: datetime) -> TemporalQuery:
        """Get time range for relative period like 'last month'."""
        delta = self.GRANULARITY_MAP.get(period, timedelta(days=1))
        start = now - delta
        return TemporalQuery(
            has_temporal=True,
            time_range=(start, now),
            recency_weight=1.0,
            granularity=period,
            relative_reference=f"last_{period}",
        )

    def _get_current_period(self, period: str, now: datetime) -> TemporalQuery:
        """Get time range for current period like 'this month'."""
        if period == "month":
            start = datetime(now.year, now.month, 1)
            end = now
        elif period == "quarter":
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            start = datetime(now.year, quarter_month, 1)
            end = now
        elif period == "year":
            start = datetime(now.year, 1, 1)
            end = now
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            end = now
        else:
            start = now - timedelta(days=1)
            end = now

        return TemporalQuery(
            has_temporal=True,
            time_range=(start, end),
            recency_weight=0.5,
            granularity=period,
            relative_reference=f"this_{period}",
        )


# ─── Temporal Retrieval Helper ─────────────────────────────────────────────────

def calculate_temporal_score(
    doc_timestamp: datetime,
    query: TemporalQuery,
    base_score: float,
) -> float:
    """
    Adjust document score based on temporal relevance.

    Args:
        doc_timestamp: Document creation time
        query: Parsed temporal query
        base_score: Original retrieval score

    Returns:
        Adjusted score incorporating temporal factors
    """
    if not query.has_temporal:
        return base_score

    # Check if document is within time range
    if query.time_range:
        start, end = query.time_range
        if not (start <= doc_timestamp <= end):
            # Document is outside time range - penalize heavily
            return base_score * 0.1

    # Apply recency weighting
    if query.recency_weight > 0:
        # Calculate how recent the document is (0-1)
        days_old = (datetime.utcnow() - doc_timestamp).days
        recency = math.exp(-0.693 * days_old / DEFAULT_HALF_LIFE_DAYS)

        # Blend recency with base score
        # High recency_weight means we care more about recency
        adjusted = (
            (1 - query.recency_weight) * base_score +
            query.recency_weight * recency
        )
        return adjusted

    return base_score


# ─── Temporal Agent Node ───────────────────────────────────────────────────────

async def temporal_agent(state: AgentState) -> AgentState:
    """
    Temporal agent node for LangGraph workflow.

    This node:
    1. Parses temporal information from query
    2. Stores temporal query in state
    3. Will be used by retrieval agent for time-aware filtering

    Args:
        state: Current agent state

    Returns:
        Updated agent state with temporal query
    """
    state.setdefault("agent_trace", {})
    state.setdefault("temporal_trace", {})

    query = state.get("rewritten_query", state.get("query", ""))
    query_type = state.get("query_type", "")

    # Skip temporal parsing for non-RAG queries
    if query_type in ("chitchat", "save_note"):
        state["temporal_trace"]["skipped"] = True
        state["temporal_query"] = TemporalQuery(has_temporal=False)
        return state

    # Parse temporal information
    parser = TemporalQueryParser()
    temporal_query = parser.parse(query)

    state["temporal_query"] = temporal_query

    state["temporal_trace"] = {
        "has_temporal": temporal_query.has_temporal,
        "granularity": temporal_query.granularity,
        "recency_weight": temporal_query.recency_weight,
        "relative_reference": temporal_query.relative_reference,
    }

    if temporal_query.has_temporal and temporal_query.time_range:
        start, end = temporal_query.time_range
        state["temporal_trace"]["time_range"] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        log.info(f"Temporal: Detected {temporal_query.granularity} query, range: {start.date()} to {end.date()}")
    elif temporal_query.has_temporal:
        log.info(f"Temporal: Detected recency query, weight={temporal_query.recency_weight}")
    else:
        log.debug("Temporal: No temporal information detected")

    return state
