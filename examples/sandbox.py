from __future__ import annotations

from io import StringIO

from just_bash import Sandbox, SandboxOptions

print("=== Sandbox API ===")

stdout_buffer = StringIO()
with Sandbox.create(SandboxOptions(cwd="/app")) as sandbox:
    sandbox.write_files(
        {
            "/app/hello.txt": "hello from sandbox\n",
            "/app/script.sh": "printf 'script says hi\\n'\n",
        }
    )
    sandbox.mk_dir("/app/logs", recursive=True)

    command = sandbox.run_command("bash /app/script.sh", stdout=stdout_buffer)
    detached = sandbox.run_command("cat", ["/app/hello.txt"], detached=True)

    print(f"inline exit={command.exit_code} stdout={command.stdout().strip()}")
    print(f"captured stdout={stdout_buffer.getvalue().strip()}")

    finished = detached.wait()
    print(f"detached exit={finished.exit_code} stdout={detached.stdout().strip()}")
    print(f"read_back={sandbox.read_file('/app/hello.txt').strip()}")
