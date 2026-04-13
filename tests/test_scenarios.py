from __future__ import annotations

from dataclasses import replace

import pytest

from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTelemetryConfig,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    build_minimal_scenario,
)
from simulador_multirotor.trajectories import TrajectoryContract


def test_minimal_scenario_uses_reasonable_defaults() -> None:
    scenario = build_minimal_scenario()

    assert scenario.trajectory.kind == "hover"
    assert scenario.time.duration_s == pytest.approx(1.0)
    assert scenario.time.dt_s == pytest.approx(0.02)
    assert isinstance(scenario.build_trajectory(), TrajectoryContract)
    assert scenario.reference_at(0.0).position_m == (0.0, 0.0, 1.0)


def test_scenario_trajectory_selection_is_registry_driven() -> None:
    scenario = replace(
        build_minimal_scenario(),
        trajectory=ScenarioTrajectoryConfig(
            kind="line",
            valid_until_s=1.0,
            parameters={
                "start_position_m": (0.0, 0.0, 0.0),
                "velocity_m_s": (1.0, 0.0, 0.0),
            },
        ),
    )

    reference = scenario.reference_at(0.5)

    assert reference.position_m == pytest.approx((0.5, 0.0, 0.0))
    assert reference.metadata["trajectory_kind"] == "line"


def test_scenario_validation_reports_clear_errors() -> None:
    with pytest.raises(ValueError, match="positive"):
        ScenarioTimeConfig(duration_s=0.0, dt_s=0.02)


def test_telemetry_detail_level_is_validated() -> None:
    with pytest.raises(ValueError, match="detail_level"):
        ScenarioTelemetryConfig(detail_level="verbose")


def test_runner_reads_time_and_metadata_from_scenario() -> None:
    scenario = replace(
        build_minimal_scenario(),
        time=ScenarioTimeConfig(duration_s=0.06, dt_s=0.03),
        metadata=ScenarioMetadata(name="custom-run", seed=17, tags=("phase-2",)),
    )

    history = SimulationRunner().run(scenario)

    assert history.final_time_s == pytest.approx(0.06, abs=1e-12)
    assert len(history.steps) == 2
    assert history.scenario_metadata["metadata"]["name"] == "custom-run"
    assert history.scenario_metadata["metadata"]["seed"] == 17
    assert history.steps[0].reference.metadata["trajectory_kind"] == "hover"


def test_seeded_noise_is_reproducible_and_centralized() -> None:
    base_scenario = build_minimal_scenario()
    noisy_scenario = replace(
        base_scenario,
        metadata=ScenarioMetadata(name="noisy-run", seed=42),
        disturbances=ScenarioDisturbanceConfig(
            enabled=True,
            observation_position_noise_std_m=0.02,
            observation_velocity_noise_std_m_s=0.01,
        ),
    )
    different_seed = replace(noisy_scenario, metadata=ScenarioMetadata(name="noisy-run", seed=99))

    first = SimulationRunner().run(noisy_scenario)
    second = SimulationRunner().run(noisy_scenario)
    third = SimulationRunner().run(different_seed)

    assert first == second
    assert first != third
