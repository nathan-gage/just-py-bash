# just-py-bash

Python bindings for [just-bash](https://github.com/vercel-labs/just-bash).

`just-py-bash` exposes the same long-lived virtual shell through two public API styles:

- `Bash` for synchronous code
- `AsyncBash` for `asyncio` applications

Each session owns a dedicated Node.js worker process and a real upstream `just-bash` `Bash` instance, so upstream semantics are preserved:

- the virtual filesystem persists across `exec()` calls
- shell state is isolated per `exec()` call
- results come back as structured Python objects

## Install

```bash
uv add just-py-bash
```

A working Node.js runtime is still required at execution time.

## Synchronous API

Use `Bash` in scripts, CLIs, and synchronous services.

```python
from just_py_bash import Bash, ExecutionLimits

with Bash(
    cwd="/workspace",
    files={"/workspace/hello.txt": "hello\n"},
    execution_limits=ExecutionLimits(max_command_count=500),
) as bash:
    result = bash.exec("cat hello.txt")
    print(result.stdout, end="")

    bash.write_text("note.txt", "from python\n")
    print(bash.read_text("note.txt"), end="")
```

### Sync API surface

- `Bash(...)`
- `Bash.exec(...) -> ExecResult`
- `Bash.read_text(...) -> str`
- `Bash.read_bytes(...) -> bytes`
- `Bash.write_text(...) -> None`
- `Bash.write_bytes(...) -> None`
- `Bash.get_env() -> dict[str, str]`
- `Bash.get_cwd() -> str`
- `Bash.close() -> None`

## Asynchronous API

Use `AsyncBash` when you are already inside an event loop. Its bridge is implemented with native `asyncio` subprocesses, tasks, and locks rather than thread offloading.

```python
import asyncio

from just_py_bash import AsyncBash


async def main() -> None:
    async with AsyncBash(cwd="/workspace") as bash:
        await bash.write_text("note.txt", "hello from async\n")

        result = await bash.exec("cat note.txt")
        print(result.stdout, end="")

        pwd = await bash.get_cwd()
        print(f"cwd={pwd}")


asyncio.run(main())
```

`AsyncBash` mirrors the sync API, but methods are awaited:

- `AsyncBash(...)`
- `await AsyncBash.exec(...) -> ExecResult`
- `await AsyncBash.read_text(...) -> str`
- `await AsyncBash.read_bytes(...) -> bytes`
- `await AsyncBash.write_text(...) -> None`
- `await AsyncBash.write_bytes(...) -> None`
- `await AsyncBash.get_env() -> dict[str, str]`
- `await AsyncBash.get_cwd() -> str`
- `await AsyncBash.close() -> None`

## Custom commands

Python-defined commands work with both session styles because custom command execution happens inside the Python wrapper.

```python
from just_py_bash import Bash


def greet(args: list[str], ctx) -> dict[str, str | int]:
    name = args[0] if args else "world"
    return {"stdout": f"hello, {name}!\n", "exit_code": 0}


with Bash(custom_commands={"greet": greet}) as bash:
    result = bash.exec("greet mars")
    print(result.stdout, end="")
```

Async custom commands are supported too. With `AsyncBash`, nested execution is async as well:

```python
import asyncio

from just_py_bash import AsyncBash


async def pwd(args: list[str], ctx) -> dict[str, str | int]:
    del args
    nested = await ctx.exec("pwd")
    return {"stdout": nested.stdout, "exit_code": 0}


async def main() -> None:
    async with AsyncBash(custom_commands={"pwd-from-python": pwd}) as bash:
        result = await bash.exec("pwd-from-python")
        print(result.stdout, end="")


asyncio.run(main())
```

## Result handling

`exec()` returns an `ExecResult` with:

- `stdout: str`
- `stderr: str`
- `exit_code: int`
- `ok: bool`
- `check()` / `check_returncode()`

Example:

```python
from just_py_bash import Bash

with Bash() as bash:
    result = bash.exec("false")

if not result.ok:
    print(result.exit_code)
    print(result.stderr)
```

## Backend selection

By default the package uses its vendored `just-bash` runtime. To point at a different backend artifact, set:

- `JUST_PY_BASH_JS_ENTRY`
- `JUST_PY_BASH_PACKAGE_JSON`
- optionally `JUST_PY_BASH_NODE`

## Development bootstrap

For development in this repo, the wrapper can use `vendor/just-bash` directly:

```bash
cd vendor/just-bash
pnpm install
pnpm build
cd ../..
uv run pytest
```

## Conformance testing

The test suite treats upstream `just-bash` as the semantic oracle for current wrapper parity.

- `tests/parity/` compares the Python wrapper against a direct Node reference harness
- `tests/contracts/` covers Python-specific guarantees like custom commands and packaging
- `tests/api/` covers the public API contract

## Design notes

See [`docs/wrapping-plan.md`](docs/wrapping-plan.md).
