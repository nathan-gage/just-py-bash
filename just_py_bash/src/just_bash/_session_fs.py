from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from ._bridge import NodeBridge
from ._codec import decode_bytes_payload, encode_file_value
from ._exceptions import BridgeError
from ._fs import DirentEntry, FsStat
from ._types import (
    BytesPayload,
    ChmodRequestPayload,
    CpRequestPayload,
    FsStatWire,
    LinkRequestPayload,
    MkdirRequestPayload,
    PathPairRequestPayload,
    ResolvePathRequestPayload,
    RmRequestPayload,
    SymlinkRequestPayload,
    UtimesRequestPayload,
    WriteBytesRequestPayload,
    WriteTextRequestPayload,
)

if TYPE_CHECKING:
    from ._async_api import AsyncBash


class SessionFs:
    def __init__(self, bridge: NodeBridge) -> None:
        self._bridge = bridge

    def read_text(self, path: str) -> str:
        return self._bridge.request("read_text", {"path": path})

    def read_bytes(self, path: str) -> bytes:
        payload = self._bridge.request("read_bytes", {"path": path})
        return decode_bytes_payload(payload)

    def write_text(self, path: str, content: str) -> None:
        self._bridge.request("write_text", {"path": path, "content": content})

    def write_bytes(self, path: str, content: bytes) -> None:
        self._bridge.request(
            "write_bytes",
            {"path": path, "content": encode_file_value(content)},
        )

    def append_text(self, path: str, content: str) -> None:
        payload: WriteTextRequestPayload = {"path": path, "content": content}
        self._bridge.request_raw("append_text", payload)

    def append_bytes(self, path: str, content: bytes) -> None:
        payload: WriteBytesRequestPayload = {"path": path, "content": encode_file_value(content)}
        self._bridge.request_raw("append_bytes", payload)

    def exists(self, path: str) -> bool:
        return bool(self._bridge.request("exists", {"path": path}))

    def stat(self, path: str) -> FsStat:
        payload = self._bridge.request("stat", {"path": path})
        return FsStat.from_wire(payload)

    def lstat(self, path: str) -> FsStat:
        payload = cast(FsStatWire, self._bridge.request_raw("lstat", {"path": path}))
        return FsStat.from_wire(payload)

    def mkdir(self, path: str, *, recursive: bool = False) -> None:
        payload: MkdirRequestPayload = {"path": path}
        if recursive:
            payload["recursive"] = True
        self._bridge.request("mkdir", payload)

    def readdir(self, path: str) -> list[str]:
        payload = self._bridge.request("readdir", {"path": path})
        return _coerce_string_list(payload)

    def readdir_with_file_types(self, path: str) -> list[DirentEntry]:
        payload = self._bridge.request_raw("readdir_with_file_types", {"path": path})
        return _coerce_dirent_list(payload)

    def rm(self, path: str, *, recursive: bool = False, force: bool = False) -> None:
        payload: RmRequestPayload = {"path": path}
        if recursive:
            payload["recursive"] = True
        if force:
            payload["force"] = True
        self._bridge.request("rm", payload)

    def cp(self, src: str, dest: str, *, recursive: bool = False) -> None:
        payload: CpRequestPayload = {"src": src, "dest": dest}
        if recursive:
            payload["recursive"] = True
        self._bridge.request("cp", payload)

    def mv(self, src: str, dest: str) -> None:
        payload: PathPairRequestPayload = {"src": src, "dest": dest}
        self._bridge.request("mv", payload)

    def resolve_path(self, path: str, *, base: str | None = None) -> str:
        payload: ResolvePathRequestPayload = {"path": path}
        if base is not None:
            payload["base"] = base
        return cast(str, self._bridge.request_raw("resolve_path", payload))

    def get_all_paths(self) -> list[str]:
        payload = self._bridge.request_raw("get_all_paths")
        return _coerce_string_list(payload)

    def chmod(self, path: str, mode: int) -> None:
        payload: ChmodRequestPayload = {"path": path, "mode": int(mode)}
        self._bridge.request("chmod", payload)

    def symlink(self, target: str, link_path: str) -> None:
        payload: SymlinkRequestPayload = {"target": target, "linkPath": link_path}
        self._bridge.request_raw("symlink", payload)

    def link(self, existing_path: str, new_path: str) -> None:
        payload: LinkRequestPayload = {"existingPath": existing_path, "newPath": new_path}
        self._bridge.request_raw("link", payload)

    def readlink(self, path: str) -> str:
        return self._bridge.request("readlink", {"path": path})

    def realpath(self, path: str) -> str:
        return self._bridge.request("realpath", {"path": path})

    def utimes(self, path: str, atime: datetime, mtime: datetime) -> None:
        payload: UtimesRequestPayload = {
            "path": path,
            "atimeMs": _encode_datetime_ms(atime),
            "mtimeMs": _encode_datetime_ms(mtime),
        }
        self._bridge.request_raw("utimes", payload)


