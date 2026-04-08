from __future__ import annotations

import json
import shlex
from typing import Final
from uuid import uuid4

from just_py_bash import Bash, CustomCommandContext

PARAGRAPHS: Final[list[str]] = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
]


def ok(*, stdout: str = "", stderr: str = "", exit_code: int = 0) -> dict[str, str | int]:
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
    }


def uuid_command(args: list[str], ctx: CustomCommandContext) -> dict[str, str | int]:
    del ctx

    count = 1
    if "-n" in args:
        index = args.index("-n")
        if index + 1 >= len(args):
            return ok(stderr="uuid: missing value for -n\n", exit_code=1)
        try:
            count = int(args[index + 1])
        except ValueError:
            return ok(stderr="uuid: invalid count\n", exit_code=1)
        if count < 1:
            return ok(stderr="uuid: invalid count\n", exit_code=1)

    return ok(stdout="\n".join(str(uuid4()) for _ in range(count)) + "\n")


def json_format_command(args: list[str], ctx: CustomCommandContext) -> dict[str, str | int]:
    input_text = ctx.stdin

    if args and not input_text:
        nested = ctx.exec(f"cat {shlex.quote(args[0])}")
        if nested.exit_code != 0:
            return ok(stderr=f"json-format: {args[0]}: No such file\n", exit_code=1)
        input_text = nested.stdout

    if not input_text.strip():
        return ok(stderr="json-format: no input\n", exit_code=1)

    try:
        parsed = json.loads(input_text)
    except json.JSONDecodeError:
        return ok(stderr="json-format: invalid JSON\n", exit_code=1)

    return ok(stdout=json.dumps(parsed, indent=2) + "\n")


def lorem_command(args: list[str], ctx: CustomCommandContext) -> dict[str, str | int]:
    del ctx

    count = 1
    if args:
        try:
            count = int(args[0])
        except ValueError:
            return ok(stderr="lorem: invalid paragraph count\n", exit_code=1)
        if count < 1:
            return ok(stderr="lorem: invalid paragraph count\n", exit_code=1)

    output = "\n\n".join(PARAGRAPHS[index % len(PARAGRAPHS)] for index in range(count))
    return ok(stdout=output + "\n")


def wordcount_command(args: list[str], ctx: CustomCommandContext) -> dict[str, str | int]:
    input_text = ctx.stdin

    if args and not input_text:
        nested = ctx.exec(f"cat {shlex.quote(args[0])}")
        if nested.exit_code != 0:
            return ok(stderr=f"wordcount: {args[0]}: No such file\n", exit_code=1)
        input_text = nested.stdout

    lines = len(input_text.splitlines())
    words = len(input_text.split())
    chars = len(input_text)
    return ok(stdout=f"Lines: {lines}\nWords: {words}\nChars: {chars}\n")


def reverse_command(args: list[str], ctx: CustomCommandContext) -> dict[str, str | int]:
    del args
    reversed_lines = [line[::-1] for line in ctx.stdin.splitlines()]
    trailing_newline = "\n" if ctx.stdin.endswith("\n") else ""
    return ok(stdout="\n".join(reversed_lines) + trailing_newline)


COMMANDS = {
    "uuid": uuid_command,
    "json-format": json_format_command,
    "lorem": lorem_command,
    "wordcount": wordcount_command,
    "reverse": reverse_command,
}


def show(title: str, body: str) -> None:
    print(title)
    print(body, end="" if body.endswith("\n") else "\n")
    print()


def main() -> None:
    with Bash(
        custom_commands=COMMANDS,
        files={"/data/sample.json": '{"name":"Alice","age":30,"city":"NYC"}'},
    ) as bash:
        print("=== Python Custom Commands Demo ===\n")

        show("1. Generate UUIDs:", bash.exec("uuid -n 3").stdout)
        show("2. Format JSON from file:", bash.exec("json-format /data/sample.json").stdout)
        show("3. Format JSON from pipe:", bash.exec("printf '{\"a\":1,\"b\":2}' | json-format").stdout)
        show("4. Generate lorem ipsum (2 paragraphs):", bash.exec("lorem 2").stdout)
        show("5. Count words in lorem ipsum:", bash.exec("lorem | wordcount").stdout)
        show("6. Reverse text:", bash.exec("echo 'Hello World' | reverse").stdout)
        show("7. Combine with built-ins (sort UUIDs):", bash.exec("uuid -n 5 | sort").stdout)
        show("8. Complex pipeline:", bash.exec("lorem 3 | wordcount | grep Words").stdout)


if __name__ == "__main__":
    main()
