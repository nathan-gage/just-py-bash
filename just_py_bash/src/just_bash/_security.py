from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from ._exceptions import JustBashError
from ._option_hooks import SecurityViolation


@dataclass(slots=True, kw_only=True)
class ViolationSummary:
    type: str
    count: int
    first_seen: int
    last_seen: int
    paths: list[str]


class SecurityViolationError(JustBashError):
    def __init__(self, message: str, violation: SecurityViolation) -> None:
        super().__init__(message)
        self.violation = violation


class SecurityViolationLogger:
    def __init__(
        self,
        *,
        max_violations_per_type: int = 100,
        max_violations_total: int = 1000,
        include_stack_traces: bool = True,
        on_violation: Callable[[SecurityViolation], object] | None = None,
        log_to_console: bool = False,
    ) -> None:
        self._max_violations_per_type = max_violations_per_type
        self._max_violations_total = max_violations_total
        self._include_stack_traces = include_stack_traces
        self._on_violation = on_violation
        self._log_to_console = log_to_console
        self._violations: list[SecurityViolation] = []
        self._violations_by_type: dict[str, list[SecurityViolation]] = defaultdict(list)

    def record(self, violation: SecurityViolation) -> None:
        processed = violation if self._include_stack_traces else self._without_stack(violation)

        self._violations.insert(0, processed)
        if len(self._violations) > self._max_violations_total:
            del self._violations[self._max_violations_total :]

        by_type = self._violations_by_type[processed.type]
        if len(by_type) < self._max_violations_per_type:
            by_type.append(processed)

        if self._log_to_console:
            print(
                f"[SecurityViolation] {processed.type}: {processed.message} {processed.path}",
                file=sys.stderr,
            )

        if self._on_violation is not None:
            self._on_violation(processed)

    def get_violations(self) -> list[SecurityViolation]:
        return list(self._violations)

    def get_violations_by_type(self, violation_type: str) -> list[SecurityViolation]:
        return list(self._violations_by_type.get(violation_type, ()))

    def get_summary(self) -> list[ViolationSummary]:
        summaries: list[ViolationSummary] = []
        for violation_type, violations in self._violations_by_type.items():
            if not violations:
                continue
            paths = sorted({violation.path for violation in violations})
            first_seen = min(violation.timestamp for violation in violations)
            last_seen = max(violation.timestamp for violation in violations)
            summaries.append(
                ViolationSummary(
                    type=violation_type,
                    count=len(violations),
                    first_seen=first_seen,
                    last_seen=last_seen,
                    paths=paths,
                )
            )
        summaries.sort(key=lambda item: item.count, reverse=True)
        return summaries

    def get_total_count(self) -> int:
        return len(self._violations)

    def has_violations(self) -> bool:
        return bool(self._violations)

    def clear(self) -> None:
        self._violations.clear()
        self._violations_by_type.clear()

    def create_callback(self) -> Callable[[SecurityViolation], None]:
        return self.record

    @staticmethod
    def _without_stack(violation: SecurityViolation) -> SecurityViolation:
        return SecurityViolation(
            timestamp=violation.timestamp,
            type=violation.type,
            message=violation.message,
            path=violation.path,
            stack=None,
            execution_id=violation.execution_id,
        )


def create_console_violation_callback() -> Callable[[SecurityViolation], None]:
    def callback(violation: SecurityViolation) -> None:
        suffix = f"\n  ExecutionId: {violation.execution_id}" if violation.execution_id else ""
        print(
            "[DefenseInDepth] Security violation detected:"
            f"\n  Type: {violation.type}"
            f"\n  Path: {violation.path}"
            f"\n  Message: {violation.message}"
            f"{suffix}",
            file=sys.stderr,
        )

    return callback


__all__ = [
    "SecurityViolationError",
    "SecurityViolationLogger",
    "ViolationSummary",
    "create_console_violation_callback",
]
