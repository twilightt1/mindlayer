"""
Integration tests for the SourceSyncService dispatcher.

Tests the sync flow components that can be tested with mocks or minimal setup.
Focus on connector validation, error handling, and result creation.
"""
import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.ingestion.types import ConnectorItem, ItemError, SyncResult


class MockConnector:
    """Mock connector for testing."""
    
    def __init__(self, items=None, errors=None, cursor=None, raise_fetch=None, raise_validate=None):
        self.items = items or []
        self.errors = errors or []
        self.last_cursor = cursor
        self.config = {}
        self.fetch_errors = self.errors
        self._raise_fetch = raise_fetch
        self._raise_validate = raise_validate
    
    def validate_config(self):
        if self._raise_validate:
            raise self._raise_validate
    
    async def fetch_items(self):
        if self._raise_fetch:
            raise self._raise_fetch
        return self.items


class TestSyncResultCreation:
    """Tests for SyncResult creation and initialization."""

    def test_sync_result_initial_state(self):
        """SyncResult should have correct initial values."""
        started = datetime.now(UTC)
        result = SyncResult(
            source_id="test-source",
            started_at=started,
            finished_at=started,
        )
        
        assert result.source_id == "test-source"
        assert result.items_yielded == 0
        assert result.memories_added == 0
        assert result.memories_updated == 0
        assert result.memories_skipped == 0
        assert len(result.errors) == 0
        assert len(result.notes) == 0

    def test_item_error_creation(self):
        """ItemError should store message and source_ref."""
        error = ItemError(message="Test error", source_ref="ref123")
        
        assert error.message == "Test error"
        assert error.source_ref == "ref123"

    def test_sync_result_with_errors(self):
        """SyncResult should track errors."""
        result = SyncResult(
            source_id="test",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        result.errors.append(ItemError(message="Error 1"))
        result.errors.append(ItemError(message="Error 2", source_ref="ref"))
        
        assert len(result.errors) == 2
        assert result.errors[0].message == "Error 1"
        assert result.errors[1].source_ref == "ref"


class TestConnectorValidation:
    """Tests for connector validation in sync flow."""

    @pytest.mark.asyncio
    async def test_no_connector_for_source_type(self, db):
        """Should return error when no connector registered."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "nonexistent_connector"
        source.config = {}
        source.sync_cursor = None
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", side_effect=KeyError("No connector")):
            result = await service.sync(source)
        
        assert len(result.errors) == 1
        assert "No connector" in result.errors[0].message

    @pytest.mark.asyncio
    async def test_invalid_connector_config(self, db):
        """Should return error when connector config is invalid."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "rss"
        source.config = {}
        source.sync_cursor = None
        
        mock_connector = MockConnector(raise_validate=ValueError("Missing feed_url"))
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", return_value=mock_connector):
            result = await service.sync(source)
        
        assert len(result.errors) >= 1
        assert "Config invalid" in result.errors[0].message


class TestFetchErrors:
    """Tests for fetch error handling."""

    @pytest.mark.asyncio
    async def test_connector_fetch_error(self, db):
        """Should record errors when connector fetch fails."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "rss"
        source.config = {}
        source.sync_cursor = None
        
        mock_connector = MockConnector(raise_fetch=Exception("Network error"))
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", return_value=mock_connector):
            result = await service.sync(source)
        
        assert len(result.errors) >= 1
        assert "Fetch failed" in result.errors[0].message

    @pytest.mark.asyncio
    async def test_partial_fetch_errors_recorded(self, db):
        """Should record per-item fetch errors without failing sync."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "web_clip"
        source.config = {}
        source.sync_cursor = None
        
        # Empty items - just testing error recording
        mock_connector = MockConnector(items=[])
        mock_connector.fetch_errors = [
            ItemError(message="Failed to fetch https://bad-url.com", source_ref="bad-url"),
            ItemError(message="Failed to parse https://broken.com", source_ref="broken"),
        ]
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", return_value=mock_connector):
            result = await service.sync(source)
        
        assert result.items_yielded == 0
        assert len(result.errors) == 2
        assert any("bad-url" in err.source_ref for err in result.errors if err.source_ref)


class TestIncrementalSync:
    """Tests for incremental sync behavior."""

    @pytest.mark.asyncio
    async def test_cursor_passed_to_connector(self, db):
        """Should pass sync_cursor to connector for incremental sync."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "rss"
        source.config = {"feed_url": "https://example.com/feed"}
        source.sync_cursor = "2025-01-01T00:00:00"
        
        captured_cursor = None
        
        def capture_connector(source_type, config, initial_cursor=None):
            nonlocal captured_cursor
            captured_cursor = initial_cursor
            return MockConnector(items=[])
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", side_effect=capture_connector):
            await service.sync(source)
        
        assert captured_cursor == "2025-01-01T00:00:00"

    @pytest.mark.asyncio
    async def test_cursor_updated_after_sync(self, db):
        """Should update source.sync_cursor after sync."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "rss"
        source.config = {"feed_url": "https://example.com/feed"}
        source.sync_cursor = None
        
        mock_connector = MockConnector(items=[], cursor="2025-06-15T12:00:00")
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", return_value=mock_connector):
            await service.sync(source)
        
        assert source.sync_cursor == "2025-06-15T12:00:00"


class TestConnectorItemValidation:
    """Tests for ConnectorItem validation."""

    def test_connector_item_required_fields(self):
        """ConnectorItem should require title and content."""
        item = ConnectorItem(
            title="Test",
            content="Content",
        )
        
        assert item.title == "Test"
        assert item.content == "Content"
        assert item.source_ref is None
        assert item.tags == []

    def test_connector_item_all_fields(self):
        """ConnectorItem should accept all fields."""
        item = ConnectorItem(
            title="Full Item",
            content="Full content",
            summary="Summary text",
            source_ref="ref-123",
            source_url="https://example.com",
            source_excerpt="Excerpt...",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
        )
        
        assert item.title == "Full Item"
        assert item.summary == "Summary text"
        assert item.source_ref == "ref-123"
        assert item.source_url == "https://example.com"
        assert item.source_excerpt == "Excerpt..."
        assert item.tags == ["tag1", "tag2"]
        assert item.metadata == {"key": "value"}

    def test_connector_item_captured_at_default(self):
        """ConnectorItem should have captured_at with default."""
        item = ConnectorItem(
            title="Test",
            content="Content",
        )
        
        # Should have a default captured_at (near now)
        assert item.captured_at is not None
        assert item.captured_at.year == datetime.now(UTC).year


class TestErrorPropagation:
    """Tests for error propagation in sync flow."""

    @pytest.mark.asyncio
    async def test_not_implemented_error(self, db):
        """Should handle NotImplementedError from connector."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "not_impl"
        source.config = {}
        source.sync_cursor = None
        
        mock_connector = MockConnector(raise_fetch=NotImplementedError("Connector not ready"))
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", return_value=mock_connector):
            result = await service.sync(source)
        
        assert len(result.errors) >= 1
        assert "not yet implemented" in result.errors[0].message.lower() or "not ready" in result.errors[0].message.lower()


class TestSyncNotes:
    """Tests for sync result notes."""

    @pytest.mark.asyncio
    async def test_no_connector_adds_note(self, db):
        """Should add note when no connector is registered."""
        from app.ingestion.dispatcher import SourceSyncService
        
        source = MagicMock()
        source.id = uuid4()
        source.source_type = "unknown"
        source.config = {}
        source.sync_cursor = None
        
        service = SourceSyncService(db)
        
        with patch("app.ingestion.dispatcher.get_connector_for_source", side_effect=KeyError("No connector")):
            result = await service.sync(source)
        
        assert len(result.notes) >= 1
        assert any("connector" in note.lower() for note in result.notes)
