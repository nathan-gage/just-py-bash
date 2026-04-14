from __future__ import annotations

from typing import TYPE_CHECKING

from ._types import BackendErrorPayload

if TYPE_CHECKING:
    from ._models import ExecResult


class JustBashError(RuntimeError):
    """Base exception for the package."""


class BackendUnavailableError(JustBashError):
    """Raised when the Node.js backend or built just-bash artifact is unavailable."""


class UnsupportedRuntimeConfigurationError(JustBashError):
    """Raised when requested runtime features are incompatible with the resolved backend runtime."""

    def __init__(
        self,
        message: str,
        *,
        feature: str,
        required_version: str | None = None,
        actual_version: str | None = None,
        required_platform: str | None = None,
        actual_platform: str | None = None,
        configuration: tuple[str, ...] = (),
        node_command: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.feature = feature
        self.required_version = required_version
        self.actual_version = actual_version
        self.required_platform = required_platform
        self.actual_platform = actual_platform
        self.configuration = configuration
        self.node_command = node_command


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
        details: BackendErrorPayload | None = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.details: BackendErrorPayload = {} if details is None else details


class CommandFailedError(JustBashError):
    """Raised by :meth:`ExecResult.check` for non-zero exit codes."""

    def __init__(self, result: ExecResult) -> None:
        stderr = result.stderr.strip()
        message = f"just-bash command failed with exit code {result.exit_code}"
        if stderr:
            message = f"{message}: {stderr}"
        super().__init__(message)
        self.result = result
