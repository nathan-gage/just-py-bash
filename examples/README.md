# Examples

These examples mirror the spirit of the vendored `just-bash` README and `examples/` directory, but use the Python wrapper API.

Run them from the repository root:

```bash
uv run python examples/quickstart_sync.py
uv run python examples/quickstart_async.py
uv run python examples/custom_commands_sync.py
uv run python examples/custom_commands_async.py
uv run python examples/configuration_and_runtimes.py
```

Optional example:

```bash
uv run python examples/network_access.py
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

- The Python wrapper currently focuses on the portable session-oriented API. Unlike upstream TypeScript examples, it does not yet expose `OverlayFs`, `ReadWriteFs`, or `MountableFs` directly.
- The async examples use the native-async `AsyncBash` bridge, not thread offloading.
- The network example is intentionally separate because it depends on live internet access.
- The network example uses `http://example.com` so it remains reliable even in environments where Node's HTTPS certificate store is restricted.
