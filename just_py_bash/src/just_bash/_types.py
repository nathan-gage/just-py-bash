from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final, Literal, NotRequired, TypeAlias

from typing_extensions import TypedDict

BYTE_TAG: Final = "__just_bash_bytes__"

FileValue: TypeAlias = str | bytes
HttpMethod: TypeAlias = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]


class BytesPayload(TypedDict):
    __just_bash_bytes__: str


EncodedFileValue: TypeAlias = str | BytesPayload


class FileInitWire(TypedDict, total=False):
    kind: Literal["file_init"]
    content: EncodedFileValue
    mode: int
    mtimeMs: int


class LazyStaticFileWire(TypedDict):
    kind: Literal["lazy_static"]
    content: EncodedFileValue


class LazyCallbackFileWire(TypedDict):
    kind: Literal["lazy_callback"]
    providerName: str


InitialFileValueWire: TypeAlias = EncodedFileValue | FileInitWire | LazyStaticFileWire | LazyCallbackFileWire


class RequestTransform(TypedDict):
    """Header overrides applied at the fetch boundary.

    Header names are runtime-defined, so a structural mapping is the most precise
    contract here.
    """

    headers: Mapping[str, str]


class AllowedUrl(TypedDict):
    url: str
    transform: NotRequired[Sequence[RequestTransform]]


AllowedUrlEntry: TypeAlias = str | AllowedUrl


class NetworkConfig(TypedDict, total=False):
    allowedUrlPrefixes: Sequence[AllowedUrlEntry]
    allowedMethods: Sequence[HttpMethod]
    dangerouslyAllowFullInternetAccess: bool
    maxRedirects: int
    timeoutMs: int
    maxResponseSize: int
    denyPrivateRanges: bool


class ProcessInfo(TypedDict, total=False):
    pid: int
    ppid: int
    uid: int
    gid: int


class ExecutionLimitsWire(TypedDict, total=False):
    maxCallDepth: int
    maxCommandCount: int
    maxLoopIterations: int
    maxAwkIterations: int
    maxSedIterations: int
    maxJqIterations: int
    maxSqliteTimeoutMs: int
    maxPythonTimeoutMs: int
    maxJsTimeoutMs: int
    maxGlobOperations: int
    maxStringLength: int
    maxArrayElements: int
    maxHeredocSize: int
    maxSubstitutionDepth: int
    maxBraceExpansionResults: int
    maxOutputSize: int
    maxFileDescriptors: int
    maxSourceDepth: int


class JavaScriptConfigWire(TypedDict, total=False):
    bootstrap: str


class DefenseInDepthConfigWire(TypedDict, total=False):
    enabled: bool
    auditMode: bool
    onViolationEnabled: bool
    excludeViolationTypes: Sequence[str]


class TraceEventWire(TypedDict, total=False):
    category: str
    name: str
    durationMs: float
    details: Mapping[str, object]


class FetchOptionsWire(TypedDict, total=False):
    method: str
    headers: Mapping[str, str]
    body: str
    followRedirects: bool
    timeoutMs: int


class FetchResultWire(TypedDict, total=False):
    status: int
    statusText: str
    headers: Mapping[str, str]
    body: str
    url: str


class SecurityViolationWire(TypedDict, total=False):
    timestamp: int
    type: str
    message: str
    path: str
    stack: str | None
    executionId: str


class InMemoryFsWire(TypedDict, total=False):
    kind: Literal["in_memory"]
    files: Mapping[str, InitialFileValueWire]


class OverlayFsWire(TypedDict, total=False):
    kind: Literal["overlay"]
    root: str
    mountPoint: str
    readOnly: bool
    maxFileReadSize: int
    allowSymlinks: bool


class ReadWriteFsWire(TypedDict, total=False):
    kind: Literal["read_write"]
    root: str
    maxFileReadSize: int
    allowSymlinks: bool


class MountConfigWire(TypedDict):
    mountPoint: str
    filesystem: FsConfigWire


class MountableFsWire(TypedDict, total=False):
    kind: Literal["mountable"]
    base: FsConfigWire
    mounts: Sequence[MountConfigWire]


FsConfigWire: TypeAlias = InMemoryFsWire | OverlayFsWire | ReadWriteFsWire | MountableFsWire


