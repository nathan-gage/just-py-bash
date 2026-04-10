# just-py-bash roadmap

This roadmap tracks three things:

1. what the wrapper already ships
2. how much confidence we have in that shipped surface
3. the planned work for reaching fuller upstream parity

## Product direction

The direction for this project is now explicit:

- `just-py-bash` is aiming for **full parity with upstream `just-bash` over time**.
- That parity target means **all user-facing upstream surfaces**, not just the core session constructor.
- The primary product is a **native-feeling Python SDK** that preserves upstream semantics.
- Sync and async Python APIs are both first-class and required wherever the wrapped surface makes sense in Python.
- When an upstream shape maps cleanly to Python, the wrapper should stay close to upstream naming and behavior.
- Naming should stay as close to upstream as Python allows: keep class names in upstream-style `PascalCase`, and adapt function names, keyword arguments, and fields to `snake_case` where that improves Python fit without changing semantics.
- When an upstream shape does not map cleanly to Python, the wrapper should provide a Pythonic adapter that still serializes into upstream behavior.
- The CLI is **not** a separate product: CLI parity should come from **thin launchers over upstream CLI assets**, not from reimplementing upstream flag parsing in Python.
- Differential testing against upstream `just-bash` remains the main confidence gate.

## Current snapshot

- `make all` passes locally
- The current local test count is `186 passed`
- Sync and async session APIs are well covered by public API tests plus wrapper-vs-upstream parity tests
- Init-time filesystem config parity (`fs=`) is now implemented for the upstream-style filesystem constructors
- The session-bound filesystem API is now implemented for the core upstream filesystem operations
- Richer initial file parity is now implemented via `FileInit(...)` and `LazyFile(...)`, including differential coverage for callable lazy providers
- Upstream option parity is now implemented for `fetch`, `logger`, `trace`, `defenseInDepth`, and `coverage`, with API, packaging, and differential coverage
- Defense-in-depth confidence now includes differential probes against the shipped upstream defense implementations so wrapper behavior stays locked to what upstream actually emits today

## Capability matrix

| Capability | Status | Confidence | Main coverage |
|---|---|---:|---|
| Core sync session API (`Bash`) | Implemented | Strong | `tests/api/test_session_api.py`, `tests/parity/*`, packaging tests |
| Core async session API (`AsyncBash`) | Implemented | Strong | `tests/api/test_session_api.py`, `tests/parity/test_async_*`, async custom-command tests |
| Shared virtual filesystem + isolated per-exec shell state | Implemented | Strong | API tests, curated parity scenarios |
| `exec()` option mapping (`env`, `cwd`, `stdin`, `args`, `timeout`, etc.) | Implemented | Strong | Curated parity + generated transcripts |
| File helpers (`read_*`, `write_*`) | Implemented | Strong | API tests, parity tests, generated transcripts |
| Sync custom commands | Implemented | Strong | `tests/contracts/test_custom_commands.py`, property tests |
| Async custom commands | Implemented | Moderate | `tests/contracts/test_custom_commands.py` |
| Command allowlist (`commands=`) | Implemented | Moderate | Curated parity scenario |
| Execution limits (`ExecutionLimits`) | Implemented | Moderate | `tests/parity/test_capability_parity.py`, curated parity scenarios |
| Optional Python runtime (`python=True`) | Implemented | Moderate | Optional-runtime tests, distribution tests, CLI tests |
| Optional JavaScript runtime (`javascript=True` / `JavaScriptConfig`) | Implemented | Moderate | Optional-runtime tests, distribution tests |
| Network config (`network=`) | Implemented | Moderate | `tests/parity/test_capability_parity.py` |
| Virtual process info (`process_info=`) | Implemented | Moderate | `tests/parity/test_capability_parity.py` |
| Backend overrides (`node_command`, `js_entry`, `package_json`) | Implemented | Moderate | Backend override tests, node-provider tests, bridge-failure tests |
| Alternative constructors (`from_options(...)`) | Implemented | Moderate | `tests/api/test_from_options_and_bridge_failures.py` |
| Current Python entrypoint CLI (`just-py-bash`) | Implemented | Moderate | `tests/api/test_cli.py`, packaging tests |
| Upstream CLI parity via delegation | Planned | N/A | Roadmap — CLI parity |
| Vendored/packaged runtime distribution story | Implemented | Moderate | `tests/contracts/test_distributions.py` |
| Init-time fs config objects (`fs=`) | Implemented | Strong | `tests/api/test_fs_config_api.py`, `tests/parity/test_filesystem_configs.py` |
| Session-bound low-level fs API (`exists`, `stat`, `mkdir`, `readdir`, `rm`, etc.) | Implemented | Strong | `tests/api/test_filesystem_session_api.py`, `tests/parity/test_session_fs_api.py`, `tests/contracts/test_distributions.py` |
| Richer initial file parity (`FileInit`, `LazyFile`) | Implemented | Strong | `tests/api/test_filesystem_session_api.py`, `tests/parity/test_session_fs_api.py`, `tests/api/test_fs_config_api.py`, `tests/contracts/test_distributions.py` |
| Upstream option parity (`fetch`, `logger`, `trace`, `defenseInDepth`, `coverage`) | Implemented | Strong | `tests/api/test_option_parity_api.py`, `tests/parity/test_option_parity.py`, `tests/contracts/test_distributions.py` |
| Broader upstream transform/plugin/parser/security/sandbox exports | Planned | N/A | Roadmap — Broader export parity |

