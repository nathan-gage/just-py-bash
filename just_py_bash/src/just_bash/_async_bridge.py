from __future__ import annotations

import asyncio
import inspect
import json
from asyncio.subprocess import PIPE
from collections import deque
from collections.abc import Iterator, Mapping, Sequence
from contextlib import suppress
from itertools import count
from typing import Literal, overload

from ._bridge import BackendArtifacts, resolve_backend_artifacts, resolve_node_command, write_worker_file
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
from ._custom_commands import (
    AsyncCustomCommandContext,
    AsyncCustomCommandHandlers,
    CustomCommandHandler,
    command_error_result,
    invoke_async_custom_command,
)
from ._exceptions import BackendError, BackendUnavailableError, BridgeError, BridgeTimeoutError
from ._fs import LazyFileProvider
from ._option_hooks import (
    BashLogger,
    DefenseViolationCallback,
    FeatureCoverageWriter,
    FetchCallback,
    FetchRequest,
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


def _coerce_lazy_file_content(value: object) -> str | bytes:
    if not isinstance(value, (str, bytes)):
        raise TypeError("Lazy file providers must return str, bytes, or an awaitable of either")
    return value


class AsyncNodeBridge:
    artifacts: BackendArtifacts
    backend_version: str | None
    _stderr_tail: deque[str]
    _send_lock: asyncio.Lock
    _close_lock: asyncio.Lock
    _closed: bool
    _next_id: Iterator[int]
    _pending: dict[int, asyncio.Future[WorkerResponse]]
    _custom_commands: dict[str, CustomCommandHandler]
    _lazy_file_providers: dict[str, LazyFileProvider]
    _fetch_callback: FetchCallback | None
    _logger: BashLogger | None
    _trace_callback: TraceCallback | None
    _coverage_writer: FeatureCoverageWriter | None
    _defense_violation_callback: DefenseViolationCallback | None
    _custom_command_tasks: set[asyncio.Task[None]]
    _proc: asyncio.subprocess.Process
    _stdout_task: asyncio.Task[None]
    _stderr_task: asyncio.Task[None]

    @property
    def closed(self) -> bool:
        return self._closed

    @classmethod
    async def open(
        cls,
        *,
        init_options: InitOptionsWire,
        custom_commands: AsyncCustomCommandHandlers | None = None,
        lazy_file_providers: Mapping[str, LazyFileProvider] | None = None,
        fetch_callback: FetchCallback | None = None,
        logger: BashLogger | None = None,
        trace_callback: TraceCallback | None = None,
        coverage_writer: FeatureCoverageWriter | None = None,
        defense_violation_callback: DefenseViolationCallback | None = None,
        node_command: Sequence[str] | None = None,
        js_entry: str | None = None,
        package_json: str | None = None,
    ) -> AsyncNodeBridge:
        self = cls.__new__(cls)
        self.artifacts = resolve_backend_artifacts(js_entry=js_entry, package_json=package_json)
        self.backend_version = None
        self._stderr_tail = deque(maxlen=50)
        self._send_lock = asyncio.Lock()
        self._close_lock = asyncio.Lock()
        self._closed = False
        self._next_id = count(1)
        self._pending = {}
        self._custom_commands = dict(custom_commands or {})
        self._lazy_file_providers = dict(lazy_file_providers or {})
        self._fetch_callback = fetch_callback
        self._logger = logger
        self._trace_callback = trace_callback
        self._coverage_writer = coverage_writer
        self._defense_violation_callback = defense_violation_callback
        self._custom_command_tasks = set()

        command = [*resolve_node_command(node_command), str(write_worker_file())]

        try:
            self._proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
        except OSError as exc:
            raise BackendUnavailableError(f"Failed to start the Node.js backend: {exc}") from exc

        self._stdout_task = asyncio.create_task(self._read_stdout(), name="just-py-bash-stdout")
        self._stderr_task = asyncio.create_task(self._read_stderr(), name="just-py-bash-stderr")

        init_payload: InitRequestPayload = {
            "jsEntry": str(self.artifacts.js_entry),
            "packageJson": str(self.artifacts.package_json),
            "options": init_options,
        }

        try:
            init_response = await self.request(
                "init",
                init_payload,
                timeout=60.0,
            )
        except Exception:
            await self.close()
            raise

        self.backend_version = init_response.get("backendVersion")
        return self

    @overload
    async def request(
        self,
        op: Literal["init"],
        payload: InitRequestPayload,
        *,
        timeout: float | None = None,
    ) -> InitResponse: ...

    @overload
    async def request(
        self,
        op: Literal["info"],
        payload: None = None,
        *,
        timeout: float | None = None,
    ) -> InfoResponse: ...

    @overload
    async def request(
        self,
        op: Literal["exec"],
        payload: ExecRequestPayload,
        *,
        timeout: float | None = None,
    ) -> ExecResultWire: ...

    @overload
    async def request(
        self,
        op: Literal["custom_command_exec"],
        payload: CustomCommandExecRequestPayload,
        *,
        timeout: float | None = None,
    ) -> ExecResultWire: ...

    @overload
    async def request(
        self,
        op: Literal["custom_command_complete"],
        payload: CustomCommandCompleteRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["read_text"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> str: ...

    @overload
    async def request(
        self,
        op: Literal["read_bytes"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> BytesPayload: ...

    @overload
    async def request(
        self,
        op: Literal["write_text"],
        payload: WriteTextRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["write_bytes"],
        payload: WriteBytesRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["exists"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> bool: ...

    @overload
    async def request(
        self,
        op: Literal["stat"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> FsStatWire: ...

    @overload
    async def request(
        self,
        op: Literal["mkdir"],
        payload: MkdirRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["readdir"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> list[str]: ...

    @overload
    async def request(
        self,
        op: Literal["rm"],
        payload: RmRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["cp"],
        payload: CpRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["mv"],
        payload: PathPairRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["chmod"],
        payload: ChmodRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["readlink"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> str: ...

    @overload
    async def request(
        self,
        op: Literal["realpath"],
        payload: PathRequestPayload,
        *,
        timeout: float | None = None,
    ) -> str: ...

    @overload
    async def request(
        self,
        op: Literal["lazy_file_complete"],
        payload: LazyFileCompleteRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["fetch_complete"],
        payload: FetchCompleteRequestPayload,
        *,
        timeout: float | None = None,
    ) -> None: ...

    @overload
    async def request(
        self,
        op: Literal["get_env"],
        payload: None = None,
        *,
        timeout: float | None = None,
    ) -> Mapping[str, str]: ...

    @overload
    async def request(
        self,
        op: Literal["get_cwd"],
        payload: None = None,
        *,
        timeout: float | None = None,
    ) -> str: ...

    async def request(
        self,
        op: BridgeOperation,
        payload: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> object:
        return await self.request_raw(op, payload, timeout=timeout)

    async def request_raw(
        self,
        op: BridgeOperation,
        payload: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> object:
        self._ensure_open()

        loop = asyncio.get_running_loop()
        response_future: asyncio.Future[WorkerResponse] = loop.create_future()

        async with self._send_lock:
            self._ensure_open()
            request_id = next(self._next_id)
            self._pending[request_id] = response_future

            request_message: dict[str, object] = {"id": request_id, "op": op}
            if payload is not None:
                request_message.update(payload)

            try:
                await self._write_message(request_message)
            except Exception:
                self._pending.pop(request_id, None)
                if not response_future.done():
                    response_future.cancel()
                raise

        wait_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
        try:
            response = await asyncio.wait_for(response_future, timeout=wait_timeout)
        except TimeoutError as exc:
            self._pending.pop(request_id, None)
            if not response_future.done():
                response_future.cancel()
            await self.close()
            raise BridgeTimeoutError(f"Timed out waiting for just-bash worker response to {op!r}.") from exc

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

    async def close(self) -> None:
        current_task = asyncio.current_task()

        async with self._close_lock:
            if self._closed:
                return
            self._closed = True

            self._fail_all_pending(BridgeError("just-bash bridge closed"))

            custom_command_tasks = list(self._custom_command_tasks)
            for task in custom_command_tasks:
                task.cancel()

            stdin = self._proc.stdin
            if stdin is not None and not stdin.is_closing():
                stdin.close()
                with suppress(Exception):
                    await stdin.wait_closed()

            if self._proc.returncode is None:
                with suppress(ProcessLookupError):
                    self._proc.terminate()
                try:
                    await asyncio.wait_for(self._proc.wait(), timeout=2.0)
                except TimeoutError:
                    with suppress(ProcessLookupError):
                        self._proc.kill()
                    with suppress(TimeoutError, ProcessLookupError):
                        await asyncio.wait_for(self._proc.wait(), timeout=2.0)

            background_tasks = [
                task
                for task in (self._stdout_task, self._stderr_task, *custom_command_tasks)
                if task is not current_task
            ]
            if background_tasks:
                await asyncio.gather(*background_tasks, return_exceptions=True)

    async def _write_message(self, message: Mapping[str, object]) -> None:
        stdin = self._proc.stdin
        if stdin is None:
            raise BridgeError("just-bash worker stdin is unavailable")

        try:
            body = f"{json.dumps(message, separators=(',', ':'))}\n".encode()
            stdin.write(body)
            await stdin.drain()
        except (BrokenPipeError, ConnectionResetError, OSError) as exc:
            await self.close()
            raise BridgeError(self._process_failure_message()) from exc

    async def _read_stdout(self) -> None:
        stdout = self._proc.stdout
        if stdout is None:
            self._fail_all_pending(BridgeError("just-bash worker stdout is unavailable"))
            return

        while True:
            line = await stdout.readline()
            if not line:
                break

            try:
                message = parse_worker_message(line.decode("utf-8", errors="replace"))
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
                    await self._handle_logger(logger_event)
                    continue
                if message.get("type") == "trace":
                    trace_event = parse_trace_event(message)
                    await self._handle_trace(trace_event)
                    continue
                if message.get("type") == "coverage":
                    coverage_event = parse_coverage_event(message)
                    await self._handle_coverage(coverage_event)
                    continue
                if message.get("type") == "defense_violation":
                    defense_violation_event = parse_defense_violation_event(message)
                    await self._handle_defense_violation(defense_violation_event)
                    continue
                response = parse_worker_response(message)
            except Exception as exc:
                self._fail_all_pending(exc)
                await self.close()
                return

            response_future = self._pending.pop(response["id"], None)
            if response_future is not None and not response_future.done():
                response_future.set_result(response)

        if not self._closed:
            self._fail_all_pending(BridgeError(self._process_failure_message()))

    async def _read_stderr(self) -> None:
        stderr = self._proc.stderr
        if stderr is None:
            return

        while True:
            line = await stderr.readline()
            if not line:
                return
            self._stderr_tail.append(line.decode("utf-8", errors="replace").rstrip())

    def _dispatch_custom_command(self, event: CustomCommandEvent) -> None:
        task = asyncio.create_task(
            self._handle_custom_command(event),
            name=f"just-py-bash-command-{event['name']}",
        )
        self._custom_command_tasks.add(task)
        task.add_done_callback(self._custom_command_tasks.discard)

    async def _handle_custom_command(self, event: CustomCommandEvent) -> None:
        callback = self._custom_commands.get(event["name"])
        if callback is None:
            result = command_error_result(NotImplementedError(f"Unknown custom command: {event['name']}"))
        else:
            try:
                context_payload = event["context"]
                context = AsyncCustomCommandContext(
                    _bridge=self,
                    _invocation_id=event["invocationId"],
                    cwd=context_payload["cwd"],
                    env=dict(context_payload["env"]),
                    stdin=context_payload["stdin"],
                )
                result = await invoke_async_custom_command(callback, list(event["args"]), context)
            except Exception as exc:  # pragma: no cover - exercised via contract tests
                result = command_error_result(exc)

        try:
            completion_payload: CustomCommandCompleteRequestPayload = {
                "invocationId": event["invocationId"],
                "result": result.to_wire(),
            }
            await self.request(
                "custom_command_complete",
                completion_payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except Exception:
            await self.close()

    def _fail_all_pending(self, error: BaseException) -> None:
        pending = list(self._pending.values())
        self._pending.clear()
        for response_future in pending:
            if not response_future.done():
                response_future.set_exception(error)

    def _dispatch_lazy_file(self, event: LazyFileEvent) -> None:
        task = asyncio.create_task(
            self._handle_lazy_file(event),
            name=f"just-py-bash-lazy-file-{event['providerName']}",
        )
        self._custom_command_tasks.add(task)
        task.add_done_callback(self._custom_command_tasks.discard)

    async def _handle_lazy_file(self, event: LazyFileEvent) -> None:
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
                    content = _coerce_lazy_file_content(await raw_content)
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
            await self.request(
                "lazy_file_complete",
                completion_payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except Exception:
            await self.close()

    def _dispatch_fetch(self, event: FetchEvent) -> None:
        task = asyncio.create_task(
            self._handle_fetch(event),
            name=f"just-py-bash-fetch-{event['invocationId']}",
        )
        self._custom_command_tasks.add(task)
        task.add_done_callback(self._custom_command_tasks.discard)

    async def _handle_fetch(self, event: FetchEvent) -> None:
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
                    resolved = await raw_result
                else:
                    resolved = raw_result
                completion_payload = {
                    "invocationId": event["invocationId"],
                    "result": normalize_fetch_result(resolved).to_wire(),
                }
            except Exception as exc:  # pragma: no cover - exercised via public api tests
                completion_payload = {
                    "invocationId": event["invocationId"],
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }

        try:
            await self.request("fetch_complete", completion_payload, timeout=DEFAULT_TIMEOUT_SECONDS)
        except Exception:
            await self.close()

    async def _handle_logger(self, event: LoggerEvent) -> None:
        logger = self._logger
        if logger is None:
            return
        method = getattr(logger, event.get("level", "info"), None)
        if not callable(method):
            return
        result = method(event.get("message", ""), event.get("data"))
        if inspect.isawaitable(result):
            await result

    async def _handle_trace(self, event: TraceEventMessage) -> None:
        callback = self._trace_callback
        if callback is None:
            return
        result = callback(TraceEvent.from_wire(event["event"]))
        if inspect.isawaitable(result):
            await result

    async def _handle_coverage(self, event: CoverageEvent) -> None:
        writer = self._coverage_writer
        if writer is None:
            return
        result = writer.hit(event["feature"])
        if inspect.isawaitable(result):
            await result

    async def _handle_defense_violation(self, event: DefenseViolationEvent) -> None:
        callback = self._defense_violation_callback
        if callback is None:
            return
        result = callback(SecurityViolation.from_wire(event["violation"]))
        if inspect.isawaitable(result):
            await result

    def _ensure_open(self) -> None:
        if self._closed:
            raise BridgeError("just-bash bridge is closed")
        if self._proc.returncode is not None:
            self._closed = True
            raise BridgeError(self._process_failure_message())

    def _process_failure_message(self) -> str:
        return_code = self._proc.returncode
        stderr = "\n".join(self._stderr_tail).strip()
        message = "just-bash worker exited unexpectedly"
        if return_code is not None:
            message += f" with status {return_code}"
        if stderr:
            message += f":\n{stderr}"
        return message
