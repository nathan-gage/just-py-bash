from __future__ import annotations

from collections.abc import Mapping
from typing import Final, Literal, TypeAlias

from pydantic import TypeAdapter, ValidationError

from ._exceptions import BridgeError
from ._types import BackendErrorPayload, CustomCommandEvent, WorkerResponse

DEFAULT_TIMEOUT_SECONDS = 30.0
BridgeOperation: TypeAlias = Literal[
    "custom_command_complete",
    "custom_command_exec",
    "exec",
    "get_cwd",
    "get_env",
    "info",
    "init",
    "read_bytes",
    "read_text",
    "write_bytes",
    "write_text",
]
_JSON_OBJECT_ADAPTER: Final[TypeAdapter[dict[str, object]]] = TypeAdapter(dict[str, object])
_WORKER_RESPONSE_ADAPTER: Final[TypeAdapter[WorkerResponse]] = TypeAdapter(WorkerResponse)
_BACKEND_ERROR_ADAPTER: Final[TypeAdapter[BackendErrorPayload]] = TypeAdapter(BackendErrorPayload)
_CUSTOM_COMMAND_EVENT_ADAPTER: Final[TypeAdapter[CustomCommandEvent]] = TypeAdapter(CustomCommandEvent)


def parse_worker_message(line: str) -> dict[str, object]:
    try:
        return _JSON_OBJECT_ADAPTER.validate_json(line)
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Failed to decode just-bash worker response: {exc}: {line!r}") from exc


def parse_worker_response(payload: Mapping[str, object]) -> WorkerResponse:
    try:
        return _WORKER_RESPONSE_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Received an invalid response from the just-bash worker: {exc}: {payload!r}") from exc


def parse_custom_command_event(payload: Mapping[str, object]) -> CustomCommandEvent:
    try:
        return _CUSTOM_COMMAND_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(
            f"Received an invalid custom command event from the just-bash worker: {exc}: {payload!r}"
        ) from exc


def parse_backend_error(raw_error: object) -> BackendErrorPayload:
    try:
        return _BACKEND_ERROR_ADAPTER.validate_python(raw_error)
    except ValidationError:
        if isinstance(raw_error, str):
            return {"message": raw_error}
        return {}
