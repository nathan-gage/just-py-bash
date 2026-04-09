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

Latest local validation after the current filesystem-config expansion work:

```bash
make all
```

Result:

- `make all` passes
- `80 passed`

Coverage is only one signal. For this project, the strongest confidence still comes from the black-box differential tests in `tests/parity/` that compare the Python wrapper against direct upstream `just-bash` execution.

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
| Native async session API (`AsyncBash`) | Implemented | Strong | `tests/api/test_session_api.py`, `tests/parity/test_async_*`, async custom-command contract test | Async now has the same curated + generated differential parity shape as sync. |
| Long-lived session with shared virtual filesystem across `exec()` calls | Implemented | Strong | API tests + curated parity scenarios | One of the main wrapper guarantees. |
| Per-`exec()` isolated shell state | Implemented | Strong | Curated parity scenarios | Explicitly exercised via env/cwd shell-state scenarios. |
| `exec()` options: `env`, `replace_env`, `cwd`, `stdin`, `args`, `raw_script`, `timeout` | Implemented | Strong | Curated parity scenarios + generated transcripts | This is one of the best-tested areas. |
| Text and bytes file helpers (`read_*`, `write_*`) | Implemented | Strong | API tests + parity tests + generated transcripts | Includes binary round-trips. |
| Backend version reporting | Implemented | Moderate | API tests + packaging tests | Happy path covered. |
| Sync custom commands | Implemented | Strong | `tests/contracts/test_custom_commands.py`, property tests | Includes nested exec, pipelines, built-in override, non-zero exits, exception mapping. |
| Async custom commands | Implemented | Moderate | `tests/contracts/test_custom_commands.py` | Core happy paths covered, but not fuzzed or parity-tested. |
| Command allowlist (`commands=`) | Implemented | Moderate | Curated parity scenario | Covered, but only lightly. |
| Execution limits (`ExecutionLimits`) | Implemented | Moderate | `tests/parity/test_capability_parity.py`, curated parity scenarios | Loop, heredoc, and output limits are now covered directly; more breadth is still useful. |
| Python runtime (`python=True`) | Implemented | Moderate | `tests/contracts/test_optional_runtimes.py`, `tests/contracts/test_distributions.py`, `tests/api/test_cli.py` | Direct happy path, timeout-limit behavior, installed-distribution smoke, and CLI enablement are covered. |
| JavaScript runtime (`javascript=True` / `JavaScriptConfig`) | Implemented | Moderate | `tests/contracts/test_optional_runtimes.py`, `tests/contracts/test_distributions.py` | Direct happy path and installed-distribution smoke are covered. |
| Network config (`network=`) | Implemented | Moderate | `tests/parity/test_capability_parity.py` | Local HTTP server parity covers command availability, allow-list behavior, methods, and header transforms. |
| Virtual process info (`process_info=`) | Implemented | Moderate | `tests/parity/test_capability_parity.py` | Differential tests now assert `$$`, `$PPID`, `$UID`, `/proc/self/status`, and `/proc/self/cmdline`. |
| Backend override knobs (`node_command`, `js_entry`, `package_json`) | Implemented | Moderate | `tests/contracts/test_backend_overrides.py`, `tests/contracts/test_node_provider.py`, API bridge-failure tests | Explicit args and env-var forms are covered, including `JUST_BASH_NODE`. |
| `Bash.from_options(...)` / `AsyncBash.from_options(...)` | Implemented | Moderate | `tests/api/test_from_options_and_bridge_failures.py` | Both public constructors are now exercised directly. |
| Public CLI (`just-py-bash`) | Implemented | Moderate | `tests/api/test_cli.py`, packaging tests | Source-level CLI tests now cover `--cwd`, `--python`, `--timeout`, `--version`, stdin piping, and exit-code propagation. |
| Packaged wheel runtime boot | Implemented | Moderate | `tests/contracts/test_distributions.py` | Good smoke coverage for repo-independent runtime boot. |
| Packaged sdist runtime boot | Implemented | Moderate | `tests/contracts/test_distributions.py` | Good smoke coverage for repo-independent runtime boot. |
| Packaged runtime for optional Python/JS assets | Implemented by build script | Moderate | `tests/contracts/test_distributions.py` | Installed wheel/sdist tests now verify packaged Python and JavaScript runtime smoke paths. |
| Init-time fs config objects (`InMemoryFs`, `OverlayFs`, `ReadWriteFs`, `MountableFs`, `MountConfig`) | Implemented | Moderate | `tests/api/test_fs_config_api.py`, `tests/parity/test_filesystem_configs.py` | Mirrors upstream constructor shapes for session init; sync and async parity now cover overlay/read-write/mountable behavior. |
| Low-level fs API surface (`stat`, `readdir`, `mkdir`, `rm`, etc.) | Not implemented | Planned | N/A | Current Python wrapper now supports `fs=` config objects, but still only exposes session helpers plus read/write convenience methods. |
| Upstream `fetch`, `logger`, `trace`, `defenseInDepth`, `coverage` options | Not implemented | Planned | N/A | No Python equivalents yet. |
| Upstream transform/plugin/parser/security/sandbox exports | Not implemented | Planned | N/A | Outside current session-focused wrapper scope. |