class InitOptionsWire(TypedDict, total=False):
    files: Mapping[str, InitialFileValueWire]
    env: Mapping[str, str]
    cwd: str
    fs: FsConfigWire
    executionLimits: ExecutionLimitsWire
    python: bool
    javascript: bool | JavaScriptConfigWire
    commands: Sequence[str]
    customCommandNames: Sequence[str]
    fetchEnabled: bool
    loggerEnabled: bool
    traceEnabled: bool
    coverageEnabled: bool
    defenseInDepth: bool | DefenseInDepthConfigWire
    network: NetworkConfig
    processInfo: ProcessInfo


class ExecOptionsWire(TypedDict, total=False):
    env: Mapping[str, str]
    replaceEnv: bool
    cwd: str
    rawScript: bool
    stdin: str
    args: Sequence[str]
    timeoutMs: int


class InitRequestPayload(TypedDict):
    jsEntry: str
    packageJson: str
    options: InitOptionsWire


class ExecRequestPayload(TypedDict):
    script: str
    options: ExecOptionsWire


class CustomCommandExecRequestPayload(TypedDict):
    invocationId: int
    script: str
    options: ExecOptionsWire


class CustomCommandErrorPayload(TypedDict, total=False):
    type: str
    message: str


class CustomCommandCompleteRequestPayload(TypedDict, total=False):
    invocationId: int
    result: ExecResultWire
    error: CustomCommandErrorPayload


class PathRequestPayload(TypedDict):
    path: str


class PathPairRequestPayload(TypedDict):
    src: str
    dest: str


class MkdirRequestPayload(TypedDict, total=False):
    path: str
    recursive: bool


class RmRequestPayload(TypedDict, total=False):
    path: str
    recursive: bool
    force: bool


class CpRequestPayload(TypedDict, total=False):
    src: str
    dest: str
    recursive: bool


class ChmodRequestPayload(TypedDict):
    path: str
    mode: int


class WriteTextRequestPayload(TypedDict):
    path: str
    content: str


class WriteBytesRequestPayload(TypedDict):
    path: str
    content: BytesPayload


class InitResponse(TypedDict):
    backendVersion: str | None


class InfoResponse(TypedDict):
    backendVersion: str | None
    cwd: str
    env: Mapping[str, str]


class CustomCommandContextPayload(TypedDict):
    cwd: str
    env: dict[str, str]
    stdin: str


class CustomCommandEvent(TypedDict):
    type: Literal["custom_command"]
    invocationId: int
    name: str
    args: list[str]
    context: CustomCommandContextPayload


class LazyFileEvent(TypedDict):
    type: Literal["lazy_file"]
    invocationId: int
    providerName: str


class FetchEvent(TypedDict):
    type: Literal["fetch"]
    invocationId: int
    url: str
    options: FetchOptionsWire


class LoggerEvent(TypedDict, total=False):
    type: Literal["logger"]
    level: Literal["info", "debug"]
    message: str
    data: Mapping[str, object] | None


class TraceEventMessage(TypedDict):
    type: Literal["trace"]
    event: TraceEventWire


class CoverageEvent(TypedDict):
    type: Literal["coverage"]
    feature: str


class DefenseViolationEvent(TypedDict):
    type: Literal["defense_violation"]
    violation: SecurityViolationWire


class LazyFileCompleteRequestPayload(TypedDict, total=False):
    invocationId: int
    content: EncodedFileValue
    error: CustomCommandErrorPayload


class FetchCompleteRequestPayload(TypedDict, total=False):
    invocationId: int
    result: FetchResultWire
    error: CustomCommandErrorPayload


class ExecResultWire(TypedDict, total=False):
    stdout: str
    stderr: str
    exitCode: int
    env: dict[str, str]
    metadata: dict[str, object] | None


class FsStatWire(TypedDict):
    isFile: bool
    isDirectory: bool
    isSymbolicLink: bool
    mode: int
    size: int
    mtimeMs: int


class WorkerSuccessResponse(TypedDict):
    id: int
    ok: Literal[True]
    result: object


class WorkerErrorResponse(TypedDict):
    id: int
    ok: Literal[False]
    error: object


class BackendErrorPayload(TypedDict, total=False):
    type: str
    message: str
    stack: str | None


WorkerResponse: TypeAlias = WorkerSuccessResponse | WorkerErrorResponse
