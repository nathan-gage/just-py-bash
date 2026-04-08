# tests/AGENTS.md

This directory defines the **behavioral contract** for `just-py-bash`.

The suite is organized around capabilities and responsibilities, not the order features happened to be implemented.

## Guiding principle

> The wrapper is correct when its public behavior matches upstream `just-bash` for supported features, and when planned capabilities already have explicit black-box contracts waiting for them.

## Directory layout

- `tests/api/`
  - public Python API behavior that should remain stable across refactors
- `tests/parity/`
  - upstream differential tests; this is the main oracle for wrapper correctness
- `tests/contracts/`
  - future-facing capability contracts that are intentionally `xfail(strict=True)` until implemented
- `tests/support/`
  - black-box harness code and the direct Node reference runner
- `tests/conftest.py`
  - pytest fixtures only

Choose locations based on **what the test proves**, not whether it was added early or late.

## Core philosophy

### 1. Treat tests as a product contract, not an implementation snapshot

Tests in `tests/` should survive refactors of `src/`.

That means:

- test only the **public Python API**
- use subprocesses and black-box behavior where possible
- never rely on private modules, private methods, internal worker details, or internal transport helpers from `src/`
- never import `just_py_bash._*` from tests

If `src/` changes substantially, the tests should still be valid unless the public contract changes.

### 2. Upstream `just-bash` is the semantic oracle for current wrapper parity

For the currently supported wrapper surface, the strongest tests are **differential tests**:

1. run a scenario through the Python wrapper
2. run the same scenario through a direct Node harness importing upstream `just-bash`
3. compare structured results

Prefer this style whenever possible.

### 3. We are testing interop, not reimplementing upstream in Python

Do not hand-copy large amounts of shell semantics into expected values when a direct upstream comparison is possible.

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
- test-only helpers in `tests/support/`
- standard library
- pytest / hypothesis / subprocess tooling
- the vendored upstream checkout only as an external reference runtime

Disallowed from tests:

- `just_py_bash._bridge`
- `just_py_bash._api`
- `just_py_bash._models`
- any private helper under `src/just_py_bash/_*`

If a test needs functionality that only exists in a private helper, re-create the minimum test-only helper under `tests/support/` instead.

## Suite responsibilities

### `tests/api/`: public API contracts

Use this area for direct black-box assertions about the supported Python API, for example:

- object lifecycle
- helper methods
- result semantics
- session isolation between wrapper instances

### `tests/parity/`: wrapper vs upstream parity

Use this area for:

- curated upstream parity scenarios
- generated/property-based session transcripts
- final-state snapshot comparisons when useful

When adding parity coverage, prefer this order:

1. add a small curated scenario
2. add it to the differential corpus if possible
3. add a property-based/generalized form if feasible

### `tests/contracts/`: future capability contracts

Use this area for capabilities we plan to support but have not shipped yet.

Current examples:

- Python-defined custom commands
- packaged wheel/sdist behavior without a repo checkout

Rules:

- write the black-box contract now
- mark it `xfail(strict=True)` until implemented
- prefer `NotImplementedError` as the temporary failure mode
- do not silently skip these tests

## Property testing guidance

Property testing is strongly encouraged here.

Best targets:

- generated operation sequences over a session
- empty vs omitted values
- text vs bytes round trips
- env/cwd/args/stdin combinations
- stateful read/write/exec transcripts
- future custom-command IO/context round trips

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
- expected parity with direct upstream or a direct public-API contract
- optional final snapshot operations

If you need new coverage, first ask:

- can this be expressed as another scenario?
- can it be checked by comparing wrapper vs direct upstream?

## Naming guidance

Name files and tests after the behavior being asserted.

Good:

- `tests/parity/test_curated_scenarios.py`
- `tests/contracts/test_custom_commands.py`
- `test_installed_wheel_console_script_runs_without_repo_checkout`

Avoid names that only reflect implementation order, temporary project phases, or local refactor history.

## Practical maintenance rules

- keep helpers in `tests/support/` black-box and self-contained
- keep the Node reference harness in `tests/support/reference.mjs` simple and explicit
- avoid coupling tests to the exact current worker implementation
- if a test breaks because of a refactor but the public contract did not change, fix the implementation or the black-box helper, not the contract
- prefer a few high-value properties over many brittle unit tests of internals

## Default bar for new work

For any non-trivial public feature, aim for:

1. one direct public-API contract test
2. one differential/parity test if upstream equivalence is relevant
3. one property-based or multi-scenario expansion if the state space is broad
4. one future-facing contract test if the next capability layer depends on it
