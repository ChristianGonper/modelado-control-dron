from __future__ import annotations

import json
from dataclasses import replace

import pytest

from simulador_multirotor.benchmark import run_homogeneous_mlp_benchmark
from simulador_multirotor.control import (
    FeatureNormalizationStats,
    MLPTrainingConfig,
    load_mlp_checkpoint,
    load_mlp_controller,
    train_mlp_checkpoint,
)
from simulador_multirotor.core.contracts import VehicleCommand
from simulador_multirotor.dataset import build_mlp_windows, feature_dimension_for_mode, split_dataset_episodes
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    build_minimal_scenario,
)
from simulador_multirotor.telemetry import export_history_to_json
from simulador_multirotor.dataset import load_dataset_episode


def _phase3_scenario(seed: int) -> object:
    return replace(
        build_minimal_scenario(seed=seed),
        time=ScenarioTimeConfig(
            duration_s=1.5,
            physics_dt_s=0.01,
            control_dt_s=0.02,
            telemetry_dt_s=0.02,
        ),
        trajectory=ScenarioTrajectoryConfig(
            kind="hover",
            target_position_m=(0.0, 0.0, 1.0),
            valid_until_s=1.5,
            source="native",
            parameters={"scenario": "phase3-mlp"},
        ),
        disturbances=ScenarioDisturbanceConfig(enabled=False),
        metadata=ScenarioMetadata(name="phase3-mlp", seed=seed),
    )


def _phase3_episodes(tmp_path, seeds: tuple[int, ...]) -> tuple[object, ...]:
    episodes = []
    for index, seed in enumerate(seeds):
        scenario = _phase3_scenario(seed)
        history = SimulationRunner().run(scenario)
        telemetry_path = export_history_to_json(history, tmp_path / f"telemetry-{index}.json")
        episodes.append(load_dataset_episode(telemetry_path))
    return tuple(episodes)


def test_mlp_training_round_trip_uses_train_only_normalization(tmp_path) -> None:
    episodes = _phase3_episodes(tmp_path, (11, 12, 13))
    config = MLPTrainingConfig(
        seed=21,
        feature_mode="observation_plus_tracking_errors",
        window_size=30,
        stride=10,
        hidden_layers=(32, 16),
        epochs=4,
        batch_size=4,
        learning_rate=1e-3,
    )

    result = train_mlp_checkpoint(episodes, checkpoint_path=tmp_path / "mlp.pt", config=config)
    checkpoint = load_mlp_checkpoint(result.checkpoint_path)

    assert result.checkpoint_path is not None
    assert result.checkpoint_path.exists()
    assert checkpoint.training == config
    assert checkpoint.architecture.input_dimension == config.window_size * feature_dimension_for_mode(config.feature_mode)
    assert checkpoint.feature_names[0] == "observed_position_x_m"
    assert checkpoint.target_names == ("collective_thrust_newton", "body_torque_x_nm", "body_torque_y_nm", "body_torque_z_nm")

    assignments = split_dataset_episodes(episodes, seed=config.effective_split_seed)
    train_windows = []
    for assignment in assignments:
        if assignment.split_name == "train":
            train_windows.extend(
                build_mlp_windows(
                    assignment,
                    window_size=config.window_size,
                    stride=config.stride,
                    feature_mode=config.feature_mode,
                )
            )
    expected_normalization = FeatureNormalizationStats.from_windows(
        train_windows,
        feature_mode=config.feature_mode,
        window_size=config.window_size,
    )
    assert checkpoint.normalization.mean == pytest.approx(expected_normalization.mean)
    assert checkpoint.normalization.std == pytest.approx(expected_normalization.std)
    assert len(result.history) == config.epochs
    assert result.train_window_count > 0
    assert result.validation_window_count > 0


def test_mlp_controller_loads_checkpoint_and_emits_valid_command(tmp_path) -> None:
    episodes = _phase3_episodes(tmp_path, (31, 32, 33))
    config = MLPTrainingConfig(seed=41, epochs=3, batch_size=4, hidden_layers=(16, 8))
    result = train_mlp_checkpoint(episodes, checkpoint_path=tmp_path / "controller.pt", config=config)

    controller = load_mlp_controller(result.checkpoint_path)
    sample = episodes[0].samples[0]
    command = controller.compute_action(sample.observation, sample.reference)

    assert isinstance(command, VehicleCommand)
    assert command.collective_thrust_newton >= 0.0
    assert len(command.body_torque_nm) == 3


def test_runner_executes_mlp_controller_without_special_paths(tmp_path) -> None:
    episodes = _phase3_episodes(tmp_path, (51, 52, 53))
    result = train_mlp_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "runner.pt",
        config=MLPTrainingConfig(seed=61, epochs=3, batch_size=4, hidden_layers=(16, 8)),
    )
    scenario = _phase3_scenario(51)
    controller = load_mlp_controller(result.checkpoint_path)

    history = SimulationRunner().run(scenario, controller=controller)

    assert len(history.steps) > 0
    assert history.controller_metadata["kind"] == "mlp"
    assert history.controller_metadata["source"] == "torch"


def test_homogeneous_benchmark_persists_comparable_artifacts(tmp_path) -> None:
    episodes = _phase3_episodes(tmp_path, (71, 72, 73))
    result = train_mlp_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "benchmark.pt",
        config=MLPTrainingConfig(seed=81, epochs=3, batch_size=4, hidden_layers=(16, 8)),
    )
    scenarios = (_phase3_scenario(91), _phase3_scenario(92))
    output_path = tmp_path / "benchmark.json"

    benchmark = run_homogeneous_mlp_benchmark(
        scenarios,
        checkpoint_path=result.checkpoint_path,
        output_path=output_path,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert benchmark.output_path == output_path
    assert len(benchmark.results) == 2
    assert payload["checkpoint_path"] == str(result.checkpoint_path)
    assert len(payload["results"]) == 2
    assert payload["results"][0]["baseline_metrics"]["sample_count"] > 0
    assert payload["results"][0]["comparison"]["sample_count"] > 0
