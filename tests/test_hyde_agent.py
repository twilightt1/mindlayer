"""
Tests for HyDE (Hypothetical Document Embeddings) Agent

Reference: Gao et al., arXiv 2309.08830
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.retrieval.hyde_agent import (
    HypotheticalDocument,
    generate_hypothetical_document,
    hyde_agent,
    refine_passage,
)


class TestHypotheticalDocument:
    """Test HypotheticalDocument dataclass."""

    def test_hypothetical_document_creation(self):
        """Test creating a HypotheticalDocument."""
        doc = HypotheticalDocument(
            passages=["Passage 1", "Passage 2"],
            key_concepts=["concept1", "concept2"],
            combined_text="Passage 1 Passage 2",
        )

        assert len(doc.passages) == 2
        assert len(doc.key_concepts) == 2
        assert doc.combined_text == "Passage 1 Passage 2"


class TestGenerateHypotheticalDocument:
    """Test the hypothetical document generation function."""

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent._get_client")
    async def test_generate_success(self, mock_get_client):
        """Successful generation returns HypotheticalDocument."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='{"passages": ["Passage 1 about transformers.", "Passage 2 about attention."], "key_concepts": ["transformers", "attention"]}'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await generate_hypothetical_document("What are transformers?")

        assert result is not None
        assert len(result.passages) == 2
        assert "transformers" in result.key_concepts
        assert len(result.combined_text) > 0

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent._get_client")
    async def test_generate_with_json_in_markdown(self, mock_get_client):
        """Handles JSON wrapped in markdown code blocks."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(
                content='```json\n{"passages": ["Passage 1"], "key_concepts": ["test"]}\n```'
            ))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await generate_hypothetical_document("test query")

        assert result is not None
        assert len(result.passages) == 1

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent._get_client")
    async def test_generate_api_error(self, mock_get_client):
        """API error returns None gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        result = await generate_hypothetical_document("test query")

        assert result is None

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent._get_client")
    async def test_generate_invalid_json(self, mock_get_client):
        """Invalid JSON returns None gracefully."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is not JSON"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await generate_hypothetical_document("test query")

        assert result is None


class TestRefinePassage:
    """Test passage refinement."""

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent._get_client")
    async def test_refine_success(self, mock_get_client):
        """Successful refinement returns refined text."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Refined passage about transformers and attention mechanisms."))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await refine_passage(
            query="What are transformers?",
            passage="Transformers are models."
        )

        assert "transformers" in result.lower()
        assert "attention" in result.lower()

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent._get_client")
    async def test_refine_error_fallback(self, mock_get_client):
        """Error returns original passage."""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        original = "Original passage"
        result = await refine_passage(query="test", passage=original)

        assert result == original


class TestHyDEAgent:
    """Test HyDE agent as LangGraph node."""

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_disabled(self, mock_settings):
        """When HyDE is disabled, should skip processing."""
        mock_settings.HYDE_ENABLED = False

        state = {"query": "test query"}

        result = await hyde_agent(state)

        assert result["hyde_trace"].get("enabled") is False
        assert result["hyde_result"] is None

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_skips_chitchat(self, mock_settings):
        """HyDE should skip for chitchat queries."""
        mock_settings.HYDE_ENABLED = True

        state = {
            "query": "hello",
            "query_type": "chitchat",
        }

        result = await hyde_agent(state)

        assert result["hyde_trace"].get("enabled") is False
        assert result["hyde_trace"].get("skipped_reason") == "query_type=chitchat"

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_skips_save_note(self, mock_settings):
        """HyDE should skip for save_note queries."""
        mock_settings.HYDE_ENABLED = True

        state = {
            "query": "remember that...",
            "query_type": "save_note",
        }

        result = await hyde_agent(state)

        assert result["hyde_trace"].get("enabled") is False
        assert result["hyde_trace"].get("skipped_reason") == "query_type=save_note"

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.generate_hypothetical_document")
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_generates_hypothetical_doc(self, mock_settings, mock_generate):
        """When HyDE is enabled, should generate hypothetical document."""
        mock_settings.HYDE_ENABLED = True

        mock_generate.return_value = HypotheticalDocument(
            passages=["Passage 1", "Passage 2"],
            key_concepts=["concept1"],
            combined_text="Passage 1 Passage 2",
        )

        state = {
            "query": "test query",
            "rewritten_query": "test query",
            "query_type": "rag",
        }

        result = await hyde_agent(state)

        assert result["hyde_trace"].get("enabled") is True
        assert result["hyde_trace"].get("passage_count") == 2
        assert result["hyde_result"] is not None
        assert len(result["hyde_result"]["passages"]) == 2
        assert result["hyde_result"]["key_concepts"] == ["concept1"]

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.generate_hypothetical_document")
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_generation_failure(self, mock_settings, mock_generate):
        """When generation fails, should continue without HyDE."""
        mock_settings.HYDE_ENABLED = True

        mock_generate.return_value = None  # Simulate failure

        state = {
            "query": "test query",
            "rewritten_query": "test query",
            "query_type": "rag",
        }

        result = await hyde_agent(state)

        assert result["hyde_trace"].get("enabled") is True
        assert result["hyde_trace"].get("generation_failed") is True
        assert result["hyde_result"] is None

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.generate_hypothetical_document")
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_uses_rewritten_query(self, mock_settings, mock_generate):
        """HyDE should use rewritten_query if available."""
        mock_settings.HYDE_ENABLED = True

        mock_generate.return_value = HypotheticalDocument(
            passages=["Passage"],
            key_concepts=[],
            combined_text="Passage",
        )

        state = {
            "query": "original query",
            "rewritten_query": "expanded query about transformers",
            "query_type": "rag",
        }

        await hyde_agent(state)

        # Verify the query passed to generation
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert "transformers" in call_args[0][0]


class TestHyDEEnhancement:
    """Test HyDE enhancement in retrieval."""

    @pytest.mark.asyncio
    @patch("app.retrieval.hyde_agent.settings")
    async def test_hyde_agent_tracks_timing(self, mock_settings):
        """HyDE agent should track generation latency."""
        mock_settings.HYDE_ENABLED = True

        with patch("app.retrieval.hyde_agent.generate_hypothetical_document") as mock_gen:
            mock_gen.return_value = HypotheticalDocument(
                passages=["Test"],
                key_concepts=[],
                combined_text="Test",
            )

            state = {"query": "test", "rewritten_query": "test", "query_type": "rag"}
            result = await hyde_agent(state)

            assert "generation_latency_ms" in result["hyde_trace"]
            assert result["hyde_trace"]["generation_latency_ms"] >= 0
