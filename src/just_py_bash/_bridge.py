from __future__ import annotations

import base64
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import threading
import weakref
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from itertools import count
from pathlib import Path
from queue import Empty, Queue
from typing import Final, Literal, TypeAlias, overload

from pydantic import TypeAdapter, ValidationError

from ._exceptions import BackendError, BackendUnavailableError, BridgeError, BridgeTimeoutError
from ._types import (
    BYTE_TAG,
    BackendErrorPayload,
    BytesPayload,
    EncodedFileValue,
    ExecRequestPayload,
    ExecResultWire,
    FileValue,
    InfoResponse,
    InitOptionsWire,
    InitRequestPayload,
    InitResponse,
    PathRequestPayload,
    WorkerResponse,
    WriteBytesRequestPayload,
    WriteTextRequestPayload,
)
from ._worker_source import WORKER_SOURCE

_DEFAULT_TIMEOUT_SECONDS = 30.0
BridgeOperation: TypeAlias = Literal[
    "exec",
    "get_cwd",
    "get_env",
    "info",
    "init",
    "read_bytes",
    "read_text",
    "write_bytes",
    "write_text",
]
_WORKER_RESPONSE_ADAPTER: Final[TypeAdapter[WorkerResponse]] = TypeAdapter(WorkerResponse)
_BACKEND_ERROR_ADAPTER: Final[TypeAdapter[BackendErrorPayload]] = TypeAdapter(BackendErrorPayload)


@dataclass(slots=True, frozen=True)
class BackendArtifacts:
    js_entry: Path
    package_json: Path


_worker_path_lock = threading.Lock()
_worker_path_cache: Path | None = None


def _parse_worker_response(line: str) -> WorkerResponse:
    try:
        return _WORKER_RESPONSE_ADAPTER.validate_json(line)
    except ValidationError as exc:  # pragma: no cover - defensive bridge failure
        raise BridgeError(f"Failed to decode just-bash worker response: {exc}: {line!r}") from exc


def _parse_backend_error(raw_error: object) -> BackendErrorPayload:
    try:
        return _BACKEND_ERROR_ADAPTER.validate_python(raw_error)
    except ValidationError:
        if isinstance(raw_error, str):
            return {"message": raw_error}
        return {}


def write_worker_file() -> Path:
    global _worker_path_cache

    with _worker_path_lock:
        if _worker_path_cache is not None and _worker_path_cache.exists():
            return _worker_path_cache

        digest = sha256(WORKER_SOURCE.encode("utf-8")).hexdigest()[:16]
        worker_dir = Path(tempfile.gettempdir()) / "just-py-bash"
        worker_dir.mkdir(parents=True, exist_ok=True)
        worker_path = worker_dir / f"worker-{digest}.mjs"
        if not worker_path.exists() or worker_path.read_text(encoding="utf-8") != WORKER_SOURCE:
            worker_path.write_text(WORKER_SOURCE, encoding="utf-8")
        _worker_path_cache = worker_path
        return worker_path


def resolve_node_command(node_command: Sequence[str] | None = None) -> list[str]:
    if node_command:
        return [str(part) for part in node_command]

    if configured := os.environ.get("JUST_PY_BASH_NODE"):
        return shlex.split(configured)

    node = shutil.which("node")
    if not node:
        raise BackendUnavailableError(
            "Could not find a Node.js executable. Install Node.js or set "
            "JUST_PY_BASH_NODE to the command that should run the backend.",
        )
    return [node]


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
            else js_entry_path.parent.parent / "package.json"
        )
        if not js_entry_path.exists():
            raise BackendUnavailableError(f"just-bash entrypoint not found: {js_entry_path}")
        if not package_json_path.exists():
            raise BackendUnavailableError(f"just-bash package metadata not found: {package_json_path}")
        return BackendArtifacts(js_entry=js_entry_path, package_json=package_json_path)

    env_js_entry = os.environ.get("JUST_PY_BASH_JS_ENTRY")
    env_package_json = os.environ.get("JUST_PY_BASH_PACKAGE_JSON")
    if env_js_entry:
        return resolve_backend_artifacts(
            js_entry=env_js_entry,
            package_json=env_package_json,
        )

    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parents[1]
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
        "Or point the wrapper at a different artifact with JUST_PY_BASH_JS_ENTRY "
        "and JUST_PY_BASH_PACKAGE_JSON."
    )


class NodeBridge:
    @property
    def closed(self) -> bool:
        return self._closed

    def __init__(
        self,
        *,
        init_options: InitOptionsWire,
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
        self._call_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._closed = False
        self._next_id = count(1)
        self._pending: dict[int, Queue[WorkerResponse | BaseException]] = {}

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
    def _finalize_process(proc: subprocess.Popen[str]) -> None:
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                NodeBridge._close_process_pipes(proc)
                return
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except OSError:
                    pass
        NodeBridge._close_process_pipes(proc)

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True

            self._fail_all_pending(BridgeError("just-bash bridge closed"))

            if self._proc.poll() is None:
                try:
                    self._proc.terminate()
                except OSError:
                    pass
                try:
                    self._proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    try:
                        self._proc.kill()
                    except OSError:
                        pass
                    try:
                        self._proc.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        pass

            self._close_process_pipes(self._proc)
            self._stdout_thread.join(timeout=0.2)
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
        with self._call_lock:
            self._ensure_open()
            request_id = next(self._next_id)
            response_queue: Queue[WorkerResponse | BaseException] = Queue(maxsize=1)
            with self._pending_lock:
                self._pending[request_id] = response_queue

            request_message: dict[str, object] = {"id": request_id, "op": op}
            if payload is not None:
                request_message.update(payload)

            try:
                self._send(request_message)
            except Exception:
                with self._pending_lock:
                    self._pending.pop(request_id, None)
                raise

            wait_timeout = timeout if timeout is not None else _DEFAULT_TIMEOUT_SECONDS
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
                    error_details = _parse_backend_error(raw_error)
                    detail_message = error_details.get("message")
                    error_message = (
                        detail_message if isinstance(detail_message, str) else f"Backend operation {op!r} failed"
                    )
                    error_type_value = error_details.get("type")
                    error_type = error_type_value if isinstance(error_type_value, str) else None
                    raise BackendError(error_message, error_type=error_type, details=error_details)
                case _:
                    raise BridgeError("Received an invalid response from the just-bash worker")

    def _send(self, message: Mapping[str, object]) -> None:
        stdin = self._proc.stdin
        if stdin is None:
            raise BridgeError("just-bash worker stdin is unavailable")
        try:
            stdin.write(json.dumps(message, separators=(",", ":")))
            stdin.write("\n")
            stdin.flush()
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
                response = _parse_worker_response(line)
            except BridgeError as exc:
                self._fail_all_pending(exc)
                return

            with self._pending_lock:
                response_queue = self._pending.pop(response["id"], None)
            if response_queue is not None:
                response_queue.put(response)

        if not self._closed:
            self._fail_all_pending(BridgeError(self._process_failure_message()))

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


@overload
def encode_file_value(value: str) -> str: ...


@overload
def encode_file_value(value: bytes) -> BytesPayload: ...


def encode_file_value(value: FileValue) -> EncodedFileValue:
    if isinstance(value, bytes):
        return {BYTE_TAG: base64.b64encode(value).decode("ascii")}
    return value


def decode_bytes_payload(payload: BytesPayload) -> bytes:
    return base64.b64decode(payload[BYTE_TAG].encode("ascii"))
