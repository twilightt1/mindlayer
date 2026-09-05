"""Tests for compression-before-storage (feature-flagged, best-effort)."""
from __future__ import annotations

import json

import pytest

from app.services import compression_service
from app.services.compression_service import (
    COMPRESSION_MARKER,
    _parse_verdict,
    compress_memory,
    should_compress,
)


@pytest.fixture()
def compression_on(monkeypatch):
    monkeypatch.setattr(compression_service.settings, "COMPRESSION_ENABLED", True)


def test_gate_off_by_default():
    assert should_compress("x" * 5000) is False


def test_gate_on_requires_length(compression_on):
    assert should_compress("short") is False
    assert should_compress("x" * 2000) is True


def test_parse_verdict_accepts_valid():
    verdict = _parse_verdict(json.dumps({"summary": "s", "content": "c"}), "original-longer")
    assert verdict == ("s", "c")


def test_parse_verdict_rejects_growth():
    assert _parse_verdict(json.dumps({"summary": "s", "content": "x" * 50}), "short") is None


def test_parse_verdict_rejects_malformed():
    assert _parse_verdict("not json", "original") is None
    assert _parse_verdict(json.dumps({"summary": ""}), "original") is None


async def test_compress_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(compression_service.settings, "COMPRESSION_ENABLED", False)
    assert await compress_memory("x" * 5000) is None


async def test_compress_no_key_degrades(monkeypatch, compression_on):
    monkeypatch.setattr(compression_service.settings, "OPENAI_API_KEY", "")
    assert await compress_memory("x" * 3000) is None


async def test_compress_success_adds_marker(monkeypatch, compression_on):
    class _FakeMsg:
        content = json.dumps({"summary": "chose pgvector", "content": "Decision: pgvector over chroma"})

    class _FakeChoice:
        message = _FakeMsg()

    class _FakeCompletion:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        async def create(self, **kwargs):
            return _FakeCompletion()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeOpenAI:
        def __init__(self, **kw):
            self.chat = _FakeChat()

    monkeypatch.setattr(compression_service.settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("openai.AsyncOpenAI", _FakeOpenAI)
    long_text = "Decision: pgvector. " + "filler " * 600
    result = await compress_memory(long_text)
    assert result is not None
    summary, compressed = result
    assert summary == "chose pgvector"
    assert compressed.endswith(COMPRESSION_MARKER)
    assert len(compressed) < len(long_text)


async def test_compress_llm_failure_degrades(monkeypatch, compression_on):
    class _Broken:
        def __init__(self, **kw):
            raise RuntimeError("llm down")

    monkeypatch.setattr(compression_service.settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("openai.AsyncOpenAI", _Broken)
    assert await compress_memory("x" * 3000) is None
