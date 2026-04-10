from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, cast

from ._backend_runtime import BackendRuntime

BashAst: TypeAlias = dict[str, object]


def parse(script: str, *, max_heredoc_size: int | None = None) -> BashAst:
    payload: dict[str, object] = {"script": script}
    if max_heredoc_size is not None:
        payload["options"] = {"maxHeredocSize": int(max_heredoc_size)}

    with BackendRuntime() as runtime:
        result = runtime.request("parse", payload)
    return _coerce_ast(result)


def serialize(ast: Mapping[str, object]) -> str:
    with BackendRuntime() as runtime:
        result = runtime.request("serialize", {"ast": dict(ast)})
    return str(result)


def _coerce_ast(value: object) -> BashAst:
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected a bash AST mapping, got {type(value).__name__}")
    mapping = cast(Mapping[object, object], value)
    return {str(key): item for key, item in mapping.items()}


__all__ = ["BashAst", "parse", "serialize"]
