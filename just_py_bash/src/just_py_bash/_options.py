from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._codec import encode_file_value
from ._models import ExecutionLimits, JavaScriptConfig
from ._types import ExecOptionsWire, FileValue, InitOptionsWire, NetworkConfig, ProcessInfo

if TYPE_CHECKING:
    from ._custom_commands import CustomCommandHandlers


@dataclass(slots=True, kw_only=True)
class BashOptions:
    files: Mapping[str, FileValue] | None = None
    env: Mapping[str, str] | None = None
    cwd: str | None = None
    execution_limits: ExecutionLimits | None = None
    python: bool = False
    javascript: bool | JavaScriptConfig = False
    commands: Sequence[str] | None = None
    custom_commands: CustomCommandHandlers | None = None
    network: NetworkConfig | None = None
    process_info: ProcessInfo | None = None

    def to_wire(self) -> InitOptionsWire:
        init_options: InitOptionsWire = {}

        if self.files is not None:
            init_options["files"] = {path: encode_file_value(content) for path, content in self.files.items()}
        if self.env is not None:
            init_options["env"] = dict(self.env)
        if self.cwd is not None:
            init_options["cwd"] = self.cwd
        if self.execution_limits is not None:
            init_options["executionLimits"] = self.execution_limits.to_wire()
        if self.python:
            init_options["python"] = True
        if self.javascript:
            init_options["javascript"] = (
                self.javascript.to_wire() if isinstance(self.javascript, JavaScriptConfig) else True
            )
        if self.commands is not None:
            init_options["commands"] = list(self.commands)
        if self.custom_commands is not None:
            init_options["customCommandNames"] = list(self.custom_commands)
        if self.network is not None:
            init_options["network"] = self.network
        if self.process_info is not None:
            init_options["processInfo"] = self.process_info

        return init_options


@dataclass(slots=True, kw_only=True)
class ExecOptions:
    env: Mapping[str, str] | None = None
    replace_env: bool = False
    cwd: str | None = None
    raw_script: bool = False
    stdin: str | None = None
    args: Sequence[str] | None = None
    timeout: float | None = None

    def to_wire(self) -> ExecOptionsWire:
        options: ExecOptionsWire = {}

        if self.env is not None:
            options["env"] = dict(self.env)
        if self.replace_env:
            options["replaceEnv"] = True
        if self.cwd is not None:
            options["cwd"] = self.cwd
        if self.raw_script:
            options["rawScript"] = True
        if self.stdin is not None:
            options["stdin"] = self.stdin
        if self.args is not None:
            options["args"] = list(self.args)
        if self.timeout is not None:
            options["timeoutMs"] = max(1, int(self.timeout * 1000))

        return options