## What gives confidence today

### Differential parity

`tests/parity/` is the strongest signal because it compares the Python wrapper directly against upstream `just-bash`.

That suite currently covers:

- curated sync scenarios for shell-state isolation and persistent filesystem state
- generated sync transcripts for repeated session behavior
- matching async curated and generated parity suites
- network parity using local fixtures instead of public internet dependencies
- `process_info` parity including virtual `/proc` behavior
- key execution-limit parity, including wrapper-focused coverage for loop/heredoc/output plus awk/sed/jq/sqlite/js limit fields
- filesystem-config parity for overlay, read-write, and mountable configurations
- session-fs parity for core operations, symlinks, cross-mount copies, read-only overlays, host-persistent write roots, and path failures
- richer initial file parity for metadata-aware files plus static and callable lazy files
- option parity for `fetch`, `logger`, `trace`, `coverage`, and `defenseInDepth`, including sync/async callback semantics, installed-distribution smoke, and differential coverage for real shipped defense probes

### Public API and contract tests

The rest of the test suite complements parity coverage with Python-specific guarantees:

- API tests for session lifecycle, result handling, constructors, CLI behavior, bridge failure paths, and example smoke coverage
- contract tests for custom commands, backend selection, optional runtimes, and installation/distribution behavior
- smoke coverage for installed wheel/sdist usage outside a repo checkout

## Completed foundation work

These milestones are already in place:

- [x] core sync `Bash` API
- [x] core async `AsyncBash` API
- [x] public API and parity harness structure
- [x] generated transcript parity for sync and async sessions
- [x] source-level CLI coverage for the current Python entrypoint
- [x] backend override and bridge failure-path coverage
- [x] local-fixture parity for `network` and `process_info`
- [x] broader execution-limit coverage for key current cases
- [x] wheel/sdist smoke coverage for optional Python and JavaScript runtimes
- [x] init-time filesystem config support via `fs=`
- [x] sync and async parity coverage for `OverlayFs`, `ReadWriteFs`, and `MountableFs`
- [x] session-bound filesystem API via `bash.fs` / `async_bash.fs`
- [x] richer initial file support via `FileInit(...)` and `LazyFile(...)`
- [x] sync and async parity coverage for core session-fs operations
- [x] differential parity coverage for callable lazy files
- [x] repo-root smoke coverage for the shipped non-network examples
- [x] Python-facing option support for upstream `fetch`, `logger`, `trace`, `defenseInDepth`, and `coverage`
- [x] sync and async contract coverage for option-hook completion and failure semantics
- [x] differential parity coverage for option hooks, including broader fetch scenarios and real defense probes
- [x] wheel/sdist smoke coverage for shipped option-hook support

## Roadmap

### Reliability and confidence

#### Example smoke coverage

- [x] add smoke tests for `examples/`
- [x] run the examples as public-API programs rather than testing private internals
- [x] keep examples aligned with the documented SDK surface only

#### Execution-limit breadth

These should stay wrapper-focused: verify Python-side limit fields, wire translation, and wrapper-vs-upstream parity at the execution-limit boundary. They should not turn into broad correctness tests for upstream awk/sed/jq/sqlite/JS behavior.

- [x] add targeted parity coverage for `max_awk_iterations`
- [x] add targeted parity coverage for `max_sed_iterations`
- [x] add targeted parity coverage for `max_jq_iterations`
- [x] add targeted parity coverage for `max_sqlite_timeout_ms`
- [x] add targeted parity coverage for `max_js_timeout_ms`

#### Small correctness follow-ups

- [x] change `Bash.__repr__()` so it no longer performs live bridge I/O
- [x] keep backend artifact inference behavior documented and covered
- [x] keep README and roadmap aligned with the actual shipped/tested surface

### CLI parity

The CLI path is fixed: the Python package should ship thin launchers over upstream CLI assets rather than maintain a separate Python CLI behavior model.

