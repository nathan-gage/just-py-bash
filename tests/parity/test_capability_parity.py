from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from tests.support.harness import BackendArtifacts, op_exec, public_api, run_differential_scenario

pytestmark = pytest.mark.parity


@pytest.fixture()
def local_http_server() -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._write_response()

        def do_POST(self) -> None:
            self._write_response()

        def _write_response(self) -> None:
            length = int(self.headers.get("content-length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            payload = {
                "method": self.command,
                "path": self.path,
                "xInjected": self.headers.get("x-injected"),
                "body": body,
            }
            encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, name="just-py-bash-network-test", daemon=True)
    thread.start()
    try:
        address = server.server_address
        host = str(address[0])
        port = int(address[1])
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2.0)
        server.server_close()


def test_network_disabled_keeps_curl_unavailable_against_upstream(
    local_http_server: str,
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result, reference_result = run_differential_scenario(
        init_kwargs={},
        operations=[op_exec(f"curl -s {local_http_server}/inspect")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    exec_result = python_result["results"][0]["value"]
    assert exec_result["exitCode"] != 0


def test_network_config_enables_curl_methods_and_header_transforms_against_upstream(
    local_http_server: str,
    backend_artifacts: BackendArtifacts,
) -> None:
    init_kwargs = {
        "network": {
            "allowedUrlPrefixes": [
                {
                    "url": local_http_server,
                    "transform": [{"headers": {"X-Injected": "from-network-config"}}],
                },
            ],
            "allowedMethods": ["GET", "HEAD", "POST"],
            "denyPrivateRanges": False,
        },
    }
    python_result, reference_result = run_differential_scenario(
        init_kwargs=init_kwargs,
        operations=[
            op_exec(f"curl -s {local_http_server}/inspect?kind=get"),
            op_exec(f"curl -s -X POST -d 'alpha=beta' {local_http_server}/inspect"),
        ],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result

    get_payload = json.loads(python_result["results"][0]["value"]["stdout"])
    post_payload = json.loads(python_result["results"][1]["value"]["stdout"])

    assert get_payload == {
        "body": "",
        "method": "GET",
        "path": "/inspect?kind=get",
        "xInjected": "from-network-config",
    }
    assert post_payload == {
        "body": "alpha=beta",
        "method": "POST",
        "path": "/inspect",
        "xInjected": "from-network-config",
    }


def test_process_info_matches_upstream_and_virtual_proc_files(
    backend_artifacts: BackendArtifacts,
) -> None:
    init_kwargs = {
        "process_info": {
            "pid": 4321,
            "ppid": 1234,
            "uid": 2001,
            "gid": 3001,
        },
    }
    python_result, reference_result = run_differential_scenario(
        init_kwargs=init_kwargs,
        operations=[
            op_exec('printf "%s|%s|%s|%s" "$$" "$PPID" "$UID" "$EUID"'),
            op_exec("cat /proc/self/status"),
            op_exec("cat /proc/self/cmdline | od -An -tx1"),
        ],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result

    basic = python_result["results"][0]["value"]["stdout"]
    status = python_result["results"][1]["value"]["stdout"]
    cmdline = python_result["results"][2]["value"]["stdout"]

    assert basic == "4321|1234|2001|2001"
    assert "Pid:\t4321" in status
    assert "PPid:\t1234" in status
    assert "Uid:\t2001\t2001\t2001\t2001" in status
    assert "Gid:\t3001\t3001\t3001\t3001" in status
    assert "142 141 163 150" in cmdline


@pytest.mark.parametrize(
    ("name", "init_kwargs", "script", "expected_exit_code", "expected_stderr_substring"),
    [
        (
            "loop_iterations",
            {"execution_limits": public_api().ExecutionLimits(max_loop_iterations=2)},
            "while true; do echo tick; done",
            126,
            "maxLoopIterations",
        ),
        (
            "heredoc_size",
            {"execution_limits": public_api().ExecutionLimits(max_heredoc_size=4)},
            "cat <<'EOF'\nhello\nEOF",
            2,
            "Heredoc size limit exceeded",
        ),
        (
            "output_size",
            {"execution_limits": public_api().ExecutionLimits(max_output_size=5)},
            "printf 'abcdef'",
            126,
            "maxOutputSize",
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_execution_limits_match_upstream_for_shipped_limit_types(
    name: str,
    init_kwargs: dict[str, Any],
    script: str,
    expected_exit_code: int,
    expected_stderr_substring: str,
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result, reference_result = run_differential_scenario(
        init_kwargs=init_kwargs,
        operations=[op_exec(script, raw_script=True if "EOF" in script else False)],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result, name

    exec_result = python_result["results"][0]["value"]
    assert exec_result["exitCode"] == expected_exit_code
    assert expected_stderr_substring in exec_result["stderr"]
