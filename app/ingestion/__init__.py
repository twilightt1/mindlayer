"""
MindLayer ingestion package.

A connector is a class that knows how to pull "memories" from a single
source type (manual notes, file uploads, web pages, Google Drive,
Notion, Gmail, etc.) and produce a uniform `ConnectorItem` stream.

Connectors are **stateless wrappers** around a `Source` row — they
read the `config` JSONB for credentials and use httpx / a vendor SDK
to talk to the remote system. The `SourceSyncService` (dispatcher)
takes the items each connector yields, dedupes them against existing
memories, and persists them as `Memory` + `MemorySource` rows.

The connector layer is the only place that knows the specifics of a
remote system. Everything else (the dispatcher, the API, the agent)
talks to connectors via the abstract `BaseConnector` interface.
"""
from app.ingestion.types import ConnectorItem, SyncResult
from app.ingestion.base import BaseConnector
from app.ingestion.dispatcher import SourceSyncService
from app.ingestion.connectors.registry import get_connector_for_source

__all__ = [
    "ConnectorItem",
    "SyncResult",
    "BaseConnector",
    "SourceSyncService",
    "get_connector_for_source",
]
