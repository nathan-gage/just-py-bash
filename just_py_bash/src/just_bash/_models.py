from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Final, TypeAlias

from pydantic import ConfigDict, Field, StrictInt, StrictStr, TypeAdapter, ValidationError
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from ._exceptions import CommandFailedError
from ._types import ExecutionLimitsWire, FileValue, JavaScriptConfigWire

__all__ = ["ExecResult", "ExecutionLimits", "FileValue", "JavaScriptConfig"]

_MODEL_CONFIG: Final = ConfigDict(
    alias_generator=to_camel,
    extra="ignore",
    populate_by_name=True,
    validate_assignment=True,
)
NonNegativeLimit: TypeAlias = Annotated[StrictInt | None, Field(default=None, ge=0)]


@dataclass(config=_MODEL_CONFIG, kw_only=True, slots=True)
class ExecutionLimits:
    """Validated Python wrapper for just-bash execution limits."""

    max_call_depth: NonNegativeLimit
    max_command_count: NonNegativeLimit
    max_loop_iterations: NonNegativeLimit
    max_awk_iterations: NonNegativeLimit
    max_sed_iterations: NonNegativeLimit
    max_jq_iterations: NonNegativeLimit
    max_sqlite_timeout_ms: NonNegativeLimit
    max_python_timeout_ms: NonNegativeLimit
    max_js_timeout_ms: NonNegativeLimit
    max_glob_operations: NonNegativeLimit
    max_string_length: NonNegativeLimit
    max_array_elements: NonNegativeLimit
    max_heredoc_size: NonNegativeLimit
    max_substitution_depth: NonNegativeLimit
    max_brace_expansion_results: NonNegativeLimit
    max_output_size: NonNegativeLimit
    max_file_descriptors: NonNegativeLimit
    max_source_depth: NonNegativeLimit

    def to_wire(self) -> ExecutionLimitsWire:
        payload = _EXECUTION_LIMITS_ADAPTER.dump_python(self, by_alias=True, exclude_none=True)
        return _EXECUTION_LIMITS_WIRE_ADAPTER.validate_python(payload)


@dataclass(config=_MODEL_CONFIG, kw_only=True, slots=True)
class JavaScriptConfig:
    """Validated configuration for just-bash's optional QuickJS runtime."""

    bootstrap: StrictStr | None = None

    def to_wire(self) -> JavaScriptConfigWire:
        payload = _JAVASCRIPT_CONFIG_ADAPTER.dump_python(self, by_alias=True, exclude_none=True)
        return _JAVASCRIPT_CONFIG_WIRE_ADAPTER.validate_python(payload)


@dataclass(config=_MODEL_CONFIG, slots=True)
class ExecResult:
    """Validated result from :meth:`just_bash.Bash.exec`."""

    stdout: StrictStr = ""
    stderr: StrictStr = ""
    exit_code: StrictInt = 0
    env: dict[str, StrictStr] = Field(default_factory=dict)
    metadata: dict[str, object] | None = None

    @classmethod
    def from_wire(cls, payload: Mapping[str, object]) -> ExecResult:
        return cls(
            stdout=_string_field(payload, "stdout"),
            stderr=_string_field(payload, "stderr"),
            exit_code=_int_field(payload, "exitCode", fallback_key="exit_code"),
            env=_env_field(payload.get("env")),
            metadata=_metadata_field(payload.get("metadata")),
        )

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def returncode(self) -> int:
        return self.exit_code

    def check(self) -> ExecResult:
        if not self.ok:
            raise CommandFailedError(self)
        return self

    def check_returncode(self) -> ExecResult:
        return self.check()


def _string_field(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key, "")
    return value if isinstance(value, str) else str(value)


def _int_field(payload: Mapping[str, object], key: str, *, fallback_key: str | None = None) -> int:
    value = payload.get(key)
    if value is None and fallback_key is not None:
        value = payload.get(fallback_key)
    return int(value) if isinstance(value, (int, str)) else 0


def _env_field(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}

    try:
        return _ENV_ADAPTER.validate_python(value)
    except ValidationError:
        return {}


def _metadata_field(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None

    try:
        return _METADATA_ADAPTER.validate_python(value)
    except ValidationError:
        return None


_ENV_ADAPTER: Final = TypeAdapter(dict[str, str])
_METADATA_ADAPTER: Final = TypeAdapter(dict[str, object])
_EXECUTION_LIMITS_ADAPTER: Final = TypeAdapter(ExecutionLimits)
_EXECUTION_LIMITS_WIRE_ADAPTER: Final = TypeAdapter(ExecutionLimitsWire)
_JAVASCRIPT_CONFIG_ADAPTER: Final = TypeAdapter(JavaScriptConfig)
_JAVASCRIPT_CONFIG_WIRE_ADAPTER: Final = TypeAdapter(JavaScriptConfigWire)
_EXEC_RESULT_ADAPTER: Final = TypeAdapter(ExecResult)
