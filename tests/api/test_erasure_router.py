"""Wiring tests for the erasure-receipts router — CI-safe, no live DB."""
from __future__ import annotations

import uuid

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.api.v1.erasure import router
from app.schemas.Orivory import ErasureReceiptCreate, ErasureReceiptItem


def test_erasure_routes_registered():
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/erasure-receipts" in paths
    assert "/erasure-receipts/{receipt_id}" in paths


def test_erasure_create_rejects_empty_list():
    with pytest.raises(ValidationError):
        ErasureReceiptCreate(memory_ids=[])


def test_erasure_create_rejects_oversized_batch():
    with pytest.raises(ValidationError):
        ErasureReceiptCreate(memory_ids=[uuid.uuid4() for _ in range(101)])


def test_receipt_item_schema_fields():
    assert set(ErasureReceiptItem.model_fields) == {
        "id", "user_id", "requested_memory_ids", "status", "detail", "created_at",
    }
