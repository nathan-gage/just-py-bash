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
from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from itertools import count
from pathlib import Path
from queue import Empty, Queue
from typing import Any, cast

from ._exceptions import (
    BackendError,
    BackendUnavailableError,
    BridgeError,
    BridgeTimeoutError,
)
from ._worker_source import WORKER_SOURCE

BYTE_TAG = "__just_py_bash_bytes__"
_DEFAULT_TIMEOUT_SECONDS = 30.0


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
        init_options: dict[str, Any],
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
        self._pending: dict[int, Queue[dict[str, Any] | BaseException]] = {}

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
            result = self.request(
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

        self.backend_version = result.get("backendVersion")

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

    def request(
        self,
        op: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
    ) -> Any:
        with self._call_lock:
            self._ensure_open()
            request_id = next(self._next_id)
            response_queue: Queue[dict[str, Any] | BaseException] = Queue(maxsize=1)
            with self._pending_lock:
                self._pending[request_id] = response_queue

            message = {"id": request_id, "op": op}
            if payload:
                message.update(payload)

            try:
                self._send(message)
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

            if response.get("ok"):
                return response.get("result")

            raw_error = response.get("error")
            error: dict[str, Any] = {}
            if isinstance(raw_error, dict):
                for key, value in cast(dict[object, object], raw_error).items():
                    error[str(key)] = value

            message = error.get("message")
            if not isinstance(message, str):
                message = f"Backend operation {op!r} failed"

            error_type = error.get("type")
            if not isinstance(error_type, str):
                error_type = None

            raise BackendError(
                message,
                error_type=error_type,
                details=error,
            )

    def _send(self, message: dict[str, Any]) -> None:
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
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                self._fail_all_pending(BridgeError(f"Failed to decode just-bash worker response: {exc}: {line!r}"))
                return

            request_id = message.get("id")
            if not isinstance(request_id, int):
                continue

            with self._pending_lock:
                response_queue = self._pending.pop(request_id, None)
            if response_queue is not None:
                response_queue.put(message)

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


def encode_file_value(value: str | bytes) -> str | dict[str, str]:
    if isinstance(value, bytes):
        return {
            BYTE_TAG: base64.b64encode(value).decode("ascii"),
        }
    return value


def decode_bytes_payload(payload: dict[str, str]) -> bytes:
    return base64.b64decode(payload[BYTE_TAG].encode("ascii"))
