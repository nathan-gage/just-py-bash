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
from just_bash import Bash

with Bash(cwd="/workspace") as bash:
    bash.exec("export NAME=alice; echo 'hello from the shared filesystem' > greeting.txt; cd /tmp")

    result = bash.exec(
        'printf "name=%s cwd=%s file=%s\n" "${NAME:-missing}" "$PWD" "$(cat greeting.txt)"',
    )
    print(result.stdout, end="")

    bash.fs.write_text("note.txt", "written via bash.fs\n")
    print(bash.read_text("note.txt"), end="")
```

### Asynchronous API

`AsyncBash` is implemented with native `asyncio` subprocesses, tasks, futures, and locks.

```python
import asyncio

from just_bash import AsyncBash


async def main() -> None:
    async with AsyncBash(cwd="/workspace") as bash:
        await bash.exec("export NAME=alice; echo 'hello from async shared filesystem' > greeting.txt; cd /tmp")

        result = await bash.exec(
            'printf "name=%s cwd=%s file=%s\n" "${NAME:-missing}" "$PWD" "$(cat greeting.txt)"',
        )
        print(result.stdout, end="")

        await bash.fs.write_text("note.txt", "written via async bash.fs\n")
        print(await bash.read_text("note.txt"), end="")


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

## Supported Commands

The wrapper delegates command execution to upstream `just-bash`, so the Python API gets the same command families. For programmatic introspection, use:

```python
from just_bash import (
    get_command_names,
    get_javascript_command_names,
    get_network_command_names,
    get_python_command_names,
)

print(len(get_command_names()))
print(sorted(get_network_command_names()))
print(sorted(get_python_command_names()))
print(sorted(get_javascript_command_names()))
```

<details>
<summary><strong>Current upstream command categories</strong></summary>

### File Operations

`cat`, `cp`, `file`, `ln`, `ls`, `mkdir`, `mv`, `readlink`, `rm`, `rmdir`, `split`, `stat`, `touch`, `tree`

### Text Processing

`awk`, `base64`, `column`, `comm`, `cut`, `diff`, `expand`, `fold`, `grep` (+ `egrep`, `fgrep`), `head`, `join`, `md5sum`, `nl`, `od`, `paste`, `printf`, `rev`, `rg`, `sed`, `sha1sum`, `sha256sum`, `sort`, `strings`, `tac`, `tail`, `tr`, `unexpand`, `uniq`, `wc`, `xargs`

### Data Processing

`jq` (JSON), `sqlite3` (SQLite), `xan` (CSV), `yq` (YAML/XML/TOML/CSV)

### Optional Runtimes

`js-exec` (requires `javascript=True` / `JavaScriptConfig(...)`), `python3` / `python` (requires `python=True`)

### Compression & Archives

`gzip` (+ `gunzip`, `zcat`), `tar`

### Navigation & Environment

`basename`, `cd`, `dirname`, `du`, `echo`, `env`, `export`, `find`, `hostname`, `printenv`, `pwd`, `tee`

### Shell Utilities

`alias`, `bash`, `chmod`, `clear`, `date`, `expr`, `false`, `help`, `history`, `seq`, `sh`, `sleep`, `time`, `timeout`, `true`, `unalias`, `which`, `whoami`

### Network

`curl`, `html-to-markdown` (require `network=...`)

All commands support `--help` for usage information.

</details>

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

- `files`: initial in-memory files; values can be plain text/bytes, `FileInit(...)`, or `LazyFile(...)`
- `env`: initial environment
- `cwd`: starting directory
- `fs`: upstream-style filesystem config object (`InMemoryFs`, `OverlayFs`, `ReadWriteFs`, `MountableFs`)
- `execution_limits`: validated execution protection settings
- `python=True`: enable `python` / `python3`
- `javascript=True` or `JavaScriptConfig(...)`: enable `js-exec`
- `commands`: allowlist commands
- `custom_commands`: register Python-defined commands
- `network`: configure allow-listed network access
- `process_info`: process metadata passed to the backend

### Filesystem configuration objects

The wrapper now exposes upstream-style init-time filesystem config objects:

- `InMemoryFs(files=...)`
- `OverlayFs(root=..., mount_point=..., read_only=...)`
- `ReadWriteFs(root=...)`
- `MountableFs(base=..., mounts=[MountConfig(...)])`

