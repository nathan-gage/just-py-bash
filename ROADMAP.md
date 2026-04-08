# just-py-bash roadmap

This document is the working inventory for the wrapper: what exists today, what is actually covered by automated tests, and what should be improved next.

## Review scope

This roadmap was prepared by reviewing:

- `just_py_bash/src/just_bash/`
- `tests/`
- `examples/`
- `README.md`
- `pyproject.toml`
- `Makefile`
- `just_py_bash/tools/build_packaged_runtime.sh`

## Current snapshot

Latest local validation during this review:

```bash
uv run coverage run -m pytest -q
uv run coverage report -m
```

Result:

- `31 passed`
- total Python coverage: `77.59%`

Coverage is only one signal. For this project, the strongest confidence comes from the black-box differential tests in `tests/parity/` that compare the Python wrapper against direct upstream `just-bash` execution.

## Confidence legend

- **Strong**: covered by direct public-API tests and/or differential parity tests, often with property-based expansion
- **Moderate**: covered by focused tests, but only for a narrow slice of the feature
- **Smoke-only**: one or two happy-path tests exist, but failure modes and edge cases are not well covered
- **None**: implemented in code but not meaningfully exercised by automated tests
- **Planned**: not implemented yet

## Capability matrix

| Capability | Implementation status | Test confidence | Where it is covered | Notes |
|---|---|---:|---|---|
| Synchronous session API (`Bash`) | Implemented | Strong | `tests/api/test_session_api.py`, `tests/parity/*`, packaging tests | Core public surface works and is exercised end-to-end. |
| Native async session API (`AsyncBash`) | Implemented | Moderate | `tests/api/test_session_api.py`, async custom-command contract test | Happy-path async use is covered, but there is no async differential parity corpus yet. |
| Long-lived session with shared virtual filesystem across `exec()` calls | Implemented | Strong | API tests + curated parity scenarios | One of the main wrapper guarantees. |
| Per-`exec()` isolated shell state | Implemented | Strong | Curated parity scenarios | Explicitly exercised via env/cwd shell-state scenarios. |
| `exec()` options: `env`, `replace_env`, `cwd`, `stdin`, `args`, `raw_script`, `timeout` | Implemented | Strong | Curated parity scenarios + generated transcripts | This is one of the best-tested areas. |
| Text and bytes file helpers (`read_*`, `write_*`) | Implemented | Strong | API tests + parity tests + generated transcripts | Includes binary round-trips. |
| Backend version reporting | Implemented | Moderate | API tests + packaging tests | Happy path covered. |
| Sync custom commands | Implemented | Strong | `tests/contracts/test_custom_commands.py`, property tests | Includes nested exec, pipelines, built-in override, non-zero exits, exception mapping. |
| Async custom commands | Implemented | Moderate | `tests/contracts/test_custom_commands.py` | Core happy paths covered, but not fuzzed or parity-tested. |
| Command allowlist (`commands=`) | Implemented | Moderate | Curated parity scenario | Covered, but only lightly. |
| Execution limits (`ExecutionLimits`) | Implemented | Smoke-only | One curated scenario touches `max_command_count` | Most limit fields are wired but not specifically tested. |
| Python runtime (`python=True`) | Implemented | Smoke-only | `tests/contracts/test_optional_runtimes.py` | One direct happy-path test. |
| JavaScript runtime (`javascript=True` / `JavaScriptConfig`) | Implemented | Smoke-only | `tests/contracts/test_optional_runtimes.py` | One direct happy-path test. |
| Network config (`network=`) | Implemented | None | Example + README only | No automated test currently exercises network wiring or command availability. |
| Virtual process info (`process_info=`) | Implemented | None | Code only | No tests currently assert `/proc`, `$$`, `UID`, etc. |
| Backend override knobs (`node_command`, `js_entry`, `package_json`) | Implemented | None | Code only | Important escape hatch, but untested. |
| `Bash.from_options(...)` / `AsyncBash.from_options(...)` | Implemented | None | Code only | Public constructors exist but are not exercised by tests. |
| Public CLI (`just-py-bash`) | Implemented | Smoke-only | Packaging tests only | Only a basic installed-console-script path is covered. Option parsing is not. |
| Packaged wheel runtime boot | Implemented | Moderate | `tests/contracts/test_distributions.py` | Good smoke coverage for repo-independent runtime boot. |
| Packaged sdist runtime boot | Implemented | Moderate | `tests/contracts/test_distributions.py` | Good smoke coverage for repo-independent runtime boot. |
| Packaged runtime for optional Python/JS assets | Implemented by build script | None | Not exercised in installed-wheel/sdist tests | `just_py_bash/tools/build_packaged_runtime.sh` prepares these assets, but distribution tests do not verify them. |
| Low-level upstream fs classes (`OverlayFs`, `ReadWriteFs`, `MountableFs`) | Not implemented | Planned | N/A | Explicitly called out as missing in README/examples. |
| Low-level fs API surface (`stat`, `readdir`, `mkdir`, `rm`, etc.) | Not implemented | Planned | N/A | Current Python wrapper only exposes session helpers plus read/write convenience methods. |
| Upstream `fetch`, `logger`, `trace`, `defenseInDepth`, `coverage` options | Not implemented | Planned | N/A | No Python equivalents yet. |
| Upstream transform/plugin/parser/security/sandbox exports | Not implemented | Planned | N/A | Outside current session-focused wrapper scope. |