## What is implemented today

### Public Python API

The package already ships a usable session-oriented wrapper around upstream `just-bash`:

- `Bash` for synchronous code
- `AsyncBash` for `asyncio`
- `ExecResult`, `ExecutionLimits`, `JavaScriptConfig`
- typed network/process-info models
- init-time fs config objects (`InMemoryFs`, `OverlayFs`, `ReadWriteFs`, `MountableFs`, `MountConfig`) plus `fs=` session construction
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
- generated wrapper transcript parity
- sync and async filesystem-config parity for shipped fs constructors

## What is properly tested today

### Differential parity coverage

The strongest evidence today comes from `tests/parity/`.

Curated scenarios currently cover:

- shell state isolation while filesystem state persists
- `stdin`, `replace_env`, `cwd`, `args`, and `timeout`
- binary file round-trips
- initial files and command allowlists
- empty-string / empty-list / empty-env transport behavior
- unicode environment transport plus `raw_script` behavior
- local-network config parity against a test HTTP server
- `process_info` parity including virtual `/proc` surfaces
- targeted execution-limit parity for loop, heredoc, and output limits
- overlay/read-write/mountable filesystem config parity, including read-only overlays and persistent host writes
- the same curated corpus through `AsyncBash`

Generated transcripts add randomized coverage for:

- text vs bytes writes
- text vs bytes reads
- repeated `exec()` calls
- environment overrides
- cwd overrides
- argument passthrough
- final session snapshot consistency
- the same randomized transcript model through `AsyncBash`

### Public contract coverage

The public API tests verify:

- `backend_version`
- `ExecResult.check()` / `CommandFailedError`
- session isolation between independent `Bash` instances
- file helper round-trips
- idempotent `close()` behavior
- basic async session behavior
- `Bash.from_options(...)` and `AsyncBash.from_options(...)`
- `InMemoryFs` acceptance through `Bash(...)` and `AsyncBash(...)`
- CLI behavior for `--cwd`, `--python`, `--timeout`, `--version`, stdin piping, and exit-code propagation
- bridge unhappy paths including malformed worker responses, worker crashes, backend-unavailable cases, and timeout behavior

### Capability contract coverage

Contract tests currently verify:

- sync custom commands
- nested exec from custom commands
- pipeline participation
- built-in override behavior
- non-zero exit-code propagation
- exception-to-shell-failure mapping
- async custom commands
- backend override knobs (`JUST_BASH_NODE`, `JUST_BASH_JS_ENTRY`, `JUST_BASH_PACKAGE_JSON`, explicit args)
- installed wheel/sdist boot and console-script smoke paths
- installed wheel/sdist smoke for optional Python and JavaScript runtimes
- optional Python and JavaScript runtime happy paths plus Python timeout-limit behavior

## What needs improvement

### 1. Finish test coverage for features that already exist

The biggest recent improvement was expanding coverage for already-shipped features instead of adding a large new API surface.

Completed recently:

