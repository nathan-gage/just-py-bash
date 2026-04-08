from __future__ import annotations

from just_py_bash import Bash, CommandFailedError


def test_backend_version_is_exposed() -> None:
    with Bash() as bash:
        assert bash.backend_version
        assert isinstance(bash.get_env(), dict)


def test_exec_result_check_raises_for_non_zero_exit_codes() -> None:
    with Bash() as bash:
        result = bash.exec("false")

    assert result.exit_code == 1
    try:
        result.check()
    except CommandFailedError as exc:
        assert exc.result.exit_code == 1
    else:  # pragma: no cover - defensive
        raise AssertionError("expected CommandFailedError")


def test_sessions_are_isolated() -> None:
    with Bash() as left, Bash() as right:
        left.exec("echo left > only-here.txt")

        left_contents = left.exec("cat only-here.txt")
        right_contents = right.exec("cat only-here.txt")

    assert left_contents.stdout == "left\n"
    assert right_contents.exit_code != 0


def test_read_write_helpers_round_trip_text_and_bytes() -> None:
    with Bash(cwd="/workspace") as bash:
        bash.write_text("note.txt", "hello\n")
        bash.write_bytes("blob.bin", b"\x00\x01abc")

        text = bash.read_text("note.txt")
        blob = bash.read_bytes("blob.bin")

    assert text == "hello\n"
    assert blob == b"\x00\x01abc"
