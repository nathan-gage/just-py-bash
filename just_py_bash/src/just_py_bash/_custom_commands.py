from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeAlias, TypedDict, TypeGuard

from ._options import ExecOptions
from ._types import ExecOptionsWire, ExecResultWire

if TYPE_CHECKING:
    from ._async_bridge import AsyncNodeBridge
    from ._bridge import NodeBridge
    from ._models import ExecResult


class CustomCommandResultDict(TypedDict, total=False):
    stdout: str
    stderr: str
    exit_code: int
    exitCode: int


class ExecResultLike(Protocol):
    stdout: str
    stderr: str
    exit_code: int


CustomCommandReturn: TypeAlias = CustomCommandResultDict | ExecResultLike
CustomCommandCoroutine: TypeAlias = Coroutine[object, object, CustomCommandReturn]
CustomCommandCallback: TypeAlias = Callable[
    [list[str], "CustomCommandContext"], CustomCommandReturn | CustomCommandCoroutine
]
AsyncCustomCommandCallback: TypeAlias = Callable[
    [list[str], "AsyncCustomCommandContext"], CustomCommandReturn | CustomCommandCoroutine
]
CustomCommandHandler: TypeAlias = Callable[..., CustomCommandReturn | CustomCommandCoroutine]
CustomCommands: TypeAlias = Mapping[str, CustomCommandCallback]
AsyncCustomCommands: TypeAlias = Mapping[str, AsyncCustomCommandCallback]
CustomCommandHandlers: TypeAlias = Mapping[str, CustomCommandHandler]
AsyncCustomCommandHandlers: TypeAlias = Mapping[str, CustomCommandHandler]


@dataclass(slots=True, frozen=True)
class CommandResultWire:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    def to_wire(self) -> ExecResultWire:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exitCode": self.exit_code,
        }


@dataclass(slots=True)
class CustomCommandContext:
    _bridge: NodeBridge
    _invocation_id: int
    cwd: str
    env: dict[str, str]
    stdin: str

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
        from ._models import ExecResult

        payload = self._bridge.request(
            "custom_command_exec",
            {
                "invocationId": self._invocation_id,
                "script": command_line,
                "options": _exec_options_to_wire(
                    env=env,
                    replace_env=replace_env,
                    cwd=cwd,
                    raw_script=raw_script,
                    stdin=stdin,
                    args=args,
                    timeout=timeout,
                ),
            },
            timeout=None if timeout is None else timeout + 5.0,
        )
        return ExecResult.from_wire(payload)

    async def exec_async(
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
        return await asyncio.to_thread(
            self.exec,
            command_line,
            env=env,
            replace_env=replace_env,
            cwd=cwd,
            raw_script=raw_script,
            stdin=stdin,
            args=args,
            timeout=timeout,
        )


@dataclass(slots=True)
class AsyncCustomCommandContext:
    _bridge: AsyncNodeBridge
    _invocation_id: int
    cwd: str
    env: dict[str, str]
    stdin: str

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
        from ._models import ExecResult

        payload = await self._bridge.request(
            "custom_command_exec",
            {
                "invocationId": self._invocation_id,
                "script": command_line,
                "options": _exec_options_to_wire(
                    env=env,
                    replace_env=replace_env,
                    cwd=cwd,
                    raw_script=raw_script,
                    stdin=stdin,
                    args=args,
                    timeout=timeout,
                ),
            },
            timeout=None if timeout is None else timeout + 5.0,
        )
        return ExecResult.from_wire(payload)

    async def exec_async(
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
        return await self.exec(
            command_line,
            env=env,
            replace_env=replace_env,
            cwd=cwd,
            raw_script=raw_script,
            stdin=stdin,
            args=args,
            timeout=timeout,
        )


def _exec_options_to_wire(
    *,
    env: Mapping[str, str] | None,
    replace_env: bool,
    cwd: str | None,
    raw_script: bool,
    stdin: str | None,
    args: Sequence[str] | None,
    timeout: float | None,
) -> ExecOptionsWire:
    return ExecOptions(
        env=env,
        replace_env=replace_env,
        cwd=cwd,
        raw_script=raw_script,
        stdin=stdin,
        args=args,
        timeout=timeout,
    ).to_wire()


def is_custom_command_coroutine(value: object) -> TypeGuard[CustomCommandCoroutine]:
    return asyncio.iscoroutine(value)


def is_custom_command_return(value: object) -> TypeGuard[CustomCommandReturn]:
    return not is_custom_command_coroutine(value)


def is_custom_command_mapping(value: object) -> TypeGuard[CustomCommandResultDict]:
    return isinstance(value, Mapping)


def is_exec_result_like(value: CustomCommandReturn) -> TypeGuard[ExecResultLike]:
    return not is_custom_command_mapping(value)


def invoke_custom_command(
    callback: CustomCommandHandler,
    args: list[str],
    context: CustomCommandContext,
) -> CommandResultWire:
    result = callback(args, context)
    if is_custom_command_coroutine(result):
        resolved = asyncio.run(result)
    else:
        if not is_custom_command_return(result):
            raise TypeError("Custom commands must return a mapping, ExecResult-like object, or coroutine")
        resolved = result
    return normalize_custom_command_result(resolved)


async def invoke_async_custom_command(
    callback: CustomCommandHandler,
    args: list[str],
    context: AsyncCustomCommandContext,
) -> CommandResultWire:
    result = callback(args, context)
    if is_custom_command_coroutine(result):
        resolved = await result
    else:
        if not is_custom_command_return(result):
            raise TypeError("Custom commands must return a mapping, ExecResult-like object, or coroutine")
        resolved = result
    return normalize_custom_command_result(resolved)


def normalize_custom_command_result(value: CustomCommandReturn) -> CommandResultWire:
    if is_custom_command_mapping(value):
        stdout = value.get("stdout", "")
        stderr = value.get("stderr", "")
        exit_code = value.get("exit_code", value.get("exitCode", 0))
        return CommandResultWire(
            stdout=str(stdout),
            stderr=str(stderr),
            exit_code=int(exit_code),
        )

    if is_exec_result_like(value):
        return CommandResultWire(
            stdout=str(value.stdout),
            stderr=str(value.stderr),
            exit_code=int(value.exit_code),
        )

    raise TypeError("Custom commands must return a mapping or ExecResult-like object")


def command_error_result(error: BaseException) -> CommandResultWire:
    return CommandResultWire(stderr=f"{error}\n", exit_code=1)
