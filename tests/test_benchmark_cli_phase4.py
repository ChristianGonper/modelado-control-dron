from __future__ import annotations

import json
from dataclasses import replace

import pytest

from simulador_multirotor.app import main
from simulador_multirotor.dataset import load_dataset_episode
from simulador_multirotor.dataset.artifacts import prepare_dataset_artifacts
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    build_minimal_scenario,
)
from simulador_multirotor.telemetry import export_history_to_json


def _benchmark_training_scenario(seed: int) -> object:
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
            parameters={"scenario": "phase4-benchmark-cli"},
        ),
        disturbances=ScenarioDisturbanceConfig(enabled=False),
        metadata=ScenarioMetadata(name="phase4-benchmark-cli", seed=seed),
    )


def _benchmark_episodes(tmp_path, seeds: tuple[int, ...]) -> tuple[object, ...]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    episodes = []
    for index, seed in enumerate(seeds):
        scenario = _benchmark_training_scenario(seed)
        history = SimulationRunner().run(scenario)
        telemetry_path = export_history_to_json(history, tmp_path / f"telemetry-{index}.json")
        episodes.append(load_dataset_episode(telemetry_path))
    return tuple(episodes)


def _prepare_dataset_artifact(tmp_path) -> object:
    episodes = _benchmark_episodes(tmp_path / "telemetry", (11, 12, 13, 14))
    telemetry_paths = [episode.traceability.source_path for episode in episodes]
    dataset_dir = tmp_path / "dataset"
    return prepare_dataset_artifacts(
        [path for path in telemetry_paths if path is not None],
        output_dir=dataset_dir,
        seed=21,
        split_seed=21,
        feature_mode="observation_plus_tracking_errors",
    )


def _train_main_benchmark_checkpoints(tmp_path, *, workspace, run_id: str) -> None:
    dataset_result = _prepare_dataset_artifact(tmp_path)
    common_args = [
        "--dataset",
        str(dataset_result.output_dir),
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--seed",
        "21",
        "--split-seed",
        "21",
        "--feature-mode",
        "observation_plus_tracking_errors",
        "--epochs",
        "1",
        "--batch-size",
        "4",
        "--learning-rate",
        "0.001",
    ]

    assert (
        main(
            [
                "neural",
                "train",
                "mlp",
                *common_args,
                "--window-size",
                "30",
                "--stride",
                "10",
                "--hidden-layers",
                "16,8",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "neural",
                "train",
                "gru",
                *common_args,
                "--hidden-size",
                "16",
                "--num-layers",
                "1",
                "--dropout",
                "0.0",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "neural",
                "train",
                "lstm",
                *common_args,
                "--hidden-size",
                "16",
                "--num-layers",
                "1",
                "--dropout",
                "0.0",
            ]
        )
        == 0
    )


def test_neural_benchmark_main_cli_uses_conventional_checkpoints_and_persists_artifacts(tmp_path, capsys) -> None:
    workspace = tmp_path / "artifacts" / "neural"
    run_id = "phase4-main-benchmark"
    _train_main_benchmark_checkpoints(tmp_path, workspace=workspace, run_id=run_id)
    capsys.readouterr()

    exit_code = main(
        [
            "neural",
            "benchmark",
            "main",
            "--workspace",
            str(workspace),
            "--run-id",
            run_id,
        ]
    )

    captured = capsys.readouterr()
    benchmark_dir = workspace / run_id / "benchmark" / "main"
    benchmark_path = benchmark_dir / "benchmark.json"
    manifest_path = benchmark_dir / "manifest.json"
    summary_path = benchmark_dir / "benchmark-summary.md"

    assert exit_code == 0
    assert "benchmark_path:" in captured.out
    assert "benchmark_manifest:" in captured.out
    assert "benchmark_summary:" in captured.out
    assert "scenario_set_key: main-homogeneous-v1" in captured.out
    assert benchmark_path.exists()
    assert manifest_path.exists()
    assert summary_path.exists()

    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary_text = summary_path.read_text(encoding="utf-8")

    assert payload["benchmark_kind"] == "main"
    assert payload["scenario_set_key"] == "main-homogeneous-v1"
    assert payload["command"] == "multirotor-sim neural benchmark main"
    assert payload["argv"] == [
        "neural",
        "benchmark",
        "main",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
    ]
    assert len(payload["results"]) == 5
    assert payload["checkpoint_paths"]["mlp"] == str(workspace / run_id / "train" / "mlp" / "checkpoint.pt")
    assert payload["results"][0]["baseline"]["cpu_inference_time_s_total"] > 0.0
    assert payload["results"][0]["mlp"]["trace"]["time_s"]
    assert payload["results"][0]["gru"]["cpu_inference_time_s_mean"] > 0.0
    assert payload["results"][0]["lstm"]["compute_action_count"] > 0

    assert manifest["artifact_kind"] == "benchmark"
    assert manifest["benchmark_kind"] == "main"
    assert manifest["scenario_set_key"] == "main-homogeneous-v1"
    assert manifest["checkpoint_paths"]["gru"] == str(workspace / run_id / "train" / "gru" / "checkpoint.pt")
    assert manifest["checkpoint_artifacts"]["mlp"]["training"]["feature_mode"] == "observation_plus_tracking_errors"
    assert manifest["checkpoint_artifacts"]["gru"]["training"]["architecture"] == "gru"
    assert manifest["checkpoint_artifacts"]["lstm"]["training"]["architecture"] == "lstm"
    assert "Main Benchmark Summary" in summary_text
    assert "checkpoint:" in summary_text
    assert "scenario_set_key" in summary_text


def test_neural_benchmark_main_cli_rejects_missing_checkpoint_path(tmp_path, capsys) -> None:
    workspace = tmp_path / "artifacts" / "neural"
    run_id = "phase4-main-missing"
    _train_main_benchmark_checkpoints(tmp_path, workspace=workspace, run_id=run_id)
    capsys.readouterr()

    missing_checkpoint = workspace / run_id / "train" / "lstm" / "checkpoint-missing.pt"
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "neural",
                "benchmark",
                "main",
                "--mlp-checkpoint",
                str(workspace / run_id / "train" / "mlp" / "checkpoint.pt"),
                "--gru-checkpoint",
                str(workspace / run_id / "train" / "gru" / "checkpoint.pt"),
                "--lstm-checkpoint",
                str(missing_checkpoint),
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "benchmark main checkpoint does not exist" in captured.err


def test_neural_benchmark_main_cli_rejects_invalid_checkpoint_combination(tmp_path, capsys) -> None:
    workspace = tmp_path / "artifacts" / "neural"
    run_id = "phase4-main-invalid"
    _train_main_benchmark_checkpoints(tmp_path, workspace=workspace, run_id=run_id)
    capsys.readouterr()

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "neural",
                "benchmark",
                "main",
                "--mlp-checkpoint",
                str(workspace / run_id / "train" / "mlp" / "checkpoint.pt"),
                "--gru-checkpoint",
                str(workspace / run_id / "train" / "lstm" / "checkpoint.pt"),
                "--lstm-checkpoint",
                str(workspace / run_id / "train" / "gru" / "checkpoint.pt"),
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "does not contain a GRU controller" in captured.err