#### Upstream CLI asset packaging

- [ ] include upstream `dist/bin/**` assets in the packaged vendored runtime
- [ ] preserve the upstream `dist/bin/**` relative layout rather than cherry-picking individual CLI chunks
- [ ] keep CLI entrypoints, chunks, workers, and runtime assets package-relative so upstream path resolution keeps working unchanged
- [ ] verify the packaged runtime can launch upstream CLI entrypoints from installed wheel/sdist artifacts

#### CLI launcher delegation

- [ ] change `just-py-bash` to forward argv to upstream `just-bash`
- [ ] forward stdin/stdout/stderr transparently
- [ ] forward the exact process exit code transparently
- [ ] avoid reimplementing upstream CLI flag parsing in Python

#### Shell launcher parity

- [ ] add a Python package entrypoint for the upstream interactive shell path
- [ ] delegate that entrypoint to upstream `just-bash-shell`
- [ ] mirror upstream packaging shape here: because upstream ships `just-bash` and `just-bash-shell` from the main package, ship the corresponding Python launchers from the main Python package as well
- [ ] keep naming/documentation clear about the Python package binary names versus upstream binary names

#### CLI parity tests

- [ ] add installed-distribution tests for `-c`
- [ ] add installed-distribution tests for stdin piping
- [ ] add installed-distribution tests for `--root`
- [ ] add installed-distribution tests for `--cwd`
- [ ] add installed-distribution tests for `--json`
- [ ] add installed-distribution tests for script-file execution
- [ ] add installed-distribution smoke for the shell entrypoint

#### CLI documentation

- [ ] document that CLI semantics are sourced from upstream `just-bash`
- [ ] document any Python-package-specific launcher naming clearly
- [ ] remove Python-specific CLI behavior documentation once delegation is in place

### Filesystem parity

The filesystem-parity milestone is now in place for the current Python session surface.

That milestone is intentionally scoped to the session-facing API. It does **not** yet claim that every upstream `IFileSystem` method is exposed in Python; lower-level methods such as `appendFile`, `symlink`, `link`, `lstat`, `utimes`, and `readdirWithFileTypes` remain outside the current Python surface unless and until they get a clear Python-facing design plus parity coverage.

#### Session-bound fs API

- [x] add a session-bound fs API on top of upstream filesystem operations
- [x] implement `exists`
- [x] implement `stat`
- [x] implement `mkdir`
- [x] implement `readdir`
- [x] implement `rm`
- [x] implement `cp`
- [x] implement `mv`
- [x] implement `chmod`
- [x] implement `readlink`
- [x] implement `realpath`

#### Filesystem coverage

- [x] add parity coverage for cross-mount operations
- [x] add parity coverage for read-only overlay behavior
- [x] add parity coverage for host-persistent write roots
- [x] add parity coverage for symlink behavior
- [x] add parity coverage for permission and path-resolution failures

#### Richer initialization parity

- [x] add metadata-aware initial file support
- [x] add lazy file initialization support
- [x] add differential parity coverage for callable lazy files
- [x] document the exact precedence and interaction of `files=` and `fs=`
- [x] add contract/parity tests for richer initialization behavior

### Option parity

The option-parity milestone is now in place for the current upstream construction/configuration option surface.

That includes Python-facing support plus API, packaging, and wrapper-vs-upstream differential coverage for:

- [x] upstream `fetch`
- [x] upstream `logger`
- [x] upstream `trace`
- [x] upstream `defenseInDepth`
- [x] upstream `coverage`
- [x] parity or contract coverage for each added option

The defense-in-depth portion is intentionally documented against **shipped upstream behavior**, not an idealized future model. The current shipped upstream surface emits positive audit-mode `onViolation` callbacks in the worker-defense probe path, while the main-thread defense probe used here does not currently surface positive callbacks in the same way. The wrapper now differentially locks to that shipped behavior so future upstream changes will be visible immediately.

### Broader export parity

After the session API, CLI, filesystem API, and construction options are in place, expand the remaining user-facing upstream exports.

- [ ] add Python-facing wrappers for upstream transform/plugin surfaces
- [ ] add Python-facing wrappers for parser/security/sandbox surfaces
- [ ] keep naming close to upstream, using Python `snake_case` for function/field-style surfaces and upstream-style `PascalCase` for classes
- [ ] add focused examples for each adopted surface
- [ ] add contract or parity coverage for each adopted surface

## Near-term order

The current recommended order is:

1. confidence and maintenance work
2. broader export parity
3. CLI parity through thin delegation

That ordering is only a sequencing guide. The roadmap itself is organized by parity area so the desired end state stays clear.
