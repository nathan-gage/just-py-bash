from __future__ import annotations

import asyncio
import base64
import ctypes
import inspect
import json
import os
import shlex
import shutil
import subprocess
import threading
from collections.abc import Awaitable, Callable, Mapping, Sequence
from ctypes import wintypes
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from pydantic import TypeAdapter, ValidationError

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_SCRIPT = Path(__file__).resolve().with_name("reference.mjs")
REFERENCE_WORKER_SCRIPT = Path(__file__).resolve().with_name("reference_worker.mjs")
BYTE_TAG = "__just_bash_bytes__"
_JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, object])
_REFERENCE_TIMEOUT_SECONDS = 60.0


@dataclass(slots=True, frozen=True)
class BackendArtifacts:
    js_entry: Path
    package_json: Path


ReferenceLazyFileProvider = Callable[[], str | bytes | Awaitable[str | bytes]]
ReferenceFetchCallback = Callable[[Any], Any | Awaitable[Any]]
ReferenceTraceCallback = Callable[[Any], Any | Awaitable[Any]]
ReferenceDefenseViolationCallback = Callable[[Any], Any | Awaitable[Any]]


@dataclass(slots=True)
class ReferenceBridgeHooks:
    lazy_file_providers: dict[str, ReferenceLazyFileProvider]
    fetch_callback: ReferenceFetchCallback | None = None
    logger: Any = None
    trace_callback: ReferenceTraceCallback | None = None
    coverage_writer: Any = None
    defense_violation_callback: ReferenceDefenseViolationCallback | None = None
    force_interactive: bool = False

    @property
    def requires_interactive(self) -> bool:
        return (
            self.force_interactive
            or bool(self.lazy_file_providers)
            or self.fetch_callback is not None
            or self.logger is not None
            or self.trace_callback is not None
            or self.coverage_writer is not None
            or self.defense_violation_callback is not None
        )


class _ReferenceLazyFileRegistry:
    def __init__(self) -> None:
        self._next_id = 1
        self.providers: dict[str, ReferenceLazyFileProvider] = {}

    def register(self, provider: ReferenceLazyFileProvider) -> str:
        name = f"lazy_file_{self._next_id}"
        self._next_id += 1
        self.providers[name] = provider
        return name


async def _await_reference_lazy_file_result(result: Awaitable[object]) -> str | bytes:
    return _coerce_reference_lazy_file_content(await result)


async def _await_reference_callback_result(result: Awaitable[object]) -> object:
    return await result


def _coerce_reference_lazy_file_content(value: object) -> str | bytes:
    if isinstance(value, str | bytes):
        return value
    raise TypeError("Lazy file providers must return str, bytes, or an awaitable of either")


