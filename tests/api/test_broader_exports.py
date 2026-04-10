from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import StringIO

import pytest
from just_bash import (
    AsyncBash,
    AsyncSandbox,
    Bash,
    BashTransformPipeline,
    CommandCollectorPlugin,
    Sandbox,
    SandboxOptions,
    SecurityViolation,
    SecurityViolationError,
    SecurityViolationLogger,
    TeePlugin,
    create_console_violation_callback,
    get_command_names,
    get_javascript_command_names,
    get_network_command_names,
    get_python_command_names,
    parse,
    serialize,
)

pytestmark = pytest.mark.api


def test_command_registry_helpers_expose_upstream_names() -> None:
    command_names = get_command_names()
    network_names = get_network_command_names()
    python_names = get_python_command_names()
    javascript_names = get_javascript_command_names()

    assert "echo" in command_names
    assert "curl" not in command_names
    assert network_names == ["curl"]
    assert set(python_names) == {"python", "python3"}
    assert set(javascript_names) == {"js-exec", "node"}


def test_parse_and_serialize_round_trip_through_public_helpers() -> None:
    script = "echo hello | grep h && printf 'done\\n'"

    ast = parse(script)

    assert ast["type"] == "Script"
    assert serialize(ast) == script
    assert parse(serialize(ast)) == ast


def test_bash_transform_pipeline_collects_metadata_and_rewrites_script() -> None:
    result = (
        BashTransformPipeline()
        .use(
            TeePlugin(
                output_dir="/tmp/logs",
                timestamp=datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=UTC),
            )
        )
        .use(CommandCollectorPlugin())
        .transform("echo hello | grep h")
    )

    assert "tee /tmp/logs/2024-01-15T10-30-45.123Z-000-echo.stdout.txt" in result.script
    assert result.metadata["commands"] == ["echo", "exit", "grep", "tee"]
    tee_files = result.metadata["teeFiles"]
    assert isinstance(tee_files, list)
    assert tee_files[0]["command"] == "echo hello"
    assert tee_files[1]["commandName"] == "grep"


def test_bash_transform_registration_affects_transform_and_exec_metadata() -> None:
    with Bash() as bash:
        bash.register_transform_plugin(CommandCollectorPlugin())

        transformed = bash.transform("echo hello | grep h")
        result = bash.exec("echo hello | grep h")

    assert transformed.metadata == {"commands": ["echo", "grep"]}
    assert result.metadata == {"commands": ["echo", "grep"]}


def test_async_bash_transform_registration_affects_transform_and_exec_metadata() -> None:
    async def exercise() -> None:
        async with AsyncBash() as bash:
            await bash.register_transform_plugin(CommandCollectorPlugin())

            transformed = await bash.transform("echo hello | grep h")
            result = await bash.exec("echo hello | grep h")

        assert transformed.metadata == {"commands": ["echo", "grep"]}
        assert result.metadata == {"commands": ["echo", "grep"]}

    asyncio.run(exercise())


def test_security_violation_logger_tracks_and_summarizes_violations() -> None:
    seen: list[tuple[str, str | None]] = []
    logger = SecurityViolationLogger(
        max_violations_per_type=2,
        include_stack_traces=False,
        on_violation=lambda violation: seen.append((violation.type, violation.stack)),
    )

    logger.record(
        SecurityViolation(
            timestamp=10,
            type="eval",
            message="blocked eval",
            path="globalThis.eval",
            stack="stack-a",
            execution_id="exec-1",
        )
    )
    logger.record(
        SecurityViolation(
            timestamp=20,
            type="eval",
            message="blocked eval again",
            path="globalThis.eval",
            stack="stack-b",
            execution_id="exec-2",
        )
    )

    assert logger.has_violations() is True
    assert logger.get_total_count() == 2
    assert [violation.stack for violation in logger.get_violations()] == [None, None]
    assert seen == [("eval", None), ("eval", None)]

    summary = logger.get_summary()
    assert len(summary) == 1
    assert summary[0].type == "eval"
    assert summary[0].count == 2
    assert summary[0].first_seen == 10
    assert summary[0].last_seen == 20
    assert summary[0].paths == ["globalThis.eval"]

    callback = logger.create_callback()
    callback(
        SecurityViolation(
            timestamp=30,
            type="proxy",
            message="blocked proxy",
            path="globalThis.Proxy",
        )
    )
    assert logger.get_total_count() == 3

    logger.clear()
    assert logger.has_violations() is False
    assert logger.get_violations() == []


def test_create_console_violation_callback_prints_expected_summary(capsys: pytest.CaptureFixture[str]) -> None:
    callback = create_console_violation_callback()
    callback(
        SecurityViolation(
            timestamp=1,
            type="function_constructor",
            message="blocked Function",
            path="globalThis.Function",
            execution_id="exec-1",
        )
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[DefenseInDepth] Security violation detected:" in captured.err
    assert "Type: function_constructor" in captured.err
    assert "Path: globalThis.Function" in captured.err
    assert "ExecutionId: exec-1" in captured.err


def test_security_violation_error_retains_violation() -> None:
    violation = SecurityViolation(
        timestamp=1,
        type="eval",
        message="blocked eval",
        path="globalThis.eval",
    )

    error = SecurityViolationError("blocked", violation)

    assert str(error) == "blocked"
    assert error.violation == violation


def test_sandbox_sync_api_runs_commands_and_detached_handles() -> None:
    stdout_buffer = StringIO()

    with Sandbox.create(SandboxOptions(cwd="/app")) as sandbox:
        assert sandbox.domain is None

        sandbox.write_files({
            "/app/hello.txt": "hello from sandbox\n",
            "/app/data.bin": b"abc",
        })
        sandbox.mk_dir("/app/logs", recursive=True)

        command = sandbox.run_command("cat /app/hello.txt", stdout=stdout_buffer)
        detached = sandbox.run_command("cat", ["/app/hello.txt"], detached=True)

        assert command.exit_code == 0
        assert command.stdout() == "hello from sandbox\n"
        assert stdout_buffer.getvalue() == "hello from sandbox\n"
        assert sandbox.read_file("/app/data.bin", encoding="base64") == "YWJj"

        finished = detached.wait()
        assert finished.exit_code == 0
        assert detached.output() == "hello from sandbox\n"
        assert [message.data for message in detached.logs()] == ["hello from sandbox\n"]


def test_async_sandbox_api_runs_commands_and_detached_handles() -> None:
    async def exercise() -> None:
        stdout_buffer = StringIO()

        async with await AsyncSandbox.create(SandboxOptions(cwd="/app")) as sandbox:
            assert sandbox.domain is None

            await sandbox.write_files({
                "/app/hello.txt": "hello from async sandbox\n",
                "/app/data.bin": b"xyz",
            })
            await sandbox.mk_dir("/app/logs", recursive=True)

            command = await sandbox.run_command("cat /app/hello.txt", stdout=stdout_buffer)
            detached = await sandbox.run_command("cat", ["/app/hello.txt"], detached=True)

            assert command.exit_code == 0
            assert await command.stdout() == "hello from async sandbox\n"
            assert stdout_buffer.getvalue() == "hello from async sandbox\n"
            assert await sandbox.read_file("/app/data.bin", encoding="base64") == "eHl6"

            finished = await detached.wait()
            assert finished.exit_code == 0
            assert await detached.output() == "hello from async sandbox\n"
            messages: list[str] = []
            async for message in detached.logs():
                messages.append(message.data)
            assert messages == ["hello from async sandbox\n"]

    asyncio.run(exercise())
