from __future__ import annotations

import asyncio
import ctypes
import inspect
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import threading
import weakref
from collections import deque
from collections.abc import Awaitable, Mapping, Sequence
from ctypes import wintypes
from dataclasses import dataclass
from hashlib import sha256
from itertools import count
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Literal, cast, overload

from ._bridge_protocol import (
    DEFAULT_TIMEOUT_SECONDS,
    BridgeOperation,
    parse_backend_error,
    parse_coverage_event,
    parse_custom_command_event,
    parse_defense_violation_event,
    parse_fetch_event,
    parse_lazy_file_event,
    parse_logger_event,
    parse_trace_event,
    parse_worker_message,
    parse_worker_response,
)
from ._codec import encode_file_value
from ._custom_commands import CustomCommandContext, CustomCommandHandlers, command_error_result, invoke_custom_command
from ._exceptions import BackendError, BackendUnavailableError, BridgeError, BridgeTimeoutError
from ._fs import LazyFileProvider
from ._node_provider import resolve_bundled_node_command
from ._option_hooks import (
    BashLogger,
    DefenseViolationCallback,
    FeatureCoverageWriter,
    FetchCallback,
    FetchRequest,
    FetchReturn,
    SecurityViolation,
    TraceCallback,
    TraceEvent,
    normalize_fetch_result,
)
from ._types import (
    BytesPayload,
    ChmodRequestPayload,
    CoverageEvent,
    CpRequestPayload,
    CustomCommandCompleteRequestPayload,
    CustomCommandEvent,
    CustomCommandExecRequestPayload,
    DefenseViolationEvent,
    ExecRequestPayload,
    ExecResultWire,
    FetchCompleteRequestPayload,
    FetchEvent,
    FsStatWire,
    InfoResponse,
    InitOptionsWire,
    InitRequestPayload,
    InitResponse,
    LazyFileCompleteRequestPayload,
    LazyFileEvent,
    LoggerEvent,
    MkdirRequestPayload,
    PathPairRequestPayload,
    PathRequestPayload,
    RmRequestPayload,
    TraceEventMessage,
    WorkerResponse,
    WriteBytesRequestPayload,
    WriteTextRequestPayload,
)
from ._worker_source import WORKER_SOURCE


@dataclass(slots=True, frozen=True)
class BackendArtifacts:
    js_entry: Path
    package_json: Path


_worker_path_lock = threading.Lock()
_worker_path_cache: Path | None = None


def write_worker_file() -> Path:
    global _worker_path_cache

    with _worker_path_lock:
        if _worker_path_cache is not None and _worker_path_cache.exists():
            return _worker_path_cache

        digest = sha256(WORKER_SOURCE.encode("utf-8")).hexdigest()[:16]
        worker_dir = Path(tempfile.gettempdir()) / "just-py-bash"
        worker_dir.mkdir(parents=True, exist_ok=True)
        worker_path = worker_dir / f"worker-{digest}.mjs"
        # Filename embeds the content digest, so existence implies correctness.
        if not worker_path.exists():
            worker_path.write_text(WORKER_SOURCE, encoding="utf-8")
        _worker_path_cache = worker_path
        return worker_path


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
        raise BackendUnavailableError(f"Could not parse JUST_BASH_NODE command: {command!r}")

    try:
        return [argv[index] for index in range(argc.value)]
    finally:
        local_free(argv)


def resolve_node_command(node_command: Sequence[str] | None = None) -> list[str]:
    if node_command:
        return [str(part) for part in node_command]

    if configured := os.environ.get("JUST_BASH_NODE"):
        return split_command_string(configured)

    bundled = resolve_bundled_node_command()
    if bundled is not None:
        return bundled

    node = shutil.which("node")
    if not node:
        raise BackendUnavailableError(
            "Could not find a Node.js executable. Install Node.js, install just-py-bash[node], or set "
            "JUST_BASH_NODE to the command that should run the backend.",
        )
    return [node]


def infer_package_json_from_js_entry(js_entry_path: Path) -> Path:
    for parent in js_entry_path.parents:
        candidate = parent / "package.json"
        if candidate.exists():
            return candidate.resolve()
    return (js_entry_path.parent.parent / "package.json").resolve()


