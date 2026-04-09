from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from ._bridge import NodeBridge
from ._codec import decode_bytes_payload, encode_file_value
from ._exceptions import BridgeError
from ._fs import FsStat
from ._types import (
    BytesPayload,
    ChmodRequestPayload,
    CpRequestPayload,
    FsStatWire,
    MkdirRequestPayload,
    PathPairRequestPayload,
    RmRequestPayload,
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

    def exists(self, path: str) -> bool:
        return bool(self._bridge.request("exists", {"path": path}))

    def stat(self, path: str) -> FsStat:
        payload = self._bridge.request("stat", {"path": path})
        return FsStat.from_wire(payload)

    def mkdir(self, path: str, *, recursive: bool = False) -> None:
        payload: MkdirRequestPayload = {"path": path}
        if recursive:
            payload["recursive"] = True
        self._bridge.request("mkdir", payload)

    def readdir(self, path: str) -> list[str]:
        payload = self._bridge.request("readdir", {"path": path})
        return _coerce_string_list(payload)

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

    def chmod(self, path: str, mode: int) -> None:
        payload: ChmodRequestPayload = {"path": path, "mode": int(mode)}
        self._bridge.request("chmod", payload)

    def readlink(self, path: str) -> str:
        return self._bridge.request("readlink", {"path": path})

    def realpath(self, path: str) -> str:
        return self._bridge.request("realpath", {"path": path})


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

    async def exists(self, path: str) -> bool:
        return bool(await self._owner.bridge_request("exists", {"path": path}))

    async def stat(self, path: str) -> FsStat:
        payload = cast(FsStatWire, await self._owner.bridge_request("stat", {"path": path}))
        return FsStat.from_wire(payload)

    async def mkdir(self, path: str, *, recursive: bool = False) -> None:
        payload: MkdirRequestPayload = {"path": path}
        if recursive:
            payload["recursive"] = True
        await self._owner.bridge_request("mkdir", payload)

    async def readdir(self, path: str) -> list[str]:
        payload = await self._owner.bridge_request("readdir", {"path": path})
        return _coerce_string_list(payload)

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

    async def chmod(self, path: str, mode: int) -> None:
        payload: ChmodRequestPayload = {"path": path, "mode": int(mode)}
        await self._owner.bridge_request("chmod", payload)

    async def readlink(self, path: str) -> str:
        return cast(str, await self._owner.bridge_request("readlink", {"path": path}))

    async def realpath(self, path: str) -> str:
        return cast(str, await self._owner.bridge_request("realpath", {"path": path}))


def _coerce_string_list(payload: Any) -> list[str]:
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        raise BridgeError(f"Expected a sequence of directory entries, got: {payload!r}")
    entries = cast(Sequence[object], payload)
    return [str(entry) for entry in entries]