def _reference_fetch_result_to_wire(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        headers = mapping.get("headers")
        status = mapping.get("status", 0)
        return {
            "status": int(status) if isinstance(status, (int, str)) else 0,
            "statusText": str(mapping.get("statusText", "")),
            "headers": dict(cast(Mapping[str, object], headers)) if isinstance(headers, Mapping) else {},
            "body": str(mapping.get("body", "")),
            "url": str(mapping.get("url", "")),
        }

    headers = getattr(value, "headers", {})
    return {
        "status": int(getattr(value, "status", 0)),
        "statusText": str(getattr(value, "status_text", "")),
        "headers": dict(cast(Mapping[str, object], headers)) if isinstance(headers, Mapping) else {},
        "body": str(getattr(value, "body", "")),
        "url": str(getattr(value, "url", "")),
    }


def split_command_string(command: str) -> list[str]:
    if os.name != "nt":
        return shlex.split(command)

    ctypes_module: Any = ctypes
    windll = ctypes_module.windll
    command_line_to_argv = windll.shell32.CommandLineToArgvW
    command_line_to_argv.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    command_line_to_argv.restype = ctypes.POINTER(wintypes.LPWSTR)
    local_free = windll.kernel32.LocalFree
    local_free.argtypes = [wintypes.HLOCAL]
    local_free.restype = wintypes.HLOCAL

    argc = ctypes.c_int(0)
    argv = command_line_to_argv(command, ctypes.byref(argc))
    if not argv:
        raise AssertionError(f"Could not parse JUST_BASH_NODE command: {command!r}")

    try:
        return [argv[index] for index in range(argc.value)]
    finally:
        local_free(argv)


def resolve_node_command() -> list[str]:
    if configured := os.environ.get("JUST_BASH_NODE"):
        return split_command_string(configured)

    node = shutil.which("node")
    if not node:
        raise AssertionError(
            "Node.js is required for differential tests. Install Node or set JUST_BASH_NODE.",
        )
    return [node]


def infer_package_json_from_js_entry(js_entry: Path) -> Path:
    for parent in js_entry.parents:
        candidate = parent / "package.json"
        if candidate.exists():
            return candidate.resolve()
    return (js_entry.parent.parent / "package.json").resolve()


def resolve_backend_artifacts() -> BackendArtifacts:
    env_js_entry = os.environ.get("JUST_BASH_JS_ENTRY")
    env_package_json = os.environ.get("JUST_BASH_PACKAGE_JSON")
    if env_js_entry:
        js_entry = Path(env_js_entry).expanduser().resolve()
        package_json = (
            Path(env_package_json).expanduser().resolve()
            if env_package_json
            else infer_package_json_from_js_entry(js_entry)
        )
        if not js_entry.exists():
            raise AssertionError(f"Configured JS entry does not exist: {js_entry}")
        if not package_json.exists():
            raise AssertionError(f"Configured package.json does not exist: {package_json}")
        return BackendArtifacts(js_entry=js_entry, package_json=package_json)

    vendor_root = ROOT / "vendor" / "just-bash"
    candidate_roots = (
        vendor_root / "packages" / "just-bash",
        vendor_root,
    )
    for root in candidate_roots:
        package_json = root / "package.json"
        for rel in ("dist/index.js", "dist/bundle/index.js"):
            js_entry = root / rel
            if js_entry.exists() and package_json.exists():
                return BackendArtifacts(js_entry=js_entry.resolve(), package_json=package_json.resolve())

    raise AssertionError(
        "Could not locate a built just-bash artifact for reference testing. "
        "Build vendor/just-bash first or set JUST_BASH_JS_ENTRY and JUST_BASH_PACKAGE_JSON.",
    )


def encode_file_value(value: str | bytes) -> str | dict[str, str]:
    if isinstance(value, bytes):
        return {BYTE_TAG: base64.b64encode(value).decode("ascii")}
    return value


def decode_bytes_payload(payload: dict[str, str]) -> bytes:
    return base64.b64decode(payload[BYTE_TAG].encode("ascii"))


def public_api() -> Any:
    return import_module("just_bash")


def normalize_exec_result(result: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exitCode": result.exit_code,
        "env": dict(result.env),
    }
    if result.metadata is not None:
        payload["metadata"] = dict(result.metadata)
    return payload


def normalize_fs_stat(result: Any) -> dict[str, Any]:
    mtime = result.mtime
    if not isinstance(mtime, datetime):  # pragma: no cover - defensive
        raise AssertionError(f"expected datetime mtime, got {mtime!r}")

    normalized = mtime if mtime.tzinfo is not None else mtime.replace(tzinfo=UTC)
    return {
        "isFile": bool(result.is_file),
        "isDirectory": bool(result.is_directory),
        "isSymbolicLink": bool(result.is_symbolic_link),
        "mode": int(result.mode),
        "size": int(result.size),
        "mtimeMs": int(normalized.astimezone(UTC).timestamp() * 1000),
    }


def normalize_dirent_entry(result: Any) -> dict[str, Any]:
    return {
        "name": str(result.name),
        "isFile": bool(result.is_file),
        "isDirectory": bool(result.is_directory),
        "isSymbolicLink": bool(result.is_symbolic_link),
    }


def normalize_dirent_entries(results: Sequence[Any]) -> list[dict[str, Any]]:
    return [normalize_dirent_entry(result) for result in results]


def normalize_operation_error(error: BaseException) -> dict[str, Any]:
    error_type = getattr(error, "error_type", None)
    if not isinstance(error_type, str) or not error_type:
        error_type = type(error).__name__

    return {
        "kind": "error",
        "type": error_type,
        "message": str(error),
    }


def wrap_success(value: Any) -> dict[str, Any]:
    return {
        "kind": "ok",
        "value": value,
    }


def execution_limits_to_reference(execution_limits: Any) -> dict[str, int]:
    payload: dict[str, int] = {}
    mapping = {
        "max_call_depth": "maxCallDepth",
        "max_command_count": "maxCommandCount",
        "max_loop_iterations": "maxLoopIterations",
        "max_awk_iterations": "maxAwkIterations",
        "max_sed_iterations": "maxSedIterations",
        "max_jq_iterations": "maxJqIterations",
        "max_sqlite_timeout_ms": "maxSqliteTimeoutMs",
        "max_python_timeout_ms": "maxPythonTimeoutMs",
        "max_js_timeout_ms": "maxJsTimeoutMs",
        "max_glob_operations": "maxGlobOperations",
        "max_string_length": "maxStringLength",
        "max_array_elements": "maxArrayElements",
        "max_heredoc_size": "maxHeredocSize",
        "max_substitution_depth": "maxSubstitutionDepth",
        "max_brace_expansion_results": "maxBraceExpansionResults",
        "max_output_size": "maxOutputSize",
        "max_file_descriptors": "maxFileDescriptors",
        "max_source_depth": "maxSourceDepth",
    }
    for python_name, wire_name in mapping.items():
        value = getattr(execution_limits, python_name, None)
        if value is not None:
            payload[wire_name] = value
    return payload


def javascript_config_to_reference(config: Any) -> bool | dict[str, str]:
    if config is True:
        return True
    bootstrap = getattr(config, "bootstrap", None)
    payload: dict[str, str] = {}
    if bootstrap is not None:
        payload["bootstrap"] = bootstrap
    return payload


def _encode_reference_defense_in_depth(
    config: Any,
) -> tuple[bool | dict[str, object], ReferenceDefenseViolationCallback | None]:
    api = public_api()
    if isinstance(config, bool):
        return config, None

    if isinstance(config, api.DefenseInDepthConfig):
        payload: dict[str, object] = {}
        if config.enabled is not None:
            payload["enabled"] = config.enabled
        if config.audit_mode is not None:
            payload["auditMode"] = config.audit_mode
        if config.exclude_violation_types is not None:
            payload["excludeViolationTypes"] = [str(value) for value in config.exclude_violation_types]
        if config.on_violation is not None:
            payload["onViolationEnabled"] = True
        return payload, config.on_violation

    raise AssertionError(f"Unsupported defense_in_depth value for reference harness: {config!r}")


def _encode_datetime_ms(value: datetime) -> int:
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return int(normalized.astimezone(UTC).timestamp() * 1000)


def _encode_reference_initial_file_value(
    value: Any,
    *,
    registry: _ReferenceLazyFileRegistry | None = None,
) -> object:
    api = public_api()
    if isinstance(value, api.FileInit):
        payload: dict[str, object] = {
            "kind": "file_init",
            "content": encode_file_value(value.content),
        }
        if value.mode is not None:
            payload["mode"] = value.mode
        if value.mtime is not None:
            payload["mtimeMs"] = _encode_datetime_ms(value.mtime)
        return payload

    if isinstance(value, api.LazyFile):
        provider = value.provider
        if callable(provider):
            if registry is None:
                raise AssertionError("reference harness does not support callable lazy file providers")
            return {
                "kind": "lazy_callback",
                "providerName": registry.register(cast(ReferenceLazyFileProvider, provider)),
            }
        return {
            "kind": "lazy_static",
            "content": encode_file_value(provider),
        }

    if callable(value):
        if registry is None:
            raise AssertionError("reference harness does not support callable lazy file providers")
        return {
            "kind": "lazy_callback",
            "providerName": registry.register(cast(ReferenceLazyFileProvider, value)),
        }

    return encode_file_value(value)


def _encode_reference_files(
    files: Mapping[str, Any],
    *,
    registry: _ReferenceLazyFileRegistry | None = None,
) -> dict[str, object]:
    return {path: _encode_reference_initial_file_value(value, registry=registry) for path, value in files.items()}


def _encode_reference_filesystem(
    filesystem: Any,
    *,
    registry: _ReferenceLazyFileRegistry | None = None,
) -> object:
    api = public_api()
    if isinstance(filesystem, api.InMemoryFs):
        in_memory_payload: dict[str, object] = {"kind": "in_memory"}
        if filesystem.files is not None:
            in_memory_payload["files"] = _encode_reference_files(
                dict(filesystem.files),
                registry=registry,
            )
        return in_memory_payload
    if isinstance(filesystem, api.OverlayFs):
        overlay_payload: dict[str, object] = {"kind": "overlay", "root": filesystem.root}
        if filesystem.mount_point is not None:
            overlay_payload["mountPoint"] = filesystem.mount_point
        if filesystem.read_only:
            overlay_payload["readOnly"] = True
        if filesystem.max_file_read_size is not None:
            overlay_payload["maxFileReadSize"] = filesystem.max_file_read_size
        if filesystem.allow_symlinks:
            overlay_payload["allowSymlinks"] = True
        return overlay_payload
    if isinstance(filesystem, api.ReadWriteFs):
        read_write_payload: dict[str, object] = {"kind": "read_write", "root": filesystem.root}
        if filesystem.max_file_read_size is not None:
            read_write_payload["maxFileReadSize"] = filesystem.max_file_read_size
        if filesystem.allow_symlinks:
            read_write_payload["allowSymlinks"] = True
        return read_write_payload
    if isinstance(filesystem, api.MountableFs):
        mountable_payload: dict[str, object] = {"kind": "mountable"}
        if filesystem.base is not None:
            mountable_payload["base"] = _encode_reference_filesystem(filesystem.base, registry=registry)
        if filesystem.mounts is not None:
            mountable_payload["mounts"] = [
                {
                    "mountPoint": mount.mount_point,
                    "filesystem": _encode_reference_filesystem(mount.filesystem, registry=registry),
                }
                for mount in filesystem.mounts
            ]
        return mountable_payload
    return filesystem


def to_reference_bridge_init(
    init_kwargs: Mapping[str, Any],
) -> tuple[dict[str, Any], ReferenceBridgeHooks]:
    payload: dict[str, Any] = {}
    registry = _ReferenceLazyFileRegistry()

    files = init_kwargs.get("files")
    if files is not None:
        payload["files"] = _encode_reference_files(dict(files), registry=registry)

    env = init_kwargs.get("env")
    if env is not None:
        payload["env"] = dict(env)

    cwd = init_kwargs.get("cwd")
    if cwd is not None:
        payload["cwd"] = cwd

    filesystem = init_kwargs.get("fs")
    if filesystem is not None:
        payload["fs"] = _encode_reference_filesystem(filesystem, registry=registry)

    commands = init_kwargs.get("commands")
    if commands is not None:
        payload["commands"] = list(commands)

    if init_kwargs.get("python"):
        payload["python"] = True

    javascript = init_kwargs.get("javascript")
    if javascript:
        payload["javascript"] = javascript_config_to_reference(javascript)

    execution_limits = init_kwargs.get("execution_limits")
    if execution_limits is not None:
        payload["executionLimits"] = execution_limits_to_reference(execution_limits)

    fetch = init_kwargs.get("fetch")
    if fetch is not None:
        payload["fetchEnabled"] = True

    logger = init_kwargs.get("logger")
    if logger is not None:
        payload["loggerEnabled"] = True

    trace = init_kwargs.get("trace")
    if trace is not None:
        payload["traceEnabled"] = True

    coverage = init_kwargs.get("coverage")
    if coverage is not None:
        payload["coverageEnabled"] = True

    defense_in_depth = init_kwargs.get("defense_in_depth")
    defense_violation_callback: ReferenceDefenseViolationCallback | None = None
    if defense_in_depth is not None:
        encoded_defense, defense_violation_callback = _encode_reference_defense_in_depth(defense_in_depth)
        payload["defenseInDepth"] = encoded_defense

    network = init_kwargs.get("network")
    if network is not None:
        payload["network"] = dict(network)

    process_info = init_kwargs.get("process_info")
    if process_info is not None:
        payload["processInfo"] = dict(process_info)

    return payload, ReferenceBridgeHooks(
        lazy_file_providers=dict(registry.providers),
        fetch_callback=fetch,
        logger=logger,
        trace_callback=trace,
        coverage_writer=coverage,
        defense_violation_callback=defense_violation_callback,
        force_interactive=defense_in_depth is not None,
    )


def to_reference_init_options(init_kwargs: Mapping[str, Any]) -> dict[str, Any]:
    payload, hooks = to_reference_bridge_init(init_kwargs)
    if hooks.requires_interactive:
        raise AssertionError("reference harness does not support interactive callback-backed option hooks")
    return payload


def to_reference_exec_options(exec_kwargs: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "env" in exec_kwargs:
        payload["env"] = dict(exec_kwargs["env"])

    if exec_kwargs.get("replace_env"):
        payload["replaceEnv"] = True

    if "cwd" in exec_kwargs:
        payload["cwd"] = exec_kwargs["cwd"]

    if exec_kwargs.get("raw_script"):
        payload["rawScript"] = True

    if "stdin" in exec_kwargs:
        payload["stdin"] = exec_kwargs["stdin"]

    if "args" in exec_kwargs:
        payload["args"] = list(exec_kwargs["args"])

    if "timeout" in exec_kwargs and exec_kwargs["timeout"] is not None:
        payload["timeoutMs"] = max(1, int(exec_kwargs["timeout"] * 1000))

    return payload


def to_reference_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    op = operation["op"]
    if op == "exec":
        payload: dict[str, Any] = {
            "op": "exec",
            "script": operation["script"],
        }
        if "kwargs" in operation:
            payload["options"] = to_reference_exec_options(operation["kwargs"])
        return payload

    if op in {"write_bytes", "append_bytes"}:
        return {
            "op": op,
            "path": operation["path"],
            "content": encode_file_value(operation["content"]),
        }

    if op == "probe_defense_violation":
        return {
            "op": "probe_defense_violation",
            "kind": operation["kind"],
        }

    return dict(operation)


class _InteractiveReferenceScenario:
    def __init__(
        self,
        *,
        js_entry: Path,
        package_json: Path,
        init_options: Mapping[str, Any],
        operations: Sequence[Mapping[str, Any]],
        hooks: ReferenceBridgeHooks,
    ) -> None:
        self._js_entry = js_entry
        self._package_json = package_json
        self._init_options = dict(init_options)
        self._operations = [dict(operation) for operation in operations]
        self._hooks = hooks
        self._proc: subprocess.Popen[str] | None = None
        self._stderr_tail: list[str] = []
        self._stderr_thread: threading.Thread | None = None
        self._write_lock = threading.Lock()

    def run(self) -> dict[str, Any]:
        self._proc = subprocess.Popen(
            [*resolve_node_command(), str(REFERENCE_WORKER_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr,
            name="interactive-reference-stderr",
            daemon=True,
        )
        self._stderr_thread.start()

        try:
            self._send_line(
                {
                    "id": 1,
                    "op": "run",
                    "jsEntry": str(self._js_entry),
                    "packageJson": str(self._package_json),
                    "initOptions": self._init_options,
                    "operations": self._operations,
                },
            )

            stdout = self._proc.stdout
            if stdout is None:  # pragma: no cover - defensive
                raise AssertionError("interactive reference harness did not expose stdout")

            while True:
                line = stdout.readline()
                if line == "":
                    raise AssertionError(self._process_failure_message())

                try:
                    message = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AssertionError(
                        f"interactive reference harness returned invalid JSON: {exc}: {line!r}",
                    ) from exc

                if message.get("type") == "lazy_file":
                    self._handle_lazy_file(message)
                    continue
                if message.get("type") == "fetch":
                    self._handle_fetch(message)
                    continue
                if message.get("type") == "logger":
                    self._handle_logger(message)
                    continue
                if message.get("type") == "trace":
                    self._handle_trace(message)
                    continue
                if message.get("type") == "coverage":
                    self._handle_coverage(message)
                    continue
                if message.get("type") == "defense_violation":
                    self._handle_defense_violation(message)
                    continue

                if message.get("id") != 1:
                    raise AssertionError(f"interactive reference harness returned an unexpected message: {message!r}")

                if message.get("ok") is True:
                    try:
                        return _JSON_OBJECT_ADAPTER.validate_python(message.get("result"))
                    except ValidationError as exc:
                        raise AssertionError(
                            f"interactive reference harness returned an invalid payload: {exc}\n{message!r}",
                        ) from exc

                error = message.get("error")
                raise AssertionError(
                    f"interactive reference harness failed\nerror: {error!r}\nstderr:\n{self._joined_stderr()}"
                )
        finally:
            self.close()

    def _send_line(self, payload: Mapping[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise AssertionError("interactive reference harness is not writable")

        with self._write_lock:
            try:
                proc.stdin.write(json.dumps(dict(payload)) + "\n")
                proc.stdin.flush()
            except BrokenPipeError as exc:
                raise AssertionError(self._process_failure_message()) from exc

    def _handle_lazy_file(self, event: Mapping[str, object]) -> None:
        invocation_id = event.get("invocationId")
        provider_name = event.get("providerName")
        if not isinstance(invocation_id, int) or not isinstance(provider_name, str):
            raise AssertionError(f"interactive reference harness emitted an invalid lazy file event: {event!r}")

        provider = self._hooks.lazy_file_providers.get(provider_name)
        if provider is None:
            self._send_line(
                {
                    "op": "lazy_file_complete",
                    "invocationId": invocation_id,
                    "error": {"message": f"Unknown lazy file provider: {provider_name}"},
                },
            )
            return

        try:
            raw_content: object = provider()
            if inspect.isawaitable(raw_content):
                content = asyncio.run(_await_reference_lazy_file_result(raw_content))
            else:
                content = _coerce_reference_lazy_file_content(raw_content)
            completion_payload: dict[str, object] = {
                "op": "lazy_file_complete",
                "invocationId": invocation_id,
                "content": encode_file_value(content),
            }
        except Exception as exc:
            completion_payload = {
                "op": "lazy_file_complete",
                "invocationId": invocation_id,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }

        self._send_line(completion_payload)

    def _handle_fetch(self, event: Mapping[str, object]) -> None:
        invocation_id = event.get("invocationId")
        if not isinstance(invocation_id, int):
            raise AssertionError(f"interactive reference harness emitted an invalid fetch event: {event!r}")

        callback = self._hooks.fetch_callback
        if callback is None:
            self._send_line(
                {
                    "op": "fetch_complete",
                    "invocationId": invocation_id,
                    "error": {"message": "No fetch callback configured"},
                },
            )
            return

        api = public_api()
        try:
            request = api.FetchRequest.from_wire(str(event.get("url", "")), event.get("options"))
            raw_result: object = callback(request)
            if inspect.isawaitable(raw_result):
                resolved = asyncio.run(_await_reference_callback_result(raw_result))
            else:
                resolved = raw_result
            completion_payload: dict[str, object] = {
                "op": "fetch_complete",
                "invocationId": invocation_id,
                "result": _reference_fetch_result_to_wire(resolved),
            }
        except Exception as exc:
            completion_payload = {
                "op": "fetch_complete",
                "invocationId": invocation_id,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }

        self._send_line(completion_payload)

    def _handle_logger(self, event: Mapping[str, object]) -> None:
        logger = self._hooks.logger
        if logger is None:
            return
        level = event.get("level", "info")
        if not isinstance(level, str):
            raise AssertionError(f"interactive reference harness emitted an invalid logger event: {event!r}")
        method = getattr(logger, level, None)
        if not callable(method):
            return
        result = method(str(event.get("message", "")), event.get("data"))
        if inspect.isawaitable(result):
            asyncio.run(_await_reference_callback_result(result))

    def _handle_trace(self, event: Mapping[str, object]) -> None:
        callback = self._hooks.trace_callback
        if callback is None:
            return
        payload = event.get("event")
        if not isinstance(payload, Mapping):
            raise AssertionError(f"interactive reference harness emitted an invalid trace event: {event!r}")
        api = public_api()
        result = callback(api.TraceEvent.from_wire(cast(Mapping[str, object], payload)))
        if inspect.isawaitable(result):
            asyncio.run(_await_reference_callback_result(result))

    def _handle_coverage(self, event: Mapping[str, object]) -> None:
        writer = self._hooks.coverage_writer
        if writer is None:
            return
        hit = getattr(writer, "hit", None)
        if not callable(hit):
            return
        result = hit(str(event.get("feature", "")))
        if inspect.isawaitable(result):
            asyncio.run(_await_reference_callback_result(result))

    def _handle_defense_violation(self, event: Mapping[str, object]) -> None:
        callback = self._hooks.defense_violation_callback
        if callback is None:
            return
        payload = event.get("violation")
        if not isinstance(payload, Mapping):
            raise AssertionError(f"interactive reference harness emitted an invalid defense violation event: {event!r}")
        api = public_api()
        result = callback(api.SecurityViolation.from_wire(cast(Mapping[str, object], payload)))
        if inspect.isawaitable(result):
            asyncio.run(_await_reference_callback_result(result))

    def _read_stderr(self) -> None:
        proc = self._proc
        if proc is None or proc.stderr is None:
            return
        for line in proc.stderr:
            self._stderr_tail.append(line.rstrip())

    def _joined_stderr(self) -> str:
        return "\n".join(self._stderr_tail).strip()

    def _process_failure_message(self) -> str:
        proc = self._proc
        stderr = self._joined_stderr()
        message = "interactive reference harness exited unexpectedly"
        if proc is not None:
            return_code = proc.poll()
            if return_code is not None:
                message += f" with status {return_code}"
        if stderr:
            message += f"\nstderr:\n{stderr}"
        return message

    def close(self) -> None:
        proc = self._proc
        if proc is None:
            return

        stdin = proc.stdin
        if stdin is not None and not stdin.closed:
            stdin.close()

        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)

        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=1)

        stdout = proc.stdout
        if stdout is not None and not stdout.closed:
            stdout.close()

        stderr = proc.stderr
        if stderr is not None and not stderr.closed:
            stderr.close()

        self._proc = None


def run_reference_scenario(
    *,
    js_entry: Path,
    package_json: Path,
    init_options: Mapping[str, Any] | None = None,
    operations: Sequence[Mapping[str, Any]],
    hooks: ReferenceBridgeHooks | None = None,
) -> dict[str, Any]:
    effective_hooks = hooks or ReferenceBridgeHooks(lazy_file_providers={})
    if effective_hooks.requires_interactive:
        return _InteractiveReferenceScenario(
            js_entry=js_entry,
            package_json=package_json,
            init_options=init_options or {},
            operations=operations,
            hooks=effective_hooks,
        ).run()

    request = {
        "jsEntry": str(js_entry),
        "packageJson": str(package_json),
        "initOptions": dict(init_options or {}),
        "operations": [dict(operation) for operation in operations],
    }
    completed = subprocess.run(
        [*resolve_node_command(), str(REFERENCE_SCRIPT)],
        input=json.dumps(request),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"reference harness failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    try:
        payload = _JSON_OBJECT_ADAPTER.validate_json(completed.stdout)
    except ValidationError as exc:
        raise AssertionError(f"reference harness returned an invalid payload: {exc}\n{completed.stdout}") from exc
    return payload


def op_exec(script: str, **kwargs: Any) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "exec", "script": script}
    if kwargs:
        operation["kwargs"] = kwargs
    return operation


def op_read_text(path: str) -> dict[str, Any]:
    return {"op": "read_text", "path": path}


def op_read_bytes(path: str) -> dict[str, Any]:
    return {"op": "read_bytes", "path": path}


def op_write_text(path: str, content: str) -> dict[str, Any]:
    return {"op": "write_text", "path": path, "content": content}


def op_write_bytes(path: str, content: bytes) -> dict[str, Any]:
    return {"op": "write_bytes", "path": path, "content": content}


def op_append_text(path: str, content: str) -> dict[str, Any]:
    return {"op": "append_text", "path": path, "content": content}


def op_append_bytes(path: str, content: bytes) -> dict[str, Any]:
    return {"op": "append_bytes", "path": path, "content": content}


def op_exists(path: str) -> dict[str, Any]:
    return {"op": "exists", "path": path}


def op_stat(path: str) -> dict[str, Any]:
    return {"op": "stat", "path": path}


def op_lstat(path: str) -> dict[str, Any]:
    return {"op": "lstat", "path": path}


def op_mkdir(path: str, *, recursive: bool = False) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "mkdir", "path": path}
    if recursive:
        operation["recursive"] = True
    return operation


def op_readdir(path: str) -> dict[str, Any]:
    return {"op": "readdir", "path": path}


def op_readdir_with_file_types(path: str) -> dict[str, Any]:
    return {"op": "readdir_with_file_types", "path": path}


def op_rm(path: str, *, recursive: bool = False, force: bool = False) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "rm", "path": path}
    if recursive:
        operation["recursive"] = True
    if force:
        operation["force"] = True
    return operation


def op_cp(src: str, dest: str, *, recursive: bool = False) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "cp", "src": src, "dest": dest}
    if recursive:
        operation["recursive"] = True
    return operation


def op_mv(src: str, dest: str) -> dict[str, Any]:
    return {"op": "mv", "src": src, "dest": dest}


def op_resolve_path(path: str, *, base: str | None = None) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "resolve_path", "path": path}
    if base is not None:
        operation["base"] = base
    return operation