def resolve_backend_artifacts(
    *,
    js_entry: str | os.PathLike[str] | None = None,
    package_json: str | os.PathLike[str] | None = None,
) -> BackendArtifacts:
    if js_entry is not None:
        js_entry_path = Path(js_entry).expanduser().resolve()
        package_json_path = (
            Path(package_json).expanduser().resolve()
            if package_json is not None
            else infer_package_json_from_js_entry(js_entry_path)
        )
        if not js_entry_path.exists():
            raise BackendUnavailableError(f"just-bash entrypoint not found: {js_entry_path}")
        if not package_json_path.exists():
            raise BackendUnavailableError(f"just-bash package metadata not found: {package_json_path}")
        return BackendArtifacts(js_entry=js_entry_path, package_json=package_json_path)

    env_js_entry = os.environ.get("JUST_BASH_JS_ENTRY")
    env_package_json = os.environ.get("JUST_BASH_PACKAGE_JSON")
    if env_js_entry:
        return resolve_backend_artifacts(
            js_entry=env_js_entry,
            package_json=env_package_json,
        )

    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parents[2]
    candidate_roots = [
        package_dir / "_vendor" / "just-bash",
        repo_root / "vendor" / "just-bash",
    ]

    candidate_entries = ("dist/index.js", "dist/bundle/index.js")
    for root in candidate_roots:
        package_json_path = root / "package.json"
        for entry in candidate_entries:
            js_entry_path = root / entry
            if js_entry_path.exists() and package_json_path.exists():
                return BackendArtifacts(
                    js_entry=js_entry_path.resolve(),
                    package_json=package_json_path.resolve(),
                )

    searched = "\n".join(f"  - {root / entry}" for root in candidate_roots for entry in candidate_entries)
    raise BackendUnavailableError(
        "Could not find a built just-bash backend. Searched:\n"
        f"{searched}\n\n"
        "For development in this repo, build the vendored checkout first:\n"
        "  (cd vendor/just-bash && pnpm install && pnpm build)\n\n"
        "Or point the wrapper at a different artifact with JUST_BASH_JS_ENTRY "
        "and JUST_BASH_PACKAGE_JSON."
    )


async def _await_lazy_file_result(result: Awaitable[str | bytes]) -> str | bytes:
    return await result


async def _await_fetch_result(result: Awaitable[object]) -> object:
    return await result


def _coerce_lazy_file_content(value: object) -> str | bytes:
    if not isinstance(value, (str, bytes)):
        raise TypeError("Lazy file providers must return str, bytes, or an awaitable of either")
    return value


