from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.support.harness import (
    BackendArtifacts,
    run_async_differential_scenario,
    session_snapshot_operations,
)
from tests.support.parity_cases import initial_state_strategy, operation_strategy

pytestmark = [pytest.mark.parity, pytest.mark.generated]


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
    ],
)
@given(
    init_kwargs=initial_state_strategy(),
    operations=st.lists(operation_strategy(), min_size=1, max_size=8),
)
def test_async_generated_transcripts_match_upstream(
    init_kwargs: dict[str, Any],
    operations: list[dict[str, Any]],
    backend_artifacts: BackendArtifacts,
) -> None:
    python_result, reference_result = run_async_differential_scenario(
        init_kwargs=init_kwargs,
        operations=[*operations, *session_snapshot_operations(root="/workspace")],
        backend_artifacts=backend_artifacts,
    )

    assert python_result == reference_result
