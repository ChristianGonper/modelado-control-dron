from __future__ import annotations

import json

import pytest

from simulador_multirotor.app import main
from simulador_multirotor.metrics import compute_tracking_metrics
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import load_simulation_scenario, reference_scenario_path, save_simulation_scenario


def test_external_scenario_round_trip_preserves_simulation_behavior(tmp_path) -> None:
    source_path = reference_scenario_path("hover")
    scenario = load_simulation_scenario(source_path)
    output_path = tmp_path / "hover-round-trip.json"

    save_simulation_scenario(scenario, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    loaded = load_simulation_scenario(output_path)

    assert payload["schema_version"] == 1
    assert loaded.to_dict() == scenario.to_dict()

    runner = SimulationRunner()
    original_history = runner.run(scenario)
    round_trip_history = runner.run(loaded)

    assert original_history.final_time_s == pytest.approx(round_trip_history.final_time_s, abs=1e-12)
    assert original_history.final_state.position_m == pytest.approx(round_trip_history.final_state.position_m, abs=1e-12)
    assert original_history.final_state.linear_velocity_m_s == pytest.approx(
        round_trip_history.final_state.linear_velocity_m_s,
        abs=1e-12,
    )
    assert compute_tracking_metrics(original_history).to_dict() == compute_tracking_metrics(round_trip_history).to_dict()


def test_cli_executes_reference_scenario() -> None:
    scenario_path = reference_scenario_path("hover")

    assert main(["--scenario", str(scenario_path)]) == 0
