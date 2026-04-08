from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeAlias, TypedDict, TypeGuard

from ._options import ExecOptions
from ._types import ExecResultWire

if TYPE_CHECKING:
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
CustomCommands: TypeAlias = Mapping[str, CustomCommandCallback]


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

        options = ExecOptions(
            env=env,
            replace_env=replace_env,
            cwd=cwd,
            raw_script=raw_script,
            stdin=stdin,
            args=args,
            timeout=timeout,
        )
        payload = self._bridge.request(
            "custom_command_exec",
            {
                "invocationId": self._invocation_id,
                "script": command_line,
                "options": options.to_wire(),
            },
            timeout=None if timeout is None else timeout + 5.0,
        )
        return ExecResult.from_wire(payload)


def is_custom_command_coroutine(value: object) -> TypeGuard[CustomCommandCoroutine]:
    return asyncio.iscoroutine(value)


def is_custom_command_return(value: object) -> TypeGuard[CustomCommandReturn]:
    return not is_custom_command_coroutine(value)


def is_custom_command_mapping(value: object) -> TypeGuard[CustomCommandResultDict]:
    return isinstance(value, Mapping)


def is_exec_result_like(value: CustomCommandReturn) -> TypeGuard[ExecResultLike]:
    return not is_custom_command_mapping(value)


def invoke_custom_command(
    callback: CustomCommandCallback,
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
