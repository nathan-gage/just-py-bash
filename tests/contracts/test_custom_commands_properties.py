from __future__ import annotations

from typing import Any, Literal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tests.contracts.test_custom_commands import (
    CUSTOM_COMMAND_CONTEXT_REASON,
    CUSTOM_COMMANDS_REASON,
    make_custom_command_session,
)

BLACKLIST_CATEGORIES: tuple[Literal["Cs"], ...] = ("Cs",)
TEXT_VALUES = st.text(
    alphabet=st.characters(
        blacklist_categories=BLACKLIST_CATEGORIES,
        blacklist_characters="\r",
    ),
    min_size=0,
    max_size=20,
)
EXIT_CODES = st.integers(min_value=0, max_value=9)


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMAND_CONTEXT_REASON,
)
@settings(max_examples=12, deadline=None)
@given(arg=TEXT_VALUES, stdin=TEXT_VALUES, token=TEXT_VALUES)
def test_custom_command_reflects_args_stdin_and_env(
    arg: str,
    stdin: str,
    token: str,
) -> None:
    def reflect(args: list[str], ctx: Any) -> dict[str, Any]:
        return {
            "stdout": f"{args[0] if args else ''}|{ctx.stdin}|{ctx.env.get('TOKEN', '')}",
            "stderr": "",
            "exit_code": 0,
        }

    with make_custom_command_session(custom_commands={"reflect": reflect}) as bash:
        result = bash.exec("reflect", args=[arg], stdin=stdin, env={"TOKEN": token})

    assert result.stdout == f"{arg}|{stdin}|{token}"
    assert result.stderr == ""
    assert result.exit_code == 0


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason=CUSTOM_COMMANDS_REASON,
)
@settings(max_examples=12, deadline=None)
@given(stdout=TEXT_VALUES, stderr=TEXT_VALUES, exit_code=EXIT_CODES)
def test_custom_command_result_fields_round_trip(
    stdout: str,
    stderr: str,
    exit_code: int,
) -> None:
    def emit(args: list[str], ctx: Any) -> dict[str, Any]:
        del args, ctx
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
        }

    with make_custom_command_session(custom_commands={"emit": emit}) as bash:
        result = bash.exec("emit")

    assert result.stdout == stdout
    assert result.stderr == stderr
    assert result.exit_code == exit_code
