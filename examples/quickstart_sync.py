from __future__ import annotations

from just_py_bash import Bash, ExecutionLimits


def main() -> None:
    with Bash(
        cwd="/workspace",
        files={"/workspace/hello.txt": "hello from just-py-bash\n"},
        execution_limits=ExecutionLimits(max_command_count=500),
    ) as bash:
        result = bash.exec("cat hello.txt")
        print("cat hello.txt")
        print(result.stdout, end="")

        bash.write_text("note.txt", "written from Python\n")
        listing = bash.exec("ls -1")
        print("\nls -1")
        print(listing.stdout, end="")

        note = bash.read_text("note.txt")
        print("\nread_text('note.txt')")
        print(note, end="")


if __name__ == "__main__":
    main()