## What is implemented today

### Public Python API

The package already ships a usable session-oriented wrapper around upstream `just-bash`:

- `Bash` for synchronous code
- `AsyncBash` for `asyncio`
- `ExecResult`, `ExecutionLimits`, `JavaScriptConfig`
- typed network/process-info models
- custom command support for sync and async Python callables
- convenience file helpers (`read_text`, `read_bytes`, `write_text`, `write_bytes`)
- a minimal `just-py-bash` CLI

### Bridge architecture

The current design is solid and intentionally simple:

- Python owns the public API and validation
- a dedicated Node worker hosts a real upstream `just-bash` `Bash` instance
- the worker speaks a small JSON line protocol
- sync and async Python bridges are separate implementations
- the package can boot either the repo vendored backend or the packaged backend under `just_py_bash/src/just_bash/_vendor/just-bash`

### Packaging/runtime story

The repo already has a credible packaging story:

- a packaged backend is built into `just_py_bash/src/just_bash/_vendor/just-bash`
- `just_py_bash/tools/build_packaged_runtime.sh` bundles upstream runtime artifacts, worker files, WASM payloads, and package metadata
- wheel/sdist installation is tested from isolated virtual environments with no repo checkout

### Testing story

The current suite is already well structured:

- `tests/api/`: public Python API contract tests
- `tests/parity/`: direct wrapper-vs-upstream differential tests
- `tests/contracts/`: custom commands, packaging, and optional runtime contracts
- `tests/support/reference.mjs`: direct Node reference harness

The best-tested areas are:

- basic sync session behavior
- state persistence vs shell-state isolation
- file helper round-trips
- exec option translation
- sync custom command behavior
- differential parity for generated wrapper transcripts

## What is properly tested today

### Differential parity coverage

The strongest evidence today comes from `tests/parity/`.

Curated scenarios currently cover:

- shell state isolation while filesystem state persists
- `stdin`, `replace_env`, `cwd`, `args`, and `timeout`
- binary file round-trips
- initial files and command allowlists
- empty-string / empty-list / empty-env transport behavior
- unicode plus `raw_script` behavior

Generated transcripts add randomized coverage for:

- text vs bytes writes
- text vs bytes reads
- repeated `exec()` calls
- environment overrides
- cwd overrides
- argument passthrough
- final session snapshot consistency

### Public contract coverage

The public API tests verify:

- `backend_version`
- `ExecResult.check()` / `CommandFailedError`
- session isolation between independent `Bash` instances
- file helper round-trips
- idempotent `close()` behavior
- basic async session behavior

### Capability contract coverage

Contract tests currently verify:

- sync custom commands
- nested exec from custom commands
- pipeline participation
- built-in override behavior
- non-zero exit-code propagation
- exception-to-shell-failure mapping
- async custom commands
- installed wheel/sdist boot and console-script smoke paths
- optional Python and JavaScript runtime happy paths

## What needs improvement

### 1. Finish test coverage for features that already exist

These are the most valuable near-term additions because they improve confidence without changing the public API.

#### High priority gaps

- **Network config is implemented but untested**
  - Add a local HTTP server based test so network coverage does not depend on the public internet.
  - Verify that `curl` is unavailable without `network=` and available when configured.
  - Verify allow-list, methods, and request-transform behavior.

- **`process_info` is implemented but untested**
  - Add tests for `$$`, `$PPID`, `$UID`, `$EUID`, `/proc/self/status`, and `/proc/self/cmdline`.
  - Confirm wrapper values reach upstream intact.

- **Backend override knobs are untested**
  - Add tests for `node_command`, `js_entry`, and `package_json`.
  - Verify the environment-variable forms too (`JUST_BASH_NODE`, `JUST_BASH_JS_ENTRY`, `JUST_BASH_PACKAGE_JSON`).

- **Bridge unhappy-path behavior is under-tested**
  - Add tests for `BackendUnavailableError`, `BridgeTimeoutError`, malformed worker responses, worker crashes, and close-after-failure behavior.
  - Current bridge coverage is the weakest in the repo even though it is the critical integration layer.

#### Medium priority gaps

- **Execution limits need breadth, not just existence**
  - Add targeted tests for more than `max_command_count`.
  - At minimum cover loop, output, heredoc, and runtime timeout related limits.

- **CLI coverage is too shallow**
  - Add tests for `--cwd`, `--python`, `--timeout`, `--version`, stdin piping, and exit-code propagation.
  - Decide whether the CLI is intentionally minimal or intended to track more of upstream CLI behavior.

