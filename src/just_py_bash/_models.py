from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from ._exceptions import CommandFailedError

type FileValue = str | bytes


@dataclass(slots=True, kw_only=True)
class ExecutionLimits:
    """Pythonic wrapper for just-bash execution limits."""

    max_call_depth: int | None = None
    max_command_count: int | None = None
    max_loop_iterations: int | None = None
    max_heredoc_size: int | None = None

    def to_wire(self) -> dict[str, int]:
        payload: dict[str, int] = {}
        if self.max_call_depth is not None:
            payload["maxCallDepth"] = self.max_call_depth
        if self.max_command_count is not None:
            payload["maxCommandCount"] = self.max_command_count
        if self.max_loop_iterations is not None:
            payload["maxLoopIterations"] = self.max_loop_iterations
        if self.max_heredoc_size is not None:
            payload["maxHeredocSize"] = self.max_heredoc_size
        return payload


@dataclass(slots=True, kw_only=True)
class JavaScriptConfig:
    """Configuration for just-bash's optional QuickJS runtime."""

    bootstrap: str | None = None

    def to_wire(self) -> dict[str, str]:
        payload: dict[str, str] = {}
        if self.bootstrap is not None:
            payload["bootstrap"] = self.bootstrap
        return payload


@dataclass(slots=True)
class ExecResult:
    """Structured result from :meth:`just_py_bash.Bash.exec`."""

    stdout: str
    stderr: str
    exit_code: int
    env: dict[str, str]
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_wire(cls, payload: dict[str, Any]) -> Self:
        stdout = payload.get("stdout", "")
        stderr = payload.get("stderr", "")
        exit_code = payload.get("exitCode", 0)

        env: dict[str, str] = {}
        raw_env = payload.get("env")
        if isinstance(raw_env, dict):
            for key, value in raw_env.items():
                if isinstance(key, str) and isinstance(value, str):
                    env[key] = value

        metadata: dict[str, Any] | None = None
        raw_metadata = payload.get("metadata")
        if isinstance(raw_metadata, dict):
            metadata = {}
            for key, value in raw_metadata.items():
                metadata[str(key)] = value

        return cls(
            stdout=stdout if isinstance(stdout, str) else "",
            stderr=stderr if isinstance(stderr, str) else "",
            exit_code=exit_code if isinstance(exit_code, int) else 0,
            env=env,
            metadata=metadata,
        )

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def returncode(self) -> int:
        return self.exit_code

    def check(self) -> Self:
        if not self.ok:
            raise CommandFailedError(self)
        return self

    def check_returncode(self) -> Self:
        return self.check()
