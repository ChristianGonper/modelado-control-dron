from __future__ import annotations

import csv
import json
from dataclasses import replace

import numpy as np

from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import ScenarioDisturbanceConfig, ScenarioMetadata, ScenarioTelemetryConfig, build_minimal_scenario
from simulador_multirotor.telemetry import export_history_to_csv, export_history_to_json, export_history_to_numpy


def _read_csv_rows(path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def test_telemetry_schema_records_errors_and_events() -> None:
    history = SimulationRunner().run(build_minimal_scenario())

    first_step = history.steps[0]
    last_step = history.steps[-1]

    assert first_step.error.position_norm_m > 0.0
    assert first_step.events[0].kind == "simulation_start"
    assert last_step.events[-1].kind == "simulation_complete"
    assert history.telemetry_metadata["detail_level"] == "standard"
    assert history.vehicle_metadata["mass_kg"] == history.scenario_metadata["vehicle"]["mass_kg"]
    assert history.controller_metadata["kind"] == "cascade"
    assert history.scenario_metadata["telemetry"]["detail_level"] == "standard"


def test_telemetry_preserves_true_and_observed_state_separately() -> None:
    scenario = replace(
        build_minimal_scenario(),
        metadata=ScenarioMetadata(name="noisy-telemetry", seed=7),
        disturbances=ScenarioDisturbanceConfig(
            enabled=True,
            observation_position_noise_std_m=0.05,
            observation_velocity_noise_std_m_s=0.01,
        ),
    )

    history = SimulationRunner().run(scenario)
    step = history.steps[0]
    payload = step.to_dict(detail_level="full")

    assert step.observation.true_state.time_s == step.observation.observed_state.time_s
    assert step.observation.true_state != step.observation.observed_state
    assert payload["observation"]["true_state"]["time_s"] == step.observation.true_state.time_s
    assert payload["observation"]["observed_state"]["time_s"] == step.observation.observed_state.time_s


def test_export_formats_preserve_metadata_and_detail_level_control(tmp_path) -> None:
    compact_scenario = replace(
        build_minimal_scenario(),
        telemetry=ScenarioTelemetryConfig(detail_level="compact", sample_dt_s=0.08),
    )
    full_scenario = replace(
        build_minimal_scenario(),
        telemetry=ScenarioTelemetryConfig(detail_level="full"),
    )

    compact_history = SimulationRunner().run(compact_scenario)
    full_history = SimulationRunner().run(full_scenario)

    csv_path = export_history_to_csv(compact_history, tmp_path / "telemetry.csv")
    csv_rows = _read_csv_rows(csv_path)
    assert len(csv_rows) < len(compact_history.steps)
    assert "observation_position_x_m" not in csv_rows[0]
    assert csv_rows[0]["event_kinds_json"]

    json_path = export_history_to_json(full_history, tmp_path / "telemetry.json")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["telemetry"]["detail_level"] == "full"
    assert payload["scenario"]["metadata"]["name"] == full_scenario.metadata.name
    assert payload["vehicle"]["mass_kg"] == full_scenario.vehicle.mass_kg
    assert payload["controller"]["kind"] == "cascade"
    assert "observation_position_x_m" in payload["samples"][0]
    assert len(payload["samples"]) == len(full_history.steps)

    npz_path = export_history_to_numpy(full_history, tmp_path / "telemetry.npz")
    with np.load(npz_path, allow_pickle=False) as archive:
        metadata = json.loads(archive["metadata_json"].item())
        assert int(archive["sample_count"]) == len(full_history.steps)
        assert metadata["telemetry"]["detail_level"] == "full"
        assert metadata["vehicle"]["mass_kg"] == full_scenario.vehicle.mass_kg
        assert archive["state_position_m"].shape[1] == 3
