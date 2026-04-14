# Examples

These examples mirror the vendor `just-bash` README and example set, but show the Pythonic `just-py-bash` API surface.

Run any example from the repository root:

```bash
uv run --with-editable ./just_py_bash python examples/quickstart_sync.py
uv run --with-editable ./just_py_bash python examples/quickstart_async.py
uv run --with-editable ./just_py_bash python examples/custom_commands_sync.py
uv run --with-editable ./just_py_bash python examples/custom_commands_async.py
uv run --with-editable ./just_py_bash python examples/configuration_and_runtimes.py
uv run --with-editable ./just_py_bash python examples/filesystem_surfaces.py
uv run --with-editable ./just_py_bash python examples/network_access.py
uv run --with-editable ./just_py_bash python examples/option_hooks.py
uv run --with-editable ./just_py_bash python examples/parser_and_command_registry.py
uv run --with-editable ./just_py_bash python examples/transforms.py
uv run --with-editable ./just_py_bash python examples/sandbox.py
uv run --with-editable ./just_py_bash python examples/security_helpers.py
```

All listed examples are smoke-tested from the repo root with the same invocation style.

## Example guide

| File | What it demonstrates | Upstream area |
|---|---|---|
| `quickstart_sync.py` | Core `Bash` usage, shell-state reset semantics, shared filesystem state, and `bash.fs` helpers | Quick start |
| `quickstart_async.py` | Native-async `AsyncBash` usage with the same session semantics and async filesystem helpers | Quick start |
| `custom_commands_sync.py` | Python-defined commands, pipelines, nested `ctx.exec(...)`, and built-in composition | Custom commands |
| `custom_commands_async.py` | Async custom commands with `AsyncBash` and async nested exec | Custom commands |
| `configuration_and_runtimes.py` | Session options, per-exec overrides, `replace_env`, raw scripts, and optional Python / JavaScript runtimes | Configuration |
| `filesystem_surfaces.py` | `FileInit`, `LazyFile`, `FsStat`, `DirentEntry`, and the session-bound `bash.fs` API | Filesystem surfaces |
| `network_access.py` | Allow-listed network access, method policy, and header transforms using a local HTTP fixture | Network access |
| `option_hooks.py` | Python callback hooks for `fetch`, `logger`, `trace`, `coverage`, and `defense_in_depth` | Option hooks |
| `parser_and_command_registry.py` | Upstream command-name helpers plus standalone `parse(...)` / `serialize(...)` | Parser / command registry |
| `transforms.py` | `BashTransformPipeline`, `TeePlugin`, `CommandCollectorPlugin`, and session-integrated transform registration | Transform surfaces |
| `sandbox.py` | Upstream-style `Sandbox` API with file writes, inline execution, detached commands, and readback | Sandbox helpers |
| `security_helpers.py` | `SecurityViolationLogger` and `SecurityViolationError` helper surfaces | Security helpers |

## Notes

- The examples intentionally stay on the public Python API. They do not import private `just_bash._*` modules.
- The network example no longer depends on outbound internet; it uses a local HTTP fixture so it remains smoke-testable in CI.
- The async examples use the native-async `AsyncBash` / `AsyncSandbox` bridge style rather than thread offloading.
- If you are exploring the CLI launchers, see the main `README.md` for `just-py-bash` / `just-py-bash-shell` usage examples.
