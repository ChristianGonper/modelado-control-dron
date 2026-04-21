from __future__ import annotations

import json

from simulador_multirotor.app import main
from simulador_multirotor.dataset.artifacts import prepare_dataset_artifacts
from simulador_multirotor.scenarios import SOURCE_BATTERY_KEY, build_source_battery_scenarios
from simulador_multirotor.validation import run_source_battery, validate_source_battery_scenario


def test_source_battery_scenarios_are_explicit_and_reproducible() -> None:
    scenarios = build_source_battery_scenarios()

    assert len(scenarios) == 10
    assert {scenario.trajectory.kind for scenario in scenarios} == {"circle", "lissajous"}
    assert all(validate_source_battery_scenario(scenario) == () for scenario in scenarios)
    assert all(scenario.time.duration_s == 6.0 for scenario in scenarios)
    assert all(scenario.telemetry.detail_level == "full" for scenario in scenarios)
    assert all(scenario.trajectory.parameters["source_battery_key"] == SOURCE_BATTERY_KEY for scenario in scenarios)


def test_source_battery_cli_persists_public_artifacts(tmp_path, capsys) -> None:
    output_dir = tmp_path / "source-battery"

    exit_code = main(
        [
            "validation",
            "source-battery",
            "--output-dir",
            str(output_dir),
            "--overwrite",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source_battery_path:" in captured.out
    assert "source_battery_manifest:" in captured.out
    assert "source_battery_summary:" in captured.out
    assert "source_battery_episode_count: 10" in captured.out
    assert (output_dir / "source-battery.json").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "source-battery-summary.md").exists()


def test_source_battery_outputs_prepare_a_dataset_with_windows_for_all_models(tmp_path) -> None:
    battery_dir = tmp_path / "source-battery"
    bundle = run_source_battery(output_dir=battery_dir, overwrite=True)

    dataset_result = prepare_dataset_artifacts(
        [episode.telemetry_path for episode in bundle.episodes],
        output_dir=tmp_path / "dataset",
        seed=21,
        split_seed=21,
        feature_mode="observation_plus_tracking_errors",
    )

    dataset_payload = json.loads(dataset_result.dataset_path.read_text(encoding="utf-8"))
    assert dataset_payload["episode_count"] == 10
    assert dataset_payload["window_counts"]["mlp"]["total_window_count"] > 0
    assert dataset_payload["window_counts"]["gru"]["total_window_count"] > 0
    assert dataset_payload["window_counts"]["lstm"]["total_window_count"] > 0
    assert dataset_payload["split_counts"]["train"] > 0
    assert dataset_payload["split_counts"]["validation"] > 0
    assert dataset_payload["split_counts"]["test"] > 0
