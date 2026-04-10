from __future__ import annotations

import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_PACKAGE_ROOT = Path("src") / "just_bash"
_RUNTIME_ROOT = _PACKAGE_ROOT / "_vendor" / "just-bash"
_BUILD_SCRIPT = Path("tools") / "build_packaged_runtime.sh"
_MISSING_RUNTIME_MESSAGE = (
    "Could not assemble the packaged just-bash runtime. "
    "Build vendor/just-bash first with `make bootstrap-just-bash`, or build from an sdist "
    "that already contains the packaged runtime payload."
)


class JustBashBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        del version, build_data

        project_root = Path(self.root)
        runtime_root = project_root / _RUNTIME_ROOT
        if source_vendor_checkout_build_ready(project_root):
            build_script = project_root / _BUILD_SCRIPT
            if not build_script.exists():
                raise RuntimeError(f"Missing packaged runtime build script: {build_script}")

            completed = subprocess.run(
                ["bash", str(build_script)],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"{_MISSING_RUNTIME_MESSAGE}\n\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
                )

            if not packaged_runtime_ready(runtime_root):
                raise RuntimeError(
                    f"Packaged runtime build finished without producing the expected runtime payload at {runtime_root}",
                )

            return

        if packaged_runtime_ready(runtime_root):
            return

        raise RuntimeError(_MISSING_RUNTIME_MESSAGE)


def source_vendor_checkout_build_ready(project_root: Path) -> bool:
    vendor_root = project_root.parent / "vendor" / "just-bash"
    required_files = (
        "package.json",
        "dist/index.js",
        "dist/bin/just-bash.js",
        "dist/bin/shell/shell.js",
        "src/commands/python3/worker.js",
    )
    return (
        all(vendor_root.joinpath(relative_path).is_file() for relative_path in required_files)
        and vendor_root.joinpath("node_modules").is_dir()
    )


def packaged_runtime_ready(runtime_root: Path) -> bool:
    if not runtime_root.joinpath("package.json").is_file():
        return False

    entry_candidates = (
        runtime_root / "dist" / "index.js",
        runtime_root / "dist" / "bundle" / "index.js",
    )
    if not any(path.is_file() for path in entry_candidates):
        return False

    cli_candidates = (
        runtime_root / "dist" / "bin" / "just-bash.js",
        runtime_root / "dist" / "bin" / "shell" / "shell.js",
    )
    if not all(path.is_file() for path in cli_candidates):
        return False

    return runtime_root.joinpath("vendor", "cpython-emscripten").is_dir()