def op_get_all_paths() -> dict[str, Any]:
    return {"op": "get_all_paths"}


def op_chmod(path: str, mode: int) -> dict[str, Any]:
    return {"op": "chmod", "path": path, "mode": mode}


def op_symlink(target: str, link_path: str) -> dict[str, Any]:
    return {"op": "symlink", "target": target, "linkPath": link_path}


def op_link(existing_path: str, new_path: str) -> dict[str, Any]:
    return {"op": "link", "existingPath": existing_path, "newPath": new_path}


def op_readlink(path: str) -> dict[str, Any]:
    return {"op": "readlink", "path": path}


def op_realpath(path: str) -> dict[str, Any]:
    return {"op": "realpath", "path": path}


def op_utimes(path: str, atime: datetime, mtime: datetime) -> dict[str, Any]:
    normalized_atime = atime if atime.tzinfo is not None else atime.replace(tzinfo=UTC)
    normalized_mtime = mtime if mtime.tzinfo is not None else mtime.replace(tzinfo=UTC)
    return {
        "op": "utimes",
        "path": path,
        "atimeMs": int(normalized_atime.astimezone(UTC).timestamp() * 1000),
        "mtimeMs": int(normalized_mtime.astimezone(UTC).timestamp() * 1000),
    }


def op_get_env() -> dict[str, Any]:
    return {"op": "get_env"}