class NodeBridge:
    @property
    def closed(self) -> bool:
        return self._closed

    def __init__(
        self,
        *,
        init_options: InitOptionsWire,
        custom_commands: CustomCommandHandlers | None = None,
        lazy_file_providers: Mapping[str, LazyFileProvider] | None = None,
        fetch_callback: FetchCallback | None = None,
        logger: BashLogger | None = None,
        trace_callback: TraceCallback | None = None,
        coverage_writer: FeatureCoverageWriter | None = None,
        defense_violation_callback: DefenseViolationCallback | None = None,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> None:
        self.artifacts = resolve_backend_artifacts(
            js_entry=js_entry,
            package_json=package_json,
        )
        self.backend_version: str | None = None
        self._stderr_tail: deque[str] = deque(maxlen=50)
        self._pending_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._closed = False
        self._next_id = count(1)
        self._pending: dict[int, Queue[WorkerResponse | BaseException]] = {}
        self._custom_commands = dict(custom_commands or {})
        self._lazy_file_providers = dict(lazy_file_providers or {})
        self._fetch_callback = fetch_callback
        self._logger = logger
        self._trace_callback = trace_callback
        self._coverage_writer = coverage_writer
        self._defense_violation_callback = defense_violation_callback

        command = [*resolve_node_command(node_command), str(write_worker_file())]

        try:
            self._proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            raise BackendUnavailableError(f"Failed to start the Node.js backend: {exc}") from exc

        self._stdout_thread = threading.Thread(
            target=self._read_stdout,
            name="just-py-bash-stdout",
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr,
            name="just-py-bash-stderr",
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()
        self._finalizer = weakref.finalize(self, self._finalize_process, self._proc)

        try:
            init_response = self.request(
                "init",
                {
                    "jsEntry": str(self.artifacts.js_entry),
                    "packageJson": str(self.artifacts.package_json),
                    "options": init_options,
                },
                timeout=60.0,
            )
        except Exception:
            self.close()
            raise

        self.backend_version = init_response.get("backendVersion")

    @staticmethod
    def _close_process_pipes(proc: subprocess.Popen[str]) -> None:
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is None or stream.closed:
                continue
            try:
                stream.close()
            except OSError:
                pass

    @staticmethod
    def _finalize_process(proc: subprocess.Popen[str], wait_timeout: float = 1.0) -> None:
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                NodeBridge._close_process_pipes(proc)
                return
            try:
                proc.wait(timeout=wait_timeout)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except OSError:
                    pass
                else:
                    try:
                        proc.wait(timeout=wait_timeout)
                    except subprocess.TimeoutExpired:
                        pass
        NodeBridge._close_process_pipes(proc)

    def close(self) -> None:
        current_thread = threading.current_thread()

        with self._close_lock:
            if self._closed:
                return
            self._closed = True

            self._fail_all_pending(BridgeError("just-bash bridge closed"))
            self._finalize_process(self._proc, wait_timeout=2.0)
            if self._stdout_thread is not current_thread:
                self._stdout_thread.join(timeout=0.2)
            if self._stderr_thread is not current_thread:
                self._stderr_thread.join(timeout=0.2)
            self._finalizer.detach()

    @overload
    def request(
        self,
        op: Literal["init"],
        payload: InitRequestPayload,
        *,
        timeout: float | None = None,
    ) -> InitResponse: ...

    @overload
    def request(
        self,
        op: Literal["info"],
        payload: None = None,
        *,
        timeout: float | None = None,
    ) -> InfoResponse: ...

    @overload
    def request(
        self,
        op: Literal["exec"],
        payload: ExecRequestPayload,
        *,
        timeout: float | None = None,
    ) -> ExecResultWire: ...

    @overload
    def request(
        self,
        op: Literal["custom_command_exec"],
        payload: CustomCommandExecRequestPayload,
        *,
        timeout: float | None = None,
    ) -> ExecResultWire: ...

    @overload
    def request(
        self,
        op: Literal["custom_command_complete"],
        payload: CustomCommandCompleteRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["read_text"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> str: ...

    @overload
    def request(
        self,
        op: Literal["read_bytes"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> BytesPayload: ...

    @overload
    def request(
        self,
        op: Literal["write_text"],
        payload: WriteTextRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["write_bytes"],
        payload: WriteBytesRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["exists"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> bool: ...

    @overload
    def request(
        self,
        op: Literal["stat"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> FsStatWire: ...

    @overload
    def request(
        self,
        op: Literal["mkdir"],
        payload: MkdirRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["readdir"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> list[str]: ...

    @overload
    def request(
        self,
        op: Literal["rm"],
        payload: RmRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["cp"],
        payload: CpRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["mv"],
        payload: PathPairRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["chmod"],
        payload: ChmodRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["readlink"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> str: ...

    @overload
    def request(
        self,
        op: Literal["realpath"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> str: ...

    @overload
    def request(
        self,
        op: Literal["lazy_file_complete"],
        payload: LazyFileCompleteRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["fetch_complete"],
        payload: FetchCompleteRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    def request(
        self,
        op: Literal["get_env"],
        payload: None = None,
        *,
        timeout: float | None = None,
    ) -> Mapping[str, str]: ...

    @overload
    def request(
        self,
        op: Literal["get_cwd"],
        payload: None = None,
        *,
        timeout: float | None = None,
    ) -> str: ...

    def request(
        self,
        op: BridgeOperation,
        payload: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> object:
        self._ensure_open()

        response_queue: Queue[WorkerResponse | BaseException] = Queue(maxsize=1)
        with self._send_lock:
            self._ensure_open()
            request_id = next(self._next_id)
            with self._pending_lock:
                self._pending[request_id] = response_queue

            request_message: dict[str, object] = {"id": request_id, "op": op}
            if payload is not None:
                request_message.update(payload)

            try:
                self._write_message(request_message)
            except Exception:
                with self._pending_lock:
                    self._pending.pop(request_id, None)
                raise

        wait_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
        try:
            response = response_queue.get(timeout=wait_timeout)
        except Empty as exc:
            with self._pending_lock:
                self._pending.pop(request_id, None)
            self.close()
            raise BridgeTimeoutError(f"Timed out waiting for just-bash worker response to {op!r}.") from exc

        if isinstance(response, BaseException):
            raise response

        match response:
            case {"ok": True, "result": result}:
                return result
            case {"ok": False, "error": raw_error}:
                error_details = parse_backend_error(raw_error)
                error_message = error_details.get("message") or f"Backend operation {op!r} failed"
                raise BackendError(
                    error_message,
                    error_type=error_details.get("type"),
                    details=error_details,
                )
            case _:
                raise BridgeError("Received an invalid response from the just-bash worker")

    def _write_message(self, message: Mapping[str, object]) -> None:
        stdin = self._proc.stdin
        if stdin is None:
            raise BridgeError("just-bash worker stdin is unavailable")
        try:
            print(json.dumps(message, separators=(",", ":")), file=stdin, flush=True)
        except OSError as exc:
            self.close()
            raise BridgeError(self._process_failure_message()) from exc

    def _read_stdout(self) -> None:
        stdout = self._proc.stdout
        if stdout is None:
            self._fail_all_pending(BridgeError("just-bash worker stdout is unavailable"))
            return

        for line in stdout:
            try:
                message = parse_worker_message(line)
                if message.get("type") == "custom_command":
                    custom_command_event = parse_custom_command_event(message)
                    self._dispatch_custom_command(custom_command_event)
                    continue
                if message.get("type") == "lazy_file":
                    lazy_file_event = parse_lazy_file_event(message)
                    self._dispatch_lazy_file(lazy_file_event)
                    continue
                if message.get("type") == "fetch":
                    fetch_event = parse_fetch_event(message)
                    self._dispatch_fetch(fetch_event)
                    continue
                if message.get("type") == "logger":
                    logger_event = parse_logger_event(message)
                    self._handle_logger(logger_event)
                    continue
                if message.get("type") == "trace":
                    trace_event = parse_trace_event(message)
                    self._handle_trace(trace_event)
                    continue
                if message.get("type") == "coverage":
                    coverage_event = parse_coverage_event(message)
                    self._handle_coverage(coverage_event)
                    continue
                if message.get("type") == "defense_violation":
                    defense_violation_event = parse_defense_violation_event(message)
                    self._handle_defense_violation(defense_violation_event)
                    continue
                response = parse_worker_response(message)
            except Exception as exc:
                self._fail_all_pending(exc)
                self.close()
                return

            with self._pending_lock:
                response_queue = self._pending.pop(response["id"], None)
            if response_queue is not None:
                response_queue.put(response)

        if not self._closed:
            self._fail_all_pending(BridgeError(self._process_failure_message()))

    def _dispatch_custom_command(self, event: CustomCommandEvent) -> None:
        thread = threading.Thread(
            target=self._handle_custom_command,
            args=(event,),
            name=f"just-py-bash-command-{event['name']}",
            daemon=True,
        )
        thread.start()

    def _handle_custom_command(self, event: CustomCommandEvent) -> None:
        callback = self._custom_commands.get(event["name"])
        if callback is None:
            result = command_error_result(NotImplementedError(f"Unknown custom command: {event['name']}"))
        else:
            try:
                context_payload = event["context"]
                context = CustomCommandContext(
                    _bridge=self,
                    _invocation_id=event["invocationId"],
                    cwd=context_payload["cwd"],
                    env=dict(context_payload["env"]),
                    stdin=context_payload["stdin"],
                )
                result = invoke_custom_command(callback, list(event["args"]), context)
            except Exception as exc:  # pragma: no cover - exercised via contract tests
                result = command_error_result(exc)

        try:
            completion_payload: CustomCommandCompleteRequestPayload = {
                "invocationId": event["invocationId"],
                "result": result.to_wire(),
            }
            self.request(
                "custom_command_complete",
                completion_payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except Exception:
            self.close()

    def _dispatch_lazy_file(self, event: LazyFileEvent) -> None:
        thread = threading.Thread(
            target=self._handle_lazy_file,
            args=(event,),
            name=f"just-py-bash-lazy-file-{event['providerName']}",
            daemon=True,
        )
        thread.start()

    def _handle_lazy_file(self, event: LazyFileEvent) -> None:
        provider = self._lazy_file_providers.get(event["providerName"])
        if provider is None:
            completion_payload: LazyFileCompleteRequestPayload = {
                "invocationId": event["invocationId"],
                "error": {"message": f"Unknown lazy file provider: {event['providerName']}"},
            }
        else:
            try:
                raw_content: object = provider()
                if inspect.isawaitable(raw_content):
                    content = asyncio.run(_await_lazy_file_result(raw_content))
                else:
                    content = _coerce_lazy_file_content(raw_content)
                completion_payload = {
                    "invocationId": event["invocationId"],
                    "content": encode_file_value(content),
                }
            except Exception as exc:  # pragma: no cover - exercised via public api tests
                completion_payload = {
                    "invocationId": event["invocationId"],
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }

        try:
            self.request(
                "lazy_file_complete",
                completion_payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except Exception:
            self.close()

    def _dispatch_fetch(self, event: FetchEvent) -> None:
        thread = threading.Thread(
            target=self._handle_fetch,
            args=(event,),
            name=f"just-py-bash-fetch-{event['invocationId']}",
            daemon=True,
        )
        thread.start()

    def _handle_fetch(self, event: FetchEvent) -> None:
        callback = self._fetch_callback
        if callback is None:
            completion_payload: FetchCompleteRequestPayload = {
                "invocationId": event["invocationId"],
                "error": {"message": "No fetch callback configured"},
            }
        else:
            try:
                request = FetchRequest.from_wire(event["url"], event.get("options"))
                raw_result: object = callback(request)
                if inspect.isawaitable(raw_result):
                    resolved = asyncio.run(_await_fetch_result(raw_result))
                else:
                    resolved = raw_result
                completion_payload = {
                    "invocationId": event["invocationId"],
                    "result": normalize_fetch_result(cast(FetchReturn, resolved)).to_wire(),
                }
            except Exception as exc:  # pragma: no cover - exercised via public api tests
                completion_payload = {
                    "invocationId": event["invocationId"],
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }

        try:
            self.request("fetch_complete", completion_payload, timeout=DEFAULT_TIMEOUT_SECONDS)
        except Exception:
            self.close()

    def _handle_logger(self, event: LoggerEvent) -> None:
        logger = self._logger
        if logger is None:
            return
        method_name = event.get("level", "info")
        method = getattr(logger, method_name, None)
        if not callable(method):
            return
        result = method(event.get("message", ""), event.get("data"))
        if inspect.isawaitable(result):
            asyncio.run(_await_fetch_result(result))

    def _handle_trace(self, event: TraceEventMessage) -> None:
        callback = self._trace_callback
        if callback is None:
            return
        result = callback(TraceEvent.from_wire(event["event"]))
        if inspect.isawaitable(result):
            asyncio.run(_await_fetch_result(result))

    def _handle_coverage(self, event: CoverageEvent) -> None:
        writer = self._coverage_writer
        if writer is None:
            return
        result = writer.hit(event["feature"])
        if inspect.isawaitable(result):
            asyncio.run(_await_fetch_result(result))

    def _handle_defense_violation(self, event: DefenseViolationEvent) -> None:
        callback = self._defense_violation_callback
        if callback is None:
            return
        result = callback(SecurityViolation.from_wire(event["violation"]))
        if inspect.isawaitable(result):
            asyncio.run(_await_fetch_result(result))

    def _read_stderr(self) -> None:
        stderr = self._proc.stderr
        if stderr is None:
            return
        for line in stderr:
            self._stderr_tail.append(line.rstrip())

    def _fail_all_pending(self, error: BaseException) -> None:
        with self._pending_lock:
            pending = list(self._pending.values())
            self._pending.clear()
        for response_queue in pending:
            response_queue.put(error)

    def _ensure_open(self) -> None:
        if self._closed:
            raise BridgeError("just-bash bridge is closed")
        if self._proc.poll() is not None:
            self._closed = True
            raise BridgeError(self._process_failure_message())

    def _process_failure_message(self) -> str:
        return_code = self._proc.poll()
        stderr = "\n".join(self._stderr_tail).strip()
        message = "just-bash worker exited unexpectedly"
        if return_code is not None:
            message += f" with status {return_code}"
        if stderr:
            message += f":\n{stderr}"
        return message
