from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from typing import Any, Protocol, cast

import pytest

from tests.support.harness import (
    BackendArtifacts,
    op_exec,
    op_probe_defense_violation,
    public_api,
    run_async_differential_scenario,
    run_differential_scenario,
)

pytestmark = pytest.mark.parity

ScenarioRunner = Callable[..., tuple[dict[str, Any], dict[str, Any]]]


class _FetchRequestLike(Protocol):
    url: str
    method: str
    headers: Mapping[str, object]
    body: object
    follow_redirects: object
    timeout_ms: object


class _TraceEventLike(Protocol):
    category: str
    name: str
    details: Mapping[str, object] | None


class _SecurityViolationLike(Protocol):
    type: str
    message: str
    path: str
    execution_id: str | None


class _RecorderLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, object] | None]] = []

    def info(self, message: str, data: MappingLike | None = None) -> None:
        self.events.append(("info", message, _normalize_mapping(data)))

    def debug(self, message: str, data: MappingLike | None = None) -> None:
        self.events.append(("debug", message, _normalize_mapping(data)))


class _CoverageRecorder:
    def __init__(self) -> None:
        self.hits: list[str] = []

    def hit(self, feature: str) -> None:
        self.hits.append(feature)


MappingLike = dict[str, object] | None


def _normalize_mapping(data: object) -> dict[str, object] | None:
    if not isinstance(data, Mapping):
        return None
    mapping = cast(Mapping[object, object], data)
    return {str(key): value for key, value in mapping.items()}


def _normalize_fetch_request(request: object) -> dict[str, object]:
    typed_request = cast(_FetchRequestLike, request)
    normalized_headers = {str(key): value for key, value in typed_request.headers.items()}
    return {
        "url": typed_request.url,
        "method": typed_request.method,
        "headers": normalized_headers,
        "body": typed_request.body,
        "follow_redirects": typed_request.follow_redirects,
        "timeout_ms": typed_request.timeout_ms,
    }


def _normalize_trace_event(event: object) -> dict[str, object]:
    typed_event = cast(_TraceEventLike, event)
    normalized_details: dict[str, object] | None = None
    if typed_event.details is not None:
        normalized_details = {
            str(key): value for key, value in typed_event.details.items() if not str(key).endswith("TimeMs")
        }
    return {
        "category": typed_event.category,
        "name": typed_event.name,
        "details": normalized_details,
    }


def _without_timeout_ms(requests: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{key: value for key, value in request.items() if key != "timeout_ms"} for request in requests]


def _normalize_security_violation(violation: object) -> dict[str, object]:
    typed_violation = cast(_SecurityViolationLike, violation)
    return {
        "type": typed_violation.type,
        "message": typed_violation.message,
        "path": typed_violation.path,
        "execution_id": typed_violation.execution_id,
    }


