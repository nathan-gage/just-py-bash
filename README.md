# just-py-bash

[![PyPI](https://img.shields.io/pypi/v/just-py-bash.svg)](https://pypi.org/project/just-py-bash/)
[![Python Versions](https://img.shields.io/pypi/pyversions/just-py-bash.svg)](https://pypi.org/project/just-py-bash/)
[![CI](https://github.com/nathan-gage/just-py-bash/actions/workflows/ci.yml/badge.svg)](https://github.com/nathan-gage/just-py-bash/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-api%20%2B%20parity%20%2B%20packaging-blue.svg)](#testing-and-coverage)

`just-py-bash` gives Python the same long-lived virtual shell that [just-bash](https://github.com/vercel-labs/just-bash) exposes in TypeScript.

Use it when you want shell-like scripting from Python without spinning up a brand-new subprocess workflow for every operation. Each session keeps a shared virtual filesystem, every `exec()` call follows upstream `just-bash` semantics, and results come back as structured Python objects.

## Why just-py-bash?

- `Bash` for synchronous code and `AsyncBash` for native `asyncio`
- shared virtual filesystem across calls, with isolated shell state per `exec()`
- structured `ExecResult` results instead of raw `subprocess` plumbing
- custom Python commands, optional `python` / `js-exec`, and allow-listed network access
- thin CLI launchers plus an optional first-party bundled Node.js runtime

## Install

> Requires Python 3.11+

| Use case | Command |
| --- | --- |
| Install the main package | `uv add just-py-bash` |
| Install with a bundled Node.js runtime | `uv add 'just-py-bash[node]'` |
| Install from a local checkout | `uv add ./just_py_bash` |

Install name: `just-py-bash`  
Import name: `just_bash`

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
| Build the main package | `make build-package` |
| Build the bundled runtime wheel | `make build-bundled-runtime` |
