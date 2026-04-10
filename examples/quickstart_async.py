from __future__ import annotations

import asyncio

from just_bash import AsyncBash


async def main() -> None:
    async with AsyncBash(cwd="/workspace") as bash:
        await bash.exec("export NAME=alice; echo 'hello from async shared filesystem' > greeting.txt; cd /tmp")

        print("shell state resets, filesystem persists")
        result = await bash.exec('printf "name=%s cwd=%s file=%s\n" "${NAME:-missing}" "$PWD" "$(cat greeting.txt)"')
        print(result.stdout, end="")

        await bash.fs.write_text("note.txt", "written via async bash.fs\n")
        print("\nread_text('note.txt')")
        print(await bash.read_text("note.txt"), end="")


if __name__ == "__main__":
    asyncio.run(main())
