# Versioning

This repository publishes two Python packages with intentionally different version semantics:

- `just-py-bash`
- `just-bash-bundled-runtime`

Both packages use dynamic versioning from Git tags, but the meaning of those versions is different.

## `just-py-bash`

### Base version policy

`just-py-bash` tracks the vendored upstream `just-bash` package version.

If upstream releases:

- `2.14.1`

then the normal Python package release is:

- `2.14.1`

### Follow-up releases

If the Python wrapper needs a release without a new upstream `just-bash` version, use a PEP 440 post-release:

- `2.14.1.post1`
- `2.14.1.post2`

That means:

> same upstream `just-bash` payload, but a Python-package-only follow-up release

### Release tags

`just-py-bash` release tags are:

- `vX.Y.Z`
- `vX.Y.Z.postN`

Examples:

- `v2.14.1`
- `v2.14.1.post1`

### Auto-sync behavior

The upstream sync workflow does not blindly follow the latest upstream `main` commit.
When the upstream version changes, it finds the commit where that version was introduced and vendors that commit.

That keeps release-candidate PRs aligned to the actual upstream version boundary instead of random later same-version commits.

## `just-bash-bundled-runtime`

### Base version policy

`just-bash-bundled-runtime` does **not** track the `just-py-bash` version.
Its base version tracks the bundled Node.js runtime version shipped inside the wheel.

The source of truth lives in:

- `just_bash_bundled_runtime/pyproject.toml`
- `[tool.just-bash-bundled-runtime].node-version`

Example:

- `node-version = "22.22.2"`

means the package release version is based on:

- `22.22.2`

### Meaning of the version

For `22.22.2`:

- major `22` = Node major line
- minor `22` = Node upstream minor
- patch `2` = Node upstream patch

In plain English:

> this package bundles Node.js `22.22.2`

### Follow-up releases

If the bundled runtime package needs a packaging-only rerelease without changing the bundled Node payload, use a PEP 440 post-release:

- `22.22.2.post1`
- `22.22.2.post2`

That means:

> still bundles Node.js `22.22.2`, but this is a follow-up package release

Typical reasons:

- wheel metadata fixes
- packaging/build fixes
- release process corrections

### Release tags

`just-bash-bundled-runtime` release tags are namespaced:

- `runtime/vX.Y.Z`
- `runtime/vX.Y.Z.postN`

Examples:

- `runtime/v22.22.2`
- `runtime/v22.22.2.post1`

The tag namespace is only for Git organization. The built Python package version remains:

- `22.22.2`
- `22.22.2.post1`

### Runtime line tracking

The tracked Node major line lives in:

- `[tool.just-bash-bundled-runtime].target-major`

The sync workflow updates `node-version` to the latest Node.js LTS patch in that major line.

Example:

- `target-major = 22`
- current `node-version = 22.22.2`
- next Node LTS patch becomes `22.23.0`

Then the next runtime release candidate will target:

- package version `22.23.0`
- release tag `runtime/v22.23.0`

## Compatibility contract

`just-py-bash[node]` depends on a compatible major runtime line, not an exact matching wrapper version.

Current dependency:

- `just-bash-bundled-runtime>=22,<23`

That means:

> any bundled runtime package in the Node 22 line is acceptable for the optional `node` extra

## Release flow

Both packages are tag-driven.

### `just-py-bash`

Tag push:

- `vX.Y.Z`
- `vX.Y.Z.postN`

Flow:

1. build
2. publish to TestPyPI
3. publish to PyPI
4. create/update GitHub release

### `just-bash-bundled-runtime`

Tag push:

- `runtime/vX.Y.Z`
- `runtime/vX.Y.Z.postN`

Flow:

1. build
2. publish to TestPyPI
3. publish to PyPI
4. create/update GitHub release

## Automated release candidates

Sync PRs labeled `release-candidate` are auto-tagged only after they are merged to `main`.

That means:

- merge first
- tag on the merge commit second
- publish from the tag-triggered release workflow last

This keeps publishing tied to tagged commits on `main`.
