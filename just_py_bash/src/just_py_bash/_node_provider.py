from __future__ import annotations

from collections.abc import Callable, Sequence

from ._exceptions import BackendUnavailableError

bundled_get_node_command: Callable[[], tuple[str, ...]] | None

try:
    from just_bash_bundled_runtime import get_node_command as bundled_get_node_command
except ImportError:  # pragma: no cover - exercised via runtime absence in subprocess tests
    bundled_get_node_command = None


def resolve_bundled_node_command() -> list[str] | None:
    if bundled_get_node_command is None:
        return None

    try:
        command = bundled_get_node_command()
    except FileNotFoundError as exc:
        raise BackendUnavailableError(str(exc)) from exc

    return normalize_command(command)


def normalize_command(command: str | Sequence[str]) -> list[str]:
    if isinstance(command, str):
        if not command:
            raise BackendUnavailableError("The bundled Node provider returned an empty command string.")
        return [command]

    parts = [str(part) for part in command]
    if not parts or any(not part for part in parts):
        raise BackendUnavailableError("The bundled Node provider returned an empty command sequence.")
    return parts
