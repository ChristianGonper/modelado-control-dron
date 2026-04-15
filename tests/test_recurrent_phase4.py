from __future__ import annotations

import json
from dataclasses import replace

import pytest

from simulador_multirotor.benchmark import run_homogeneous_neural_benchmark
from simulador_multirotor.control import (
    FeatureNormalizationStats,
    MLPTrainingConfig,
    RecurrentTrainingConfig,
    load_gru_controller,
    load_lstm_controller,
    load_recurrent_checkpoint,
    train_gru_checkpoint,
    train_lstm_checkpoint,
    train_mlp_checkpoint,
)
from simulador_multirotor.dataset import (
    DatasetEpisode,
    build_recurrent_windows,
    feature_dimension_for_mode,
    load_dataset_episode,
    split_dataset_episodes,
)
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    build_minimal_scenario,
)
from simulador_multirotor.telemetry import export_history_to_json


def _phase4_scenario(seed: int) -> object:
    return replace(
        build_minimal_scenario(seed=seed),
        time=ScenarioTimeConfig(
            duration_s=4.0,
            physics_dt_s=0.01,
            control_dt_s=0.02,
            telemetry_dt_s=0.02,
        ),
        trajectory=ScenarioTrajectoryConfig(
            kind="hover",
            target_position_m=(0.0, 0.0, 1.0),
            valid_until_s=4.0,
            source="native",
            parameters={"scenario": "phase4-recurrent"},
        ),
        disturbances=ScenarioDisturbanceConfig(enabled=False),
        metadata=ScenarioMetadata(name="phase4-recurrent", seed=seed),
    )


def _phase4_episodes(tmp_path, seeds: tuple[int, ...]) -> tuple[DatasetEpisode, ...]:
    episodes: list[DatasetEpisode] = []
    for index, seed in enumerate(seeds):
        scenario = _phase4_scenario(seed)
        history = SimulationRunner().run(scenario)
        telemetry_path = export_history_to_json(history, tmp_path / f"telemetry-{index}.json")
        episodes.append(load_dataset_episode(telemetry_path))
    return tuple(episodes)


def _train_recurrent_model(
    architecture: str,
    episodes: tuple[DatasetEpisode, ...],
    tmp_path,
):
    config = RecurrentTrainingConfig(
        architecture=architecture,
        seed=21 if architecture == "gru" else 31,
        feature_mode="observation_plus_tracking_errors",
        hidden_size=16,
        epochs=2,
        batch_size=4,
        learning_rate=1e-3,
    )
    checkpoint_path = tmp_path / f"{architecture}.pt"
    if architecture == "gru":
        result = train_gru_checkpoint(episodes, checkpoint_path=checkpoint_path, config=config)
    else:
        result = train_lstm_checkpoint(episodes, checkpoint_path=checkpoint_path, config=config)
    return result


