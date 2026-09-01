"""
Tests for Temporal Memory System

Reference: TimeR4 + EM-LLM research
"""

from datetime import datetime, timedelta

import pytest

from app.memory.temporal_encoder import (
    DEFAULT_HALF_LIFE_DAYS,
    TemporalEncoder,
    TemporalFeatures,
    TemporalQuery,
    TemporalQueryParser,
    calculate_temporal_score,
    temporal_agent,
)


class TestTemporalEncoder:
    """Test TemporalEncoder."""

    def test_encode_absolute(self):
        """Test absolute time encoding."""
        encoder = TemporalEncoder()

        t1 = datetime(2024, 1, 1)
        t2 = datetime(2024, 6, 1)

        v1 = encoder.encode_absolute(t1)
        v2 = encoder.encode_absolute(t2)

        # Different times should produce different vectors
        assert len(v1) == 64
        assert len(v2) == 64
        assert v1 != v2

    def test_encode_absolute_same_time(self):
        """Same time should produce same vector."""
        encoder = TemporalEncoder()

        t = datetime(2024, 1, 1)

        v1 = encoder.encode_absolute(t)
        v2 = encoder.encode_absolute(t)

        assert v1 == v2

    def test_encode_cyclical(self):
        """Test cyclical encoding."""
        encoder = TemporalEncoder()

        # Monday, January
        d1 = datetime(2024, 1, 1)  # Monday
        features = encoder.encode_cyclical(d1)

        assert "day_of_week" in features
        assert "month" in features
        assert "day_of_year" in features
        assert "hour" in features
        assert "quarter" in features

        # Each feature should be [sin, cos] pair
        assert len(features["day_of_week"]) == 2
        assert len(features["month"]) == 2

    def test_encode_cyclical_same_dow(self):
        """Same day of week should have similar encoding."""
        encoder = TemporalEncoder()

        # Two Mondays
        d1 = datetime(2024, 1, 1)  # Monday
        d2 = datetime(2024, 1, 8)  # Monday

        f1 = encoder.encode_cyclical(d1)
        f2 = encoder.encode_cyclical(d2)

        # Day of week should be identical
        assert f1["day_of_week"] == f2["day_of_week"]

    def test_encode_document(self):
        """Test document encoding returns all features."""
        encoder = TemporalEncoder()

        timestamp = datetime(2024, 6, 15)
        features = encoder.encode_document(timestamp)

        assert isinstance(features, TemporalFeatures)
        assert features.timestamp == timestamp
        assert len(features.temporal_vector) == 64
        assert 0 <= features.decay_weight <= 1.0
        assert features.cyclical_features is not None

    def test_decay_weight_recent(self):
        """Recent documents should have high decay weight."""
        encoder = TemporalEncoder()

        recent = datetime.utcnow() - timedelta(days=1)
        features = encoder.encode_document(recent)

        # Recent document should have decay weight close to 1
        assert features.decay_weight > 0.95

    def test_decay_weight_old(self):
        """Old documents should have low decay weight."""
        encoder = TemporalEncoder()

        old = datetime.utcnow() - timedelta(days=DEFAULT_HALF_LIFE_DAYS)
        features = encoder.encode_document(old)

        # Old document should have decay weight close to 0.5
        assert features.decay_weight < 0.6


class TestTemporalQueryParser:
    """Test TemporalQueryParser."""

    def test_no_temporal(self):
        """Non-temporal query returns no temporal info."""
        parser = TemporalQueryParser()

        result = parser.parse("What are transformers?")

        assert result.has_temporal is False
        assert result.time_range is None

    def test_last_month(self):
        """'Last month' extracts correct range."""
        parser = TemporalQueryParser()

        result = parser.parse("What did I conclude last month?")

        assert result.has_temporal is True
        assert result.granularity == "month"
        assert result.recency_weight == 1.0
        assert result.relative_reference == "last_month"
        assert result.time_range is not None

        start, end = result.time_range
        assert end >= start

    def test_this_quarter(self):
        """'This quarter' extracts current quarter."""
        parser = TemporalQueryParser()

        result = parser.parse("What did I write this quarter?")

        assert result.has_temporal is True
        assert result.granularity == "quarter"
        assert result.relative_reference == "this_quarter"

    def test_recently(self):
        """'Recently' defaults to last 30 days."""
        parser = TemporalQueryParser()

        result = parser.parse("What did I find recently?")

        assert result.has_temporal is True
        assert result.relative_reference == "recent"
        assert result.recency_weight == 1.0

    def test_last_week(self):
        """'Last week' extracts correct range."""
        parser = TemporalQueryParser()

        result = parser.parse("Show me notes from last week")

        assert result.has_temporal is True
        assert result.granularity == "week"
        assert result.recency_weight == 1.0

    def test_past_days(self):
        """'Past 5 days' extracts correct range."""
        parser = TemporalQueryParser()

        result = parser.parse("What happened in the past 5 days?")

        assert result.has_temporal is True
        assert result.granularity == "day"

    def test_chitchat(self):
        """Handles casual queries without temporal intent."""
        parser = TemporalQueryParser()

        queries = [
            "hello there",
            "how are you",
            "thanks",
            "bye",
        ]

        for q in queries:
            result = parser.parse(q)
            assert result.has_temporal is False


