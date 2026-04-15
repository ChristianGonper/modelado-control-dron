from __future__ import annotations

import json
from dataclasses import replace
from math import cos, sin

import pytest

from simulador_multirotor.core.attitude import quaternion_from_euler
from simulador_multirotor.core.contracts import TrajectoryReference, VehicleCommand, VehicleState
from simulador_multirotor.dataset import (
    DatasetEpisode,
    DatasetExtractionError,
    DatasetSample,
    PHASE2_DATASET_CONTRACT,
    build_feature_vector,
    build_target_vector,
    extract_dataset_episode,
    feature_dimension_for_mode,
    feature_names_for_mode,
    load_dataset_episode,
)
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import ScenarioDisturbanceConfig, ScenarioMetadata, build_minimal_scenario
from simulador_multirotor.telemetry import export_history_to_json


def _make_sample() -> DatasetSample:
    observed_orientation = quaternion_from_euler(0.0, 0.0, 0.25)
    true_state = VehicleState(
        position_m=(1.0, 2.0, 3.0),
        orientation_wxyz=observed_orientation,
        linear_velocity_m_s=(4.0, 5.0, 6.0),
        angular_velocity_rad_s=(7.0, 8.0, 9.0),
        time_s=0.5,
    )
    observed_state = VehicleState(
        position_m=(1.1, 2.1, 3.1),
        orientation_wxyz=observed_orientation,
        linear_velocity_m_s=(4.1, 5.1, 6.1),
        angular_velocity_rad_s=(7.0, 8.0, 9.0),
        time_s=0.5,
    )
    reference = TrajectoryReference(
        time_s=0.5,
        position_m=(10.0, 11.0, 12.0),
        velocity_m_s=(13.0, 14.0, 15.0),
        yaw_rad=1.0,
        valid_from_s=0.0,
        acceleration_m_s2=(16.0, 17.0, 18.0),
    )
    command = VehicleCommand(collective_thrust_newton=9.81, body_torque_nm=(0.1, 0.2, 0.3))
    return DatasetSample(
        index=0,
        time_s=0.5,
        true_state=true_state,
        observed_state=observed_state,
        reference=reference,
        command=command,
        metadata={"episode_id": "episode-1"},
    )


def test_dataset_contract_feature_dimensions_and_order() -> None:
    sample = _make_sample()

    raw_features = build_feature_vector(sample, "raw_observation")
    error_features = build_feature_vector(sample, "observation_plus_tracking_errors")

    assert PHASE2_DATASET_CONTRACT.schema_version == 1
    assert feature_names_for_mode("raw_observation")[0] == "observed_position_x_m"
    assert feature_dimension_for_mode("raw_observation") == 24
    assert feature_dimension_for_mode("observation_plus_tracking_errors") == 32
    assert len(raw_features) == 24
    assert len(error_features) == 32
    assert raw_features[:3] == pytest.approx((1.1, 2.1, 3.1))
    assert raw_features[3:6] == pytest.approx((4.1, 5.1, 6.1))
    assert raw_features[6:10] == pytest.approx(sample.observed_state.orientation_wxyz)
    assert raw_features[13:16] == pytest.approx((10.0, 11.0, 12.0))
    assert raw_features[19:22] == pytest.approx((16.0, 17.0, 18.0))
    assert raw_features[22] == pytest.approx(sin(1.0))
    assert raw_features[23] == pytest.approx(cos(1.0))
    position_error, velocity_error, yaw_error = sample.tracking_error_observed
    assert error_features[24:27] == pytest.approx(position_error)
    assert error_features[27:30] == pytest.approx(velocity_error)
    assert error_features[30] == pytest.approx(sin(yaw_error))
    assert error_features[31] == pytest.approx(cos(yaw_error))
    assert build_target_vector(sample) == pytest.approx((9.81, 0.1, 0.2, 0.3))


def test_dataset_extraction_preserves_traceability_and_shapes(tmp_path) -> None:
    scenario = replace(
        build_minimal_scenario(),
        metadata=ScenarioMetadata(name="phase2-dataset", seed=42),
        disturbances=ScenarioDisturbanceConfig(
            enabled=True,
            observation_position_noise_std_m=0.01,
            observation_velocity_noise_std_m_s=0.01,
        ),
    )
    history = SimulationRunner().run(scenario)
    telemetry_path = export_history_to_json(history, tmp_path / "telemetry.json")

    episode = load_dataset_episode(telemetry_path)

    assert episode.sample_count == len(history.steps)
    assert episode.traceability.scenario_name == "phase2-dataset"
    assert episode.traceability.scenario_seed == 42
    assert episode.traceability.controller_kind == "cascade"
    assert "observation_noise" in episode.traceability.disturbance_regime
    assert episode.split_key[0] == episode.trajectory_kind
    assert episode.feature_matrix("raw_observation").shape[1] == 24
    assert episode.feature_matrix("observation_plus_tracking_errors").shape[1] == 32
    assert episode.target_matrix.shape[1] == 4
    assert episode.samples[0].observation.observed_state == episode.samples[0].observed_state


def test_dataset_extractor_rejects_missing_metadata(tmp_path) -> None:
    scenario = replace(
        build_minimal_scenario(),
        metadata=ScenarioMetadata(name="broken-dataset", seed=7),
    )
    history = SimulationRunner().run(scenario)
    telemetry_path = export_history_to_json(history, tmp_path / "telemetry.json")
    payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
    payload["scenario"].pop("metadata", None)
    telemetry_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetExtractionError, match="scenario.metadata"):
        extract_dataset_episode(telemetry_path)


def test_dataset_extractor_rejects_missing_columns(tmp_path) -> None:
    scenario = replace(
        build_minimal_scenario(),
        metadata=ScenarioMetadata(name="broken-columns", seed=9),
    )
    history = SimulationRunner().run(scenario)
    telemetry_path = export_history_to_json(history, tmp_path / "telemetry.json")
    payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
    payload["samples"][0].pop("observed_state_position_x_m", None)
    telemetry_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetExtractionError, match="observed_state_position_x_m"):
        load_dataset_episode(telemetry_path)
