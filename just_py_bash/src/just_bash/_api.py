from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Self

from ._bridge import NodeBridge
from ._codec import decode_bytes_payload, encode_file_value
from ._custom_commands import CustomCommands
from ._fs import FileSystemConfig
from ._models import ExecResult, ExecutionLimits, JavaScriptConfig
from ._options import BashOptions, ExecOptions
from ._types import FileValue, NetworkConfig, ProcessInfo


class Bash:
    """Python wrapper around a long-lived just-bash session.

    Each instance owns a dedicated Node.js worker process and a single just-bash
    ``Bash`` instance inside that worker.

    just-bash semantics are preserved:
    - filesystem state is shared across ``exec`` calls
    - shell state is isolated per ``exec`` call
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
        custom_commands: CustomCommands | None = None,
        network: NetworkConfig | None = None,
        process_info: ProcessInfo | None = None,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> None:
        self._open_bridge(
            BashOptions(
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
            ),
            node_command=node_command,
            js_entry=js_entry,
            package_json=package_json,
        )

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
        self._open_bridge(
            options,
            node_command=node_command,
            js_entry=js_entry,
            package_json=package_json,
        )
        return self

    def _open_bridge(
        self,
        options: BashOptions,
        *,
        node_command: Sequence[str] | None,
        js_entry: str | os.PathLike[str] | None,
        package_json: str | os.PathLike[str] | None,
    ) -> None:
        self._bridge = NodeBridge(
            init_options=options.to_wire(),
            custom_commands=options.custom_commands,
            node_command=node_command,
            js_entry=js_entry,
            package_json=package_json,
        )

    @property
    def backend_version(self) -> str | None:
        return self._bridge.backend_version

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        cwd = None if self.closed else self.get_cwd()
        return f"Bash(backend_version={self.backend_version!r}, cwd={cwd!r})"

    def close(self) -> None:
        self._bridge.close()

    def exec(
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
        return self.exec_with_options(
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

    def exec_with_options(self, command_line: str, options: ExecOptions) -> ExecResult:
        payload = self._bridge.request(
            "exec",
            {
                "script": command_line,
                "options": options.to_wire(),
            },
            timeout=None if options.timeout is None else options.timeout + 5.0,
        )
        return ExecResult.from_wire(payload)

    def read_text(self, path: str) -> str:
        return self._bridge.request("read_text", {"path": path})

    def read_bytes(self, path: str) -> bytes:
        payload = self._bridge.request("read_bytes", {"path": path})
        return decode_bytes_payload(payload)

    def write_text(self, path: str, content: str) -> None:
        self._bridge.request("write_text", {"path": path, "content": content})

    def write_bytes(self, path: str, content: bytes) -> None:
        self._bridge.request(
            "write_bytes",
            {"path": path, "content": encode_file_value(content)},
        )

    def get_env(self) -> dict[str, str]:
        return dict(self._bridge.request("get_env"))

    def get_cwd(self) -> str:
        return self._bridge.request("get_cwd")

    @property
    def closed(self) -> bool:
        return self._bridge.closed
