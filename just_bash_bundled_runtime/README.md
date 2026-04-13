# just-bash-bundled-runtime

[![PyPI](https://img.shields.io/pypi/v/just-bash-bundled-runtime.svg)](https://pypi.org/project/just-bash-bundled-runtime/)
[![Python Versions](https://img.shields.io/pypi/pyversions/just-bash-bundled-runtime.svg)](https://pypi.org/project/just-bash-bundled-runtime/)
[![CI](https://github.com/nathan-gage/just-py-bash/actions/workflows/full-ci.yml/badge.svg)](https://github.com/nathan-gage/just-py-bash/actions/workflows/full-ci.yml)

`just-bash-bundled-runtime` is the first-party bundled Node.js runtime provider for `just-py-bash`.

Most users should install it indirectly via the main package extra:

```bash
uv add 'just-py-bash[node]'
```

That gives `just-py-bash` a bundled `node` binary to use when no system Node.js is available on `PATH`.

## What it provides

- a platform-specific wheel containing a vendored Node.js runtime
- helper functions to locate the bundled executable from Python
- runtime metadata including the bundled Node version, platform, archive URL, and SHA-256
- runtime payloads built from official Node.js release archives and verified against upstream `SHASUMS256.txt`

## Install

> Requires Python 3.11+

| Use case | Command |
| --- | --- |
| Recommended: install through the main package extra | `uv add 'just-py-bash[node]'` |
| Install the runtime package directly | `uv add just-bash-bundled-runtime` |
| Install from a local checkout | `uv add ./just_bash_bundled_runtime` |

Install name: `just-bash-bundled-runtime`  
Import name: `just_bash_bundled_runtime`

## Quick start

```python
import subprocess

from just_bash_bundled_runtime import get_node_command, get_runtime_metadata

metadata = get_runtime_metadata()
print(metadata["node_version"])
print(metadata["platform"])

completed = subprocess.run(
    [*get_node_command(), "--version"],
    check=True,
    capture_output=True,
    text=True,
)
print(completed.stdout.strip())
```

## Public helpers

The package exports:

- `get_node_command()`
- `get_node_executable()`
- `get_runtime_metadata()`
- `get_runtime_root()`

## How `just-py-bash` uses it

When the companion package is installed, `just-py-bash` resolves Node.js in this order:

1. `node_command=` passed to `Bash(...)` or `AsyncBash(...)`
2. `JUST_BASH_NODE`
3. the bundled runtime from `just-bash-bundled-runtime`
4. a system `node` on `PATH`

That means most consumers only need to install `just-py-bash[node]`; the main package handles the runtime discovery automatically.

## Development

Populate the local runtime payload:

```bash
python just_bash_bundled_runtime/tools/vendor_runtime.py
```

Build a wheel from the repository root:

```bash
uv build just_bash_bundled_runtime --wheel --out-dir dist-node
```

## Versioning

Package versioning for `just-bash-bundled-runtime` is intentionally independent from `just-py-bash` and tracks the bundled Node.js version.

See [VERSIONING.md](https://github.com/nathan-gage/just-py-bash/blob/main/VERSIONING.md) for the runtime package version policy and release tag semantics.
