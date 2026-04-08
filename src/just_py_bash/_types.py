from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Final, Literal, NotRequired, Protocol, TypeAlias, TypeGuard

from typing_extensions import TypedDict

BYTE_TAG: Final = "__just_py_bash_bytes__"

FileValue: TypeAlias = str | bytes
HttpMethod: TypeAlias = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]


class BytesPayload(TypedDict):
    __just_py_bash_bytes__: str


EncodedFileValue: TypeAlias = str | BytesPayload


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


class InitOptionsWire(TypedDict, total=False):
    files: Mapping[str, EncodedFileValue]
    env: Mapping[str, str]
    cwd: str
    executionLimits: ExecutionLimitsWire
    python: bool
    javascript: bool | JavaScriptConfigWire
    commands: Sequence[str]
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


class PathRequestPayload(TypedDict):
    path: str


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


class ExecResultWire(TypedDict, total=False):
    stdout: str
    stderr: str
    exitCode: int
    env: dict[str, str]
    metadata: dict[str, object] | None


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


class ObjectItems(Protocol):
    def items(self) -> Iterable[tuple[object, object]]: ...


class StringObjectItems(Protocol):
    def items(self) -> Iterable[tuple[str, object]]: ...


class StringStringItems(Protocol):
    def items(self) -> Iterable[tuple[str, str]]: ...


def has_object_items(value: object) -> TypeGuard[ObjectItems]:
    return isinstance(value, Mapping)


def is_string_object_mapping(value: object) -> TypeGuard[StringObjectItems]:
    return has_object_items(value) and all(isinstance(key, str) for key, _ in value.items())


def is_string_string_mapping(value: object) -> TypeGuard[StringStringItems]:
    return has_object_items(value) and all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    )


def to_string_object_dict(value: object) -> dict[str, object] | None:
    if not is_string_object_mapping(value):
        return None
    return dict(value.items())


def to_string_string_dict(value: object) -> dict[str, str] | None:
    if not is_string_string_mapping(value):
        return None
    return dict(value.items())
