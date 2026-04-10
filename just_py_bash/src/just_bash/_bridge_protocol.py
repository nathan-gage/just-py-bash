from __future__ import annotations

from collections.abc import Mapping
from typing import Final, Literal, TypeAlias

from pydantic import TypeAdapter, ValidationError

from ._exceptions import BridgeError
from ._types import (
    BackendErrorPayload,
    CoverageEvent,
    CustomCommandEvent,
    DefenseViolationEvent,
    FetchEvent,
    LazyFileEvent,
    LoggerEvent,
    TraceEventMessage,
    WorkerResponse,
)

DEFAULT_TIMEOUT_SECONDS = 30.0
BridgeOperation: TypeAlias = Literal[
    "chmod",
    "cp",
    "custom_command_complete",
    "custom_command_exec",
    "exec",
    "exists",
    "fetch_complete",
    "get_cwd",
    "get_env",
    "info",
    "init",
    "lazy_file_complete",
    "mkdir",
    "mv",
    "read_bytes",
    "read_text",
    "readdir",
    "readlink",
    "realpath",
    "rm",
    "stat",
    "write_bytes",
    "write_text",
]
_JSON_OBJECT_ADAPTER: Final[TypeAdapter[dict[str, object]]] = TypeAdapter(dict[str, object])
_WORKER_RESPONSE_ADAPTER: Final[TypeAdapter[WorkerResponse]] = TypeAdapter(WorkerResponse)
_BACKEND_ERROR_ADAPTER: Final[TypeAdapter[BackendErrorPayload]] = TypeAdapter(BackendErrorPayload)
_CUSTOM_COMMAND_EVENT_ADAPTER: Final[TypeAdapter[CustomCommandEvent]] = TypeAdapter(CustomCommandEvent)
_LAZY_FILE_EVENT_ADAPTER: Final[TypeAdapter[LazyFileEvent]] = TypeAdapter(LazyFileEvent)
_FETCH_EVENT_ADAPTER: Final[TypeAdapter[FetchEvent]] = TypeAdapter(FetchEvent)
_LOGGER_EVENT_ADAPTER: Final[TypeAdapter[LoggerEvent]] = TypeAdapter(LoggerEvent)
_TRACE_EVENT_ADAPTER: Final[TypeAdapter[TraceEventMessage]] = TypeAdapter(TraceEventMessage)
_COVERAGE_EVENT_ADAPTER: Final[TypeAdapter[CoverageEvent]] = TypeAdapter(CoverageEvent)
_DEFENSE_VIOLATION_EVENT_ADAPTER: Final[TypeAdapter[DefenseViolationEvent]] = TypeAdapter(DefenseViolationEvent)


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


def parse_lazy_file_event(payload: Mapping[str, object]) -> LazyFileEvent:
    try:
        return _LAZY_FILE_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Received an invalid lazy file event from the just-bash worker: {exc}: {payload!r}") from exc


def parse_fetch_event(payload: Mapping[str, object]) -> FetchEvent:
    try:
        return _FETCH_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Received an invalid fetch event from the just-bash worker: {exc}: {payload!r}") from exc


def parse_logger_event(payload: Mapping[str, object]) -> LoggerEvent:
    try:
        return _LOGGER_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Received an invalid logger event from the just-bash worker: {exc}: {payload!r}") from exc


def parse_trace_event(payload: Mapping[str, object]) -> TraceEventMessage:
    try:
        return _TRACE_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Received an invalid trace event from the just-bash worker: {exc}: {payload!r}") from exc


def parse_coverage_event(payload: Mapping[str, object]) -> CoverageEvent:
    try:
        return _COVERAGE_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Received an invalid coverage event from the just-bash worker: {exc}: {payload!r}") from exc


def parse_defense_violation_event(payload: Mapping[str, object]) -> DefenseViolationEvent:
    try:
        return _DEFENSE_VIOLATION_EVENT_ADAPTER.validate_python(dict(payload))
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(
            f"Received an invalid defense violation event from the just-bash worker: {exc}: {payload!r}"
        ) from exc


def parse_backend_error(raw_error: object) -> BackendErrorPayload:
    try:
        return _BACKEND_ERROR_ADAPTER.validate_python(raw_error)
    except ValidationError:
        if isinstance(raw_error, str):
            return {"message": raw_error}
        return {}
