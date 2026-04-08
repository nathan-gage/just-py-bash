from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from just_py_bash._bridge import decode_bytes_payload, resolve_node_command

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SCRIPT = ROOT / "tests" / "js" / "reference.mjs"


def run_reference_scenario(
    *,
    js_entry: Path,
    package_json: Path,
    init_options: dict[str, Any] | None = None,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    request = {
        "jsEntry": str(js_entry),
        "packageJson": str(package_json),
        "initOptions": init_options or {},
        "operations": operations,
    }
    completed = subprocess.run(
        [*resolve_node_command(), str(REFERENCE_SCRIPT)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(f"reference harness failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}")
    return json.loads(completed.stdout)


__all__ = ["decode_bytes_payload", "run_reference_scenario"]
