from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from ._codec import encode_file_value
from ._types import (
    FileValue,
    FsConfigWire,
    InMemoryFsWire,
    MountableFsWire,
    MountConfigWire,
    OverlayFsWire,
    ReadWriteFsWire,
)


@dataclass(slots=True, kw_only=True)
class InMemoryFs:
    files: Mapping[str, FileValue] | None = None

    def to_wire(self) -> FsConfigWire:
        payload: InMemoryFsWire = {"kind": "in_memory"}
        if self.files is not None:
            payload["files"] = {path: encode_file_value(content) for path, content in self.files.items()}
        return payload


@dataclass(slots=True, kw_only=True)
class OverlayFs:
    root: str
    mount_point: str | None = None
    read_only: bool = False
    max_file_read_size: int | None = None
    allow_symlinks: bool = False

    def to_wire(self) -> FsConfigWire:
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

    def to_wire(self) -> FsConfigWire:
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

    def to_wire(self) -> MountConfigWire:
        return {
            "mountPoint": self.mount_point,
            "filesystem": filesystem_to_wire(self.filesystem),
        }


@dataclass(slots=True, kw_only=True)
class MountableFs:
    base: FileSystemConfig | None = None
    mounts: Sequence[MountConfig] | None = None

    def to_wire(self) -> FsConfigWire:
        payload: MountableFsWire = {"kind": "mountable"}
        if self.base is not None:
            payload["base"] = filesystem_to_wire(self.base)
        if self.mounts is not None:
            payload["mounts"] = [mount.to_wire() for mount in self.mounts]
        return payload


FileSystemConfig: TypeAlias = InMemoryFs | OverlayFs | ReadWriteFs | MountableFs


def filesystem_to_wire(filesystem: FileSystemConfig) -> FsConfigWire:
    return filesystem.to_wire()


__all__ = [
    "FileSystemConfig",
    "InMemoryFs",
    "MountConfig",
    "MountableFs",
    "OverlayFs",
    "ReadWriteFs",
    "filesystem_to_wire",
]
