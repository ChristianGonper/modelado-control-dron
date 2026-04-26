from __future__ import annotations

from dataclasses import replace
import json

import pytest

from simulador_multirotor.app import main
from simulador_multirotor.dataset import load_dataset_episode, split_dataset_episodes
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    build_minimal_scenario,
)
from simulador_multirotor.telemetry import export_history_to_json


def _dataset_scenario(seed: int) -> object:
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
            parameters={"scenario": "phase2-dataset-cli"},
        ),
        disturbances=ScenarioDisturbanceConfig(enabled=False),
        metadata=ScenarioMetadata(name="phase2-dataset-cli", seed=seed),
    )


def _dataset_episodes(tmp_path) -> tuple[object, ...]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    episodes = []
    for index, seed in enumerate((11, 12, 13, 14)):
        scenario = _dataset_scenario(seed)
        history = SimulationRunner().run(scenario)
        telemetry_path = export_history_to_json(history, tmp_path / f"telemetry-{index}.json")
        episodes.append(load_dataset_episode(telemetry_path))
    return tuple(episodes)


def test_dataset_cli_prepares_manifest_and_summary(tmp_path, capsys) -> None:
    episodes = _dataset_episodes(tmp_path / "telemetry")
    telemetry_paths = [episode.traceability.source_path for episode in episodes]
    output_dir = tmp_path / "artifacts" / "phase2-dataset"

    exit_code = main(
        [
            "neural",
            "dataset",
            "prepare",
            "--telemetry",
            *[str(path) for path in telemetry_paths if path is not None],
            "--output-dir",
            str(output_dir),
            "--seed",
            "21",
            "--split-seed",
            "21",
            "--feature-mode",
            "observation_plus_tracking_errors",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "dataset_artifact:" in captured.out
    assert "dataset_manifest:" in captured.out
    assert "dataset_summary:" in captured.out

    dataset_path = output_dir / "dataset.json"
    manifest_path = output_dir / "manifest.json"
    summary_path = output_dir / "dataset-summary.md"
    assert dataset_path.exists()
    assert manifest_path.exists()
    assert summary_path.exists()

    dataset_payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    split_assignments = split_dataset_episodes(episodes, seed=21)
    assignment_by_episode_id = {assignment.episode_id: assignment for assignment in split_assignments}
    expected_split_counts = {"train": 0, "validation": 0, "test": 0, "unassigned": 0}
    for assignment in split_assignments:
        expected_split_counts[assignment.split_name or "unassigned"] += 1

    assert dataset_payload["artifact_kind"] == "dataset"
    assert dataset_payload["stage"] == "dataset"
    assert dataset_payload["episode_count"] == 4
    assert dataset_payload["source_telemetry_paths"] == [str(path) for path in telemetry_paths if path is not None]
    assert dataset_payload["split_seed"] == 21
    assert dataset_payload["split_counts"] == expected_split_counts
    for payload_episode in dataset_payload["episodes"]:
        assignment = assignment_by_episode_id[payload_episode["episode_id"]]
        assert payload_episode["traceability"]["scenario_name"] == "phase2-dataset-cli"
        assert payload_episode["split_name"] == assignment.split_name
    assert dataset_payload["window_counts"]["mlp"]["total_window_count"] > 0
    assert dataset_payload["window_counts"]["gru"]["total_window_count"] > 0
    assert dataset_payload["window_counts"]["lstm"]["total_window_count"] > 0
    assert manifest_payload["artifact_kind"] == "dataset"
    assert manifest_payload["output_path"] == str(manifest_path)
    assert manifest_payload["dataset_path"] == str(dataset_path)
    assert manifest_payload["episode_count"] == 4
    assert manifest_payload["source_telemetry_paths"] == [str(path) for path in telemetry_paths if path is not None]
    assert "Dataset Preparation Summary" in summary_path.read_text(encoding="utf-8")


def test_dataset_cli_rejects_missing_telemetry_path(tmp_path, capsys) -> None:
    output_dir = tmp_path / "artifacts" / "phase2-dataset-missing"

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "neural",
                "dataset",
                "prepare",
                "--telemetry",
                str(tmp_path / "missing.json"),
                "--output-dir",
                str(output_dir),
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "telemetry path does not exist" in captured.err
    assert not output_dir.exists()


def test_dataset_cli_rejects_empty_telemetry_list(tmp_path, capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["neural", "dataset", "prepare"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "--telemetry" in captured.err


def test_dataset_cli_rejects_existing_output_dir_without_overwrite(tmp_path, capsys) -> None:
    episodes = _dataset_episodes(tmp_path / "telemetry-existing")
    telemetry_paths = [episode.traceability.source_path for episode in episodes]
    output_dir = tmp_path / "artifacts" / "phase2-existing"
    output_dir.mkdir(parents=True)

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "neural",
                "dataset",
                "prepare",
                "--telemetry",
                *[str(path) for path in telemetry_paths if path is not None],
                "--output-dir",
                str(output_dir),
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "output directory already exists" in captured.err


def test_dataset_cli_rejects_overwrite_on_unmanaged_directory(tmp_path, capsys) -> None:
    episodes = _dataset_episodes(tmp_path / "telemetry-unmanaged")
    telemetry_paths = [episode.traceability.source_path for episode in episodes]
    output_dir = tmp_path / "artifacts" / "broad-target"
    output_dir.mkdir(parents=True)
    sentinel = output_dir / "keep-me.txt"
    sentinel.write_text("do not delete", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "neural",
                "dataset",
                "prepare",
                "--telemetry",
                *[str(path) for path in telemetry_paths if path is not None],
                "--output-dir",
                str(output_dir),
                "--overwrite",
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "not a managed dataset artifact directory" in captured.err
    assert sentinel.exists()


def test_dataset_cli_allows_overwrite_on_managed_directory(tmp_path, capsys) -> None:
    episodes = _dataset_episodes(tmp_path / "telemetry-managed")
    telemetry_paths = [episode.traceability.source_path for episode in episodes]
    output_dir = tmp_path / "artifacts" / "managed"

    first_exit = main(
        [
            "neural",
            "dataset",
            "prepare",
            "--telemetry",
            *[str(path) for path in telemetry_paths if path is not None],
            "--output-dir",
            str(output_dir),
        ]
    )
    capsys.readouterr()

    second_exit = main(
        [
            "neural",
            "dataset",
            "prepare",
            "--telemetry",
            *[str(path) for path in telemetry_paths if path is not None],
            "--output-dir",
            str(output_dir),
            "--overwrite",
        ]
    )

    captured = capsys.readouterr()
    assert first_exit == 0
    assert second_exit == 0
    assert "dataset_artifact:" in captured.out
    assert (output_dir / "dataset.json").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "dataset-summary.md").exists()