def _without_execution_id(violations: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{key: value for key, value in violation.items() if key != "execution_id"} for violation in violations]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_fetch_option_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    python_requests: list[dict[str, object]] = []
    reference_requests: list[dict[str, object]] = []

    async def python_fetch(request: Any) -> Any:
        python_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return api.FetchResult(
            status=200,
            status_text="OK",
            headers={"content-type": "text/plain"},
            body="python-fetch\n",
            url=request.url,
        )

    async def reference_fetch(request: Any) -> Any:
        reference_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return api.FetchResult(
            status=200,
            status_text="OK",
            headers={"content-type": "text/plain"},
            body="python-fetch\n",
            url=request.url,
        )

    python_result, reference_result = runner(
        init_kwargs={"fetch": python_fetch},
        reference_init_kwargs={"fetch": reference_fetch},
        operations=[op_exec("curl -s https://example.com")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "python-fetch\n"
    assert python_requests == reference_requests
    assert python_requests == [
        {
            "url": "https://example.com",
            "method": "GET",
            "headers": {},
            "body": None,
            "follow_redirects": True,
            "timeout_ms": None,
        }
    ]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_fetch_option_post_body_headers_and_mapping_result_match_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_requests: list[dict[str, object]] = []
    reference_requests: list[dict[str, object]] = []

    async def python_fetch(request: Any) -> Any:
        python_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return {
            "status": 201,
            "statusText": "Created",
            "headers": {"content-type": "text/plain"},
            "body": "mapped-fetch\n",
            "url": request.url,
        }

    async def reference_fetch(request: Any) -> Any:
        reference_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return {
            "status": 201,
            "statusText": "Created",
            "headers": {"content-type": "text/plain"},
            "body": "mapped-fetch\n",
            "url": request.url,
        }

    python_result, reference_result = runner(
        init_kwargs={"fetch": python_fetch},
        reference_init_kwargs={"fetch": reference_fetch},
        operations=[
            op_exec("curl -s -X POST -H 'content-type: application/json' -d '{\"a\":1}' https://example.com/api")
        ],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "mapped-fetch\n"
    assert python_requests == reference_requests
    assert python_requests == [
        {
            "url": "https://example.com/api",
            "method": "POST",
            "headers": {"content-type": "application/json"},
            "body": '{"a":1}',
            "follow_redirects": True,
            "timeout_ms": None,
        }
    ]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_fetch_option_http_failure_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_requests: list[dict[str, object]] = []
    reference_requests: list[dict[str, object]] = []

    async def python_fetch(request: Any) -> Any:
        python_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return {
            "status": 404,
            "statusText": "Not Found",
            "headers": {"content-type": "text/plain"},
            "body": "missing\n",
            "url": request.url,
        }

    async def reference_fetch(request: Any) -> Any:
        reference_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return {
            "status": 404,
            "statusText": "Not Found",
            "headers": {"content-type": "text/plain"},
            "body": "missing\n",
            "url": request.url,
        }

    python_result, reference_result = runner(
        init_kwargs={"fetch": python_fetch},
        reference_init_kwargs={"fetch": reference_fetch},
        operations=[op_exec("curl -sf https://example.com/missing")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["exitCode"] == 22
    assert python_result["results"][0]["value"]["stdout"] == ""
    assert python_result["results"][0]["value"]["stderr"] == ""
    assert python_requests == reference_requests
    assert python_requests == [
        {
            "url": "https://example.com/missing",
            "method": "GET",
            "headers": {},
            "body": None,
            "follow_redirects": True,
            "timeout_ms": None,
        }
    ]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_fetch_option_callback_failure_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_requests: list[dict[str, object]] = []
    reference_requests: list[dict[str, object]] = []

    async def python_fetch(request: Any) -> Any:
        python_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        raise RuntimeError("fetch boom")

    async def reference_fetch(request: Any) -> Any:
        reference_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        raise RuntimeError("fetch boom")

    python_result, reference_result = runner(
        init_kwargs={"fetch": python_fetch},
        reference_init_kwargs={"fetch": reference_fetch},
        operations=[op_exec("curl -s https://example.com")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["exitCode"] == 1
    assert python_result["results"][0]["value"]["stdout"] == ""
    assert python_result["results"][0]["value"]["stderr"] == ""
    assert python_requests == reference_requests
    assert python_requests == [
        {
            "url": "https://example.com",
            "method": "GET",
            "headers": {},
            "body": None,
            "follow_redirects": True,
            "timeout_ms": None,
        }
    ]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_fetch_option_js_exec_consumer_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_requests: list[dict[str, object]] = []
    reference_requests: list[dict[str, object]] = []

    async def python_fetch(request: Any) -> Any:
        python_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return {
            "status": 200,
            "statusText": "OK",
            "headers": {"content-type": "application/json"},
            "body": '{"ok":true}',
            "url": request.url,
        }

    async def reference_fetch(request: Any) -> Any:
        reference_requests.append(_normalize_fetch_request(request))
        await asyncio.sleep(0)
        return {
            "status": 200,
            "statusText": "OK",
            "headers": {"content-type": "application/json"},
            "body": '{"ok":true}',
            "url": request.url,
        }

    python_result, reference_result = runner(
        init_kwargs={"fetch": python_fetch, "javascript": True},
        reference_init_kwargs={"fetch": reference_fetch, "javascript": True},
        operations=[
            op_exec(
                "js-exec -c \"var response = await fetch('https://example.com/api'); var data = await response.json(); console.log(data.ok ? 'js-fetch' : 'bad')\""
            )
        ],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "js-fetch\n"
    assert _without_timeout_ms(python_requests) == _without_timeout_ms(reference_requests)
    assert _without_timeout_ms(python_requests) == [
        {
            "url": "https://example.com/api",
            "method": "GET",
            "headers": {},
            "body": None,
            "follow_redirects": None,
        }
    ]
    assert len(python_requests) == 1
    assert isinstance(python_requests[0]["timeout_ms"], int)
    assert isinstance(reference_requests[0]["timeout_ms"], int)
    assert python_requests[0]["timeout_ms"] > 0
    assert reference_requests[0]["timeout_ms"] > 0


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_logger_option_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_logger = _RecorderLogger()
    reference_logger = _RecorderLogger()

    python_result, reference_result = runner(
        init_kwargs={"logger": python_logger},
        reference_init_kwargs={"logger": reference_logger},
        operations=[op_exec("printf 'out\\n'; printf 'err\\n' >&2; false")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_logger.events == reference_logger.events
    assert python_logger.events == [
        ("info", "exec", {"command": "printf 'out\\n'; printf 'err\\n' >&2; false"}),
        ("debug", "stdout", {"output": "out\n"}),
        ("info", "stderr", {"output": "err\n"}),
        ("info", "exit", {"exitCode": 1}),
    ]


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_trace_option_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_events: list[dict[str, object]] = []
    reference_events: list[dict[str, object]] = []

    def python_trace(event: Any) -> None:
        python_events.append(_normalize_trace_event(event))

    def reference_trace(event: Any) -> None:
        reference_events.append(_normalize_trace_event(event))

    init_kwargs = {
        "files": {"/workspace/a.txt": "a\n", "/workspace/b.txt": "b\n"},
        "cwd": "/workspace",
        "trace": python_trace,
    }
    reference_init_kwargs = {
        "files": {"/workspace/a.txt": "a\n", "/workspace/b.txt": "b\n"},
        "cwd": "/workspace",
        "trace": reference_trace,
    }

    python_result, reference_result = runner(
        init_kwargs=init_kwargs,
        reference_init_kwargs=reference_init_kwargs,
        operations=[op_exec("find . -maxdepth 1 -type f | sort")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_events == reference_events
    assert python_events
    assert any(event["category"] == "find" for event in python_events)


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_coverage_option_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    python_coverage = _CoverageRecorder()
    reference_coverage = _CoverageRecorder()

    python_result, reference_result = runner(
        init_kwargs={"coverage": python_coverage},
        reference_init_kwargs={"coverage": reference_coverage},
        operations=[op_exec("echo coverage")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_coverage.hits == reference_coverage.hits
    assert python_coverage.hits
    assert any(hit.startswith("bash:") or hit.startswith("cmd:") for hit in python_coverage.hits)


@pytest.mark.parametrize(
    "runner",
    [run_differential_scenario, run_async_differential_scenario],
    ids=["sync", "async"],
)
def test_defense_in_depth_option_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
) -> None:
    api = public_api()
    init_kwargs = {
        "defense_in_depth": api.DefenseInDepthConfig(
            enabled=True,
            audit_mode=True,
            exclude_violation_types=["webassembly"],
        ),
    }

    python_result, reference_result = runner(
        init_kwargs=init_kwargs,
        operations=[op_exec('echo defense && printf %s "$PWD"')],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    assert python_result["results"][0]["value"]["stdout"] == "defense\n/home/user"


@pytest.mark.parametrize(
    ("runner", "kind"),
    [
        (run_differential_scenario, "main"),
        (run_async_differential_scenario, "main"),
        (run_differential_scenario, "worker"),
        (run_async_differential_scenario, "worker"),
    ],
    ids=["sync-main", "async-main", "sync-worker", "async-worker"],
)
def test_defense_violation_probe_matches_upstream(
    backend_artifacts: BackendArtifacts,
    runner: ScenarioRunner,
    kind: str,
) -> None:
    if kind == "worker" and not (backend_artifacts.package_json.parent / "dist" / "security" / "index.js").exists():
        pytest.skip("WorkerDefenseInDepth is not shipped as an importable module in this backend artifact")

    api = public_api()
    python_violations: list[dict[str, object]] = []
    reference_violations: list[dict[str, object]] = []

    def python_on_violation(violation: Any) -> None:
        python_violations.append(_normalize_security_violation(violation))

    def reference_on_violation(violation: Any) -> None:
        reference_violations.append(_normalize_security_violation(violation))

    python_result, reference_result = runner(
        init_kwargs={
            "defense_in_depth": api.DefenseInDepthConfig(
                enabled=True,
                audit_mode=True,
                on_violation=python_on_violation,
            )
        },
        reference_init_kwargs={
            "defense_in_depth": api.DefenseInDepthConfig(
                enabled=True,
                audit_mode=True,
                on_violation=reference_on_violation,
            )
        },
        operations=[op_probe_defense_violation(kind)],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
    expected_violation_count = 0 if kind == "main" else 1
    assert python_result["results"][0]["value"] == {
        "kind": kind,
        "returnValue": 42,
        "violationCount": expected_violation_count,
    }
    assert _without_execution_id(python_violations) == _without_execution_id(reference_violations)
    assert len(python_violations) == expected_violation_count
    if kind == "worker":
        assert python_violations[0]["type"] == "function_constructor"
        assert python_violations[0]["path"] == "globalThis.Function"
        assert isinstance(python_violations[0]["message"], str)
        assert python_violations[0]["execution_id"] is None or isinstance(
            python_violations[0]["execution_id"],
            str,
        )
        assert reference_violations[0]["execution_id"] is None or isinstance(
            reference_violations[0]["execution_id"],
            str,
        )
