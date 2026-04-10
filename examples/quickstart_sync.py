from __future__ import annotations

from just_bash import Bash


def main() -> None:
    with Bash(cwd="/workspace") as bash:
        bash.exec("export NAME=alice; echo 'hello from the shared filesystem' > greeting.txt; cd /tmp")

        print("shell state resets, filesystem persists")
        result = bash.exec('printf "name=%s cwd=%s file=%s\n" "${NAME:-missing}" "$PWD" "$(cat greeting.txt)"')
        print(result.stdout, end="")

        bash.fs.write_text("note.txt", "written via bash.fs\n")
        print("\nread_text('note.txt')")
        print(bash.read_text("note.txt"), end="")


if __name__ == "__main__":
    main()
