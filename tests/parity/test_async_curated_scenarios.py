from __future__ import annotations

from typing import Any

import pytest

from tests.support.harness import BackendArtifacts, run_async_differential_scenario
from tests.support.parity_cases import CURATED_SCENARIOS, ScenarioFactory

pytestmark = pytest.mark.parity


@pytest.mark.parametrize(
    ("name", "init_factory", "operations"),
    CURATED_SCENARIOS,
    ids=[f"async::{name}" for name, _, _ in CURATED_SCENARIOS],
)
def test_async_scenarios_match_upstream(
    name: str,
    init_factory: ScenarioFactory,
    operations: list[dict[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result, reference_result = run_async_differential_scenario(
        init_kwargs=init_factory(),
        operations=operations,
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result, name
