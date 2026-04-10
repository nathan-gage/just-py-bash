from __future__ import annotations

from typing import cast

from ._backend_runtime import BackendRuntime


def get_command_names() -> list[str]:
    return _get_names("all")


def get_network_command_names() -> list[str]:
    return _get_names("network")


def get_python_command_names() -> list[str]:
    return _get_names("python")


def get_javascript_command_names() -> list[str]:
    return _get_names("javascript")


def _get_names(kind: str) -> list[str]:
    with BackendRuntime() as runtime:
        result = runtime.request("get_command_names", {"kind": kind})
    if not isinstance(result, list):
        raise TypeError(f"Expected a list of command names, got {type(result).__name__}")
    result_list = cast(list[object], result)
    return [str(value) for value in result_list]


__all__ = [
    "get_command_names",
    "get_javascript_command_names",
    "get_network_command_names",
    "get_python_command_names",
]