class TestCalculateTemporalScore:
    """Test temporal score calculation."""

    def test_no_temporal_returns_base(self):
        """Without temporal query, returns base score."""
        query = TemporalQuery(has_temporal=False)
        score = calculate_temporal_score(
            doc_timestamp=datetime.utcnow(),
            query=query,
            base_score=0.8,
        )

        assert score == 0.8

    def test_within_time_range(self):
        """Document within time range keeps score."""
        now = datetime.utcnow()
        query = TemporalQuery(
            has_temporal=True,
            time_range=(now - timedelta(days=7), now),
            recency_weight=0.5,
        )

        doc_time = now - timedelta(days=3)
        score = calculate_temporal_score(
            doc_timestamp=doc_time,
            query=query,
            base_score=0.8,
        )

        assert 0 < score <= 1.0

    def test_outside_time_range_penalized(self):
        """Document outside time range gets penalized."""
        now = datetime.utcnow()
        query = TemporalQuery(
            has_temporal=True,
            time_range=(now - timedelta(days=7), now),
            recency_weight=0.5,
        )

        # Document from 30 days ago
        doc_time = now - timedelta(days=30)
        score = calculate_temporal_score(
            doc_timestamp=doc_time,
            query=query,
            base_score=0.8,
        )

        # Should be heavily penalized
        assert score < 0.1


class TestTemporalAgent:
    """Test temporal_agent as LangGraph node."""

    @pytest.mark.asyncio
    async def test_temporal_skips_chitchat(self):
        """Temporal agent skips for chitchat queries."""
        state = {
            "query": "hello",
            "query_type": "chitchat",
        }

        result = await temporal_agent(state)

        assert result["temporal_trace"].get("skipped") is True
        assert result["temporal_query"] is not None
        assert result["temporal_query"].has_temporal is False

    @pytest.mark.asyncio
    async def test_temporal_detects_last_month(self):
        """Temporal agent detects 'last month' query."""
        state = {
            "query": "What did I conclude last month?",
            "rewritten_query": "What did I conclude last month?",
            "query_type": "rag",
        }

        result = await temporal_agent(state)

        assert result["temporal_trace"].get("has_temporal") is True
        assert result["temporal_trace"].get("granularity") == "month"
        assert result["temporal_trace"].get("recency_weight") == 1.0

    @pytest.mark.asyncio
    async def test_temporal_no_temporal_query(self):
        """Temporal agent handles non-temporal queries."""
        state = {
            "query": "What are transformers?",
            "rewritten_query": "What are transformers?",
            "query_type": "rag",
        }

        result = await temporal_agent(state)

        assert result["temporal_trace"].get("has_temporal") is False
        assert result["temporal_query"].has_temporal is False

    @pytest.mark.asyncio
    async def test_temporal_trace_has_time_range(self):
        """Temporal trace includes parsed time range."""
        state = {
            "query": "Notes from the last quarter",
            "rewritten_query": "Notes from the last quarter",
            "query_type": "rag",
        }

        result = await temporal_agent(state)

        trace = result["temporal_trace"]
        if trace.get("has_temporal"):
            assert "time_range" in trace or "granularity" in trace


class TestIntegration:
    """Integration tests."""

    def test_temporal_encoder_consistency(self):
        """Temporal encoder produces consistent results."""
        encoder = TemporalEncoder()

        # Same input = same output
        t = datetime(2024, 6, 15, 10, 30)
        v1 = encoder.encode_absolute(t)
        v2 = encoder.encode_absolute(t)

        assert v1 == v2

    def test_temporal_encoder_deterministic(self):
        """Encoder is deterministic across instances with same reference."""
        t = datetime(2024, 6, 15)
        ref = datetime(2020, 1, 1)

        encoder1 = TemporalEncoder(reference_date=ref)
        encoder2 = TemporalEncoder(reference_date=ref)

        # With same reference date, should produce same encoding
        v1 = encoder1.encode_absolute(t)
        v2 = encoder2.encode_absolute(t)

        assert v1 == v2

    @pytest.mark.asyncio
    async def test_temporal_agent_idempotent(self):
        """Multiple calls don't corrupt state."""
        state = {
            "query": "Notes from last week",
            "rewritten_query": "Notes from last week",
            "query_type": "rag",
        }

        result1 = await temporal_agent(state)
        result2 = await temporal_agent(result1)

        # Results should be consistent
        assert result1["temporal_trace"] == result2["temporal_trace"]
