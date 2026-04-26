from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from simulador_multirotor.app import main
from simulador_multirotor.control import (
    MLPTrainingConfig,
    RecurrentTrainingConfig,
    load_mlp_checkpoint,
    load_recurrent_checkpoint,
)
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


def _phase3_scenario(seed: int) -> object:
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
            parameters={"scenario": "phase3-cli"},
        ),
        disturbances=ScenarioDisturbanceConfig(enabled=False),
        metadata=ScenarioMetadata(name="phase3-cli", seed=seed),
    )


def _phase3_episodes(tmp_path, seeds: tuple[int, ...]) -> tuple[object, ...]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    episodes = []
    for index, seed in enumerate(seeds):
        scenario = _phase3_scenario(seed)
        history = SimulationRunner().run(scenario)
        telemetry_path = export_history_to_json(history, tmp_path / f"telemetry-{index}.json")
        episodes.append(load_dataset_episode(telemetry_path))
    return tuple(episodes)


def _prepare_dataset_artifact(tmp_path) -> object:
    episodes = _phase3_episodes(tmp_path / "telemetry", (11, 12, 13, 14))
    telemetry_paths = [episode.traceability.source_path for episode in episodes]
    dataset_dir = tmp_path / "dataset"
    return prepare_dataset_artifacts(
        [path for path in telemetry_paths if path is not None],
        output_dir=dataset_dir,
        seed=21,
        split_seed=21,
        feature_mode="observation_plus_tracking_errors",
    )