- local-network parity tests using a test HTTP server
- `process_info` parity tests for `$$`, `$PPID`, `$UID`, `/proc`, and cmdline behavior
- backend override knob tests for explicit args and env vars
- bridge unhappy-path tests for unavailable backends, malformed worker responses, crashes, timeouts, and close-after-failure
- broader execution-limit tests
- source-level CLI option tests
- installed wheel/sdist runtime tests for Python and JavaScript
- `from_options(...)` tests for both sync and async
- async curated and generated differential parity harnesses
- async failure-path tests
- Python-side fs config classes plus sync/async parity coverage for overlay, read-write, and mountable behavior

Remaining near-term gaps:

- **Examples are documented but not exercised**
  - Add smoke tests or at least snippet tests for `examples/`.

- **Execution-limit breadth can still improve**
  - The most important limits now have coverage, but there is still room to add targeted tests for awk/sed/jq/sqlite/JS-specific limits.

- **CLI scope should be clarified explicitly**
  - We now test the current helper CLI well enough to trust it, but the project should still decide whether that CLI is intentionally minimal or meant to approach upstream CLI parity.

### 2. Address a few specific code-level issues discovered in review

- **Broken documentation link**
  - `README.md` previously referenced `docs/wrapping-plan.md`, which did not exist.
  - This roadmap replaces that missing document.

- **`js_entry` package metadata inference was fragile and is now fixed**
  - `resolve_backend_artifacts()` and the test harness now walk parent directories to find `package.json` when only `js_entry` is supplied.
  - That makes `dist/bundle/index.js` overrides work without requiring an explicit `package_json` argument.

- **`Bash.__repr__()` performs live bridge I/O**
  - Sync `Bash.__repr__()` calls `get_cwd()` for open sessions.
  - This is surprising for `repr()` and can fail if the worker is unhealthy.
  - Prefer the non-I/O style already used by `AsyncBash.__repr__()`.

- **Public constructors were unevenly exercised and are now covered**
  - `from_options(...)` is now exercised for both sync and async APIs.

### 3. Expand the current session-oriented API carefully

Before chasing full upstream parity, there is room to improve the current Pythonic wrapper surface itself.

Potential additions:

- richer file initialization parity with upstream (`FileInit`, lazy file providers)
- more session helpers beyond raw text/bytes read/write if they stay useful and Pythonic
- clearer docs for packaged-runtime refresh flow and release process
- clearer statement of CLI scope: helper CLI vs near-upstream CLI parity

### 4. Plan the next upstream parity work

The largest construction-time parity gap is no longer `fs=` support; that milestone is now in place. The next question is how far the Python wrapper should go beyond init-time filesystem config objects.

Recommended order:

1. **Decide whether a session-bound fs proxy belongs in the public API**
   - `stat`, `exists`, `mkdir`, `readdir`, `rm`, `cp`, `mv`, `chmod`, `readlink`, `realpath`, etc.
   - This is a much larger bridge/API expansion than serialized init-time config objects.

2. **Improve richer file-initialization parity if users need it**
   - upstream-style metadata/lazy file initialization
   - clearer semantics where `files=` and `fs=` overlap

3. **Only then consider lower-priority upstream APIs**
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
- [x] Fix `js_entry` / `package_json` inference for bundle paths

### Phase 1: Test the features we already ship

- [x] network tests using a local HTTP server
- [x] `process_info` tests
- [x] backend override knob tests
- [x] bridge failure / timeout tests
- [x] broader execution-limit tests
- [x] CLI option tests
- [x] installed-wheel/sdist tests for Python and JavaScript runtimes
- [x] `from_options(...)` tests
- [ ] example smoke tests

### Phase 2: Bring async confidence up to sync confidence

- [x] async differential parity harness
- [x] async failure-path tests
- [ ] async packaging smoke tests if useful

### Phase 3: Close the largest upstream parity gap

- [x] Python-side fs config classes
- [x] `Bash(fs=...)` and `AsyncBash(fs=...)`
- [x] tests for overlay/read-write/mountable behavior
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

The recent expansion work closed most of the highest-value confidence gaps for the current API surface and added the first filesystem-construction milestone via upstream-style `fs=` config objects.

What remains is now clearer:

- example smoke coverage
- a few deeper execution-limit cases
- an explicit decision about long-term CLI scope
- a decision about whether low-level fs proxy methods belong in the Python API

With those confidence gaps mostly addressed, the next major roadmap question is no longer whether to support `fs=` at all, but whether to go further and expose a larger session-bound filesystem API.
