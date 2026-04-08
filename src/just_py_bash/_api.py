from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Self

from ._bridge import NodeBridge, decode_bytes_payload, encode_file_value
from ._models import ExecResult, ExecutionLimits, FileValue, JavaScriptConfig


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
        execution_limits: ExecutionLimits | None = None,
        python: bool = False,
        javascript: bool | JavaScriptConfig = False,
        commands: Sequence[str] | None = None,
        network: Mapping[str, Any] | None = None,
        process_info: Mapping[str, int] | None = None,
        node_command: Sequence[str] | None = None,
        js_entry: str | None = None,
        package_json: str | None = None,
    ) -> None:
        init_options: dict[str, Any] = {}

        if files is not None:
            init_options["files"] = {path: encode_file_value(content) for path, content in files.items()}
        if env is not None:
            init_options["env"] = dict(env)
        if cwd is not None:
            init_options["cwd"] = cwd
        if execution_limits is not None:
            init_options["executionLimits"] = execution_limits.to_wire()
        if python:
            init_options["python"] = True
        if javascript:
            init_options["javascript"] = javascript.to_wire() if isinstance(javascript, JavaScriptConfig) else True
        if commands is not None:
            init_options["commands"] = list(commands)
        if network is not None:
            init_options["network"] = dict(network)
        if process_info is not None:
            init_options["processInfo"] = dict(process_info)

        self._bridge = NodeBridge(
            init_options=init_options,
            node_command=node_command,
            js_entry=js_entry,
            package_json=package_json,
        )
        self.backend_version = self._bridge.backend_version

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
        options: dict[str, Any] = {}
        if env is not None:
            options["env"] = dict(env)
        if replace_env:
            options["replaceEnv"] = True
        if cwd is not None:
            options["cwd"] = cwd
        if raw_script:
            options["rawScript"] = True
        if stdin is not None:
            options["stdin"] = stdin
        if args is not None:
            options["args"] = list(args)
        if timeout is not None:
            options["timeoutMs"] = max(1, int(timeout * 1000))

        payload = self._bridge.request(
            "exec",
            {
                "script": command_line,
                "options": options,
            },
            timeout=None if timeout is None else timeout + 5.0,
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
