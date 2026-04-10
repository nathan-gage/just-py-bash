from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, Self, cast

from ._backend_runtime import BackendRuntime


class TransformPlugin(Protocol):
    def to_wire(self) -> dict[str, object]: ...


@dataclass(slots=True, kw_only=True)
class BashTransformResult:
    script: str
    ast: dict[str, object]
    metadata: dict[str, object]

    @classmethod
    def from_wire(cls, payload: Mapping[str, object]) -> BashTransformResult:
        ast = payload.get("ast")
        metadata = payload.get("metadata")
        return cls(
            script=str(payload.get("script", "")),
            ast=_mapping_to_dict(ast, field_name="ast"),
            metadata=_mapping_to_dict(metadata, field_name="metadata"),
        )


@dataclass(slots=True)
class CommandCollectorPlugin:
    def to_wire(self) -> dict[str, object]:
        return {"kind": "command_collector"}


@dataclass(slots=True, kw_only=True)
class TeePlugin:
    output_dir: str
    target_command_pattern: str | re.Pattern[str] | None = None
    timestamp: datetime | None = None

    def to_wire(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": "tee",
            "outputDir": self.output_dir,
        }
        if self.target_command_pattern is not None:
            source, flags = _pattern_to_wire(self.target_command_pattern)
            payload["targetCommandPatternSource"] = source
            if flags:
                payload["targetCommandPatternFlags"] = flags
        if self.timestamp is not None:
            payload["timestampMs"] = int(self.timestamp.timestamp() * 1000)
        return payload


def _empty_plugins() -> list[TransformPlugin]:
    return []


@dataclass(slots=True)
class BashTransformPipeline:
    _plugins: list[TransformPlugin] = field(default_factory=_empty_plugins)

    def use(self, plugin: TransformPlugin) -> Self:
        self._plugins.append(plugin)
        return self

    @property
    def plugins(self) -> tuple[TransformPlugin, ...]:
        return tuple(self._plugins)

    def transform(self, script: str) -> BashTransformResult:
        with BackendRuntime() as runtime:
            result = runtime.request(
                "transform_script",
                {
                    "script": script,
                    "plugins": [plugin.to_wire() for plugin in self._plugins],
                },
            )
        if not isinstance(result, Mapping):
            raise TypeError(f"Expected a transform result mapping, got {type(result).__name__}")
        return BashTransformResult.from_wire(cast(Mapping[str, object], result))


def _mapping_to_dict(value: object, *, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected {field_name} to be a mapping, got {type(value).__name__}")
    mapping = cast(Mapping[object, object], value)
    return {str(key): item for key, item in mapping.items()}


def _pattern_to_wire(pattern: str | re.Pattern[str]) -> tuple[str, str]:
    if isinstance(pattern, str):
        return pattern, ""

    flags = ""
    supported = (
        (re.IGNORECASE, "i"),
        (re.MULTILINE, "m"),
        (re.DOTALL, "s"),
    )
    remaining_flags = pattern.flags
    remaining_flags &= ~(re.UNICODE | re.NOFLAG)
    for flag, code in supported:
        if pattern.flags & flag:
            flags += code
            remaining_flags &= ~flag
    if remaining_flags:
        raise ValueError("TeePlugin target_command_pattern only supports IGNORECASE, MULTILINE, and DOTALL")
    return pattern.pattern, flags


__all__ = [
    "BashTransformPipeline",
    "BashTransformResult",
    "CommandCollectorPlugin",
    "TeePlugin",
    "TransformPlugin",
]
