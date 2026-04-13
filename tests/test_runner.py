from __future__ import annotations

from dataclasses import replace

import pytest

from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import ScenarioTrajectoryConfig, build_minimal_scenario


@pytest.mark.parametrize(
    ("kind", "parameters"),
    [
        (
            "line",
            {
                "start_position_m": (0.0, 0.0, 0.0),
                "velocity_m_s": (1.0, 0.0, 0.0),
            },
        ),
        (
            "circle",
            {
                "center_m": (0.0, 0.0, 1.0),
                "radius_m": 1.0,
                "angular_speed_rad_s": 2.0 * 3.141592653589793,
                "start_phase_rad": 0.0,
            },
        ),
    ],
)
def test_runner_executes_scenarios_with_native_trajectories(kind: str, parameters: dict[str, object]) -> None:
    scenario = replace(
        build_minimal_scenario(),
        trajectory=ScenarioTrajectoryConfig(
            kind=kind,
            valid_until_s=0.4,
            parameters=parameters,
        ),
    )

    history = SimulationRunner().run(scenario)

    assert len(history.steps) > 0
    assert history.final_time_s == pytest.approx(scenario.duration_s, abs=1e-9)
    assert history.steps[0].reference.metadata["trajectory_kind"] == kind
    assert history.steps[0].events[0].kind == "simulation_start"