- **Async parity should match sync parity quality**
  - Add a differential async harness that runs the same scenarios through `AsyncBash`.
  - Right now async support is real, but the deepest parity machinery is sync-only.

- **Installed distribution tests should cover optional runtimes**
  - The build script packages Python/JS runtime assets, but installed-wheel/sdist tests only run a simple `printf`.
  - Add installed-distribution tests for `python=True` and `javascript=True`.

- **Examples are documented but not exercised**
  - Add smoke tests or at least snippet tests for `examples/`.

### 2. Address a few specific code-level issues discovered in review

- **Broken documentation link**
  - `README.md` previously referenced `docs/wrapping-plan.md`, which did not exist.
  - This roadmap replaces that missing document.

- **`js_entry` package metadata inference is fragile**
  - `resolve_backend_artifacts()` and the test harness infer `package.json` as `js_entry.parent.parent / "package.json"` when only `js_entry` is given.
  - That is correct for `dist/index.js`, but not for `dist/bundle/index.js` unless `package_json` is also supplied.
  - This should be made robust.

- **`Bash.__repr__()` performs live bridge I/O**
  - Sync `Bash.__repr__()` calls `get_cwd()` for open sessions.
  - This is surprising for `repr()` and can fail if the worker is unhealthy.
  - Prefer the non-I/O style already used by `AsyncBash.__repr__()`.

- **Public constructors are unevenly exercised**
  - `from_options(...)` exists for both sync and async APIs but is not tested.
  - Public exports should either be covered or explicitly de-scoped.

### 3. Expand the current session-oriented API carefully

Before chasing full upstream parity, there is room to improve the current Pythonic wrapper surface itself.

Potential additions:

- richer file initialization parity with upstream (`FileInit`, lazy file providers)
- more session helpers beyond raw text/bytes read/write if they stay useful and Pythonic
- clearer docs for packaged-runtime refresh flow and release process
- clearer statement of CLI scope: helper CLI vs near-upstream CLI parity

### 4. Plan the larger upstream parity work

If the goal is to support more of the remaining upstream TypeScript surface, the next major milestone should be filesystem support.

Recommended order:

1. **Add Python fs config objects**
   - `InMemoryFs`
   - `OverlayFs`
   - `ReadWriteFs`
   - `MountableFs`

2. **Support `Bash(fs=...)` / `AsyncBash(fs=...)`**
   - Initially as serialized config specs, not as full live Python filesystem implementations.

3. **Expose a session-bound fs proxy only if needed**
   - `stat`, `exists`, `mkdir`, `readdir`, `rm`, `cp`, `mv`, `chmod`, `readlink`, `realpath`, etc.
   - This is a larger bridge/API expansion and should come after init-time `fs=` support.

4. **Only then consider lower-priority upstream APIs**
   - `fetch`
   - `logger`
   - `trace`
   - `defenseInDepth`
   - `coverage`
   - transform plugins
   - parser/sandbox/security exports

## Suggested phased roadmap

### Phase 0: Documentation and correctness

- [x] Add a real roadmap document
- [x] Point README at it
- [ ] Fix `js_entry` / `package_json` inference for bundle paths

### Phase 1: Test the features we already ship

- [ ] network tests using a local HTTP server
- [ ] `process_info` tests
- [ ] backend override knob tests
- [ ] bridge failure / timeout tests
- [ ] broader execution-limit tests
- [ ] CLI option tests
- [ ] installed-wheel/sdist tests for Python and JavaScript runtimes
- [ ] `from_options(...)` tests
- [ ] example smoke tests

### Phase 2: Bring async confidence up to sync confidence

- [ ] async differential parity harness
- [ ] async failure-path tests
- [ ] async packaging smoke tests if useful

### Phase 3: Close the largest upstream parity gap

- [ ] Python-side fs config classes
- [ ] `Bash(fs=...)` and `AsyncBash(fs=...)`
- [ ] tests for overlay/read-write/mountable behavior
- [ ] decide whether low-level fs proxies belong in the public API

### Phase 4: Optional advanced parity

- [ ] richer initial-file parity (metadata/lazy files)
- [ ] selected upstream callback/plugin surfaces as justified by user demand
- [ ] decide whether `Sandbox`/parser/transform exports are in or out of scope

## Bottom line

The project already has a solid and useful core:

- the session-oriented wrapper works
- the sync API is well covered
- the custom-command story is good
- the packaging story is real
- parity testing against upstream is already the backbone of confidence

The biggest near-term opportunity is **not** a giant new feature. It is to **finish testing the features that are already present but only lightly covered or not covered at all**, especially:

- `network`
- `process_info`
- backend override knobs
- bridge error handling
- installed-distribution optional runtimes

Once those are covered, the natural next major roadmap item is support for the missing upstream filesystem classes and `fs=`-based session construction.
