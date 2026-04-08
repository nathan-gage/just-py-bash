from __future__ import annotations

import asyncio

from just_py_bash import AsyncBash


async def main() -> None:
    async with AsyncBash(cwd="/workspace") as bash:
        await bash.write_text("note.txt", "hello from async just-py-bash\n")

        result = await bash.exec("cat note.txt")
        print("cat note.txt")
        print(result.stdout, end="")

        cwd = await bash.get_cwd()
        env = await bash.get_env()
        print(f"\ncwd={cwd}")
        print(f"env vars available={len(env)}")


if __name__ == "__main__":
    asyncio.run(main())
