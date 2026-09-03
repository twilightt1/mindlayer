"""Unit tests for the ErasureReceipt model: shape and defaults."""
from __future__ import annotations

import uuid

from app.models.erasure_receipt import ErasureReceipt


def test_erasure_receipt_defaults():
    receipt = ErasureReceipt(user_id=uuid.uuid4(), requested_memory_ids=[str(uuid.uuid4())])
    assert receipt.status == "completed"
    assert receipt.detail == {}
    assert len(receipt.requested_memory_ids) == 1


def test_erasure_receipt_empty_targets_default():
    receipt = ErasureReceipt(user_id=uuid.uuid4())
    assert receipt.requested_memory_ids == []
    assert receipt.status == "completed"