`files=` and `InMemoryFs(files=...)` both support richer initial values too:

- plain text / bytes
- `FileInit(content=..., mode=..., mtime=...)`
- `LazyFile(provider=...)`

`LazyFile(provider=...)` accepts either:

- static deferred content (`str` / `bytes`), or
- a Python callable returning `str` / `bytes` (sync or async)

These are serialized when the session starts and decoded into real upstream `just-bash` filesystem instances inside the Node worker. The filesystem config classes are config objects, not live Python filesystem implementations.

```python
from just_bash import Bash, MountConfig, MountableFs, OverlayFs, ReadWriteFs

with Bash(
    fs=MountableFs(
        mounts=[
            MountConfig(
                mount_point="/workspace",
                filesystem=ReadWriteFs(root="/tmp/project"),
            ),
            MountConfig(
                mount_point="/docs",
                filesystem=OverlayFs(
                    root="/path/to/docs",
                    mount_point="/",
                    read_only=True,
                ),
            ),
        ],
    ),
    cwd="/workspace",
) as bash:
    result = bash.exec("cp /docs/README.md ./README.copy.md && ls")
    print(result.stdout, end="")
```

If you pass both `files=` and `fs=`, upstream `just-bash` semantics apply and `fs=` takes precedence.

### Session filesystem API

Each session now also exposes a session-bound filesystem proxy at `bash.fs` / `async_bash.fs`.

Available methods:

- `read_text(path)`
- `read_bytes(path)`
- `write_text(path, content)`
- `write_bytes(path, content)`
- `exists(path)`
- `stat(path)` → `FsStat`
- `mkdir(path, recursive=False)`
- `readdir(path)`
- `rm(path, recursive=False, force=False)`
- `cp(src, dest, recursive=False)`
- `mv(src, dest)`
- `chmod(path, mode)`
- `readlink(path)`
- `realpath(path)`

Paths are resolved with upstream `just-bash` session semantics, so relative paths are interpreted against the session cwd.

```python
from datetime import UTC, datetime

from just_bash import Bash, FileInit, LazyFile

with Bash(
    files={
        "seed.txt": FileInit(
            content="seed\n",
            mode=0o640,
            mtime=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
        ),
        "lazy.txt": LazyFile(provider=lambda: "lazy content\n"),
    },
    cwd="/workspace",
) as bash:
    bash.fs.mkdir("docs")
    bash.fs.write_text("docs/note.txt", "hello\n")
    bash.fs.cp("docs/note.txt", "copy.txt")
    bash.exec("ln -s copy.txt link.txt")

    stat = bash.fs.stat("copy.txt")
    print(stat.mode)
    print(bash.fs.readlink("link.txt"))
    print(bash.fs.realpath("link.txt"))
```

### Per-exec options

- `env`: environment variables for this execution only
- `cwd`: working directory for this execution only
- `stdin`: standard input passed to the script
- `args`: argv passed directly to the first command
- `replace_env`: start with an empty environment instead of merging
- `raw_script`: skip leading-whitespace normalization
- `timeout`: cooperative timeout in seconds

`AsyncBash.exec(...)` accepts the same options; you just `await` the call.

## Option Hooks and Callback Surfaces

The wrapper exposes upstream construction-time hooks as Python callables and protocol-style objects.

- `fetch`: intercept or implement HTTP requests for `curl` and other network consumers
- `logger`: receive upstream `info(...)` / `debug(...)` events
- `trace`: receive structured `TraceEvent` timing callbacks
- `coverage`: receive feature-hit notifications
- `defense_in_depth`: configure the upstream defense layer and optionally receive `SecurityViolation` objects

