# just-bash-bundled-runtime

This directory contains the first-party bundled Node.js runtime provider used by `just-py-bash[node]`.

The packaged runtime is built from official Node.js release archives and verified against upstream `SHASUMS256.txt`.

Populate the local runtime payload:

```bash
python scripts/vendor_node_provider.py --package-dir just_bash_bundled_runtime
```

Build a wheel from the repository root:

```bash
uv build just_bash_bundled_runtime --wheel --out-dir dist-node
```