class AsyncSessionFs:
    def __init__(self, owner: AsyncBash) -> None:
        self._owner = owner

    async def read_text(self, path: str) -> str:
        return cast(str, await self._owner.bridge_request("read_text", {"path": path}))

    async def read_bytes(self, path: str) -> bytes:
        payload = cast(BytesPayload, await self._owner.bridge_request("read_bytes", {"path": path}))
        return decode_bytes_payload(payload)

    async def write_text(self, path: str, content: str) -> None:
        await self._owner.bridge_request("write_text", {"path": path, "content": content})

    async def write_bytes(self, path: str, content: bytes) -> None:
        await self._owner.bridge_request(
            "write_bytes",
            {"path": path, "content": encode_file_value(content)},
        )

    async def append_text(self, path: str, content: str) -> None:
        payload: WriteTextRequestPayload = {"path": path, "content": content}
        await self._owner.bridge_request("append_text", payload)

    async def append_bytes(self, path: str, content: bytes) -> None:
        payload: WriteBytesRequestPayload = {"path": path, "content": encode_file_value(content)}
        await self._owner.bridge_request("append_bytes", payload)

    async def exists(self, path: str) -> bool:
        return bool(await self._owner.bridge_request("exists", {"path": path}))

    async def stat(self, path: str) -> FsStat:
        payload = cast(FsStatWire, await self._owner.bridge_request("stat", {"path": path}))
        return FsStat.from_wire(payload)

    async def lstat(self, path: str) -> FsStat:
        payload = cast(FsStatWire, await self._owner.bridge_request("lstat", {"path": path}))
        return FsStat.from_wire(payload)

    async def mkdir(self, path: str, *, recursive: bool = False) -> None:
        payload: MkdirRequestPayload = {"path": path}
        if recursive:
            payload["recursive"] = True
        await self._owner.bridge_request("mkdir", payload)

    async def readdir(self, path: str) -> list[str]:
        payload = await self._owner.bridge_request("readdir", {"path": path})
        return _coerce_string_list(payload)

    async def readdir_with_file_types(self, path: str) -> list[DirentEntry]:
        payload = await self._owner.bridge_request("readdir_with_file_types", {"path": path})
        return _coerce_dirent_list(payload)

    async def rm(self, path: str, *, recursive: bool = False, force: bool = False) -> None:
        payload: RmRequestPayload = {"path": path}
        if recursive:
            payload["recursive"] = True
        if force:
            payload["force"] = True
        await self._owner.bridge_request("rm", payload)

    async def cp(self, src: str, dest: str, *, recursive: bool = False) -> None:
        payload: CpRequestPayload = {"src": src, "dest": dest}
        if recursive:
            payload["recursive"] = True
        await self._owner.bridge_request("cp", payload)

    async def mv(self, src: str, dest: str) -> None:
        payload: PathPairRequestPayload = {"src": src, "dest": dest}
        await self._owner.bridge_request("mv", payload)

    async def resolve_path(self, path: str, *, base: str | None = None) -> str:
        payload: ResolvePathRequestPayload = {"path": path}
        if base is not None:
            payload["base"] = base
        return cast(str, await self._owner.bridge_request("resolve_path", payload))

    async def get_all_paths(self) -> list[str]:
        payload = await self._owner.bridge_request("get_all_paths", {})
        return _coerce_string_list(payload)

    async def chmod(self, path: str, mode: int) -> None:
        payload: ChmodRequestPayload = {"path": path, "mode": int(mode)}
        await self._owner.bridge_request("chmod", payload)

    async def symlink(self, target: str, link_path: str) -> None:
        payload: SymlinkRequestPayload = {"target": target, "linkPath": link_path}
        await self._owner.bridge_request("symlink", payload)

    async def link(self, existing_path: str, new_path: str) -> None:
        payload: LinkRequestPayload = {"existingPath": existing_path, "newPath": new_path}
        await self._owner.bridge_request("link", payload)

    async def readlink(self, path: str) -> str:
        return cast(str, await self._owner.bridge_request("readlink", {"path": path}))

    async def realpath(self, path: str) -> str:
        return cast(str, await self._owner.bridge_request("realpath", {"path": path}))

    async def utimes(self, path: str, atime: datetime, mtime: datetime) -> None:
        payload: UtimesRequestPayload = {
            "path": path,
            "atimeMs": _encode_datetime_ms(atime),
            "mtimeMs": _encode_datetime_ms(mtime),
        }
        await self._owner.bridge_request("utimes", payload)


def _coerce_string_list(payload: Any) -> list[str]:
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        raise BridgeError(f"Expected a sequence of directory entries, got: {payload!r}")
    entries = cast(Sequence[object], payload)
    return [str(entry) for entry in entries]


def _coerce_dirent_list(payload: Any) -> list[DirentEntry]:
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        raise BridgeError(f"Expected a sequence of typed directory entries, got: {payload!r}")

    entries = cast(Sequence[object], payload)
    dirents: list[DirentEntry] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise BridgeError(f"Expected a directory entry mapping, got: {entry!r}")
        mapping = cast(Mapping[str, object], entry)
        dirents.append(
            DirentEntry.from_wire({
                "name": str(mapping.get("name", "")),
                "isFile": bool(mapping.get("isFile")),
                "isDirectory": bool(mapping.get("isDirectory")),
                "isSymbolicLink": bool(mapping.get("isSymbolicLink")),
            })
        )
    return dirents


def _encode_datetime_ms(value: datetime) -> int:
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return int(normalized.astimezone(UTC).timestamp() * 1000)
