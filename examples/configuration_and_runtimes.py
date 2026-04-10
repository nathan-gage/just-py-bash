from __future__ import annotations

from just_bash import Bash, JavaScriptConfig


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def show_runtime_result(name: str, stdout: str, stderr: str, exit_code: int) -> None:
    if exit_code == 0:
        print(stdout, end="")
        return

    detail = stderr.strip() or f"exit code {exit_code}"
    print(f"{name} unavailable in this backend build: {detail}")


def main() -> None:
    with Bash(
        cwd="/workspace",
        files={"/workspace/notes.txt": "alpha\nbeta\ngamma\n"},
        env={"GREETING": "hello"},
        python=True,
        javascript=JavaScriptConfig(bootstrap="globalThis.prefix = 'bootstrapped';"),
    ) as bash:
        section("Per-exec env and cwd overrides")
        print(bash.exec("printf '%s from %s\\n' \"$GREETING\" \"$(pwd)\"").stdout, end="")
        print(
            bash.exec(
                "printf '%s from %s\\n' \"$TEMP\" \"$(pwd)\"",
                env={"TEMP": "override"},
                cwd="/tmp",
            ).stdout,
            end="",
        )

        section("replace_env")
        print(
            bash.exec(
                "printf '%s / %s\\n' \"$ONLY\" \"${GREETING:-unset}\"",
                replace_env=True,
                env={"ONLY": "this"},
            ).stdout,
            end="",
        )

        section("stdin and args")
        print(bash.exec("cat", stdin="hello from stdin\n").stdout, end="")
        print(bash.exec("grep", args=["-n", "beta", "notes.txt"], cwd="/workspace").stdout, end="")

        section("raw_script")
        print(bash.exec("cat <<EOF\n  indented\nEOF", raw_script=True).stdout, end="")

        section("python runtime")
        python_result = bash.exec('python -c "print(sum([2, 3, 5]))"')
        show_runtime_result("python", python_result.stdout, python_result.stderr, python_result.exit_code)

        section("javascript runtime")
        javascript_result = bash.exec("js-exec -c 'console.log(globalThis.prefix + \":\" + (2 + 3))'")
        show_runtime_result(
            "js-exec",
            javascript_result.stdout,
            javascript_result.stderr,
            javascript_result.exit_code,
        )


if __name__ == "__main__":
    main()