def op_get_cwd() -> dict[str, Any]:
    return {"op": "get_cwd"}


def op_probe_defense_violation(kind: str) -> dict[str, Any]:
    return {"op": "probe_defense_violation", "kind": kind}


def run_python_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    bash_type = public_api().Bash
    with bash_type(**dict(init_kwargs)) as bash:
        results: list[Any] = []
        for operation in operations:
            op = operation["op"]
            try:
                if op == "exec":
                    result = bash.exec(operation["script"], **dict(operation.get("kwargs", {})))
                    results.append(wrap_success(normalize_exec_result(result)))
                elif op == "read_text":
                    results.append(wrap_success(bash.read_text(operation["path"])))
                elif op == "read_bytes":
                    results.append(wrap_success(encode_file_value(bash.read_bytes(operation["path"]))))
                elif op == "write_text":
                    bash.write_text(operation["path"], operation["content"])
                    results.append(wrap_success(None))
                elif op == "write_bytes":
                    bash.write_bytes(operation["path"], operation["content"])
                    results.append(wrap_success(None))
                elif op == "append_text":
                    bash.fs.append_text(operation["path"], operation["content"])
                    results.append(wrap_success(None))
                elif op == "append_bytes":
                    bash.fs.append_bytes(operation["path"], operation["content"])
                    results.append(wrap_success(None))
                elif op == "exists":
                    results.append(wrap_success(bash.fs.exists(operation["path"])))
                elif op == "stat":
                    results.append(wrap_success(normalize_fs_stat(bash.fs.stat(operation["path"]))))
                elif op == "lstat":
                    results.append(wrap_success(normalize_fs_stat(bash.fs.lstat(operation["path"]))))
                elif op == "mkdir":
                    bash.fs.mkdir(operation["path"], recursive=bool(operation.get("recursive", False)))
                    results.append(wrap_success(None))
                elif op == "readdir":
                    results.append(wrap_success(bash.fs.readdir(operation["path"])))
                elif op == "readdir_with_file_types":
                    results.append(
                        wrap_success(normalize_dirent_entries(bash.fs.readdir_with_file_types(operation["path"])))
                    )
                elif op == "rm":
                    bash.fs.rm(
                        operation["path"],
                        recursive=bool(operation.get("recursive", False)),
                        force=bool(operation.get("force", False)),
                    )
                    results.append(wrap_success(None))
                elif op == "cp":
                    bash.fs.cp(
                        operation["src"],
                        operation["dest"],
                        recursive=bool(operation.get("recursive", False)),
                    )
                    results.append(wrap_success(None))
                elif op == "mv":
                    bash.fs.mv(operation["src"], operation["dest"])
                    results.append(wrap_success(None))
                elif op == "resolve_path":
                    results.append(
                        wrap_success(
                            bash.fs.resolve_path(operation["path"], base=cast(str | None, operation.get("base")))
                        )
                    )
                elif op == "get_all_paths":
                    results.append(wrap_success(bash.fs.get_all_paths()))
                elif op == "chmod":
                    bash.fs.chmod(operation["path"], int(operation["mode"]))
                    results.append(wrap_success(None))
                elif op == "symlink":
                    bash.fs.symlink(operation["target"], operation["linkPath"])
                    results.append(wrap_success(None))
                elif op == "link":
                    bash.fs.link(operation["existingPath"], operation["newPath"])
                    results.append(wrap_success(None))
                elif op == "readlink":
                    results.append(wrap_success(bash.fs.readlink(operation["path"])))
                elif op == "realpath":
                    results.append(wrap_success(bash.fs.realpath(operation["path"])))
                elif op == "utimes":
                    bash.fs.utimes(
                        operation["path"],
                        datetime.fromtimestamp(int(operation["atimeMs"]) / 1000, tz=UTC),
                        datetime.fromtimestamp(int(operation["mtimeMs"]) / 1000, tz=UTC),
                    )
                    results.append(wrap_success(None))
                elif op == "get_env":
                    results.append(wrap_success(bash.get_env()))
                elif op == "get_cwd":
                    results.append(wrap_success(bash.get_cwd()))
                elif op == "probe_defense_violation":
                    results.append(
                        wrap_success(bash._bridge.request("probe_defense_violation", {"kind": operation["kind"]}))
                    )
                else:  # pragma: no cover - defensive
                    raise AssertionError(f"unknown op: {op}")
            except Exception as error:
                results.append(normalize_operation_error(error))

        return {
            "backendVersion": bash.backend_version,
            "results": results,
        }


