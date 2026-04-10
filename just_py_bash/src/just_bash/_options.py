from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ._fs import InitialFileValue, LazyFileProvider, LazyFileRegistry, encode_initial_files, filesystem_to_wire
from ._models import ExecutionLimits, JavaScriptConfig
from ._option_hooks import (
    BashLogger,
    DefenseInDepthConfig,
    DefenseViolationCallback,
    FeatureCoverageWriter,
    FetchCallback,
    TraceCallback,
)
from ._types import ExecOptionsWire, InitOptionsWire, NetworkConfig, ProcessInfo

if TYPE_CHECKING:
    from ._custom_commands import CustomCommandHandlers
    from ._fs import FileSystemConfig


@dataclass(slots=True, kw_only=True)
class BridgeOptionHooks:
    lazy_file_providers: dict[str, LazyFileProvider]
    fetch_callback: FetchCallback | None = None
    logger: BashLogger | None = None
    trace_callback: TraceCallback | None = None
    coverage_writer: FeatureCoverageWriter | None = None
    defense_violation_callback: DefenseViolationCallback | None = None


@dataclass(slots=True, kw_only=True)
class BashOptions:
    files: Mapping[str, InitialFileValue] | None = None
    env: Mapping[str, str] | None = None
    cwd: str | None = None
    fs: FileSystemConfig | None = None
    execution_limits: ExecutionLimits | None = None
    python: bool = False
    javascript: bool | JavaScriptConfig = False
    commands: Sequence[str] | None = None
    custom_commands: CustomCommandHandlers | None = None
    fetch: FetchCallback | None = None
    logger: BashLogger | None = None
    trace: TraceCallback | None = None
    defense_in_depth: bool | DefenseInDepthConfig | None = None
    coverage: FeatureCoverageWriter | None = None
    network: NetworkConfig | None = None
    process_info: ProcessInfo | None = None

    def to_bridge_init(self) -> tuple[InitOptionsWire, BridgeOptionHooks]:
        init_options: InitOptionsWire = {}
        registry = LazyFileRegistry()

        if self.files is not None:
            init_options["files"] = encode_initial_files(self.files, registry=registry)
        if self.env is not None:
            init_options["env"] = dict(self.env)
        if self.cwd is not None:
            init_options["cwd"] = self.cwd
        if self.fs is not None:
            init_options["fs"] = filesystem_to_wire(self.fs, registry=registry)
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
        if self.fetch is not None:
            init_options["fetchEnabled"] = True
        if self.logger is not None:
            init_options["loggerEnabled"] = True
        if self.trace is not None:
            init_options["traceEnabled"] = True
        if self.coverage is not None:
            init_options["coverageEnabled"] = True
        if self.defense_in_depth is not None:
            init_options["defenseInDepth"] = (
                self.defense_in_depth.to_wire()
                if isinstance(self.defense_in_depth, DefenseInDepthConfig)
                else self.defense_in_depth
            )
        if self.network is not None:
            init_options["network"] = self.network
        if self.process_info is not None:
            init_options["processInfo"] = self.process_info

        hooks = BridgeOptionHooks(
            lazy_file_providers=dict(registry.providers),
            fetch_callback=self.fetch,
            logger=self.logger,
            trace_callback=self.trace,
            coverage_writer=self.coverage,
            defense_violation_callback=(
                self.defense_in_depth.on_violation if isinstance(self.defense_in_depth, DefenseInDepthConfig) else None
            ),
        )
        return init_options, hooks

    def to_wire(self) -> InitOptionsWire:
        init_options, hooks = self.to_bridge_init()
        if hooks.lazy_file_providers:
            raise ValueError("Lazy file callbacks require bridge-aware initialization")
        if hooks.fetch_callback is not None:
            raise ValueError("Custom fetch callbacks require bridge-aware initialization")
        if hooks.logger is not None:
            raise ValueError("Logger callbacks require bridge-aware initialization")
        if hooks.trace_callback is not None:
            raise ValueError("Trace callbacks require bridge-aware initialization")
        if hooks.coverage_writer is not None:
            raise ValueError("Coverage writers require bridge-aware initialization")
        if hooks.defense_violation_callback is not None:
            raise ValueError("Defense violation callbacks require bridge-aware initialization")
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
