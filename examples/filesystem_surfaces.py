from __future__ import annotations

from datetime import UTC, datetime

from just_bash import Bash, FileInit, LazyFile


def main() -> None:
    seeded_mtime = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)

    with Bash(
        cwd="/workspace",
        files={
            "/workspace/meta.txt": FileInit(content="meta\n", mode=0o640, mtime=seeded_mtime),
            "/workspace/lazy.txt": LazyFile(provider=lambda: "lazy content\n"),
        },
    ) as bash:
        print("=== Filesystem surfaces ===")
        print(f"exists(meta.txt)={bash.fs.exists('meta.txt')}")

        stat = bash.fs.stat("meta.txt")
        print(f"mode={oct(stat.mode)}")
        print(f"mtime={stat.mtime.isoformat()}")
        print(f"lazy={bash.fs.read_text('lazy.txt').strip()}")

        bash.fs.mkdir("docs")
        bash.fs.write_text("docs/note.txt", "from bash.fs\n")
        bash.fs.cp("docs/note.txt", "copy.txt")
        bash.exec("ln -s copy.txt link.txt")

        print(f"listing={','.join(sorted(bash.fs.readdir('.')))}")
        print(f"link={bash.fs.readlink('link.txt')}")
        print(f"realpath={bash.fs.realpath('link.txt')}")
        print(f"copy={bash.fs.read_text('copy.txt').strip()}")


if __name__ == "__main__":
    main()
