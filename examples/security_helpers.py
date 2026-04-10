from __future__ import annotations

from just_bash import SecurityViolation, SecurityViolationError, SecurityViolationLogger

print("=== Security helpers ===")

logger = SecurityViolationLogger(include_stack_traces=False)
violation = SecurityViolation(
    timestamp=1,
    type="eval",
    message="blocked eval",
    path="globalThis.eval",
    stack="hidden stack",
    execution_id="exec-1",
)
logger.record(violation)

summary = logger.get_summary()[0]
print(f"total={logger.get_total_count()}")
print(f"summary={summary.type}:{summary.count}:{summary.paths[0]}")
print(f"stored_stack={logger.get_violations()[0].stack}")

error = SecurityViolationError("security violation", violation)
print(f"error_message={error}")
print(f"error_type={error.violation.type}")
