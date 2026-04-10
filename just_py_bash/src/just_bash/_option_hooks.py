from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, TypeAlias, cast, runtime_checkable

from ._types import (
    DefenseInDepthConfigWire,
    FetchOptionsWire,
    FetchResultWire,
    SecurityViolationWire,
    TraceEventWire,
)

JsonMapping: TypeAlias = Mapping[str, object]


def _empty_string_dict() -> dict[str, str]:
    return {}


@runtime_checkable
class BashLogger(Protocol):
    def info(self, message: str, data: Mapping[str, object] | None = None) -> object: ...

    def debug(self, message: str, data: Mapping[str, object] | None = None) -> object: ...


@runtime_checkable
class FeatureCoverageWriter(Protocol):
    def hit(self, feature: str) -> object: ...


@dataclass(slots=True, kw_only=True)
class TraceEvent:
    category: str
    name: str
    duration_ms: float
    details: dict[str, object] | None = None

    @classmethod
    def from_wire(cls, payload: Mapping[str, object]) -> TraceEvent:
        details = payload.get("details")
        return cls(
            category=str(payload.get("category", "")),
            name=str(payload.get("name", "")),
            duration_ms=_float_value(payload.get("durationMs")),
            details=_object_dict(details),
        )

    def to_wire(self) -> TraceEventWire:
        payload: TraceEventWire = {
            "category": self.category,
            "name": self.name,
            "durationMs": self.duration_ms,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload


TraceCallback: TypeAlias = Callable[[TraceEvent], object | Awaitable[object]]


@dataclass(slots=True, kw_only=True)
class SecurityViolation:
    timestamp: int
    type: str
    message: str
    path: str
    stack: str | None = None
    execution_id: str | None = None

    @classmethod
    def from_wire(cls, payload: Mapping[str, object]) -> SecurityViolation:
        stack = payload.get("stack")
        execution_id = payload.get("executionId")
        return cls(
            timestamp=_int_value(payload.get("timestamp")),
            type=str(payload.get("type", "")),
            message=str(payload.get("message", "")),
            path=str(payload.get("path", "")),
            stack=stack if isinstance(stack, str) else None,
            execution_id=execution_id if isinstance(execution_id, str) else None,
        )

    def to_wire(self) -> SecurityViolationWire:
        payload: SecurityViolationWire = {
            "timestamp": int(self.timestamp),
            "type": self.type,
            "message": self.message,
            "path": self.path,
        }
        if self.stack is not None:
            payload["stack"] = self.stack
        if self.execution_id is not None:
            payload["executionId"] = self.execution_id
        return payload


DefenseViolationCallback: TypeAlias = Callable[[SecurityViolation], object | Awaitable[object]]


@dataclass(slots=True, kw_only=True)
class DefenseInDepthConfig:
    enabled: bool | None = None
    audit_mode: bool | None = None
    on_violation: DefenseViolationCallback | None = None
    exclude_violation_types: Sequence[str] | None = None

    def to_wire(self) -> DefenseInDepthConfigWire:
        payload: DefenseInDepthConfigWire = {}
        if self.enabled is not None:
            payload["enabled"] = self.enabled
        if self.audit_mode is not None:
            payload["auditMode"] = self.audit_mode
        if self.exclude_violation_types is not None:
            payload["excludeViolationTypes"] = [str(value) for value in self.exclude_violation_types]
        if self.on_violation is not None:
            payload["onViolationEnabled"] = True
        return payload


@dataclass(slots=True, kw_only=True)
class FetchRequest:
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=_empty_string_dict)
    body: str | None = None
    follow_redirects: bool | None = None
    timeout_ms: int | None = None

    @classmethod
    def from_wire(cls, url: str, payload: Mapping[str, object] | None = None) -> FetchRequest:
        raw: Mapping[str, object] = payload or {}
        body = raw.get("body")
        follow_redirects = raw.get("followRedirects")
        timeout_ms = raw.get("timeoutMs")
        return cls(
            url=url,
            method=str(raw.get("method", "GET")),
            headers=_string_dict(raw.get("headers")),
            body=body if isinstance(body, str) else None,
            follow_redirects=follow_redirects if isinstance(follow_redirects, bool) else None,
            timeout_ms=int(timeout_ms) if isinstance(timeout_ms, int) else None,
        )

    def to_wire(self) -> FetchOptionsWire:
        payload: FetchOptionsWire = {"method": self.method, "headers": dict(self.headers)}
        if self.body is not None:
            payload["body"] = self.body
        if self.follow_redirects is not None:
            payload["followRedirects"] = self.follow_redirects
        if self.timeout_ms is not None:
            payload["timeoutMs"] = int(self.timeout_ms)
        return payload


@dataclass(slots=True, kw_only=True)
class FetchResult:
    status: int
    status_text: str = ""
    headers: dict[str, str] = field(default_factory=_empty_string_dict)
    body: str = ""
    url: str = ""

    @classmethod
    def from_wire(cls, payload: Mapping[str, object]) -> FetchResult:
        return cls(
            status=_int_value(payload.get("status")),
            status_text=str(payload.get("statusText", "")),
            headers=_string_dict(payload.get("headers")),
            body=str(payload.get("body", "")),
            url=str(payload.get("url", "")),
        )

    def to_wire(self) -> FetchResultWire:
        return {
            "status": int(self.status),
            "statusText": self.status_text,
            "headers": dict(self.headers),
            "body": self.body,
            "url": self.url,
        }


FetchReturn: TypeAlias = FetchResult | Mapping[str, object]
FetchCallback: TypeAlias = Callable[[FetchRequest], FetchReturn | Awaitable[FetchReturn]]


def normalize_fetch_result(value: FetchReturn) -> FetchResult:
    if isinstance(value, FetchResult):
        return value
    return FetchResult.from_wire(value)


def _string_dict(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    mapping = cast(Mapping[object, object], value)
    return {str(key): str(item) for key, item in mapping.items()}


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _float_value(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _object_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    mapping = cast(Mapping[object, object], value)
    return {str(key): item for key, item in mapping.items()}


__all__ = [
    "BashLogger",
    "DefenseInDepthConfig",
    "DefenseViolationCallback",
    "FeatureCoverageWriter",
    "FetchCallback",
    "FetchRequest",
    "FetchResult",
    "SecurityViolation",
    "TraceCallback",
    "TraceEvent",
    "normalize_fetch_result",
]
