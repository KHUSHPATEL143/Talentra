"""API helper tests."""

from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock

import pytest
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from app.api.routes.parse import _enqueue_dead_letter, _merge_batch_file_result, _read_and_validate_file
from app.models.schemas import BatchJobFileResult


@pytest.mark.asyncio
async def test_read_and_validate_file_accepts_plain_text() -> None:
    """TXT uploads under the file-size limit should validate successfully."""

    upload = UploadFile(filename="resume.txt", file=io.BytesIO(b"hello world"), headers=Headers({"content-type": "text/plain"}))

    file_bytes, mime_type = await _read_and_validate_file(upload)

    assert file_bytes == b"hello world"
    assert mime_type == "text/plain"


def test_merge_batch_file_result_updates_one_entry_only() -> None:
    """Batch status updates should only modify the targeted file row."""

    entries = [
        BatchJobFileResult(file_name="one.pdf", job_id="job-1", status="queued"),
        BatchJobFileResult(file_name="two.pdf", job_id="job-2", status="queued"),
    ]

    updated = _merge_batch_file_result(entries, "job-2", status="failed", error="parse failed")

    assert updated[0].status == "queued"
    assert updated[0].error is None
    assert updated[1].status == "failed"
    assert updated[1].error == "parse failed"


@pytest.mark.asyncio
async def test_enqueue_dead_letter_preserves_failed_payload_and_error() -> None:
    """Failed batch items should be written to the dead-letter queue with replay metadata."""

    redis = AsyncMock()
    payload = {
        "file_name": "broken.pdf",
        "file_job_id": "job-1",
        "mime_type": "application/pdf",
        "file_bytes": "YmFzZTY0",
    }

    await _enqueue_dead_letter(redis, "batch-1", payload, "parse failed")

    redis.rpush.assert_awaited_once()
    key, raw_value = redis.rpush.await_args.args
    assert key == "job:batch-1:dead_letter"
    assert json.loads(raw_value) == {
        "file_name": "broken.pdf",
        "file_job_id": "job-1",
        "mime_type": "application/pdf",
        "file_bytes": "YmFzZTY0",
        "error": "parse failed",
    }
