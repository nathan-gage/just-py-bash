from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import count
from typing import TypeAlias

from ._codec import encode_file_value
from ._types import (
    DirentEntryWire,
    FileInitWire,
    FileValue,
    FsConfigWire,
    FsStatWire,
    InitialFileValueWire,
    InMemoryFsWire,
    LazyCallbackFileWire,
    LazyStaticFileWire,
    MountableFsWire,
    MountConfigWire,
    OverlayFsWire,
    ReadWriteFsWire,
)

LazyFileProvider: TypeAlias = Callable[[], FileValue | Awaitable[FileValue]]
LazyFileSource: TypeAlias = FileValue | LazyFileProvider


@dataclass(slots=True, kw_only=True)
class FileInit:
    content: FileValue
    mode: int | None = None
    mtime: datetime | None = None


@dataclass(slots=True)
class LazyFile:
    provider: LazyFileSource


@dataclass(slots=True, frozen=True)
class DirentEntry:
    name: str
    is_file: bool
    is_directory: bool
    is_symbolic_link: bool

    @classmethod
    def from_wire(cls, payload: DirentEntryWire) -> DirentEntry:
        return cls(
            name=str(payload["name"]),
            is_file=bool(payload["isFile"]),
            is_directory=bool(payload["isDirectory"]),
            is_symbolic_link=bool(payload["isSymbolicLink"]),
        )

    def to_wire(self) -> DirentEntryWire:
        return {
            "name": self.name,
            "isFile": self.is_file,
            "isDirectory": self.is_directory,
            "isSymbolicLink": self.is_symbolic_link,
        }


@dataclass(slots=True, frozen=True)
class FsStat:
    is_file: bool
    is_directory: bool
    is_symbolic_link: bool
    mode: int
    size: int
    mtime: datetime

    @classmethod
    def from_wire(cls, payload: FsStatWire) -> FsStat:
        return cls(
            is_file=bool(payload["isFile"]),
            is_directory=bool(payload["isDirectory"]),
            is_symbolic_link=bool(payload["isSymbolicLink"]),
            mode=int(payload["mode"]),
            size=int(payload["size"]),
            mtime=datetime.fromtimestamp(int(payload["mtimeMs"]) / 1000, tz=UTC),
        )

    def to_wire(self) -> FsStatWire:
        return {
            "isFile": self.is_file,
            "isDirectory": self.is_directory,
            "isSymbolicLink": self.is_symbolic_link,
            "mode": self.mode,
            "size": self.size,
            "mtimeMs": _encode_datetime_ms(self.mtime),
        }


InitialFileValue: TypeAlias = FileValue | FileInit | LazyFile | LazyFileProvider


class LazyFileRegistry:
    def __init__(self) -> None:
        self._next_id = count(1)
        self.providers: dict[str, LazyFileProvider] = {}

    def register(self, provider: LazyFileProvider) -> str:
        name = f"lazy_file_{next(self._next_id)}"
        self.providers[name] = provider
        return name


@dataclass(slots=True, kw_only=True)
class InMemoryFs:
    files: Mapping[str, InitialFileValue] | None = None

    def to_wire(self, registry: LazyFileRegistry | None = None) -> FsConfigWire:
        payload: InMemoryFsWire = {"kind": "in_memory"}
        if self.files is not None:
            payload["files"] = encode_initial_files(self.files, registry=registry)
        return payload


@dataclass(slots=True, kw_only=True)
class OverlayFs:
    root: str
    mount_point: str | None = None
    read_only: bool = False
    max_file_read_size: int | None = None
    allow_symlinks: bool = False

    def to_wire(self, registry: LazyFileRegistry | None = None) -> FsConfigWire:
        del registry
        payload: OverlayFsWire = {
            "kind": "overlay",
            "root": self.root,
        }
        if self.mount_point is not None:
            payload["mountPoint"] = self.mount_point
        if self.read_only:
            payload["readOnly"] = True
        if self.max_file_read_size is not None:
            payload["maxFileReadSize"] = self.max_file_read_size
        if self.allow_symlinks:
            payload["allowSymlinks"] = True
        return payload


