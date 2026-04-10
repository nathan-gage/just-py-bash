from __future__ import annotations

import base64
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, Self, cast

from ._backend_runtime import AsyncBackendRuntime, BackendRuntime
from ._bridge_protocol import BridgeOperation
from ._fs import FileSystemConfig, filesystem_to_wire
from ._option_hooks import DefenseInDepthConfig
from ._types import NetworkConfig


@dataclass(slots=True, kw_only=True)
class SandboxOptions:
    cwd: str | None = None
    env: Mapping[str, str] | None = None
    timeout_ms: int | None = None
    fs: FileSystemConfig | None = None
    overlay_root: str | None = None
    max_call_depth: int | None = None
    max_command_count: int | None = None
    max_loop_iterations: int | None = None
    network: NetworkConfig | None = None
    defense_in_depth: bool | DefenseInDepthConfig | None = None

    def to_wire(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.cwd is not None:
            payload["cwd"] = self.cwd
        if self.env is not None:
            payload["env"] = dict(self.env)
        if self.timeout_ms is not None:
            payload["timeoutMs"] = int(self.timeout_ms)
        if self.fs is not None:
            payload["fs"] = filesystem_to_wire(self.fs)
        if self.overlay_root is not None:
            payload["overlayRoot"] = self.overlay_root
        if self.max_call_depth is not None:
            payload["maxCallDepth"] = int(self.max_call_depth)
        if self.max_command_count is not None:
            payload["maxCommandCount"] = int(self.max_command_count)
        if self.max_loop_iterations is not None:
            payload["maxLoopIterations"] = int(self.max_loop_iterations)
        if self.network is not None:
            payload["network"] = self.network
        if self.defense_in_depth is not None:
            payload["defenseInDepth"] = (
                self.defense_in_depth.to_wire()
                if isinstance(self.defense_in_depth, DefenseInDepthConfig)
                else self.defense_in_depth
            )
        return payload


@dataclass(slots=True, kw_only=True)
class SandboxWriteFile:
    content: str | bytes
    encoding: str | None = None

    def to_wire(self) -> dict[str, str]:
        if isinstance(self.content, bytes):
            return {
                "content": base64.b64encode(self.content).decode("ascii"),
                "encoding": "base64",
            }
        if self.encoding == "base64":
            return {"content": self.content, "encoding": "base64"}
        return {"content": self.content, "encoding": "utf-8"}


@dataclass(slots=True, kw_only=True)
class SandboxOutputMessage:
    type: str
    data: str
    timestamp: datetime

    @classmethod
    def from_wire(cls, payload: Mapping[str, object]) -> SandboxOutputMessage:
        timestamp_ms = payload.get("timestampMs")
        timestamp = datetime.fromtimestamp(0, tz=UTC)
        if isinstance(timestamp_ms, (int, float)):
            timestamp = datetime.fromtimestamp(float(timestamp_ms) / 1000.0, tz=UTC)
        return cls(
            type=str(payload.get("type", "")),
            data=str(payload.get("data", "")),
            timestamp=timestamp,
        )


class _Writable(Protocol):
    def write(self, data: str, /) -> int | None: ...


class SandboxCommand:
    def __init__(
        self,
        sandbox: Sandbox,
        *,
        command_id: int,
        cmd_id: str,
        cwd: str,
        started_at: datetime,
        exit_code: int | None = None,
        stdout_cache: str | None = None,
        stderr_cache: str | None = None,
        stdout_target: _Writable | None = None,
        stderr_target: _Writable | None = None,
    ) -> None:
        self._sandbox = sandbox
        self.command_id = command_id
        self.cmd_id = cmd_id
        self.cwd = cwd
        self.started_at = started_at
        self.exit_code = exit_code
        self._stdout_cache = stdout_cache
        self._stderr_cache = stderr_cache
        self._stdout_target = stdout_target
        self._stderr_target = stderr_target
        self._streams_flushed = False

    def wait(self) -> Self:
        payload = cast(
            Mapping[str, object],
            self._sandbox.request("sandbox_command_wait", {"commandId": self.command_id}),
        )
        self._update_from_wire(payload)
        return self

    def output(self) -> str:
        if self._stdout_cache is not None and self._stderr_cache is not None:
            return self._stdout_cache + self._stderr_cache
        result = self._sandbox.request("sandbox_command_output", {"commandId": self.command_id})
        return str(result)

    def stdout(self) -> str:
        if self._stdout_cache is not None:
            return self._stdout_cache
        result = self._sandbox.request("sandbox_command_stdout", {"commandId": self.command_id})
        self._stdout_cache = str(result)
        return self._stdout_cache

    def stderr(self) -> str:
        if self._stderr_cache is not None:
            return self._stderr_cache
        result = self._sandbox.request("sandbox_command_stderr", {"commandId": self.command_id})
        self._stderr_cache = str(result)
        return self._stderr_cache

    def kill(self) -> None:
        self._sandbox.request("sandbox_command_kill", {"commandId": self.command_id})

    def logs(self) -> Iterator[SandboxOutputMessage]:
        result = self._sandbox.request("sandbox_command_logs", {"commandId": self.command_id})
        if not isinstance(result, list):
            raise TypeError(f"Expected sandbox logs to be a list, got {type(result).__name__}")
        entries = cast(list[object], result)
        for item in entries:
            if not isinstance(item, Mapping):
                raise TypeError(f"Expected sandbox log entry to be a mapping, got {type(item).__name__}")
            yield SandboxOutputMessage.from_wire(cast(Mapping[str, object], item))

    def _update_from_wire(self, payload: Mapping[str, object]) -> None:
        exit_code = payload.get("exitCode")
        if isinstance(exit_code, int):
            self.exit_code = exit_code
        stdout = payload.get("stdout")
        stderr = payload.get("stderr")
        if isinstance(stdout, str):
            self._stdout_cache = stdout
        if isinstance(stderr, str):
            self._stderr_cache = stderr
        self.flush_streams_once()

    def flush_streams_once(self) -> None:
        if self._streams_flushed:
            return
        if self._stdout_target is not None and self._stdout_cache:
            self._stdout_target.write(self._stdout_cache)
        if self._stderr_target is not None and self._stderr_cache:
            self._stderr_target.write(self._stderr_cache)
        self._streams_flushed = True


class AsyncSandboxCommand:
    def __init__(
        self,
        sandbox: AsyncSandbox,
        *,
        command_id: int,
        cmd_id: str,
        cwd: str,
        started_at: datetime,
        exit_code: int | None = None,
        stdout_cache: str | None = None,
        stderr_cache: str | None = None,
        stdout_target: _Writable | None = None,
        stderr_target: _Writable | None = None,
    ) -> None:
        self._sandbox = sandbox
        self.command_id = command_id
        self.cmd_id = cmd_id
        self.cwd = cwd
        self.started_at = started_at
        self.exit_code = exit_code
        self._stdout_cache = stdout_cache
        self._stderr_cache = stderr_cache
        self._stdout_target = stdout_target
        self._stderr_target = stderr_target
        self._streams_flushed = False

    async def wait(self) -> AsyncSandboxCommand:
        payload = cast(
            Mapping[str, object],
            await self._sandbox.request("sandbox_command_wait", {"commandId": self.command_id}),
        )
        self._update_from_wire(payload)
        return self

    async def output(self) -> str:
        if self._stdout_cache is not None and self._stderr_cache is not None:
            return self._stdout_cache + self._stderr_cache
        result = await self._sandbox.request("sandbox_command_output", {"commandId": self.command_id})
        return str(result)

    async def stdout(self) -> str:
        if self._stdout_cache is not None:
            return self._stdout_cache
        result = await self._sandbox.request("sandbox_command_stdout", {"commandId": self.command_id})
        self._stdout_cache = str(result)
        return self._stdout_cache

    async def stderr(self) -> str:
        if self._stderr_cache is not None:
            return self._stderr_cache
        result = await self._sandbox.request("sandbox_command_stderr", {"commandId": self.command_id})
        self._stderr_cache = str(result)
        return self._stderr_cache

    async def kill(self) -> None:
        await self._sandbox.request("sandbox_command_kill", {"commandId": self.command_id})

    async def logs(self) -> AsyncIterator[SandboxOutputMessage]:
        result = await self._sandbox.request("sandbox_command_logs", {"commandId": self.command_id})
        if not isinstance(result, list):
            raise TypeError(f"Expected sandbox logs to be a list, got {type(result).__name__}")
        entries = cast(list[object], result)
        for item in entries:
            if not isinstance(item, Mapping):
                raise TypeError(f"Expected sandbox log entry to be a mapping, got {type(item).__name__}")
            yield SandboxOutputMessage.from_wire(cast(Mapping[str, object], item))

    def _update_from_wire(self, payload: Mapping[str, object]) -> None:
        exit_code = payload.get("exitCode")
        if isinstance(exit_code, int):
            self.exit_code = exit_code
        stdout = payload.get("stdout")
        stderr = payload.get("stderr")
        if isinstance(stdout, str):
            self._stdout_cache = stdout
        if isinstance(stderr, str):
            self._stderr_cache = stderr
        self.flush_streams_once()

    def flush_streams_once(self) -> None:
        if self._streams_flushed:
            return
        if self._stdout_target is not None and self._stdout_cache:
            self._stdout_target.write(self._stdout_cache)
        if self._stderr_target is not None and self._stderr_cache:
            self._stderr_target.write(self._stderr_cache)
        self._streams_flushed = True


class Sandbox:
    def __init__(self, runtime: BackendRuntime, *, sandbox_id: int, domain: str | None) -> None:
        self._runtime = runtime
        self._sandbox_id = sandbox_id
        self._domain = domain
        self._closed = False

    def request(self, op: BridgeOperation, payload: Mapping[str, object]) -> object:
        return self._runtime.request(op, payload)

    @classmethod
    def create(
        cls,
        options: SandboxOptions | None = None,
    ) -> Sandbox:
        runtime = BackendRuntime()
        response = cast(
            Mapping[str, object],
            runtime.request("sandbox_create", {"options": (options or SandboxOptions()).to_wire()}),
        )
        sandbox = cls(
            runtime,
            sandbox_id=_int_or_zero(response.get("sandboxId")),
            domain=_optional_string(response.get("domain")),
        )
        return sandbox

    def __enter__(self) -> Sandbox:
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    @property
    def domain(self) -> str | None:
        return self._domain

    def run_command(
        self,
        command: str,
        args: Sequence[str] | None = None,
        *,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        sudo: bool = False,
        detached: bool = False,
        stdout: _Writable | None = None,
        stderr: _Writable | None = None,
    ) -> SandboxCommand:
        payload: dict[str, object] = {
            "sandboxId": self._sandbox_id,
            "sudo": sudo,
            "detached": detached,
        }
        if args is None:
            payload["commandLine"] = command
        else:
            payload["command"] = command
            payload["args"] = list(args)
        if cwd is not None:
            payload["cwd"] = cwd
        if env is not None:
            payload["env"] = dict(env)

        response = cast(Mapping[str, object], self._runtime.request("sandbox_run_command", payload))
        return _sync_command_from_wire(self, response, stdout_target=stdout, stderr_target=stderr)

    def write_files(self, files: Mapping[str, str | bytes | SandboxWriteFile]) -> None:
        encoded = {path: _encode_write_file(value) for path, value in files.items()}
        self._runtime.request("sandbox_write_files", {"sandboxId": self._sandbox_id, "files": encoded})

    def read_file(self, path: str, *, encoding: str = "utf-8") -> str:
        result = self._runtime.request(
            "sandbox_read_file",
            {"sandboxId": self._sandbox_id, "path": path, "encoding": encoding},
        )
        return str(result)

    def mk_dir(self, path: str, *, recursive: bool = False) -> None:
        self._runtime.request(
            "sandbox_mkdir",
            {"sandboxId": self._sandbox_id, "path": path, "recursive": recursive},
        )

    def extend_timeout(self, ms: int) -> None:
        self._runtime.request(
            "sandbox_extend_timeout",
            {"sandboxId": self._sandbox_id, "timeoutMs": int(ms)},
        )

    def stop(self) -> None:
        if self._closed:
            return
        try:
            self._runtime.request("sandbox_stop", {"sandboxId": self._sandbox_id})
        finally:
            self._runtime.close()
            self._closed = True

    close = stop


class AsyncSandbox:
    def __init__(self, runtime: AsyncBackendRuntime, *, sandbox_id: int, domain: str | None) -> None:
        self._runtime = runtime
        self._sandbox_id = sandbox_id
        self._domain = domain
        self._closed = False

    async def request(self, op: BridgeOperation, payload: Mapping[str, object]) -> object:
        return await self._runtime.request(op, payload)

    @classmethod
    async def create(
        cls,
        options: SandboxOptions | None = None,
    ) -> AsyncSandbox:
        runtime = await AsyncBackendRuntime.open()
        response = cast(
            Mapping[str, object],
            await runtime.request("sandbox_create", {"options": (options or SandboxOptions()).to_wire()}),
        )
        return cls(
            runtime,
            sandbox_id=_int_or_zero(response.get("sandboxId")),
            domain=_optional_string(response.get("domain")),
        )

    async def __aenter__(self) -> AsyncSandbox:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()

    @property
    def domain(self) -> str | None:
        return self._domain

    async def run_command(
        self,
        command: str,
        args: Sequence[str] | None = None,
        *,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
        sudo: bool = False,
        detached: bool = False,
        stdout: _Writable | None = None,
        stderr: _Writable | None = None,
    ) -> AsyncSandboxCommand:
        payload: dict[str, object] = {
            "sandboxId": self._sandbox_id,
            "sudo": sudo,
            "detached": detached,
        }
        if args is None:
            payload["commandLine"] = command
        else:
            payload["command"] = command
            payload["args"] = list(args)
        if cwd is not None:
            payload["cwd"] = cwd
        if env is not None:
            payload["env"] = dict(env)

        response = cast(Mapping[str, object], await self._runtime.request("sandbox_run_command", payload))
        return _async_command_from_wire(self, response, stdout_target=stdout, stderr_target=stderr)

    async def write_files(self, files: Mapping[str, str | bytes | SandboxWriteFile]) -> None:
        encoded = {path: _encode_write_file(value) for path, value in files.items()}
        await self._runtime.request("sandbox_write_files", {"sandboxId": self._sandbox_id, "files": encoded})

    async def read_file(self, path: str, *, encoding: str = "utf-8") -> str:
        result = await self._runtime.request(
            "sandbox_read_file",
            {"sandboxId": self._sandbox_id, "path": path, "encoding": encoding},
        )
        return str(result)

    async def mk_dir(self, path: str, *, recursive: bool = False) -> None:
        await self._runtime.request(
            "sandbox_mkdir",
            {"sandboxId": self._sandbox_id, "path": path, "recursive": recursive},
        )

    async def extend_timeout(self, ms: int) -> None:
        await self._runtime.request(
            "sandbox_extend_timeout",
            {"sandboxId": self._sandbox_id, "timeoutMs": int(ms)},
        )

    async def stop(self) -> None:
        if self._closed:
            return
        try:
            await self._runtime.request("sandbox_stop", {"sandboxId": self._sandbox_id})
        finally:
            await self._runtime.close()
            self._closed = True

    close = stop


def _encode_write_file(value: str | bytes | SandboxWriteFile) -> str | dict[str, str]:
    if isinstance(value, SandboxWriteFile):
        return value.to_wire()
    if isinstance(value, bytes):
        return {
            "content": base64.b64encode(value).decode("ascii"),
            "encoding": "base64",
        }
    return value


def _started_at_from_wire(payload: Mapping[str, object]) -> datetime:
    started_at_ms = payload.get("startedAtMs")
    if isinstance(started_at_ms, (int, float)):
        return datetime.fromtimestamp(float(started_at_ms) / 1000.0, tz=UTC)
    return datetime.fromtimestamp(0, tz=UTC)


def _sync_command_from_wire(
    sandbox: Sandbox,
    payload: Mapping[str, object],
    *,
    stdout_target: _Writable | None,
    stderr_target: _Writable | None,
) -> SandboxCommand:
    command = SandboxCommand(
        sandbox,
        command_id=_int_or_zero(payload.get("commandId")),
        cmd_id=str(payload.get("cmdId", "")),
        cwd=str(payload.get("cwd", "")),
        started_at=_started_at_from_wire(payload),
        exit_code=_optional_int(payload.get("exitCode")),
        stdout_cache=_optional_string(payload.get("stdout")),
        stderr_cache=_optional_string(payload.get("stderr")),
        stdout_target=stdout_target,
        stderr_target=stderr_target,
    )
    command.flush_streams_once()
    return command


def _async_command_from_wire(
    sandbox: AsyncSandbox,
    payload: Mapping[str, object],
    *,
    stdout_target: _Writable | None,
    stderr_target: _Writable | None,
) -> AsyncSandboxCommand:
    command = AsyncSandboxCommand(
        sandbox,
        command_id=_int_or_zero(payload.get("commandId")),
        cmd_id=str(payload.get("cmdId", "")),
        cwd=str(payload.get("cwd", "")),
        started_at=_started_at_from_wire(payload),
        exit_code=_optional_int(payload.get("exitCode")),
        stdout_cache=_optional_string(payload.get("stdout")),
        stderr_cache=_optional_string(payload.get("stderr")),
        stdout_target=stdout_target,
        stderr_target=stderr_target,
    )
    command.flush_streams_once()
    return command


def _int_or_zero(value: object) -> int:
    return value if isinstance(value, int) else 0


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = [
    "AsyncSandbox",
    "AsyncSandboxCommand",
    "Sandbox",
    "SandboxCommand",
    "SandboxOptions",
    "SandboxOutputMessage",
    "SandboxWriteFile",
]
