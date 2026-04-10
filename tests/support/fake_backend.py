from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Literal

FakeBackendMode = Literal["crash_on_exec", "hang_on_exec", "malformed_exec", "defense_violation_event"]


def write_fake_backend(path: Path, *, mode: FakeBackendMode) -> None:
    path.write_text(
        textwrap.dedent(
            f"""
            from __future__ import annotations

            import json
            import sys
            import time

            MODE = {mode!r}


            def write_message(payload: dict[str, object]) -> None:
                sys.stdout.write(json.dumps(payload) + "\\n")
                sys.stdout.flush()


            for line in sys.stdin:
                request = json.loads(line)
                op = request.get("op")

                if op == "init":
                    write_message({{"id": request["id"], "ok": True, "result": {{"backendVersion": "fake-backend"}}}})
                    continue

                if MODE == "malformed_exec" and op == "exec":
                    sys.stdout.write("this is not json\\n")
                    sys.stdout.flush()
                    continue

                if MODE == "crash_on_exec" and op == "exec":
                    raise SystemExit(3)

                if MODE == "hang_on_exec" and op == "exec":
                    time.sleep(60)
                    continue

                if MODE == "defense_violation_event" and op == "exec":
                    write_message(
                        {{
                            "type": "defense_violation",
                            "violation": {{
                                "timestamp": 123,
                                "type": "function_constructor",
                                "message": "blocked Function constructor",
                                "path": "globalThis.Function",
                                "executionId": "fake-exec",
                            }},
                        }}
                    )
                    write_message(
                        {{
                            "id": request["id"],
                            "ok": True,
                            "result": {{
                                "stdout": "ok\\n",
                                "stderr": "",
                                "exitCode": 0,
                                "env": {{}},
                            }},
                        }}
                    )
                    continue

                write_message({{"id": request["id"], "ok": True, "result": None}})
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


__all__ = ["FakeBackendMode", "write_fake_backend"]
