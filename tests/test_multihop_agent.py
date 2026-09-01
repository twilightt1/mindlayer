"""
Tests for Multi-hop Reasoning Agent

Reference: EfficientRAG - EMNLP 2024
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.multihop_agent import (
    HopResult,
    MultiHopResult,
    branch_solve_merge,
    detect_multihop,
    generate_subqueries,
    multihop_agent,
    synthesize_answer,
)


class TestHopResult:
    """Test HopResult dataclass."""

    def test_hop_result_creation(self):
        """Test creating a HopResult."""
        result = HopResult(
            hop_number=1,
            subquery="What is X?",
            retrieved_context="X is a technology...",
            answer_fragment="X is a type of AI model",
            confidence=0.85,
        )

        assert result.hop_number == 1
        assert result.subquery == "What is X?"
        assert result.confidence == 0.85


class TestMultiHopResult:
    """Test MultiHopResult dataclass."""

    def test_multihop_result_creation(self):
        """Test creating a MultiHopResult."""
        hop = HopResult(
            hop_number=1,
            subquery="test",
            retrieved_context="context",
            answer_fragment="answer",
            confidence=0.8,
        )

        result = MultiHopResult(
            is_multihop=True,
            hop_count=2,
            hop_results=[hop],
            synthesized_answer="Final answer",
            confidence=0.8,
            reasoning_chain="Hop 1...",
        )

        assert result.is_multihop is True
        assert result.hop_count == 2


class TestDetectMultihop:
    """Test multi-hop detection."""

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_detect_multihop_true(self, mock_get_client):
        """Detects multi-hop query correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_multihop": true, "hop_count": 2, "reasoning": "Compares X and Y", "key_entities": ["X", "Y"], "relationship_type": "comparison"}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await detect_multihop("How does X compare to Y?")

        assert result["is_multihop"] is True
        assert result["hop_count"] == 2
        assert "X" in result["key_entities"]

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_detect_single_hop(self, mock_get_client):
        """Detects single-hop query correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"is_multihop": false, "hop_count": 1, "reasoning": "Direct question", "key_entities": [], "relationship_type": "none"}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await detect_multihop("What is machine learning?")

        assert result["is_multihop"] is False
        assert result["hop_count"] == 1

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_detect_api_error(self, mock_get_client):
        """Handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        result = await detect_multihop("test query")

        assert result["is_multihop"] is False
        assert result["hop_count"] == 1
        assert "failed" in result["reasoning"].lower()


