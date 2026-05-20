"""Smoke test for Phase 2 ingestion layer + rename verification."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
from app.ingestion.connectors.web_clipper import clip_url, WebClipperConnector
from app.ingestion.connectors.google_drive import GoogleDriveConnector
from app.ingestion.connectors.notion import NotionConnector
from app.ingestion.connectors.gmail import GmailConnector


async def main() -> None:
    print("=" * 60)
    print("TEST 1: clip_url with a real public HTML page")
    print("=" * 60)
    try:
        item = await clip_url("https://example.com/")
        print(f"  title         = {item.title!r}")
        print(f"  content[:80]  = {item.content[:80]!r}")
        print(f"  source_ref    = {item.source_ref!r}")
        print(f"  source_url    = {item.source_url!r}")
        print(f"  excerpt[:60]  = {(item.source_excerpt or '')[:60]!r}")
        print(f"  tags          = {item.tags}")
        print(f"  metadata      = {item.metadata}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")

    print()
    print("=" * 60)
    print("TEST 2: WebClipperConnector registry + validate_config")
    print("=" * 60)
    c = WebClipperConnector(config={"urls": ["https://example.com"]})
    print(f"  source_type = {c.source_type}")
    try:
        c.validate_config()
        print("  validate_config(good) = OK")
    except Exception as e:
        print(f"  validate_config(good) = FAIL: {e}")
    c_bad = WebClipperConnector(config={})
    try:
        c_bad.validate_config()
        print("  validate_config(empty) = NOT REJECTED (BUG)")
    except ValueError as e:
        print(f"  validate_config(empty) = rejected OK ({e})")

    print()
    print("=" * 60)
    print("TEST 3: Stub connectors — bad config rejected, good config returns []")
    print("=" * 60)
    for name, cls in [
        ("Drive",  GoogleDriveConnector),
        ("Notion", NotionConnector),
        ("Gmail",  GmailConnector),
    ]:
        empty = cls(config={})
        try:
            empty.validate_config()
            print(f"  {name}: empty config NOT rejected (BUG)")
        except ValueError as e:
            print(f"  {name}: empty config rejected OK")

        if name == "Notion":
            good = cls(config={"token": "x"})
        else:
            good = cls(config={"credentials": {"access_token": "x"}})
        try:
            items = await good.fetch_items()
            print(f"  {name}: fetch_items(good) returned {len(items)} items (expected 0)")
        except Exception as e:
            print(f"  {name}: fetch_items(good) FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
