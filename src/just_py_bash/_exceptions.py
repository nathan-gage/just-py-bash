from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._models import ExecResult


class JustBashError(RuntimeError):
    """Base exception for the package."""


class BackendUnavailableError(JustBashError):
    """Raised when the Node.js backend or built just-bash artifact is unavailable."""


class BridgeError(JustBashError):
    """Raised when the Python ↔ Node bridge fails."""


class BridgeTimeoutError(BridgeError):
    """Raised when the worker does not answer within the expected time."""


class BackendError(BridgeError):
    """Raised when the Node backend returns an unexpected error."""

    def __init__(
        self,
        message: str,
        *,
        error_type: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.details = dict(details) if details is not None else {}


class CommandFailedError(JustBashError):
    """Raised by :meth:`ExecResult.check` for non-zero exit codes."""

    def __init__(self, result: ExecResult) -> None:
        stderr = result.stderr.strip()
        message = f"just-bash command failed with exit code {result.exit_code}"
        if stderr:
            message = f"{message}: {stderr}"
        super().__init__(message)
        self.result = result
