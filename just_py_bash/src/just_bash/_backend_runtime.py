from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping, Sequence

from ._async_bridge import AsyncNodeBridge
from ._bridge import NodeBridge
from ._bridge_protocol import BridgeOperation


class BackendRuntime:
    def __init__(
        self,
        *,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> None:
        self._bridge = NodeBridge(
            init_options={},
            node_command=node_command,
            js_entry=js_entry,
            package_json=package_json,
        )

    @property
    def backend_version(self) -> str | None:
        return self._bridge.backend_version

    def __enter__(self) -> BackendRuntime:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._bridge.close()

    def request(self, op: BridgeOperation, payload: Mapping[str, object]) -> object:
        return self._bridge.request_raw(op, payload)


class AsyncBackendRuntime:
    def __init__(
        self,
        *,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> None:
        self._node_command = tuple(str(part) for part in node_command) if node_command is not None else None
        self._js_entry = None if js_entry is None else str(js_entry)
        self._package_json = None if package_json is None else str(package_json)
        self._bridge: AsyncNodeBridge | None = None
        self._closed = False
        self._lock: asyncio.Lock | None = None

    @classmethod
    async def open(
        cls,
        *,
        node_command: Sequence[str] | None = None,
        js_entry: str | os.PathLike[str] | None = None,
        package_json: str | os.PathLike[str] | None = None,
    ) -> AsyncBackendRuntime:
        self = cls(node_command=node_command, js_entry=js_entry, package_json=package_json)
        await self._ensure_bridge_open_locked()
        return self

    def _guard(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _ensure_bridge_open_locked(self) -> AsyncNodeBridge:
        if self._bridge is not None:
            return self._bridge
        if self._closed:
            raise RuntimeError("just-bash backend runtime is closed")

        bridge = await AsyncNodeBridge.open(
            init_options={},
            node_command=self._node_command,
            js_entry=self._js_entry,
            package_json=self._package_json,
        )
        self._bridge = bridge
        return bridge

    @property
    def backend_version(self) -> str | None:
        if self._bridge is None:
            return None
        return self._bridge.backend_version

    async def __aenter__(self) -> AsyncBackendRuntime:
        async with self._guard():
            await self._ensure_bridge_open_locked()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        async with self._guard():
            if self._bridge is None:
                self._closed = True
                return

            bridge = self._bridge
            self._bridge = None
            self._closed = True
            await bridge.close()

    async def request(self, op: BridgeOperation, payload: Mapping[str, object]) -> object:
        async with self._guard():
            bridge = await self._ensure_bridge_open_locked()
            return await bridge.request_raw(op, payload)
