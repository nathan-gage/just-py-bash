# just-py-bash

Python bindings for [just-bash](https://github.com/vercel-labs/just-bash).

`just-py-bash` gives Python code the same long-lived virtual shell that upstream `just-bash` exposes in TypeScript, with two public API styles:

- `Bash` for synchronous code
- `AsyncBash` for native-`asyncio` code

Each session owns a dedicated Node.js worker process and a real upstream `just-bash` `Bash` instance. That means upstream semantics are preserved:

- each `exec()` call gets its own isolated shell state
- the virtual filesystem is shared across `exec()` calls
- results come back as structured Python objects

## Install

```bash
uv add just-py-bash
```

A working Node.js runtime is still required at execution time.

## Quick Start

### Synchronous API

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

### Asynchronous API

`AsyncBash` is implemented with native `asyncio` subprocesses, tasks, futures, and locks.

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

## Custom Commands

Upstream `just-bash` uses `defineCommand(...)`. The Python wrapper exposes the same capability with a Python mapping of command names to callables.

### Sync custom commands

```python
from just_py_bash import Bash, CustomCommandContext


def greet(args: list[str], ctx: CustomCommandContext) -> dict[str, str | int]:
    del ctx
    name = args[0] if args else "world"
    return {"stdout": f"hello, {name}!\n", "exit_code": 0}


with Bash(custom_commands={"greet": greet}) as bash:
    result = bash.exec("greet mars")
    print(result.stdout, end="")
```

### Async custom commands

```python
import asyncio

from just_py_bash import AsyncBash, AsyncCustomCommandContext


async def annotate(args: list[str], ctx: AsyncCustomCommandContext) -> dict[str, str | int]:
    label = args[0] if args else "note"
    nested = await ctx.exec("wc -w", stdin=ctx.stdin)
    words = nested.stdout.strip().split()[0] if nested.stdout.strip() else "0"
    return {"stdout": f"[{label}] words={words}\n", "exit_code": 0}


async def main() -> None:
    async with AsyncBash(custom_commands={"annotate": annotate}) as bash:
        result = await bash.exec("printf 'one two three' | annotate summary")
        print(result.stdout, end="")


asyncio.run(main())
```

Custom commands can:

- receive shell arguments
- read `ctx.stdin`, `ctx.cwd`, and `ctx.env`
- run nested shell commands with `ctx.exec(...)`
- participate in pipelines and redirections
- override built-in command names if desired
- return non-zero exit codes
- raise exceptions, which become shell failures

## Configuration

The Python API mirrors the upstream configuration model, adapted to Python types and keyword arguments.

```python
from just_py_bash import Bash, ExecutionLimits, JavaScriptConfig

bash = Bash(
    files={"/data/file.txt": "content"},
    env={"MY_VAR": "value"},
    cwd="/app",
    execution_limits=ExecutionLimits(max_call_depth=50),
    python=True,
    javascript=JavaScriptConfig(bootstrap="globalThis.answer = 42;"),
)

result = bash.exec("echo $TEMP", env={"TEMP": "value"}, cwd="/tmp")
result = bash.exec("cat", stdin="hello from stdin\n")
result = bash.exec("env", replace_env=True, env={"ONLY": "this"})
result = bash.exec("grep", args=["-r", "TODO", "src/"])
result = bash.exec("cat <<EOF\n  indented\nEOF", raw_script=True)
result = bash.exec("while true; do sleep 1; done", timeout=5)

bash.close()
```

### Session options

- `files`: initial in-memory files
- `env`: initial environment
- `cwd`: starting directory
- `execution_limits`: validated execution protection settings
- `python=True`: enable `python` / `python3`
- `javascript=True` or `JavaScriptConfig(...)`: enable `js-exec`
- `commands`: allowlist commands
- `custom_commands`: register Python-defined commands
- `network`: configure allow-listed network access
- `process_info`: process metadata passed to the backend

### Per-exec options

- `env`: environment variables for this execution only
- `cwd`: working directory for this execution only
- `stdin`: standard input passed to the script
- `args`: argv passed directly to the first command
- `replace_env`: start with an empty environment instead of merging
- `raw_script`: skip leading-whitespace normalization
- `timeout`: cooperative timeout in seconds

`AsyncBash.exec(...)` accepts the same options; you just `await` the call.

## Optional Capabilities

### Network Access

Network access is disabled by default. Enable it with `network=...`.

```python
from just_py_bash import Bash

with Bash(
    network={
        "allowedUrlPrefixes": [
            "http://example.com",
            "https://api.github.com/repos/vercel-labs/",
        ],
    }
) as bash:
    result = bash.exec("curl -s http://example.com | html-to-markdown | head -n 12")
    print(result.stdout, end="")
```

Like upstream `just-bash`, `curl` only exists when network access is configured.

### Python Support

The Python wrapper passes `python=True` through to upstream `just-bash`.

```python
from just_py_bash import Bash

with Bash(python=True) as bash:
    result = bash.exec('python -c "print(sum([2, 3, 5]))"')
    print(result.stdout, end="")
```

### JavaScript Support

The Python wrapper passes `javascript=True` or `JavaScriptConfig(...)` through to upstream `just-bash`.

```python
from just_py_bash import Bash, JavaScriptConfig

with Bash(javascript=JavaScriptConfig(bootstrap="globalThis.prefix = 'bootstrapped';")) as bash:
    result = bash.exec("js-exec -c 'console.log(globalThis.prefix + \":\" + (2 + 3))'")
    print(result.stdout, end="")
```

See `examples/configuration_and_runtimes.py` for a runnable end-to-end example.

## Examples

The repo includes a Python `examples/` directory that mirrors the spirit of the vendored upstream examples and README:

| File | What it shows |
|---|---|
| `examples/quickstart_sync.py` | Basic synchronous usage |
| `examples/quickstart_async.py` | Native-async usage with `AsyncBash` |
| `examples/custom_commands_sync.py` | A Python port of the upstream custom-command showcase |
| `examples/custom_commands_async.py` | Async custom commands with nested async exec |
| `examples/configuration_and_runtimes.py` | Session config, per-exec overrides, Python, and JavaScript runtimes |
| `examples/network_access.py` | Allow-listed network access with `curl` |

See [`examples/README.md`](examples/README.md) for run instructions.

## Result Handling

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

## Backend Selection

By default the package uses its vendored `just-bash` runtime. To point at a different backend artifact, set:

- `JUST_PY_BASH_JS_ENTRY`
- `JUST_PY_BASH_PACKAGE_JSON`
- optionally `JUST_PY_BASH_NODE`

## Scope Compared to Upstream TypeScript API

This wrapper intentionally focuses on the portable Python session API. It mirrors the upstream shell behavior, options, custom commands, and optional capabilities, but it does **not** yet expose the lower-level filesystem classes from the TypeScript package like `OverlayFs`, `ReadWriteFs`, or `MountableFs` directly.

If you need those exact low-level host-filesystem integration primitives today, use upstream `just-bash` from TypeScript. If you want the Pythonic session-oriented shell API, use `just-py-bash`.

## Development Bootstrap

For development in this repo, use the `Makefile` helpers instead of running the bootstrap steps by hand:

```bash
make install
make test
```

`make install` installs the Python dependencies and bootstraps the vendored `vendor/just-bash` backend. Run `make help` to see the other available development commands.

## Conformance Testing

The test suite treats upstream `just-bash` as the semantic oracle for current wrapper parity.

- `tests/parity/` compares the Python wrapper against a direct Node reference harness
- `tests/contracts/` covers Python-specific guarantees like custom commands and packaging
- `tests/api/` covers the public API contract

## Design Notes

See [`docs/wrapping-plan.md`](docs/wrapping-plan.md).
