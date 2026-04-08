from __future__ import annotations

import pytest

from tests.support.harness import public_api

pytestmark = pytest.mark.contract


def test_python_runtime_executes_when_enabled() -> None:
    Bash = public_api().Bash

    with Bash(python=True) as bash:
        result = bash.exec('python -c "print(sum([2, 3, 5]))"', timeout=30)

    assert result.exit_code == 0
    assert result.stdout == "10\n"
    assert result.stderr == ""


def test_javascript_runtime_executes_when_enabled() -> None:
    api = public_api()
    Bash = api.Bash
    JavaScriptConfig = api.JavaScriptConfig

    with Bash(javascript=JavaScriptConfig(bootstrap="globalThis.prefix = 'bootstrapped';")) as bash:
        result = bash.exec("js-exec -c 'console.log(globalThis.prefix + \":\" + (2 + 3))'", timeout=30)

    assert result.exit_code == 0
    assert result.stdout == "bootstrapped:5\n"
    assert result.stderr == ""
