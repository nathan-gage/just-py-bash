from __future__ import annotations

from collections.abc import Mapping

from just_bash import Bash, DefenseInDepthConfig, FetchRequest, FetchResult, SecurityViolation, TraceEvent


class RecorderLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, Mapping[str, object] | None]] = []

    def info(self, message: str, data: Mapping[str, object] | None = None) -> None:
        self.events.append(("info", message, data))

    def debug(self, message: str, data: Mapping[str, object] | None = None) -> None:
        self.events.append(("debug", message, data))


class CoverageRecorder:
    def __init__(self) -> None:
        self.hits: list[str] = []

    def hit(self, feature: str) -> None:
        self.hits.append(feature)


def main() -> None:
    logger = RecorderLogger()
    coverage = CoverageRecorder()
    trace_events: list[TraceEvent] = []
    fetch_requests: list[FetchRequest] = []
    violations: list[SecurityViolation] = []

    def fetch(request: FetchRequest) -> FetchResult:
        fetch_requests.append(request)
        return FetchResult(
            status=200,
            status_text="OK",
            headers={"content-type": "text/plain"},
            body="hello from fetch\n",
            url=request.url,
        )

    with Bash(
        files={"/workspace/seed.txt": "seed\n"},
        cwd="/workspace",
        logger=logger,
        trace=trace_events.append,
        coverage=coverage,
        fetch=fetch,
        javascript=True,
        defense_in_depth=DefenseInDepthConfig(enabled=True, audit_mode=True, on_violation=violations.append),
    ) as bash:
        fetch_result = bash.exec("curl -s https://example.com")
        find_result = bash.exec("find . -maxdepth 1 -type f | sort")
        js_result = bash.exec(
            'js-exec -c "try { new Function(\'return 1\')(); } catch (e) { console.log(e.message); }"',
        )

    print("=== Option hooks ===")
    print(f"fetch={fetch_result.stdout.strip()}")
    print(f"fetch_request={fetch_requests[0].method}:{fetch_requests[0].url}")
    print(f"trace_has_find={any(event.category == 'find' for event in trace_events)}")
    print(f"coverage_hits={len(coverage.hits)}")
    print(f"logger_has_exec={any(message == 'exec' for _, message, _ in logger.events)}")
    print(f"logger_has_exit={any(message == 'exit' for _, message, _ in logger.events)}")
    print(f"find_result={find_result.stdout.strip()}")
    print(f"defense_blocked={'Function constructor is not allowed' in js_result.stdout}")
    print(f"violations_recorded={len(violations)}")


if __name__ == "__main__":
    main()
