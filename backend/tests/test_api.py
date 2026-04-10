"""API helper tests."""

from __future__ import annotations

import io

import pytest
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from app.api.routes.parse import _read_and_validate_file


@pytest.mark.asyncio
async def test_read_and_validate_file_accepts_plain_text() -> None:
    """TXT uploads under the file-size limit should validate successfully."""

    upload = UploadFile(filename="resume.txt", file=io.BytesIO(b"hello world"), headers=Headers({"content-type": "text/plain"}))

    file_bytes, mime_type = await _read_and_validate_file(upload)

    assert file_bytes == b"hello world"
    assert mime_type == "text/plain"
