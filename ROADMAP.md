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
- The current local test count is `86 passed`
- Sync and async session APIs are well covered by public API tests plus wrapper-vs-upstream parity tests
- Init-time filesystem config parity (`fs=`) is now implemented for the upstream-style filesystem constructors

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
| Init-time fs config objects (`fs=`) | Implemented | Moderate | `tests/api/test_fs_config_api.py`, `tests/parity/test_filesystem_configs.py` |
| Session-bound low-level fs API (`exists`, `stat`, `mkdir`, `readdir`, `rm`, etc.) | Planned | N/A | Roadmap — Filesystem parity |
| Richer initial file parity (metadata/lazy files) | Planned | N/A | Roadmap — Filesystem parity |
| Upstream option parity (`fetch`, `logger`, `trace`, `defenseInDepth`, `coverage`) | Planned | N/A | Roadmap — Option parity |
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
- key execution-limit parity
- filesystem-config parity for overlay, read-write, and mountable configurations

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
- [x] repo-root smoke coverage for the shipped non-network examples

## Roadmap

### Reliability and confidence

#### Example smoke coverage

- [x] add smoke tests for `examples/`
- [x] run the examples as public-API programs rather than testing private internals
- [x] keep examples aligned with the documented SDK surface only

#### Execution-limit breadth

These should stay wrapper-focused: verify Python-side limit fields, wire translation, and wrapper-vs-upstream parity at the execution-limit boundary. They should not turn into broad correctness tests for upstream awk/sed/jq/sqlite/JS behavior.

- [ ] add targeted parity coverage for `max_awk_iterations`
- [ ] add targeted parity coverage for `max_sed_iterations`
- [ ] add targeted parity coverage for `max_jq_iterations`
- [ ] add targeted parity coverage for `max_sqlite_timeout_ms`
- [ ] add targeted parity coverage for `max_js_timeout_ms`

#### Small correctness follow-ups

- [ ] change `Bash.__repr__()` so it no longer performs live bridge I/O
- [ ] keep backend artifact inference behavior documented and covered
- [ ] keep README and roadmap aligned with the actual shipped/tested surface

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

The first filesystem milestone is complete. The next step is to expose a larger Python-facing filesystem surface while preserving upstream semantics.

#### Session-bound fs API

- [ ] add a session-bound fs API on top of upstream filesystem operations
- [ ] implement `exists`
- [ ] implement `stat`
- [ ] implement `mkdir`
- [ ] implement `readdir`
- [ ] implement `rm`
- [ ] implement `cp`
- [ ] implement `mv`
- [ ] implement `chmod`
- [ ] implement `readlink`
- [ ] implement `realpath`

#### Filesystem coverage

- [ ] add parity coverage for cross-mount operations
- [ ] add parity coverage for read-only overlay behavior
- [ ] add parity coverage for host-persistent write roots
- [ ] add parity coverage for symlink behavior
- [ ] add parity coverage for permission and path-resolution failures

#### Richer initialization parity

- [ ] add metadata-aware initial file support
- [ ] add lazy file initialization support
- [ ] document the exact precedence and interaction of `files=` and `fs=`
- [ ] add contract/parity tests for richer initialization behavior

### Option parity

Expand the remaining upstream construction/configuration surfaces with Pythonic wrappers that serialize directly into upstream behavior.

- [ ] add Python-facing support for upstream `fetch`
- [ ] add Python-facing support for upstream `logger`
- [ ] add Python-facing support for upstream `trace`
- [ ] add Python-facing support for upstream `defenseInDepth`
- [ ] add Python-facing support for upstream `coverage`
- [ ] add parity or contract coverage for each added option

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
2. CLI parity through thin delegation
3. filesystem parity beyond init-time `fs=`
4. option parity
5. broader export parity

That ordering is only a sequencing guide. The roadmap itself is organized by parity area so the desired end state stays clear.