@pytest.mark.parametrize(
    ("architecture", "expected_window_size", "loader"),
    [
        ("gru", 100, load_gru_controller),
        ("lstm", 150, load_lstm_controller),
    ],
)
def test_recurrent_training_round_trip_preserves_sequence_metadata(
    architecture: str,
    expected_window_size: int,
    loader,
    tmp_path,
) -> None:
    episodes = _phase4_episodes(tmp_path, (11, 12, 13))
    result = _train_recurrent_model(architecture, episodes, tmp_path)
    checkpoint = load_recurrent_checkpoint(result.checkpoint_path)

    assert result.checkpoint_path is not None
    assert result.checkpoint_path.exists()
    assert checkpoint.training.architecture == architecture
    assert checkpoint.training.window_size == expected_window_size
    assert checkpoint.training.feature_mode == "observation_plus_tracking_errors"
    assert checkpoint.training.hidden_size == 16
    assert checkpoint.feature_names[0] == "observed_position_x_m"
    assert checkpoint.target_names == (
        "collective_thrust_newton",
        "body_torque_x_nm",
        "body_torque_y_nm",
        "body_torque_z_nm",
    )

    assignments = split_dataset_episodes(episodes, seed=checkpoint.training.effective_split_seed)
    train_windows = []
    for assignment in assignments:
        if assignment.split_name == "train":
            train_windows.extend(
                build_recurrent_windows(
                    assignment,
                    architecture=architecture,
                    window_size=expected_window_size,
                    stride=10,
                    feature_mode="observation_plus_tracking_errors",
                )
            )
    expected_dimension = feature_dimension_for_mode("observation_plus_tracking_errors")
    expected_normalization = FeatureNormalizationStats.from_windows(
        train_windows,
        feature_mode="observation_plus_tracking_errors",
        window_size=expected_window_size,
    )
    controller = loader(result.checkpoint_path)
    assert checkpoint.normalization.mean == pytest.approx(expected_normalization.mean)
    assert checkpoint.normalization.std == pytest.approx(expected_normalization.std)
    assert checkpoint.normalization.feature_dimension == expected_dimension
    assert controller.kind == architecture
    assert len(result.history) == 2
    assert result.train_window_count > 0
    assert result.validation_window_count > 0


@pytest.mark.parametrize(
    ("architecture", "loader"),
    [
        ("gru", load_gru_controller),
        ("lstm", load_lstm_controller),
    ],
)
def test_recurrent_controller_loads_checkpoint_and_runs_in_runner(
    architecture: str,
    loader,
    tmp_path,
) -> None:
    episodes = _phase4_episodes(tmp_path, (21, 22, 23))
    result = _train_recurrent_model(architecture, episodes, tmp_path)
    controller = loader(result.checkpoint_path)
    sample = episodes[0].samples[0]

    command = controller.compute_action(sample.observation, sample.reference)
    controller.reset()
    history = SimulationRunner().run(_phase4_scenario(21), controller=controller)

    assert command.collective_thrust_newton >= 0.0
    assert len(command.body_torque_nm) == 3
    assert history.controller_metadata["kind"] == architecture
    assert history.controller_metadata["source"] == "torch"
    assert len(history.steps) > 0


def test_main_benchmark_persists_comparable_results_and_cpu_timing(tmp_path) -> None:
    episodes = _phase4_episodes(tmp_path, (31, 32, 33))
    mlp_result = train_mlp_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "mlp.pt",
        config=MLPTrainingConfig(
            seed=41,
            feature_mode="observation_plus_tracking_errors",
            window_size=30,
            stride=10,
            hidden_layers=(16, 8),
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )
    gru_result = _train_recurrent_model("gru", episodes, tmp_path)
    lstm_result = _train_recurrent_model("lstm", episodes, tmp_path)
    scenarios = (_phase4_scenario(51), _phase4_scenario(52))
    output_path = tmp_path / "neural-benchmark.json"

    benchmark = run_homogeneous_neural_benchmark(
        scenarios,
        mlp_checkpoint_path=mlp_result.checkpoint_path,
        gru_checkpoint_path=gru_result.checkpoint_path,
        lstm_checkpoint_path=lstm_result.checkpoint_path,
        output_path=output_path,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert benchmark.output_path == output_path
    assert len(benchmark.results) == 2
    assert payload["checkpoint_paths"]["mlp"] == str(mlp_result.checkpoint_path)
    assert payload["checkpoint_paths"]["gru"] == str(gru_result.checkpoint_path)
    assert payload["checkpoint_paths"]["lstm"] == str(lstm_result.checkpoint_path)
    assert payload["results"][0]["baseline"]["cpu_inference_time_s_total"] > 0.0
    assert payload["results"][0]["mlp"]["metrics"]["sample_count"] > 0
    assert payload["results"][0]["gru"]["cpu_inference_time_s_mean"] > 0.0
    assert payload["results"][0]["lstm"]["compute_action_count"] > 0
    assert set(payload["results"][0]["comparisons"]) == {"mlp", "gru", "lstm"}
