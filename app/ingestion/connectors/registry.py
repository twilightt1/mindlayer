"""
Registry that maps a `Source.source_type` to a connector class.

Adding a new connector:
    1. Implement the connector in `app/ingestion/connectors/<name>.py`
    2. Import it here and add it to `REGISTRY`

The dispatcher calls `get_connector_for_source(source)` to get the
right class for a given Source row.
"""
from __future__ import annotations

from typing import Type

from app.ingestion.base import BaseConnector
from app.ingestion.connectors.manual import ManualNoteConnector
from app.ingestion.connectors.file_upload import FileUploadConnector
from app.ingestion.connectors.web_clipper import WebClipperConnector
from app.ingestion.connectors.google_drive import GoogleDriveConnector
from app.ingestion.connectors.notion import NotionConnector
from app.ingestion.connectors.gmail import GmailConnector


# Map source_type string -> connector class
REGISTRY: dict[str, Type[BaseConnector]] = {
    "manual":        ManualNoteConnector,
    "file_upload":   FileUploadConnector,
    "web_clipper":   WebClipperConnector,
    "google_drive":  GoogleDriveConnector,
    "notion":        NotionConnector,
    "gmail":         GmailConnector,
}


def get_connector_for_source(
    source_type: str,
    config: dict | None = None,
    initial_cursor: str | None = None,
) -> BaseConnector:
    """
    Return a connector instance for the given source_type.
    Raises `KeyError` if no connector is registered for that type.

    `initial_cursor` is the pagination token from the last sync (from
    `Source.sync_cursor`). Remote connectors (Drive/Notion/Gmail) use
    it to resume where the previous sync left off. Local connectors
    (manual/file_upload/web_clipper) ignore it.
    """
    try:
        cls = REGISTRY[source_type]
    except KeyError as e:
        raise KeyError(f"No connector registered for source_type='{source_type}'") from e
    return cls(config=config, initial_cursor=initial_cursor)
