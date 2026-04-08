# just-py-bash wrapping plan

## Goals

1. Expose a small, Pythonic API for the upstream `just-bash` runtime.
2. Keep behavioral drift near zero by treating upstream `just-bash` as the source of truth.
3. Make future release automation mechanical: vendor an upstream release, run conformance tests, publish.

## Chosen interop model: long-lived Node worker

We wrap `just-bash` with a dedicated Node subprocess per Python `Bash` instance.

### Why this is the right first step

- **Faithful semantics**: upstream `Bash` already owns the virtual filesystem and execution model.
- **Low implementation risk**: no reimplementation of shell behavior in Python.
- **Stateful sessions**: filesystem persistence across calls comes for free.
- **Structured IO**: JSON-RPC-style messages are easy to debug and test.
- **Future-proof**: later release automation only needs to swap in a vendored JS artifact.

### What the worker owns

A single upstream `new Bash(...)` instance.

### What Python owns

- process lifecycle
- request/response transport
- Pythonic types
- timeout convenience
- conformance assertions

## Public Python interface

### Constructor

```python
Bash(
    *,
    files: Mapping[str, str | bytes] | None = None,
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
    execution_limits: ExecutionLimits | None = None,
    python: bool = False,
    javascript: bool | JavaScriptConfig = False,
    commands: Sequence[str] | None = None,
    network: Mapping[str, Any] | None = None,
    process_info: Mapping[str, int] | None = None,
)
```

This is intentionally a **narrow, high-value subset** of upstream config.
The wrapper can grow later, but these are enough to validate the shape of the binding.

### Execution

```python
result = bash.exec(
    "echo hi",
    env={"NAME": "world"},
    cwd="/tmp",
    stdin="input\n",
    args=["extra"],
    replace_env=False,
    raw_script=False,
    timeout=1.0,
)
```

### Result type

`ExecResult` mirrors upstream execution output but feels like Python:

- `stdout`
- `stderr`
- `exit_code`
- `env`
- `metadata`
- `ok`
- `check()` / `check_returncode()`

### File helpers

- `read_text(path)`
- `read_bytes(path)`
- `write_text(path, content)`
- `write_bytes(path, content)`

These are intentionally convenience methods, not a full Python filesystem facade.

## Interop contract

The bridge uses line-delimited JSON messages.

### Requests

- `init`
- `exec`
- `read_text`
- `read_bytes`
- `write_text`
- `write_bytes`
- `get_env`
- `get_cwd`

### Responses

```json
{ "id": 1, "ok": true, "result": ... }
{ "id": 1, "ok": false, "error": { "type": "Error", "message": "..." } }
```

### Binary values

Binary payloads are tagged and base64 encoded so Python `bytes` can cross the JSON boundary safely.

## What is intentionally not implemented yet

### Python-defined custom commands

That is the next meaningful extension, but it requires **reverse RPC**:

- Node would invoke Python callbacks
- Python callbacks would likely need access back into the just-bash session
- command context would need a carefully designed Python facade

That is feasible, but it is a second phase.

### Full upstream surface area

We are not exposing every upstream option on day one. The point here is to settle the shape of the wrapper and its validation strategy first.

## Conformance testing strategy

The key idea: **the Python wrapper should be tested against upstream `just-bash`, not against expectations hand-copied from docs**.

### Reference harness

`tests/js/reference.mjs` imports upstream `just-bash` directly and runs the same scenario the Python wrapper runs.

### Python-side scenarios

`tests/test_conformance.py` runs a scenario twice:

1. through the Python wrapper
2. through the direct Node reference harness

Then it compares structured outputs.

### What the current suite covers

- filesystem persistence vs shell-state isolation
- exec options (`stdin`, `cwd`, `replace_env`, `args`)
- timeout behavior
- binary file round-trips
- initial files
- command allowlists

This is the right release gate for future vendoring automation.

## Release-time vendoring plan

The bridge is already separated from artifact resolution, which makes vendoring straightforward later.

### Recommended release pipeline

1. Select upstream `just-bash` release/tag.
2. Vendor the exact JS artifact we want to ship.
3. Point `just-py-bash` at that vendored artifact.
4. Run Python unit tests.
5. Run conformance tests.
6. Publish the wheel/sdist only if conformance passes.

### Important packaging note

For published Python wheels we should prefer a **self-contained JS runtime artifact** over depending on a development checkout.

That likely means one of:

- a dedicated bundle produced specifically for `just-py-bash`
- or vendoring the upstream package plus the exact Node dependency tree it needs

The first option is usually cleaner for Python packaging.

## Why this is a good stopping point for phase 1

After this phase we will have:

- a real Python API
- a real interop mechanism
- a real parity suite

That is enough to confidently automate future release cutting without guessing what “correct wrapping” means.
