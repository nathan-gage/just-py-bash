# tests/AGENTS.md

This directory defines the **behavioral contract** for `just-py-bash`.

The test suite is intentionally organized around one idea:

> The Python package is correct when its **public behavior** matches upstream `just-bash` for every supported feature, and when future wrapper-only features have explicit tests waiting for them.

## Core philosophy

### 1. Treat tests as a product contract, not an implementation snapshot

Tests in `tests/` should survive refactors of `src/`.

That means:

- test only the **public Python API**
- use subprocesses and black-box behavior where possible
- never rely on private modules, private methods, internal worker details, or internal transport helpers from `src/`
- never import `just_py_bash._*` from tests

If `src/` changes substantially, the tests should still be valid unless the public contract changes.

### 2. Upstream `just-bash` is the semantic oracle for phase 1

For phase 1, the wrapper exists to preserve upstream behavior across the Python ↔ Node boundary.

So the strongest tests are **differential tests**:

1. run a scenario through the Python wrapper
2. run the same scenario through a direct Node harness importing upstream `just-bash`
3. compare structured results

Prefer this style whenever possible.

### 3. We are testing interop, not reimplementing upstream's suite in Python

Do not hand-copy huge amounts of shell semantics into expected values when a direct upstream comparison is possible.

The main failure modes we care about are wrapper/interop failures such as:

- serialization mismatches
- text vs bytes corruption
- omitted vs empty value bugs
- cwd/env translation bugs
- timeout propagation bugs
- session state drift
- worker lifecycle failures

### 4. Public API only

Allowed dependencies from tests:

- `just_py_bash` public exports
- test-only helpers in `tests/`
- standard library
- pytest / hypothesis / subprocess tooling
- the vendored upstream checkout only as an external reference runtime

Disallowed from tests:

- `just_py_bash._bridge`
- `just_py_bash._api`
- `just_py_bash._models`
- any private helper under `src/just_py_bash/_*`

If a test needs functionality that only exists in a private helper, re-create the minimum test-only helper under `tests/` instead.

## Phases

## Phase 1: wrapper parity

Phase 1 tests should proliferate aggressively.

Required styles:

- **curated conformance tests** for known API features
- **property-based differential tests** for many generated session transcripts
- **bridge robustness tests** for lifecycle and failure behavior
- **final-state snapshots** where useful, not just per-call results

When adding a phase 1 feature test, prefer this order:

1. add a small curated scenario
2. add it to the differential corpus if possible
3. add a property-based/generalized form if feasible

### Phase 1 target surface

Current examples include:

- constructor options we publicly support
- `exec()` behavior and option translation
- helper methods like `read_text`, `read_bytes`, `write_text`, `write_bytes`
- session isolation / persistence semantics
- encoding / binary transport
- timeout semantics

## Phase 2: Python-defined command callbacks

Phase 2 is expected to add wrapper-specific functionality that upstream JS does not natively expose as a Python API.

Tests for phase 2 should exist **before implementation** and should usually be written as:

- explicit contract tests
- `xfail(strict=True)` until the feature is public and working
- black-box tests against the proposed public API

Do not silently skip future tests. Prefer strict `xfail` with a clear reason.

## Phase 3: packaging, vendoring, release confidence

Phase 3 tests cover behavior that matters at publish time, especially:

- self-contained wheel/sdist behavior
- bundled runtime availability without a repo checkout
- release-time parity guarantees
- upgrade/vendoring confidence

These should also exist early as strict `xfail` tests when not yet implemented.

## Property testing guidance

Property testing is strongly encouraged here.

Best targets:

- generated operation sequences over a session
- empty vs omitted values
- text vs bytes round trips
- env/cwd/args/stdin combinations
- stateful read/write/exec transcripts

When using Hypothesis:

- keep generated scripts/inputs small but diverse
- prefer stable, explainable strategies over huge random grammars
- differential tests should compare the **full transcript** and, where useful, a final session snapshot
- set practical example counts; these tests should be valuable, not flaky

## Scenario design guidance

Prefer scenario-style tests over low-level transport assertions.

A scenario should usually describe:

- init kwargs
- a list of operations
- expected parity with direct upstream
- optional final snapshot operations

If you need new coverage, first ask:

- can this be expressed as another scenario?
- can it be checked by comparing wrapper vs direct upstream?

## Failure philosophy

When a not-yet-implemented future feature is being specified:

- write the test now
- mark it `xfail(strict=True)`
- prefer surfacing `NotImplementedError` for the missing behavior
- do not weaken the assertion just to keep the suite green

Once the feature exists, remove the `xfail` and keep the exact behavioral assertions if possible.

## Practical maintenance rules

- keep helpers in `tests/helpers.py` black-box and self-contained
- keep the Node reference harness in `tests/js/reference.mjs` simple and explicit
- avoid coupling tests to the exact current worker implementation
- if a test breaks because of a refactor but the public contract did not change, fix the implementation or the black-box helper, not the contract
- prefer a few high-value properties over many brittle unit tests of internals

## Default bar for new work

For any non-trivial public feature, aim for:

1. one curated contract test
2. one differential/conformance test if upstream parity is relevant
3. one property-based or multi-scenario expansion if the state space is broad
4. one future-facing `xfail` if the next phase depends on it
