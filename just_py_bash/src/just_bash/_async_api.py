from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping, Sequence
from typing import Self

from ._async_bridge import AsyncNodeBridge
from ._codec import decode_bytes_payload, encode_file_value
from ._custom_commands import AsyncCustomCommands
from ._exceptions import BridgeError
from ._fs import FileSystemConfig
from ._models import ExecResult, ExecutionLimits, JavaScriptConfig
from ._options import BashOptions, ExecOptions
from ._types import FileValue, NetworkConfig, ProcessInfo


class AsyncBash:
    """Async wrapper around a long-lived just-bash session.

    ``AsyncBash`` mirrors :class:`just_bash.Bash`, but uses native
    ``asyncio`` subprocesses, tasks, and locks internally. Construction is lazy:
    the Node.js worker is opened on first use or when entering ``async with``.
    """

    def __init__(
        self,
        *,
        files: Mapping[str, FileValue] | None = None,
        env: Mapping[str, str] | None = None,
        cwd: str | None = None,
        fs: FileSystemConfig | None = None,
        execution_limits: ExecutionLimits | None = None,
        python: bool = False,
        javascript: bool | JavaScriptConfig = False,
        commands: Sequence[str] | None = None,
        custom_commands: AsyncCustomCommands | None = None,
        network: NetworkConfig | None = None,
        process_info: ProcessInfo | None = None,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> None:
        self._options = BashOptions(
            files=files,
            env=env,
            cwd=cwd,
            fs=fs,
            execution_limits=execution_limits,
            python=python,
            javascript=javascript,
            commands=commands,
            custom_commands=custom_commands,
            network=network,
            process_info=process_info,
        )
        self._custom_commands = custom_commands
        self._node_command = tuple(str(part) for part in node_command) if node_command is not None else None
        self._js_entry = js_entry
        self._package_json = package_json
        self._bridge: AsyncNodeBridge | None = None
        self._closed = False
        self._call_lock: asyncio.Lock | None = None

    @classmethod
    def from_options(
        cls,
        options: BashOptions,
        *,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> Self:
        self = cls.__new__(cls)
        self._options = options
        self._custom_commands = options.custom_commands
        self._node_command = tuple(str(part) for part in node_command) if node_command is not None else None
        self._js_entry = js_entry
        self._package_json = package_json
        self._bridge = None
        self._closed = False
        self._call_lock = None
        return self

    @property
    def backend_version(self) -> str | None:
        if self._bridge is None:
            return None
        return self._bridge.backend_version

    @property
    def closed(self) -> bool:
        if self._bridge is None:
            return self._closed
        return self._bridge.closed

    def __repr__(self) -> str:
        return (
            f"AsyncBash(backend_version={self.backend_version!r}, "
            f"closed={self.closed!r}, opened={self._bridge is not None!r})"
        )

    async def __aenter__(self) -> Self:
        async with self._lock():
            await self._ensure_bridge_open_locked()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _lock(self) -> asyncio.Lock:
        if self._call_lock is None:
            self._call_lock = asyncio.Lock()
        return self._call_lock

    async def _ensure_bridge_open_locked(self) -> AsyncNodeBridge:
        if self._bridge is not None:
            return self._bridge
        if self._closed:
            raise BridgeError("just-bash bridge is closed")

        bridge = await AsyncNodeBridge.open(
            init_options=self._options.to_wire(),
            custom_commands=self._custom_commands,
            node_command=self._node_command,
            js_entry=None if self._js_entry is None else str(self._js_entry),
            package_json=None if self._package_json is None else str(self._package_json),
        )
        self._bridge = bridge
        return bridge

    async def close(self) -> None:
        async with self._lock():
            if self._bridge is None:
                self._closed = True
                return

            bridge = self._bridge
            self._bridge = None
            self._closed = True
            await bridge.close()

    async def exec(
        self,
        command_line: str,
        *,
        env: Mapping[str, str] | None = None,
        replace_env: bool = False,
        cwd: str | None = None,
        raw_script: bool = False,
        stdin: str | None = None,
        args: Sequence[str] | None = None,
        timeout: float | None = None,
    ) -> ExecResult:
        return await self.exec_with_options(
            command_line,
            ExecOptions(
                env=env,
                replace_env=replace_env,
                cwd=cwd,
                raw_script=raw_script,
                stdin=stdin,
                args=args,
                timeout=timeout,
            ),
        )

    async def exec_with_options(self, command_line: str, options: ExecOptions) -> ExecResult:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            payload = await bridge.request(
                "exec",
                {
                    "script": command_line,
                    "options": options.to_wire(),
                },
                timeout=None if options.timeout is None else options.timeout + 5.0,
            )
        return ExecResult.from_wire(payload)

    async def read_text(self, path: str) -> str:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            return await bridge.request("read_text", {"path": path})

    async def read_bytes(self, path: str) -> bytes:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            payload = await bridge.request("read_bytes", {"path": path})
        return decode_bytes_payload(payload)

    async def write_text(self, path: str, content: str) -> None:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            await bridge.request("write_text", {"path": path, "content": content})

    async def write_bytes(self, path: str, content: bytes) -> None:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            await bridge.request(
                "write_bytes",
                {"path": path, "content": encode_file_value(content)},
            )

    async def get_env(self) -> dict[str, str]:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            return dict(await bridge.request("get_env"))

    async def get_cwd(self) -> str:
        async with self._lock():
            bridge = await self._ensure_bridge_open_locked()
            return await bridge.request("get_cwd")
