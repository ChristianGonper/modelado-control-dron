from __future__ import annotations

import pytest

from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import build_minimal_scenario


def test_minimal_runner_executes_end_to_end() -> None:
    scenario = build_minimal_scenario()
    history = SimulationRunner().run(scenario)

    assert len(history.steps) > 0
    assert history.final_time_s == pytest.approx(scenario.duration_s, abs=1e-9)
    assert history.final_state.position_m[2] > history.initial_state.position_m[2]

