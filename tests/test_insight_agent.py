"""
Tests for Insight Cards Agent - Proactive Discovery Feature

Q2 Growth Track: "What I Didn't Know I Knew"
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.insight_agent import (
    DocumentReference,
    InsightCard,
    InsightGenerationRequest,
    InsightGenerationResult,
    InsightStatus,
    InsightSurpriseLevel,
    InsightType,
    calculate_insight_relevance,
    create_insight_card,
    generate_insights,
    refresh_insights,
    update_user_preferences,
)


class TestDocumentReference:
    """Test DocumentReference dataclass."""

    def test_creation(self):
        """Test creating a DocumentReference."""
        ref = DocumentReference(
            document_id="doc-123",
            title="Test Document",
            excerpt="Important passage...",
            relevance_score=0.85,
        )

        assert ref.document_id == "doc-123"
        assert ref.title == "Test Document"
        assert ref.relevance_score == 0.85


class TestInsightCard:
    """Test InsightCard dataclass."""

    def test_creation(self):
        """Test creating an InsightCard."""
        card = InsightCard(
            user_id="user-123",
            title="You connected X and Y in different contexts",
            insight_type=InsightType.CONNECTION,
            summary="Found unexpected link between projects",
            detail="Detailed explanation...",
            sources=[
                DocumentReference(
                    document_id="doc-1",
                    title="Project X Notes",
                    excerpt="Discussed feature A...",
                    relevance_score=0.9,
                ),
            ],
            source_count=1,
            surprise_level=InsightSurpriseLevel.HIGH,
            confidence=0.85,
        )

        assert card.user_id == "user-123"
        assert card.insight_type == InsightType.CONNECTION
        assert card.surprise_level == InsightSurpriseLevel.HIGH
        assert card.confidence == 0.85
        assert card.status == InsightStatus.NEW

    def test_to_summary(self):
        """Test to_summary method returns emoji and title."""
        card = InsightCard(
            user_id="user-123",
            title="Connection between A and B",
            insight_type=InsightType.CONNECTION,
            summary="Test summary",
            detail="Test detail",
        )

        summary = card.to_summary()
        assert "🔗" in summary  # Connection emoji
        assert "Connection between A and B" in summary


class TestInsightType:
    """Test InsightType enum."""

    def test_all_types_exist(self):
        """All insight types should exist."""
        assert InsightType.CONNECTION.value == "connection"
        assert InsightType.CONTRADICTION.value == "contradiction"
        assert InsightType.EVOLUTION.value == "evolution"
        assert InsightType.PATTERN.value == "pattern"
        assert InsightType.GAP.value == "gap"
        assert InsightType.CONFIRMATION.value == "confirmation"
        assert InsightType.SYNTHESIS.value == "synthesis"

    def test_insight_type_from_string(self):
        """Test creating InsightType from string value."""
        insight_type = InsightType("connection")
        assert insight_type == InsightType.CONNECTION


class TestInsightSurpriseLevel:
    """Test InsightSurpriseLevel enum."""

    def test_all_levels_exist(self):
        """All surprise levels should exist."""
        assert InsightSurpriseLevel.LOW.value == "low"
        assert InsightSurpriseLevel.MEDIUM.value == "medium"
        assert InsightSurpriseLevel.HIGH.value == "high"


class TestInsightStatus:
    """Test InsightStatus enum."""

    def test_all_statuses_exist(self):
        """All statuses should exist."""
        assert InsightStatus.NEW.value == "new"
        assert InsightStatus.SHOWN.value == "shown"
        assert InsightStatus.DISMISSED.value == "dismissed"
        assert InsightStatus.SAVED.value == "saved"
        assert InsightStatus.EXPIRED.value == "expired"


class TestInsightGenerationRequest:
    """Test InsightGenerationRequest dataclass."""

    def test_creation(self):
        """Test creating an InsightGenerationRequest."""
        request = InsightGenerationRequest(
            user_id="user-123",
            document_ids=["doc-1", "doc-2"],
            focus_topics=["AI", "Research"],
            exclude_insights_older_than_days=30,
        )

        assert request.user_id == "user-123"
        assert len(request.document_ids) == 2
        assert "AI" in request.focus_topics
        assert request.exclude_insights_older_than_days == 30


class TestInsightGenerationResult:
    """Test InsightGenerationResult dataclass."""

    def test_creation(self):
        """Test creating an InsightGenerationResult."""
        card = InsightCard(
            user_id="user-123",
            title="Test insight",
            insight_type=InsightType.CONNECTION,
            summary="Test",
            detail="Test detail",
        )

        result = InsightGenerationResult(
            insights=[card],
            generation_time_ms=1500.0,
            documents_analyzed=10,
        )

        assert len(result.insights) == 1
        assert result.generation_time_ms == 1500.0
        assert result.documents_analyzed == 10
        assert result.error is None


class TestGenerateInsights:
    """Test generate_insights function."""

    @pytest.mark.asyncio
    @patch("app.agents.insight_agent._get_client")
    async def test_generate_insights_success(self, mock_get_client):
        """Test successful insight generation."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"insights": [{"title": "You connected X and Y", "insight_type": "connection", "summary": "Found link", "detail": "Detailed explanation", "source_count": 2, "surprise_level": "high", "confidence": 0.85, "sources": [{"document_id": "doc-1", "title": "Doc 1", "excerpt": "Passage...", "relevance_score": 0.9}]}]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        documents = [
            {"id": "doc-1", "title": "Document 1", "content": "Content about X", "created_at": "2025-01-01"},
        ]

        insights = await generate_insights(
            documents=documents,
            recent_activity=["Query about X"],
            focus_topics=["AI"],
        )

        assert len(insights) == 1
        assert insights[0]["title"] == "You connected X and Y"
        assert insights[0]["insight_type"] == "connection"

    @pytest.mark.asyncio
    @patch("app.agents.insight_agent._get_client")
    async def test_generate_insights_error_handling(self, mock_get_client):
        """Test insight generation handles errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client

        documents = [{"id": "doc-1", "title": "Test", "content": "Content"}]

        insights = await generate_insights(
            documents=documents,
            recent_activity=[],
            focus_topics=[],
        )

        assert insights == []


class TestCreateInsightCard:
    """Test create_insight_card function."""

    @pytest.mark.asyncio
    async def test_create_from_dict(self):
        """Test creating InsightCard from LLM output dict."""
        insight_data = {
            "title": "Unexpected connection found",
            "insight_type": "connection",
            "summary": "You mentioned X in multiple places",
            "detail": "Detailed explanation of the connection",
            "source_count": 3,
            "surprise_level": "high",
            "confidence": 0.9,
            "sources": [
                {"document_id": "doc-1", "title": "Doc 1", "excerpt": "Excerpt 1", "relevance_score": 0.8},
                {"document_id": "doc-2", "title": "Doc 2", "excerpt": "Excerpt 2", "relevance_score": 0.7},
            ],
        }

        card = await create_insight_card(insight_data, "user-123")

        assert card.user_id == "user-123"
        assert card.title == "Unexpected connection found"
        assert card.insight_type == InsightType.CONNECTION
        assert card.surprise_level == InsightSurpriseLevel.HIGH
        assert card.confidence == 0.9
        assert len(card.sources) == 2

    @pytest.mark.asyncio
    async def test_invalid_insight_type_defaults_to_connection(self):
        """Test invalid insight type defaults to connection."""
        insight_data = {
            "title": "Test",
            "insight_type": "invalid_type",
            "summary": "Summary",
            "detail": "Detail",
            "surprise_level": "medium",
            "confidence": 0.5,
        }

        card = await create_insight_card(insight_data, "user-123")

        assert card.insight_type == InsightType.CONNECTION


class TestCalculateInsightRelevance:
    """Test calculate_insight_relevance function."""

    def test_basic_relevance(self):
        """Test basic relevance score."""
        card = InsightCard(
            user_id="user-123",
            title="AI research findings",
            insight_type=InsightType.CONNECTION,
            summary="Connection between topics",
            detail="Detail",
            surprise_level=InsightSurpriseLevel.MEDIUM,
            relevance_score=0.7,
        )

        user_prefs = {"focus_topics": [], "insight_types": {}}

        score = calculate_insight_relevance(card, user_prefs)

        # Base score + medium surprise boost
        assert score > 0.7

    def test_topic_boost(self):
        """Test boost for focus topic match."""
        card = InsightCard(
            user_id="user-123",
            title="AI research findings",
            insight_type=InsightType.CONNECTION,
            summary="Connection between AI topics",
            detail="Detail",
            surprise_level=InsightSurpriseLevel.LOW,
            relevance_score=0.5,
        )

        user_prefs = {"focus_topics": ["AI", "Machine Learning"], "insight_types": {}}

        score = calculate_insight_relevance(card, user_prefs)

        # Should be boosted due to AI topic match
        assert score > 0.5

    def test_shown_penalty(self):
        """Test penalty for repeatedly shown but not saved."""
        card = InsightCard(
            user_id="user-123",
            title="Test insight",
            insight_type=InsightType.CONNECTION,
            summary="Summary",
            detail="Detail",
            surprise_level=InsightSurpriseLevel.LOW,
            shown_count=5,
            status=InsightStatus.SHOWN,
            relevance_score=0.5,
        )

        user_prefs = {"focus_topics": [], "insight_types": {}}

        score = calculate_insight_relevance(card, user_prefs)

        # Should be penalized
        assert score < 0.5


class TestUpdateUserPreferences:
    """Test update_user_preferences function."""

    @pytest.mark.asyncio
    async def test_preferences_from_feedback(self):
        """Test updating preferences from feedback."""
        feedback = [
            {"insight_type": "connection", "helpful": True},
            {"insight_type": "connection", "helpful": True},
            {"insight_type": "pattern", "helpful": False},
            {"insight_type": "gap", "helpful": True},
        ]

        prefs = await update_user_preferences("user-123", feedback)

        assert "focus_topics" in prefs
        assert "insight_types" in prefs
        # Connection: 2 helpful, 0 dismissed = 1.0 score
        assert prefs["insight_types"]["connection"] == 1.0
        # Pattern: 0 helpful, 1 dismissed = 0.0 score
        assert prefs["insight_types"]["pattern"] == 0.0
        # Gap: 1 helpful, 0 dismissed = 1.0 score
        assert prefs["insight_types"]["gap"] == 1.0


class TestRefreshInsights:
    """Test refresh_insights function."""

    @pytest.mark.asyncio
    @patch("app.agents.insight_agent._get_client")
    async def test_refresh_returns_updates(self, mock_get_client):
        """Test refresh returns update recommendations."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"updates": [{"insight_id": "insight-1", "action": "keep", "new_insight_score": 0.8}, {"insight_id": "insight-2", "action": "expire", "new_insight_score": 0.1}]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        existing = [{"id": "insight-1", "title": "Old insight 1", "summary": "Summary 1"}]

        updates = await refresh_insights(
            existing_insights=existing,
            recent_activity=["New query"],
            new_documents=[{"id": "doc-new", "title": "New Document"}],
        )

        assert len(updates) == 2
        assert updates[0]["action"] == "keep"
        assert updates[1]["action"] == "expire"

    @pytest.mark.asyncio
    @patch("app.agents.insight_agent._get_client")
    async def test_refresh_error_handling(self, mock_get_client):
        """Test refresh handles errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client

        updates = await refresh_insights(
            existing_insights=[],
            recent_activity=[],
            new_documents=[],
        )

        assert updates == []


# ─── Integration-style tests (mocking external dependencies) ─────────────────

class TestInsightAgentIntegration:
    """Integration tests for insight agent flow."""

    @pytest.mark.asyncio
    @patch("app.agents.insight_agent._get_client")
    async def test_full_generation_flow(self, mock_get_client):
        """Test complete insight generation flow."""
        # Mock LLM response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"insights": [{"title": "You discussed X in multiple documents", "insight_type": "pattern", "summary": "Recurring theme found", "detail": "Detailed explanation of the pattern", "source_count": 5, "surprise_level": "medium", "confidence": 0.88, "sources": [{"document_id": "doc-1", "title": "Doc 1", "excerpt": "Excerpt", "relevance_score": 0.9}]}]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        # Test data
        documents = [
            {"id": "doc-1", "title": "Research Notes", "content": "Notes about X and Y", "created_at": "2025-01-15"},
            {"id": "doc-2", "title": "Meeting Notes", "content": "Discussed X feature", "created_at": "2025-01-20"},
        ]

        InsightGenerationRequest(
            user_id="user-123",
            document_ids=["doc-1", "doc-2"],
            focus_topics=["X"],
        )

        # Generate insights
        result = await generate_insights(
            documents=documents,
            recent_activity=["Query about X"],
            focus_topics=["X"],
        )

        assert len(result) == 1
        assert result[0]["insight_type"] == "pattern"

        # Create card
        card = await create_insight_card(result[0], "user-123")
        assert card.insight_type == InsightType.PATTERN
        assert card.confidence == 0.88

        # Calculate relevance
        prefs = {"focus_topics": ["X"], "insight_types": {}}
        score = calculate_insight_relevance(card, prefs)
        assert score > 0.88  # Should be boosted by topic match
