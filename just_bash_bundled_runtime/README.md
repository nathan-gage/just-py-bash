# just-bash-bundled-runtime

This directory contains the first-party bundled Node.js runtime provider used by `just-py-bash[node]`.

Its package version is intentionally independent from `just-py-bash` and is derived dynamically from Git release tags such as `runtime/v22.22.2`.
The tracked bundled Node.js version lives in `[tool.just-bash-bundled-runtime]` in `pyproject.toml`.
See [`../VERSIONING.md`](../VERSIONING.md) for the runtime package version policy and release tag semantics.
The packaged runtime is built from official Node.js release archives and verified against upstream `SHASUMS256.txt`.
The package now builds with Hatchling and emits platform-specific `py3-none-<platform>` wheels based on the vendored runtime payload.

Populate the local runtime payload:

```bash
python just_bash_bundled_runtime/tools/vendor_runtime.py
```

Build a wheel from the repository root:

```bash
uv build just_bash_bundled_runtime --wheel --out-dir dist-node
```