def test_neural_train_mlp_cli_persists_checkpoint_summary_and_manifest(tmp_path, capsys) -> None:
    dataset_result = _prepare_dataset_artifact(tmp_path)
    output_dir = tmp_path / "train-mlp"

    exit_code = main(
        [
            "neural",
            "train",
            "mlp",
            "--dataset",
            str(dataset_result.output_dir),
            "--output-dir",
            str(output_dir),
            "--seed",
            "21",
            "--split-seed",
            "21",
            "--feature-mode",
            "observation_plus_tracking_errors",
            "--window-size",
            "30",
            "--stride",
            "10",
            "--hidden-layers",
            "16,8",
            "--epochs",
            "2",
            "--batch-size",
            "4",
            "--learning-rate",
            "0.001",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "checkpoint_path:" in captured.out
    assert "checkpoint_summary:" in captured.out
    assert "training_manifest:" in captured.out
    assert "hidden_layers: [16, 8]" in captured.out

    checkpoint_path = output_dir / "checkpoint.pt"
    summary_path = output_dir / "checkpoint-summary.json"
    manifest_path = output_dir / "training-manifest.json"
    assert checkpoint_path.exists()
    assert summary_path.exists()
    assert manifest_path.exists()

    checkpoint = load_mlp_checkpoint(checkpoint_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert checkpoint.training == MLPTrainingConfig(
        seed=21,
        split_seed=21,
        feature_mode="observation_plus_tracking_errors",
        window_size=30,
        stride=10,
        hidden_layers=(16, 8),
        epochs=2,
        batch_size=4,
        learning_rate=0.001,
    )
    assert summary["checkpoint_kind"] == "mlp"
    assert summary["training"]["feature_mode"] == "observation_plus_tracking_errors"
    assert summary["training"]["window_size"] == 30
    assert summary["architecture"]["hidden_layers"] == [16, 8]
    assert summary["metrics"]["train_loss"] > 0.0
    assert summary["metrics"]["validation_loss"] > 0.0
    assert manifest["architecture"] == "mlp"
    assert manifest["dataset_artifact_path"] == str(dataset_result.output_dir)
    assert manifest["checkpoint_path"] == str(checkpoint_path)
    assert manifest["checkpoint_summary_path"] == str(summary_path)


def test_neural_train_gru_cli_persists_checkpoint_summary_and_manifest(tmp_path, capsys) -> None:
    dataset_result = _prepare_dataset_artifact(tmp_path)
    output_dir = tmp_path / "train-gru"

    exit_code = main(
        [
            "neural",
            "train",
            "gru",
            "--dataset",
            str(dataset_result.output_dir),
            "--output-dir",
            str(output_dir),
            "--seed",
            "31",
            "--split-seed",
            "31",
            "--feature-mode",
            "observation_plus_tracking_errors",
            "--hidden-size",
            "16",
            "--num-layers",
            "1",
            "--dropout",
            "0.0",
            "--epochs",
            "2",
            "--batch-size",
            "4",
            "--learning-rate",
            "0.001",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "checkpoint_path:" in captured.out
    assert "checkpoint_summary:" in captured.out
    assert "training_manifest:" in captured.out
    assert "hidden_size: 16" in captured.out

    checkpoint_path = output_dir / "checkpoint.pt"
    summary_path = output_dir / "checkpoint-summary.json"
    manifest_path = output_dir / "training-manifest.json"
    assert checkpoint_path.exists()
    assert summary_path.exists()
    assert manifest_path.exists()

    checkpoint = load_recurrent_checkpoint(checkpoint_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert checkpoint.training == RecurrentTrainingConfig(
        architecture="gru",
        seed=31,
        split_seed=31,
        feature_mode="observation_plus_tracking_errors",
        hidden_size=16,
        num_layers=1,
        epochs=2,
        batch_size=4,
        learning_rate=0.001,
        dropout=0.0,
    )
    assert summary["checkpoint_kind"] == "gru"
    assert summary["training"]["architecture"] == "gru"
    assert summary["training"]["feature_mode"] == "observation_plus_tracking_errors"
    assert summary["metrics"]["train_loss"] > 0.0
    assert summary["metrics"]["validation_loss"] > 0.0
    assert manifest["architecture"] == "gru"
    assert manifest["checkpoint_path"] == str(checkpoint_path)


def test_neural_train_cli_accepts_relative_dataset_directory(tmp_path, capsys, monkeypatch) -> None:
    dataset_result = _prepare_dataset_artifact(tmp_path)
    monkeypatch.chdir(tmp_path)

    relative_dataset_dir = dataset_result.output_dir.relative_to(tmp_path)
    output_dir = Path("relative-train-mlp")

    exit_code = main(
        [
            "neural",
            "train",
            "mlp",
            "--dataset",
            str(relative_dataset_dir),
            "--output-dir",
            str(output_dir),
            "--seed",
            "21",
            "--split-seed",
            "21",
            "--feature-mode",
            "observation_plus_tracking_errors",
            "--window-size",
            "30",
            "--stride",
            "10",
            "--hidden-layers",
            "16,8",
            "--epochs",
            "1",
            "--batch-size",
            "4",
            "--learning-rate",
            "0.001",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "checkpoint_path:" in captured.out
    assert output_dir.joinpath("checkpoint.pt").exists()
    assert output_dir.joinpath("training-manifest.json").exists()


@pytest.mark.parametrize("architecture", ["mlp", "gru", "lstm"])
def test_neural_inspect_checkpoint_cli_reports_supported_architectures(
    architecture: str,
    tmp_path,
    capsys,
) -> None:
    checkpoint_path = _train_checkpoint_for_inspection(architecture, tmp_path)

    exit_code = main(
        [
            "neural",
            "inspect",
            "checkpoint",
            "--checkpoint",
            str(checkpoint_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "checkpoint inspection" in captured.out
    assert f"checkpoint_kind: {architecture}" in captured.out
    assert "feature_mode: observation_plus_tracking_errors" in captured.out
    assert "window_size:" in captured.out
    assert "seed:" in captured.out
    assert "normalization_feature_dimension:" in captured.out
    assert "source_telemetry_paths:" in captured.out
    if architecture == "mlp":
        assert "hidden_layers:" in captured.out
    else:
        assert "hidden_size: 16" in captured.out
        assert "num_layers: 1" in captured.out


def _train_checkpoint_for_inspection(architecture: str, tmp_path) -> object:
    dataset_result = _prepare_dataset_artifact(tmp_path)
    if architecture == "mlp":
        assert (
            main(
            [
                "neural",
                "train",
                "mlp",
                "--dataset",
                str(dataset_result.output_dir),
                "--output-dir",
                str(tmp_path / "mlp-inspect"),
                "--seed",
                "41",
                "--split-seed",
                "41",
                "--feature-mode",
                "observation_plus_tracking_errors",
                "--window-size",
                "30",
                "--stride",
                "10",
                "--hidden-layers",
                "16,8",
                "--epochs",
                "1",
                "--batch-size",
                "4",
                "--learning-rate",
                "0.001",
            ]
        )
            == 0
        )
        return tmp_path / "mlp-inspect" / "checkpoint.pt"
    if architecture == "gru":
        assert (
            main(
            [
                "neural",
                "train",
                "gru",
                "--dataset",
                str(dataset_result.output_dir),
                "--output-dir",
                str(tmp_path / "gru-inspect"),
                "--seed",
                "51",
                "--split-seed",
                "51",
                "--feature-mode",
                "observation_plus_tracking_errors",
                "--hidden-size",
                "16",
                "--num-layers",
                "1",
                "--dropout",
                "0.0",
                "--epochs",
                "1",
                "--batch-size",
                "4",
                "--learning-rate",
                "0.001",
            ]
        )
            == 0
        )
        return tmp_path / "gru-inspect" / "checkpoint.pt"
    assert (
        main(
            [
                "neural",
                "train",
                "lstm",
                "--dataset",
                str(dataset_result.output_dir),
                "--output-dir",
                str(tmp_path / "lstm-inspect"),
                "--seed",
                "61",
                "--split-seed",
                "61",
                "--feature-mode",
                "observation_plus_tracking_errors",
                "--hidden-size",
                "16",
                "--num-layers",
                "1",
                "--dropout",
                "0.0",
                "--epochs",
                "1",
                "--batch-size",
                "4",
                "--learning-rate",
                "0.001",
            ]
        )
        == 0
    )
    return tmp_path / "lstm-inspect" / "checkpoint.pt"


def test_neural_inspect_checkpoint_rejects_invalid_checkpoint(tmp_path, capsys) -> None:
    bad_checkpoint = tmp_path / "bad.pt"
    bad_checkpoint.write_text("not a checkpoint", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(["neural", "inspect", "checkpoint", "--checkpoint", str(bad_checkpoint)])

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "invalid or incompatible checkpoint" in captured.err


def test_neural_inspect_checkpoint_rejects_incompatible_sidecar(tmp_path, capsys) -> None:
    dataset_result = _prepare_dataset_artifact(tmp_path)
    main(
        [
            "neural",
            "train",
            "mlp",
            "--dataset",
            str(dataset_result.output_dir),
            "--output-dir",
            str(tmp_path / "mlp-corrupt"),
            "--seed",
            "71",
            "--split-seed",
            "71",
            "--feature-mode",
            "observation_plus_tracking_errors",
            "--window-size",
            "30",
            "--stride",
            "10",
            "--hidden-layers",
            "16,8",
            "--epochs",
            "1",
            "--batch-size",
            "4",
            "--learning-rate",
            "0.001",
        ]
    )
    summary_path = tmp_path / "mlp-corrupt" / "checkpoint-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["checkpoint_kind"] = "gru"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(["neural", "inspect", "checkpoint", "--checkpoint", str(tmp_path / "mlp-corrupt" / "checkpoint.pt")])

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "not compatible" in captured.err
