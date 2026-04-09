# Examples

These examples mirror the spirit of the vendored `just-bash` README and `examples/` directory, but use the Python wrapper API.

Run them from the repository root:

```bash
uv run --with-editable ./just_py_bash python examples/quickstart_sync.py
uv run --with-editable ./just_py_bash python examples/quickstart_async.py
uv run --with-editable ./just_py_bash python examples/custom_commands_sync.py
uv run --with-editable ./just_py_bash python examples/custom_commands_async.py
uv run --with-editable ./just_py_bash python examples/configuration_and_runtimes.py
```

These non-network examples are smoke-tested with the same repo-root invocation.

Optional example:

```bash
uv run --with-editable ./just_py_bash python examples/network_access.py
```

## Included examples

| File | What it demonstrates | Extra requirements |
|---|---|---|
| `quickstart_sync.py` | Basic `Bash` usage, shared filesystem, Python file helpers | Node.js |
| `quickstart_async.py` | Native-async `AsyncBash` usage with `asyncio` | Node.js |
| `custom_commands_sync.py` | Python-defined commands, pipelines, nested `ctx.exec(...)`, built-in composition | Node.js |
| `custom_commands_async.py` | Native-async custom commands with `AsyncBash` and async nested exec | Node.js |
| `configuration_and_runtimes.py` | Session options, per-exec overrides, plus working Python and JavaScript runtime demos | Node.js |
| `network_access.py` | Allow-listed network access with `curl` and `html-to-markdown` | Node.js, outbound internet |

## Notes

- The Python wrapper now exposes upstream-style filesystem config objects such as `OverlayFs`, `ReadWriteFs`, and `MountableFs`, but the current example set is still centered on the session-oriented API.
- The async examples use the native-async `AsyncBash` bridge, not thread offloading.
- The network example is intentionally separate because it depends on live internet access.
- The network example uses `http://example.com` so it remains reliable even in environments where Node's HTTPS certificate store is restricted.
