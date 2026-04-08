from __future__ import annotations

import asyncio

from just_py_bash import AsyncBash, AsyncCustomCommandContext


def ok(*, stdout: str = "", stderr: str = "", exit_code: int = 0) -> dict[str, str | int]:
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
    }


async def annotate_command(args: list[str], ctx: AsyncCustomCommandContext) -> dict[str, str | int]:
    label = args[0] if args else "note"
    nested = await ctx.exec("wc -w", stdin=ctx.stdin)
    word_count = nested.stdout.strip().split()[0] if nested.stdout.strip() else "0"
    body = ctx.stdin.rstrip("\n")
    return ok(stdout=f"[{label}] words={word_count} body={body}\n")


async def main() -> None:
    async with AsyncBash(custom_commands={"annotate": annotate_command}) as bash:
        print("=== Async Custom Command Demo ===\n")

        result = await bash.exec("printf 'one two three' | annotate summary")
        print(result.stdout, end="")

        chained = await bash.exec("printf 'alpha beta' | annotate memo | tr a-z A-Z")
        print(chained.stdout, end="")


if __name__ == "__main__":
    asyncio.run(main())
