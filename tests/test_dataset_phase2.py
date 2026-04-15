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
    DatasetSplitRatios,
    build_mlp_windows,
    build_recurrent_windows,
    PHASE2_DATASET_CONTRACT,
    build_feature_vector,
    build_target_vector,
    extract_dataset_episode,
    feature_dimension_for_mode,
    feature_names_for_mode,
    load_dataset_episode,
    split_dataset_episodes,
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


def _make_episode(
    episode_id: str,
    *,
    sample_count: int = 6,
    trajectory_kind: str = "hover",
    disturbance_regime: str = "nominal",
    scenario_name: str = "episode",
    scenario_seed: int | None = 1,
    controller_kind: str = "cascade",
    controller_source: str = "internal",
    feature_offset: float = 0.0,
) -> DatasetEpisode:
    samples: list[DatasetSample] = []
    for index in range(sample_count):
        sample = _make_sample()
        base = float(index) + feature_offset
        samples.append(
            replace(
                sample,
                index=index,
                time_s=base,
                true_state=replace(
                    sample.true_state,
                    time_s=base,
                    position_m=(base, base + 1.0, base + 2.0),
                    linear_velocity_m_s=(base + 3.0, base + 4.0, base + 5.0),
                ),
                observed_state=replace(
                    sample.observed_state,
                    time_s=base,
                    position_m=(base + 0.1, base + 1.1, base + 2.1),
                    linear_velocity_m_s=(base + 3.1, base + 4.1, base + 5.1),
                ),
                reference=replace(
                    sample.reference,
                    time_s=base,
                    position_m=(base + 10.0, base + 11.0, base + 12.0),
                    velocity_m_s=(base + 13.0, base + 14.0, base + 15.0),
                    yaw_rad=1.0 + index * 0.05,
                ),
                command=VehicleCommand(
                    collective_thrust_newton=9.81 + feature_offset,
                    body_torque_nm=(0.1 + base, 0.2 + base, 0.3 + base),
                ),
                metadata={"episode_id": episode_id, "sample_index": index},
            )
        )

    scenario_payload = {
        "metadata": {"name": scenario_name, "seed": scenario_seed},
        "trajectory": {"kind": trajectory_kind},
        "controller": {"kind": controller_kind, "source": controller_source},
        "disturbances": (
            {"enabled": False}
            if disturbance_regime == "nominal"
            else {"enabled": True, "wind_velocity_m_s": (0.2, 0.0, 0.0)}
            if disturbance_regime == "wind"
            else {"enabled": True, "wind_gust_std_m_s": (0.1, 0.0, 0.0)}
            if disturbance_regime == "gusts"
            else {"enabled": True}
        ),
        "time": {"dt_s": 0.1},
    }
    return DatasetEpisode(
        episode_id=episode_id,
        scenario_payload=scenario_payload,
        controller_metadata={"kind": controller_kind, "source": controller_source},
        telemetry_metadata={"detail_level": "standard", "tracking_state_source": "true_state"},
        samples=tuple(samples),
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


def test_split_is_deterministic_and_episode_level() -> None:
    episodes = (
        _make_episode("ep-a-1", trajectory_kind="hover", disturbance_regime="nominal", scenario_seed=11),
        _make_episode("ep-a-2", trajectory_kind="hover", disturbance_regime="nominal", scenario_seed=12),
        _make_episode("ep-a-3", trajectory_kind="hover", disturbance_regime="nominal", scenario_seed=13),
        _make_episode("ep-a-4", trajectory_kind="hover", disturbance_regime="nominal", scenario_seed=14),
        _make_episode("ep-a-5", trajectory_kind="hover", disturbance_regime="nominal", scenario_seed=15),
        _make_episode("ep-b-1", trajectory_kind="circle", disturbance_regime="wind", scenario_seed=21),
        _make_episode("ep-b-2", trajectory_kind="circle", disturbance_regime="wind", scenario_seed=22),
        _make_episode("ep-b-3", trajectory_kind="circle", disturbance_regime="wind", scenario_seed=23),
        _make_episode("ep-b-4", trajectory_kind="circle", disturbance_regime="wind", scenario_seed=24),
        _make_episode("ep-b-5", trajectory_kind="circle", disturbance_regime="wind", scenario_seed=25),
    )

    first = split_dataset_episodes(episodes, seed=77)
    second = split_dataset_episodes(tuple(reversed(episodes)), seed=77)
    assert [assignment.episode_id for assignment in first] == [assignment.episode_id for assignment in second]
    assert [assignment.split_name for assignment in first] == [assignment.split_name for assignment in second]

    per_bucket: dict[tuple[object, ...], list[str]] = {}
    for assignment in first:
        per_bucket.setdefault(assignment.bucket_key, []).append(assignment.split_name or "unassigned")
        assert assignment.split_context.metadata["split_ratios"] == DatasetSplitRatios().as_dict()
        assert assignment.split_context.metadata["bucket_key"]
        assert assignment.split_context.metadata["bucket_rank"] < assignment.split_context.metadata["bucket_size"]

    assert per_bucket[("hover", "nominal")].count("train") == 3
    assert per_bucket[("hover", "nominal")].count("validation") == 1
    assert per_bucket[("hover", "nominal")].count("test") == 1
    assert per_bucket[("circle", "wind")].count("train") == 3
    assert per_bucket[("circle", "wind")].count("validation") == 1
    assert per_bucket[("circle", "wind")].count("test") == 1


def test_mlp_windowing_respects_episode_boundaries_and_stride_metadata() -> None:
    episode = _make_episode("ep-window", sample_count=40, trajectory_kind="line", disturbance_regime="nominal")
    windows = build_mlp_windows(episode)

    assert len(windows) == 2
    assert windows[0].flattened is True
    assert windows[0].features.shape == (30 * feature_dimension_for_mode("observation_plus_tracking_errors"),)
    assert windows[0].stride == 10
    assert windows[0].window_size == 30
    assert windows[0].metadata["window_size"] == 30
    assert windows[0].metadata["stride"] == 10
    assert windows[0].metadata.get("split_name") is None
    assert windows[0].samples[0].index == 0
    assert windows[0].samples[-1].index == 29
    assert windows[1].samples[0].index == 10
    assert windows[1].samples[-1].index == 39
    assert windows[0].target == pytest.approx(episode.samples[29].target_vector)
    assert windows[1].target == pytest.approx(episode.samples[39].target_vector)


def test_windowing_inherits_split_and_recurrent_sequence_ordering() -> None:
    episode = _make_episode("ep-recurrent", sample_count=8, trajectory_kind="spiral", disturbance_regime="gusts")
    assignment = split_dataset_episodes((episode,), seed=5)[0]

    mlp_windows = build_mlp_windows(assignment, window_size=4, stride=2)
    gru_windows = build_recurrent_windows(assignment, architecture="gru", window_size=4, stride=2)
    lstm_windows = build_recurrent_windows(assignment, architecture="lstm", window_size=4, stride=2)

    assert len(mlp_windows) == 3
    assert len(gru_windows) == 3
    assert len(lstm_windows) == 3
    assert {window.split_name for window in mlp_windows} == {assignment.split_name}
    assert {window.split_name for window in gru_windows} == {assignment.split_name}
    assert {window.split_name for window in lstm_windows} == {assignment.split_name}

    gru_window = gru_windows[0]
    lstm_window = lstm_windows[0]
    assert gru_window.features.shape == (4, feature_dimension_for_mode("observation_plus_tracking_errors"))
    assert lstm_window.features.shape == (4, feature_dimension_for_mode("observation_plus_tracking_errors"))
    assert gru_window.is_temporal is True
    assert lstm_window.is_temporal is True
    assert gru_window.samples[0].index == 0
    assert gru_window.samples[-1].index == 3
    assert gru_window.features[0, 0] == pytest.approx(gru_window.samples[0].observed_state.position_m[0])
    assert gru_window.features[-1, 0] == pytest.approx(gru_window.samples[-1].observed_state.position_m[0])
    assert gru_window.metadata["architecture"] == "gru"
    assert lstm_window.metadata["architecture"] == "lstm"
    assert gru_window.metadata["window_size"] == 4
    assert gru_window.metadata["stride"] == 2