def run_async_python_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    async def exercise() -> dict[str, Any]:
        bash_type = public_api().AsyncBash
        async with bash_type(**dict(init_kwargs)) as bash:
            results: list[Any] = []
            for operation in operations:
                op = operation["op"]
                try:
                    if op == "exec":
                        result = await bash.exec(operation["script"], **dict(operation.get("kwargs", {})))
                        results.append(wrap_success(normalize_exec_result(result)))
                    elif op == "read_text":
                        results.append(wrap_success(await bash.read_text(operation["path"])))
                    elif op == "read_bytes":
                        results.append(wrap_success(encode_file_value(await bash.read_bytes(operation["path"]))))
                    elif op == "write_text":
                        await bash.write_text(operation["path"], operation["content"])
                        results.append(wrap_success(None))
                    elif op == "write_bytes":
                        await bash.write_bytes(operation["path"], operation["content"])
                        results.append(wrap_success(None))
                    elif op == "append_text":
                        await bash.fs.append_text(operation["path"], operation["content"])
                        results.append(wrap_success(None))
                    elif op == "append_bytes":
                        await bash.fs.append_bytes(operation["path"], operation["content"])
                        results.append(wrap_success(None))
                    elif op == "exists":
                        results.append(wrap_success(await bash.fs.exists(operation["path"])))
                    elif op == "stat":
                        results.append(wrap_success(normalize_fs_stat(await bash.fs.stat(operation["path"]))))
                    elif op == "lstat":
                        results.append(wrap_success(normalize_fs_stat(await bash.fs.lstat(operation["path"]))))
                    elif op == "mkdir":
                        await bash.fs.mkdir(
                            operation["path"],
                            recursive=bool(operation.get("recursive", False)),
                        )
                        results.append(wrap_success(None))
                    elif op == "readdir":
                        results.append(wrap_success(await bash.fs.readdir(operation["path"])))
                    elif op == "readdir_with_file_types":
                        results.append(
                            wrap_success(
                                normalize_dirent_entries(await bash.fs.readdir_with_file_types(operation["path"]))
                            )
                        )
                    elif op == "rm":
                        await bash.fs.rm(
                            operation["path"],
                            recursive=bool(operation.get("recursive", False)),
                            force=bool(operation.get("force", False)),
                        )
                        results.append(wrap_success(None))
                    elif op == "cp":
                        await bash.fs.cp(
                            operation["src"],
                            operation["dest"],
                            recursive=bool(operation.get("recursive", False)),
                        )
                        results.append(wrap_success(None))
                    elif op == "mv":
                        await bash.fs.mv(operation["src"], operation["dest"])
                        results.append(wrap_success(None))
                    elif op == "resolve_path":
                        results.append(
                            wrap_success(
                                await bash.fs.resolve_path(
                                    operation["path"], base=cast(str | None, operation.get("base"))
                                )
                            )
                        )
                    elif op == "get_all_paths":
                        results.append(wrap_success(await bash.fs.get_all_paths()))
                    elif op == "chmod":
                        await bash.fs.chmod(operation["path"], int(operation["mode"]))
                        results.append(wrap_success(None))
                    elif op == "symlink":
                        await bash.fs.symlink(operation["target"], operation["linkPath"])
                        results.append(wrap_success(None))
                    elif op == "link":
                        await bash.fs.link(operation["existingPath"], operation["newPath"])
                        results.append(wrap_success(None))
                    elif op == "readlink":
                        results.append(wrap_success(await bash.fs.readlink(operation["path"])))
                    elif op == "realpath":
                        results.append(wrap_success(await bash.fs.realpath(operation["path"])))
                    elif op == "utimes":
                        await bash.fs.utimes(
                            operation["path"],
                            datetime.fromtimestamp(int(operation["atimeMs"]) / 1000, tz=UTC),
                            datetime.fromtimestamp(int(operation["mtimeMs"]) / 1000, tz=UTC),
                        )
                        results.append(wrap_success(None))
                    elif op == "get_env":
                        results.append(wrap_success(await bash.get_env()))
                    elif op == "get_cwd":
                        results.append(wrap_success(await bash.get_cwd()))
                    elif op == "probe_defense_violation":
                        results.append(
                            wrap_success(
                                await bash.bridge_request("probe_defense_violation", {"kind": operation["kind"]})
                            )
                        )
                    else:  # pragma: no cover - defensive
                        raise AssertionError(f"unknown op: {op}")
                except Exception as error:
                    results.append(normalize_operation_error(error))

            return {
                "backendVersion": bash.backend_version,
                "results": results,
            }

    return asyncio.run(exercise())