class TestGenerateSubqueries:
    """Test subquery generation."""

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_generate_subqueries_success(self, mock_get_client):
        """Successfully generates subqueries."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"subqueries": [{"hop": 1, "query": "What is X?", "purpose": "define X"}, {"hop": 2, "query": "How does X affect Y?", "purpose": "connect X and Y"}]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await generate_subqueries("How does X affect Y?", 2)

        assert len(result) == 2
        assert result[0]["hop"] == 1
        assert result[1]["hop"] == 2

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_generate_fallback(self, mock_get_client):
        """Falls back to original query on error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        result = await generate_subqueries("original query", 3)

        assert len(result) == 3
        assert all(sq["query"] == "original query" for sq in result)

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_generate_enough_subqueries(self, mock_get_client):
        """Ensures enough subqueries are generated."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Only return 1 subquery when 3 needed
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"subqueries": [{"hop": 1, "query": "test", "purpose": "test"}]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await generate_subqueries("test", 3)

        assert len(result) == 3


class TestSynthesizeAnswer:
    """Test answer synthesis."""

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_synthesize_success(self, mock_get_client):
        """Successfully synthesizes answer."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Synthesized answer about X and Y."))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        hop = HopResult(1, "test", "context", "fragment", 0.8)
        answer, confidence = await synthesize_answer("How does X affect Y?", [hop])

        assert "X" in answer or "Y" in answer
        assert confidence == 0.8

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_synthesize_multiple_hops(self, mock_get_client):
        """Synthesizes from multiple hops."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Combined answer."))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        hops = [
            HopResult(1, "test1", "context1", "fragment1", 0.7),
            HopResult(2, "test2", "context2", "fragment2", 0.9),
        ]
        _answer, confidence = await synthesize_answer("test query", hops)

        assert confidence == 0.8  # Average


class TestMultihopAgent:
    """Test multi-hop agent as LangGraph node."""

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent.settings")
    async def test_multihop_disabled(self, mock_settings):
        """Skips when disabled."""
        mock_settings.MULTIHOP_ENABLED = False

        state = {"query": "test query", "query_type": "rag"}

        result = await multihop_agent(state)

        assert result["multihop_trace"].get("enabled") is False
        assert result["multihop_result"] is None

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent.settings")
    async def test_multihop_skips_chitchat(self, mock_settings):
        """Skips for chitchat queries."""
        mock_settings.MULTIHOP_ENABLED = True

        state = {"query": "hello", "query_type": "chitchat"}

        result = await multihop_agent(state)

        assert result["multihop_trace"].get("skipped") is True

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent.detect_multihop")
    @patch("app.agents.multihop_agent.settings")
    async def test_multihop_single_hop(self, mock_settings, mock_detect):
        """Handles single-hop query."""
        mock_settings.MULTIHOP_ENABLED = True
        mock_settings.MULTIHOP_MAX_HOPS = 3
        mock_detect.return_value = {
            "is_multihop": False,
            "hop_count": 1,
            "reasoning": "Simple question",
            "key_entities": [],
            "relationship_type": "none",
        }

        state = {
            "query": "What is ML?",
            "rewritten_query": "What is machine learning?",
            "query_type": "rag",
        }

        result = await multihop_agent(state)

        assert result["multihop_trace"].get("mode") == "single_hop"
        assert result["multihop_result"] is None

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent.generate_subqueries")
    @patch("app.agents.multihop_agent.detect_multihop")
    @patch("app.agents.multihop_agent.settings")
    async def test_multihop_detected(self, mock_settings, mock_detect, mock_subqueries):
        """Handles multi-hop query correctly."""
        mock_settings.MULTIHOP_ENABLED = True
        mock_settings.MULTIHOP_MAX_HOPS = 3
        mock_detect.return_value = {
            "is_multihop": True,
            "hop_count": 2,
            "reasoning": "Comparison",
            "key_entities": ["X", "Y"],
            "relationship_type": "comparison",
        }
        mock_subqueries.return_value = [
            {"hop": 1, "query": "What is X?", "purpose": "define"},
            {"hop": 2, "query": "How does X compare to Y?", "purpose": "compare"},
        ]

        state = {
            "query": "How does X compare to Y?",
            "rewritten_query": "How does X compare to Y?",
            "query_type": "rag",
        }

        result = await multihop_agent(state)

        assert result["multihop_trace"].get("mode") == "multi_hop"
        assert result["multihop_trace"].get("hop_count") == 2
        assert result["multihop_subqueries"] is not None
        assert result["multihop_pending"] is True


class TestBranchSolveMerge:
    """Test branch-solve-merge helper."""

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_branch_merge_success(self, mock_get_client):
        """Successfully merges branches."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Merged analysis of branches."))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await branch_solve_merge(
            query="Compare X and Y",
            branches=["X", "Y"],
            retrieved_contexts=["Context about X", "Context about Y"],
        )

        assert "Merged" in result or "branches" in result.lower()

    @pytest.mark.asyncio
    @patch("app.agents.multihop_agent._get_client")
    async def test_branch_merge_error(self, mock_get_client):
        """Handles errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        result = await branch_solve_merge(
            query="test",
            branches=["A", "B"],
            retrieved_contexts=["ctx1", "ctx2"],
        )

        assert "failed" in result.lower()
