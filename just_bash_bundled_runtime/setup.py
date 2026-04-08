from __future__ import annotations

from pathlib import Path

from setuptools import Distribution, setup
from setuptools.command.build_py import build_py


class BinaryDistribution(Distribution):
    def has_ext_modules(self) -> bool:
        return True


class VerifiedBuildPy(build_py):
    def run(self) -> None:
        package_root = Path(__file__).resolve().parent / "src" / "just_bash_bundled_runtime"
        runtime_root = package_root / "runtime"
        metadata_path = package_root / "runtime-metadata.json"
        if not runtime_root.exists() or not metadata_path.exists():
            raise RuntimeError(
                "Bundled Node runtime is missing. Run `python scripts/vendor_node_provider.py --package-dir just_bash_bundled_runtime` first.",
            )
        super().run()


setup(distclass=BinaryDistribution, cmdclass={"build_py": VerifiedBuildPy})