def run_differential_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    backend_artifacts: BackendArtifacts,
    reference_init_kwargs: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    python_result = run_python_scenario(init_kwargs=init_kwargs, operations=operations)
    reference_options, reference_hooks = to_reference_bridge_init(
        init_kwargs if reference_init_kwargs is None else reference_init_kwargs,
    )
    reference_result = run_reference_scenario(
        js_entry=backend_artifacts.js_entry,
        package_json=backend_artifacts.package_json,
        init_options=reference_options,
        operations=[to_reference_operation(operation) for operation in operations],
        hooks=reference_hooks,
    )
    return python_result, reference_result


def run_async_differential_scenario(
    *,
    init_kwargs: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    backend_artifacts: BackendArtifacts,
    reference_init_kwargs: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    python_result = run_async_python_scenario(init_kwargs=init_kwargs, operations=operations)
    reference_options, reference_hooks = to_reference_bridge_init(
        init_kwargs if reference_init_kwargs is None else reference_init_kwargs,
    )
    reference_result = run_reference_scenario(
        js_entry=backend_artifacts.js_entry,
        package_json=backend_artifacts.package_json,
        init_options=reference_options,
        operations=[to_reference_operation(operation) for operation in operations],
        hooks=reference_hooks,
    )
    return python_result, reference_result


def session_snapshot_operations(*, root: str = "/workspace") -> list[dict[str, Any]]:
    return [
        op_get_cwd(),
        op_get_env(),
        op_exec(f"find {root} -maxdepth 2 -mindepth 1 | sort"),
    ]


__all__ = [
    "BackendArtifacts",
    "BYTE_TAG",
    "decode_bytes_payload",
    "encode_file_value",
    "infer_package_json_from_js_entry",
    "normalize_dirent_entries",
    "normalize_dirent_entry",
    "normalize_exec_result",
    "normalize_fs_stat",
    "normalize_operation_error",
    "op_append_bytes",
    "op_append_text",
    "op_chmod",
    "op_cp",
    "op_exec",
    "op_exists",
    "op_get_all_paths",
    "op_get_cwd",
    "op_get_env",
    "op_link",
    "op_lstat",
    "op_probe_defense_violation",
    "op_mkdir",
    "op_mv",
    "op_readdir",
    "op_readdir_with_file_types",
    "op_read_bytes",
    "op_read_text",
    "op_readlink",
    "op_realpath",
    "op_resolve_path",
    "op_rm",
    "op_stat",
    "op_symlink",
    "op_utimes",
    "op_write_bytes",
    "op_write_text",
    "public_api",
    "resolve_backend_artifacts",
    "resolve_node_command",
    "run_async_differential_scenario",
    "run_async_python_scenario",
    "run_differential_scenario",
    "run_python_scenario",
    "run_reference_scenario",
    "session_snapshot_operations",
    "to_reference_exec_options",
    "to_reference_init_options",
    "to_reference_operation",
    "wrap_success",
]