@dataclass(slots=True, kw_only=True)
class ReadWriteFs:
    root: str
    max_file_read_size: int | None = None
    allow_symlinks: bool = False

    def to_wire(self, registry: LazyFileRegistry | None = None) -> FsConfigWire:
        del registry
        payload: ReadWriteFsWire = {
            "kind": "read_write",
            "root": self.root,
        }
        if self.max_file_read_size is not None:
            payload["maxFileReadSize"] = self.max_file_read_size
        if self.allow_symlinks:
            payload["allowSymlinks"] = True
        return payload


@dataclass(slots=True, kw_only=True)
class MountConfig:
    mount_point: str
    filesystem: FileSystemConfig

    def to_wire(self, registry: LazyFileRegistry | None = None) -> MountConfigWire:
        return {
            "mountPoint": self.mount_point,
            "filesystem": filesystem_to_wire(self.filesystem, registry=registry),
        }


@dataclass(slots=True, kw_only=True)
class MountableFs:
    base: FileSystemConfig | None = None
    mounts: Sequence[MountConfig] | None = None

    def to_wire(self, registry: LazyFileRegistry | None = None) -> FsConfigWire:
        payload: MountableFsWire = {"kind": "mountable"}
        if self.base is not None:
            payload["base"] = filesystem_to_wire(self.base, registry=registry)
        if self.mounts is not None:
            payload["mounts"] = [mount.to_wire(registry=registry) for mount in self.mounts]
        return payload


FileSystemConfig: TypeAlias = InMemoryFs | OverlayFs | ReadWriteFs | MountableFs


def filesystem_to_wire(filesystem: FileSystemConfig, registry: LazyFileRegistry | None = None) -> FsConfigWire:
    return filesystem.to_wire(registry=registry)


def encode_initial_files(
    files: Mapping[str, InitialFileValue],
    *,
    registry: LazyFileRegistry | None = None,
) -> dict[str, InitialFileValueWire]:
    return {path: encode_initial_file_value(value, registry=registry) for path, value in files.items()}


def encode_initial_file_value(
    value: InitialFileValue,
    *,
    registry: LazyFileRegistry | None = None,
) -> InitialFileValueWire:
    if isinstance(value, FileInit):
        payload: FileInitWire = {
            "kind": "file_init",
            "content": encode_file_value(value.content),
        }
        if value.mode is not None:
            payload["mode"] = value.mode
        if value.mtime is not None:
            payload["mtimeMs"] = _encode_datetime_ms(value.mtime)
        return payload

    if isinstance(value, LazyFile):
        return _encode_lazy_file_source(value.provider, registry=registry)

    if callable(value):
        return _encode_lazy_file_source(value, registry=registry)

    return encode_file_value(value)


def _encode_lazy_file_source(
    source: LazyFileSource,
    *,
    registry: LazyFileRegistry | None = None,
) -> LazyStaticFileWire | LazyCallbackFileWire:
    if callable(source):
        if registry is None:
            raise ValueError("Lazy file callbacks require a bridge-aware serialization context")
        return {
            "kind": "lazy_callback",
            "providerName": registry.register(source),
        }

    return {
        "kind": "lazy_static",
        "content": encode_file_value(source),
    }


def _encode_datetime_ms(value: datetime) -> int:
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return int(normalized.astimezone(UTC).timestamp() * 1000)


__all__ = [
    "DirentEntry",
    "FileInit",
    "FileSystemConfig",
    "FsStat",
    "InMemoryFs",
    "InitialFileValue",
    "LazyFile",
    "LazyFileProvider",
    "MountConfig",
    "MountableFs",
    "OverlayFs",
    "ReadWriteFs",
    "encode_initial_file_value",
    "encode_initial_files",
    "filesystem_to_wire",
]
