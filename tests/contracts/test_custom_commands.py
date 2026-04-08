from __future__ import annotations

import inspect
from typing import Any

import pytest

from tests.support.harness import load_public_api

CUSTOM_COMMANDS_REASON = "Python-defined custom commands are not implemented yet"
CUSTOM_COMMAND_CONTEXT_REASON = "Python custom command context bridging is not implemented yet"


def make_custom_command_session(**kwargs: Any) -> Any:
    Bash = load_public_api().Bash
    try:
        parameters = inspect.signature(Bash).parameters
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise NotImplementedError("Could not introspect the public Bash constructor") from exc

    if "custom_commands" not in parameters:
        raise NotImplementedError("The custom_commands public API is not implemented yet")

    return Bash(**kwargs)


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMANDS_REASON,
)
def test_custom_command_round_trips_through_shell() -> None:
    def hello(args: list[str], ctx: Any) -> dict[str, Any]:
        name = args[0] if args else "world"
        del ctx
        return {
            "stdout": f"hello, {name}!\n",
            "stderr": "",
            "exit_code": 0,
        }

    with make_custom_command_session(custom_commands={"hello": hello}) as bash:
        result = bash.exec("hello alice")

    assert result.stdout == "hello, alice!\n"
    assert result.stderr == ""
    assert result.exit_code == 0


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMAND_CONTEXT_REASON,
)
def test_custom_command_receives_context_and_can_nested_exec() -> None:
    def inspect_ctx(args: list[str], ctx: Any) -> dict[str, Any]:
        del args
        nested = ctx.exec("cat note.txt")
        return {
            "stdout": f"stdin={ctx.stdin!r}|cwd={ctx.cwd}|nested={nested.stdout}",
            "stderr": "",
            "exit_code": 0,
        }

    with make_custom_command_session(
        cwd="/workspace",
        files={"/workspace/note.txt": "from-nested-exec\n"},
        custom_commands={"inspect-ctx": inspect_ctx},
    ) as bash:
        result = bash.exec("inspect-ctx", stdin="payload")

    assert result.stdout == "stdin='payload'|cwd=/workspace|nested=from-nested-exec\n"
    assert result.exit_code == 0


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMANDS_REASON,
)
def test_custom_command_can_participate_in_pipelines() -> None:
    def upper(args: list[str], ctx: Any) -> dict[str, Any]:
        del args
        return {
            "stdout": ctx.stdin.upper(),
            "stderr": "",
            "exit_code": 0,
        }

    with make_custom_command_session(custom_commands={"py-upper": upper}) as bash:
        result = bash.exec("printf 'abC' | py-upper")

    assert result.stdout == "ABC"
    assert result.stderr == ""
    assert result.exit_code == 0


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMANDS_REASON,
)
def test_custom_command_can_override_builtin_name() -> None:
    def echo(args: list[str], ctx: Any) -> dict[str, Any]:
        del ctx
        return {
            "stdout": f"python-echo:{' '.join(args)}\n",
            "stderr": "",
            "exit_code": 0,
        }

    with make_custom_command_session(custom_commands={"echo": echo}) as bash:
        result = bash.exec("echo one two")

    assert result.stdout == "python-echo:one two\n"
    assert result.exit_code == 0


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMANDS_REASON,
)
def test_custom_command_nonzero_result_is_preserved() -> None:
    def deny(args: list[str], ctx: Any) -> dict[str, Any]:
        del args, ctx
        return {
            "stdout": "",
            "stderr": "permission denied\n",
            "exit_code": 17,
        }

    with make_custom_command_session(custom_commands={"deny": deny}) as bash:
        result = bash.exec("deny")

    assert result.stdout == ""
    assert result.stderr == "permission denied\n"
    assert result.exit_code == 17


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMANDS_REASON,
)
def test_async_custom_command_is_supported() -> None:
    async def hello(args: list[str], ctx: Any) -> dict[str, Any]:
        del ctx
        return {
            "stdout": f"async:{args[0] if args else 'world'}\n",
            "stderr": "",
            "exit_code": 0,
        }

    with make_custom_command_session(custom_commands={"hello": hello}) as bash:
        result = bash.exec("hello mars")

    assert result.stdout == "async:mars\n"
    assert result.exit_code == 0


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMAND_CONTEXT_REASON,
)
def test_custom_command_exception_becomes_shell_failure() -> None:
    def explode(args: list[str], ctx: Any) -> dict[str, Any]:
        del args, ctx
        raise RuntimeError("kaboom")

    with make_custom_command_session(custom_commands={"explode": explode}) as bash:
        result = bash.exec("explode")

    assert result.exit_code != 0
    assert "kaboom" in result.stderr
