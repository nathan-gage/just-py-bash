# just-py-bash

Python bindings for [just-bash](https://github.com/vercel-labs/just-bash).

This repo is intentionally focused on the first hard part:

- define a clean Python API
- define the Python ↔ Node interop boundary
- define a conformance suite that proves the wrapper matches upstream `just-bash`

Release automation and vendoring workflows can sit on top of that once the interface is settled.

## Current shape

The wrapper uses a **long-lived Node.js worker process** per Python `Bash` instance.
That worker owns a real upstream `just-bash` `Bash` object, so we preserve upstream behavior:

- virtual filesystem persists across `exec()` calls
- shell state is isolated per `exec()` call
- results come back as structured Python objects

## Python API

```python
from just_py_bash import Bash, ExecutionLimits

with Bash(
    cwd="/workspace",
    files={"/workspace/hello.txt": "hello\n"},
    execution_limits=ExecutionLimits(max_command_count=500),
) as bash:
    result = bash.exec("cat hello.txt")
    print(result.stdout)      # hello\n
    bash.write_text("note.txt", "from python\n")
    print(bash.read_text("note.txt"))
```

Core surface area today:

- `Bash(...)`
- `Bash.exec(...) -> ExecResult`
- `Bash.read_text(...)`
- `Bash.read_bytes(...)`
- `Bash.write_text(...)`
- `Bash.write_bytes(...)`
- `Bash.get_env()`
- `Bash.get_cwd()`
- `Bash.close()`

## Development bootstrap

The wrapper expects a built `just-bash` checkout in `vendor/just-bash`.

```bash
cd vendor/just-bash
pnpm install
pnpm build
cd ../..
uv run pytest
```

If you want to point at a different backend artifact, set:

- `JUST_PY_BASH_JS_ENTRY`
- `JUST_PY_BASH_PACKAGE_JSON`
- optionally `JUST_PY_BASH_NODE`

## Conformance testing

`tests/test_conformance.py` compares the Python wrapper against a direct Node reference harness that imports upstream `just-bash` without going through the Python bridge.

That suite is the contract for future packaging and release automation.

## Design notes

See [`docs/wrapping-plan.md`](docs/wrapping-plan.md).
