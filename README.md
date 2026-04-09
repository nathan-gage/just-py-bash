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

Install name: `just-py-bash`  
Import name: `just_bash`

By default, `just-py-bash` uses a system-provided Node.js runtime.

For an explicit bundled-Node install:

```bash
uv add 'just-py-bash[node]'
```

That extra installs the first-party `just-bash-bundled-runtime` companion package.

## Quick Start

### Synchronous API

```python
from just_bash import Bash, ExecutionLimits

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

from just_bash import AsyncBash


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
from just_bash import Bash, CustomCommandContext


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

from just_bash import AsyncBash, AsyncCustomCommandContext


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
from just_bash import Bash, ExecutionLimits, JavaScriptConfig

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
from just_bash import Bash

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
from just_bash import Bash

with Bash(python=True) as bash:
    result = bash.exec('python -c "print(sum([2, 3, 5]))"')
    print(result.stdout, end="")
```

### JavaScript Support

The Python wrapper passes `javascript=True` or `JavaScriptConfig(...)` through to upstream `just-bash`.

```python
from just_bash import Bash, JavaScriptConfig

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
from just_bash import Bash

with Bash() as bash:
    result = bash.exec("false")

if not result.ok:
    print(result.exit_code)
    print(result.stderr)
```

## Backend Selection

By default the package uses its vendored `just-bash` runtime and resolves Node.js in this order:

1. `node_command=` passed to `Bash(...)` or `AsyncBash(...)`
2. `JUST_BASH_NODE`
3. the first-party bundled Node provider installed by `just-py-bash[node]`
4. a system `node` on `PATH`

To point at a different `just-bash` backend artifact, set:

- `JUST_BASH_JS_ENTRY`
- `JUST_BASH_PACKAGE_JSON`
- optionally `JUST_BASH_NODE`

If you provide only `js_entry=` or `JUST_BASH_JS_ENTRY`, the wrapper will try to infer the matching `package.json` by walking parent directories. That works for both `dist/index.js` and `dist/bundle/index.js`, but you can still pass `package_json=` / `JUST_BASH_PACKAGE_JSON` explicitly when you want to be precise.

## Scope Compared to Upstream TypeScript API

This wrapper intentionally focuses on the portable Python session API. It mirrors the upstream shell behavior, options, custom commands, and optional capabilities, but it does **not** yet expose the lower-level filesystem classes from the TypeScript package like `OverlayFs`, `ReadWriteFs`, or `MountableFs` directly.

If you need those exact low-level host-filesystem integration primitives today, use upstream `just-bash` from TypeScript. If you want the Pythonic session-oriented shell API, use `just-py-bash`.

## Contributing / Development

For development in this repo, use the `Makefile` helpers instead of running the bootstrap steps by hand:

```bash
make install
make test
```

Common recipes:

- `make install` — install Python dependencies, bootstrap `vendor/just-bash`, and prepare the packaged runtime payload used by the Python wrapper
- `make all` — local developer loop: format, lint, typecheck, and run the full test suite
- `make all-ci` — release-candidate / packaging checks: format verification, lint, typecheck, and coverage tests
- `make test-non-packaging` — run the fast test suite used by the cheap CI workflow
- `make build-packaged-runtime` — rebuild the packaged runtime payload under `src/just_bash/_vendor/just-bash`
- `make build-package` — build the main `just-py-bash` wheel and sdist
- `make build-bundled-runtime` — build the companion `just-bash-bundled-runtime` wheel
- `make clean` — remove generated build artifacts

Distribution builds materialize the packaged `src/just_bash/_vendor/just-bash` runtime during wheel/sdist creation, so that generated payload does not need to live in git.

### Using the local bundled runtime package during development

Most users should install the published extra:

```bash
uv add 'just-py-bash[node]'
```

If you are developing both packages together and want to test against the local companion package instead of the published one, install it from this repo:

```bash
uv add ./just_bash_bundled_runtime
```

The repo's own workspace is already wired to use the local package during `uv sync`.

### Versioning and release flow

- When upstream `just-bash` releases `X.Y.Z`, `just-py-bash` aims to release the matching version `X.Y.Z`.
- If the Python wrapper needs a follow-up release without a new upstream `just-bash` version, use a PEP 440 post-release such as `X.Y.Z.post1`.
- To cut a Python-only follow-up release, bump `just_py_bash/pyproject.toml` to `X.Y.Z.postN`, merge the PR after it passes CI, and then run the manual `Release just-py-bash` workflow against `main` (or the specific ref you want to publish).
- PRs intended to become releases should be labeled `release-candidate`. That label triggers the expensive Full CI workflow, including packaging and compatibility coverage.
- Merging to `main` does **not** publish automatically. Publishing is a separate manual step via the release workflows after the relevant PR has passed Full CI.

## Conformance Testing

The test suite treats upstream `just-bash` as the semantic oracle for current wrapper parity.

- `tests/parity/` compares the Python wrapper against a direct Node reference harness for both sync and async sessions, with curated scenarios and generated transcripts
- `tests/parity/` also includes capability parity checks for shipped features like `network`, `process_info`, and key execution limits using local fixtures rather than public-internet dependencies
- `tests/contracts/` covers Python-specific guarantees such as custom commands, backend override knobs, bridge failure paths, packaging, and installed wheel/sdist runtime behavior
- `tests/api/` covers the public API contract, including session lifecycle helpers, `from_options(...)`, and the minimal CLI surface

For day-to-day development, `make all` is the main confidence gate: format, lint, typecheck, and the full test suite.

## Design Notes

See [`ROADMAP.md`](ROADMAP.md).
