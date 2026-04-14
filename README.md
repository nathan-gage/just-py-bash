# just-py-bash

[![PyPI](https://img.shields.io/pypi/v/just-py-bash.svg)](https://pypi.org/project/just-py-bash/)
[![Python Versions](https://img.shields.io/pypi/pyversions/just-py-bash.svg)](https://pypi.org/project/just-py-bash/)
[![CI](https://github.com/nathan-gage/just-py-bash/actions/workflows/ci.yml/badge.svg)](https://github.com/nathan-gage/just-py-bash/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-api%20%2B%20parity%20%2B%20packaging-blue.svg)](#testing-and-coverage)

Python wrapper for [just-bash](https://github.com/vercel-labs/just-bash), a virtual bash environment with an in-memory filesystem.

[just-bash](https://github.com/vercel-labs/just-bash) is a TypeScript implementation of a bash interpreter — it runs bash scripts entirely in-process with a virtual filesystem, no real shell or OS-level sandbox required. It supports 80+ standard Unix commands (`grep`, `sed`, `awk`, `jq`, `sqlite3`, etc.), pipes, redirections, variables, loops, functions, and optional `curl`, Python, and JavaScript runtimes. It was designed for AI agents that need a safe, deterministic shell environment.

`just-py-bash` brings that same environment to Python. Each session spawns a Node.js worker running a real `just-bash` instance, and the Python API mirrors `just-bash`'s TypeScript API — you get the same command set, the same filesystem semantics, and the same isolation guarantees, with results returned as structured Python objects.

## Why use this?

- Run bash scripts from Python without a real shell, real filesystem, or subprocess plumbing
- Shared virtual filesystem across `exec()` calls, with isolated shell state (env, cwd, functions) per call
- `Bash` for synchronous code, `AsyncBash` for native `asyncio`
- Structured `ExecResult` objects instead of raw stdout/stderr byte streams
- Custom Python commands that participate in pipes, redirections, and the full shell
- Optional `python`, `js-exec`, and allow-listed `curl` support
- Thin CLI launchers plus an optional first-party bundled Node.js runtime

## Install

> Requires Python 3.11+

| Use case | Command |
| --- | --- |
| Install the main package | `uv add just-py-bash` |
| Install with a bundled Node.js runtime | `uv add 'just-py-bash[node]'` |
| Install from a local checkout | `uv add ./just_py_bash` |

Install name: `just-py-bash`  
Import name: `just_bash`

> `js-exec` / `JavaScriptConfig(...)` require Node.js >= 22.6. If you want the JavaScript runtime without depending on a system Node version, install `just-py-bash[node]`.

## Quick start

```python
from just_bash import Bash

with Bash(cwd="/workspace") as bash:
    bash.exec("echo 'hello from just-py-bash' > greeting.txt")

    result = bash.exec("printf 'cwd=%s file=%s\n' \"$PWD\" \"$(cat greeting.txt)\"")
    print(result.stdout, end="")
```

If you prefer `asyncio`, use `AsyncBash` with the same high-level shape.

## Package layout

This repo publishes two Python packages:

| Package | Purpose | Docs |
| --- | --- | --- |
| `just-py-bash` | Main Python wrapper around upstream `just-bash` | [`just_py_bash/README.md`](just_py_bash/README.md) |
| `just-bash-bundled-runtime` | First-party bundled Node.js runtime used by `just-py-bash[node]` | [`just_bash_bundled_runtime/README.md`](just_bash_bundled_runtime/README.md) |

The long-form package README intentionally lives in `just_py_bash/README.md` so PyPI renders package docs instead of workspace-level notes.

## Read the full docs

If you want the full API surface, examples, and advanced features, start here:

- **Full package README:** [`just_py_bash/README.md`](just_py_bash/README.md)
- **Bundled runtime package README:** [`just_bash_bundled_runtime/README.md`](just_bash_bundled_runtime/README.md)
- **Examples guide:** [`examples/README.md`](examples/README.md)
- **Versioning and release policy:** [`VERSIONING.md`](VERSIONING.md)

The full package README covers:

- `Bash` and `AsyncBash`
- custom commands
- filesystem config and `bash.fs`
- parser / serializer helpers
- transform pipeline helpers
- sandbox and security utilities
- CLI launchers
- backend selection and bundled runtime behavior

## Testing and coverage

The repo is tested against upstream `just-bash` semantics, not just a handful of happy-path unit tests.

- `make test` — run the full suite
- `make testcov` — run tests with combined subprocess coverage and build HTML output
- `tests/parity/` — compare the Python wrapper against a direct Node reference harness
- `tests/contracts/` — cover packaging, runtime, and distribution behavior
- `tests/api/` — cover the public Python API surface

### Conformance testing

The test suite treats upstream `just-bash` as the semantic oracle for current wrapper parity.

- `tests/parity/` compares the Python wrapper against a direct Node reference harness for both sync and async sessions, with curated scenarios, generated transcripts, dedicated filesystem-config parity coverage, and session-fs parity coverage
- `tests/parity/` also includes capability parity checks for shipped features like `network`, `process_info`, filesystem configs, richer initial files, session fs operations, key execution limits, and command-registry / parser / transform helper surfaces using direct upstream comparisons
- `tests/contracts/` covers Python-specific guarantees such as custom commands, backend override knobs, bridge failure paths, packaging, installed wheel/sdist runtime behavior, broader export helpers, and delegated CLI entrypoints
- `tests/api/` covers the public API contract, including session lifecycle helpers, `from_options(...)`, transform registration, sandbox helpers, security helpers, example smoke coverage, and delegated CLI launcher behavior

## Development

```bash
make install
make all
```

Common commands:

| Task | Command |
| --- | --- |
| Install dev tooling and build the packaged runtime | `make install` |
| Run the standard local checks | `make all` |
| Run the full CI-like suite with coverage | `make all-ci` |
| Run the fast test suite (no packaging tests) | `make test-non-packaging` |
| Build the main package | `make build-package` |
| Build the bundled runtime wheel | `make build-bundled-runtime` |
| Rebuild the packaged runtime payload | `make build-packaged-runtime` |
| Remove generated build artifacts | `make clean` |

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

See [VERSIONING.md](VERSIONING.md) for the package version semantics, tag formats, runtime-version policy, and tag-driven release flow.