```python
from collections.abc import Mapping

from just_bash import Bash, DefenseInDepthConfig, FetchRequest, FetchResult


class Logger:
    def info(self, message: str, data: Mapping[str, object] | None = None) -> None:
        print("INFO", message, data)

    def debug(self, message: str, data: Mapping[str, object] | None = None) -> None:
        print("DEBUG", message, data)


class Coverage:
    def __init__(self) -> None:
        self.hits: list[str] = []

    def hit(self, feature: str) -> None:
        self.hits.append(feature)


coverage = Coverage()
trace_events = []
violations = []


def fetch(request: FetchRequest) -> FetchResult:
    return FetchResult(
        status=200,
        status_text="OK",
        headers={"content-type": "text/plain"},
        body="hello from fetch\n",
        url=request.url,
    )


with Bash(
    logger=Logger(),
    trace=trace_events.append,
    coverage=coverage,
    fetch=fetch,
    javascript=True,
    defense_in_depth=DefenseInDepthConfig(enabled=True, audit_mode=True, on_violation=violations.append),
) as bash:
    print(bash.exec("curl -s https://example.com").stdout, end="")
    bash.exec("find . -maxdepth 1 -type f")
```

See `examples/option_hooks.py` for a runnable end-to-end example.

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

Like upstream `just-bash`, `curl` only exists when network access is configured. The repository example `examples/network_access.py` demonstrates allow-listed methods and header transforms using a local HTTP fixture, so it stays smoke-testable without depending on the public internet.

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

## Broader Upstream Exports

The wrapper now also exposes the main parser / transform / sandbox / security helper surfaces that map cleanly into Python.

### Command registry helpers and parser helpers

```python
from just_bash import get_command_names, parse, serialize

script = "echo hello | grep h"
ast = parse(script)

print("echo" in get_command_names())
print(ast["type"])
print(serialize(ast))
```

### Transform pipeline helpers

```python
from datetime import UTC, datetime

from just_bash import Bash, BashTransformPipeline, CommandCollectorPlugin, TeePlugin

pipeline = (
    BashTransformPipeline()
    .use(TeePlugin(output_dir="/tmp/logs", timestamp=datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=UTC)))
    .use(CommandCollectorPlugin())
)
result = pipeline.transform("echo hello | grep h")
print(result.metadata)

with Bash() as bash:
    bash.register_transform_plugin(CommandCollectorPlugin())
    transformed = bash.transform("echo hello | grep h")
    exec_result = bash.exec("echo hello | grep h")
    print(transformed.metadata)
    print(exec_result.metadata)
```

### Sandbox helpers

```python
from just_bash import Sandbox, SandboxOptions

with Sandbox.create(SandboxOptions(cwd="/app")) as sandbox:
    sandbox.write_files({"/app/hello.txt": "hello from sandbox\n"})
    command = sandbox.run_command("cat /app/hello.txt")
    print(command.stdout(), end="")
```

Async code can use `AsyncSandbox` with the same high-level shape.

### Security helpers

```python
from just_bash import SecurityViolation, SecurityViolationLogger

logger = SecurityViolationLogger(include_stack_traces=False)
logger.record(
    SecurityViolation(
        timestamp=1,
        type="eval",
        message="blocked eval",
        path="globalThis.eval",
    )
)
print(logger.get_summary())
```

## Examples

The repo includes a Python `examples/` directory that mirrors the spirit of the vendored upstream examples and README. These examples are smoke-tested from the repo root so they stay aligned with the shipped public API:

| File | What it shows |
|---|---|
| `examples/quickstart_sync.py` | Basic synchronous usage, shell-state reset semantics, shared filesystem state, and `bash.fs` helpers |
| `examples/quickstart_async.py` | Native-async usage with `AsyncBash` and async filesystem helpers |
| `examples/custom_commands_sync.py` | A Python port of the upstream custom-command showcase |
| `examples/custom_commands_async.py` | Async custom commands with nested async exec |
| `examples/configuration_and_runtimes.py` | Session config, per-exec overrides, `replace_env`, Python, and JavaScript runtimes |
| `examples/filesystem_surfaces.py` | `FileInit`, `LazyFile`, `FsStat`, and the session-bound filesystem API |
| `examples/network_access.py` | Allow-listed network access, method policy, and header transforms via a local HTTP fixture |
| `examples/option_hooks.py` | Python callback surfaces for `fetch`, `logger`, `trace`, `coverage`, and `defense_in_depth` |
| `examples/parser_and_command_registry.py` | Command-name helpers plus standalone `parse(...)` / `serialize(...)` |
| `examples/transforms.py` | Standalone transform pipelines and session-integrated transform registration |
| `examples/sandbox.py` | Upstream-style sandbox helpers, detached commands, and file IO |
| `examples/security_helpers.py` | Security violation logging helpers |

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

