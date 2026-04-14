from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Self, cast

from ._bridge import NodeBridge
from ._custom_commands import CustomCommands
from ._exceptions import BridgeTimeoutError
from ._fs import FileSystemConfig, InitialFileValue
from ._models import ExecResult, ExecutionLimits, JavaScriptConfig
from ._option_hooks import BashLogger, DefenseInDepthConfig, FeatureCoverageWriter, FetchCallback, TraceCallback
from ._options import BashOptions, ExecOptions
from ._session_fs import SessionFs
from ._transform import BashTransformResult, TransformPlugin
from ._types import NetworkConfig, ProcessInfo


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
        files: Mapping[str, InitialFileValue] | None = None,
        env: Mapping[str, str] | None = None,
        cwd: str | None = None,
        fs: FileSystemConfig | None = None,
        execution_limits: ExecutionLimits | None = None,
        python: bool = False,
        javascript: bool | JavaScriptConfig = False,
        commands: Sequence[str] | None = None,
        custom_commands: CustomCommands | None = None,
        fetch: FetchCallback | None = None,
        logger: BashLogger | None = None,
        trace: TraceCallback | None = None,
        defense_in_depth: bool | DefenseInDepthConfig | None = None,
        coverage: FeatureCoverageWriter | None = None,
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
                fetch=fetch,
                logger=logger,
                trace=trace,
                defense_in_depth=defense_in_depth,
                coverage=coverage,
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
        self._options = options
        self._node_command = tuple(str(part) for part in node_command) if node_command is not None else None
        self._js_entry = js_entry
        self._package_json = package_json
        init_options, hooks = options.to_bridge_init()
        self._bridge = NodeBridge(
            init_options=init_options,
            custom_commands=options.custom_commands,
            lazy_file_providers=hooks.lazy_file_providers,
            fetch_callback=hooks.fetch_callback,
            logger=hooks.logger,
            trace_callback=hooks.trace_callback,
            coverage_writer=hooks.coverage_writer,
            defense_violation_callback=hooks.defense_violation_callback,
            node_command=self._node_command,
            js_entry=self._js_entry,
            package_json=self._package_json,
        )
        self.fs = SessionFs(self._bridge)

    @property
    def backend_version(self) -> str | None:
        return self._bridge.backend_version

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Bash(backend_version={self.backend_version!r}, closed={self.closed!r})"

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
        try:
            payload = self._bridge.request(
                "exec",
                {
                    "script": command_line,
                    "options": options.to_wire(),
                },
                timeout=None if options.timeout is None else options.timeout + 5.0,
            )
        except BridgeTimeoutError:
            if options.timeout is None:
                raise
            self._open_bridge(
                self._options,
                node_command=self._node_command,
                js_entry=self._js_entry,
                package_json=self._package_json,
            )
            return _timed_out_exec_result(options.timeout)
        return ExecResult.from_wire(payload)

    def register_transform_plugin(self, plugin: TransformPlugin) -> None:
        self._bridge.request_raw("register_transform_plugin", {"plugin": plugin.to_wire()})

    def transform(self, command_line: str) -> BashTransformResult:
        raw_payload = self._bridge.request_raw("transform", {"script": command_line})
        if not isinstance(raw_payload, Mapping):
            raise TypeError(f"Expected a transform result mapping, got {type(raw_payload).__name__}")
        payload = cast(Mapping[str, object], raw_payload)
        return BashTransformResult.from_wire(payload)

    def read_text(self, path: str) -> str:
        return self.fs.read_text(path)

    def read_bytes(self, path: str) -> bytes:
        return self.fs.read_bytes(path)

    def write_text(self, path: str, content: str) -> None:
        self.fs.write_text(path, content)

    def write_bytes(self, path: str, content: bytes) -> None:
        self.fs.write_bytes(path, content)

    def get_env(self) -> dict[str, str]:
        return dict(self._bridge.request("get_env"))

    def get_cwd(self) -> str:
        return self._bridge.request("get_cwd")

    @property
    def closed(self) -> bool:
        return self._bridge.closed


def _timed_out_exec_result(timeout: float) -> ExecResult:
    timeout_ms = max(1, int(timeout * 1000))
    return ExecResult(
        stdout="",
        stderr=f"bash: execution timeout exceeded after {timeout_ms}ms; session was reset\n",
        exit_code=124,
        metadata={"timed_out": True, "timeout_ms": timeout_ms, "session_reset": True},
    )
