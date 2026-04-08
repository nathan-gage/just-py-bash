from __future__ import annotations

import base64
from typing import overload

from ._types import BYTE_TAG, BytesPayload, EncodedFileValue, FileValue


@overload
def encode_file_value(value: str) -> str: ...


@overload
def encode_file_value(value: bytes) -> BytesPayload: ...


def encode_file_value(value: FileValue) -> EncodedFileValue:
    if isinstance(value, bytes):
        return {BYTE_TAG: base64.b64encode(value).decode("ascii")}
    return value


def decode_bytes_payload(payload: BytesPayload) -> bytes:
    return base64.b64decode(payload[BYTE_TAG].encode("ascii"))