## CLI Launchers

The Python package now ships thin launchers over the upstream CLI assets:

- `just-py-bash` → delegates to upstream `just-bash`
- `just-py-bash-shell` → delegates to upstream `just-bash-shell`

These launchers forward argv, stdin, stdout, stderr, and the final exit code directly to the upstream CLI implementation. The Python package keeps Python-specific binary names, but CLI semantics come from upstream `just-bash` rather than a separate Python reimplementation.

Examples:

```bash
just-py-bash -c 'echo hello'
echo 'pwd' | just-py-bash
just-py-bash ./script.sh
just-py-bash --json -c 'echo hello'
just-py-bash-shell --cwd /
```

## Scope Compared to Upstream TypeScript API

The wrapper now covers the main upstream session API, filesystem config and session-fs surfaces, option hooks, command-name helpers, standalone parser/serializer helpers, the built-in transform pipeline/plugin surfaces (`BashTransformPipeline`, `CommandCollectorPlugin`, `TeePlugin`), upstream-style sandbox/security helper utilities, and thin CLI delegation via `just-py-bash` / `just-py-bash-shell`.

What it still does **not** expose is the full low-level TypeScript filesystem surface or live Python filesystem adapter interfaces from the TypeScript package. The Python wrapper currently covers the session-facing filesystem methods (`exists`, `stat`, `mkdir`, `readdir`, `rm`, `cp`, `mv`, `chmod`, `readlink`, `realpath`, plus the text/bytes helpers), but not the remaining lower-level pieces like `lstat`, `symlink`, `link`, `utimes`, or `readdirWithFileTypes`. If you need those full lower-level primitives directly, use upstream `just-bash` from TypeScript. If you want the Pythonic session-oriented shell API plus the portable parser / transform / sandbox / security helper surfaces described above, use `just-py-bash`.

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
- `just-py-bash` now uses dynamic versioning from Git tags, like `markserv`. Manual releases are tag-driven: create and push `vX.Y.Z` or `vX.Y.Z.postN` from `main`, and the release workflow will build, publish to PyPI, and create the GitHub release.
- Automated upstream-sync PRs labeled `release-candidate` are also tag-driven, but the tag is created automatically only after the PR is merged to `main`. That keeps PyPI publishing tied to tags that are actually on `main`.
- The upstream sync workflow now pins `vendor/just-bash` to the commit where the target upstream version was introduced, instead of blindly taking a later `origin/main` commit that still reports the same version.
- `just-bash-bundled-runtime` is versioned independently from `just-py-bash` and also uses dynamic versioning from Git tags. Its release tags are `runtime/vX.Y.Z` (or `runtime/vX.Y.Z.postN`), while the tracked bundled Node version lives separately in `[tool.just-bash-bundled-runtime]`.
- Bundled-runtime sync PRs labeled `release-candidate` are auto-tagged on merge to `main`, which triggers the same tag-driven publish workflow for that package.
- PRs intended to become releases should be labeled `release-candidate`. That label triggers the expensive Full CI workflow, including packaging and compatibility coverage.

## Conformance Testing

The test suite treats upstream `just-bash` as the semantic oracle for current wrapper parity.

- `tests/parity/` compares the Python wrapper against a direct Node reference harness for both sync and async sessions, with curated scenarios, generated transcripts, dedicated filesystem-config parity coverage, and new session-fs parity coverage
- `tests/parity/` also includes capability parity checks for shipped features like `network`, `process_info`, filesystem configs, richer initial files, session fs operations, key execution limits, and the new command-registry / parser / transform helper surfaces using direct upstream comparisons
- `tests/contracts/` covers Python-specific guarantees such as custom commands, backend override knobs, bridge failure paths, packaging, installed wheel/sdist runtime behavior, broader export helpers, and delegated CLI entrypoints
- `tests/api/` covers the public API contract, including session lifecycle helpers, `from_options(...)`, transform registration, sandbox helpers, security helpers, example smoke coverage, and delegated CLI launcher behavior

For day-to-day development, `make all` is the main confidence gate: format, lint, typecheck, and the full test suite.

