from __future__ import annotations

import json
from dataclasses import replace

import pytest

from simulador_multirotor.app import main
from simulador_multirotor.benchmark import run_ood_robustness_benchmark
from simulador_multirotor.control import (
    MLPTrainingConfig,
    RecurrentTrainingConfig,
    train_gru_checkpoint,
    train_lstm_checkpoint,
    train_mlp_checkpoint,
)
from simulador_multirotor.dataset import load_dataset_episode
from simulador_multirotor.reporting import generate_ood_report
from simulador_multirotor.robustness import OOD_ROBUSTNESS_SCENARIO_SET_KEY, build_ood_robustness_scenarios
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    build_minimal_scenario,
)
from simulador_multirotor.telemetry import export_history_to_json


def _training_scenario(seed: int) -> object:
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
            parameters={"scenario": "phase6-ood-training"},
        ),
        disturbances=ScenarioDisturbanceConfig(enabled=False),
        metadata=ScenarioMetadata(name="phase6-ood-training", seed=seed),
    )


def _training_episodes(tmp_path, seeds: tuple[int, ...]) -> tuple[object, ...]:
    episodes = []
    for index, seed in enumerate(seeds):
        scenario = _training_scenario(seed)
        history = SimulationRunner().run(scenario)
        telemetry_path = export_history_to_json(history, tmp_path / f"telemetry-{index}.json")
        episodes.append(load_dataset_episode(telemetry_path))
    return tuple(episodes)


def _train_robustness_checkpoints(tmp_path, *, workspace, run_id: str) -> dict[str, object]:
    episodes = _training_episodes(tmp_path, (11, 12, 13))
    mlp_result = train_mlp_checkpoint(
        episodes,
        checkpoint_path=workspace / run_id / "train" / "mlp" / "checkpoint.pt",
        config=MLPTrainingConfig(
            seed=21,
            feature_mode="observation_plus_tracking_errors",
            window_size=30,
            stride=10,
            hidden_layers=(16, 8),
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )
    gru_result = train_gru_checkpoint(
        episodes,
        checkpoint_path=workspace / run_id / "train" / "gru" / "checkpoint.pt",
        config=RecurrentTrainingConfig(
            architecture="gru",
            seed=31,
            feature_mode="observation_plus_tracking_errors",
            hidden_size=16,
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )
    lstm_result = train_lstm_checkpoint(
        episodes,
        checkpoint_path=workspace / run_id / "train" / "lstm" / "checkpoint.pt",
        config=RecurrentTrainingConfig(
            architecture="lstm",
            seed=41,
            feature_mode="observation_plus_tracking_errors",
            hidden_size=16,
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )
    return {
        "mlp": mlp_result.checkpoint_path,
        "gru": gru_result.checkpoint_path,
        "lstm": lstm_result.checkpoint_path,
    }


def test_neural_benchmark_ood_cli_help_mentions_method_boundary(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["neural", "benchmark", "ood", "--help"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert "not for tuning or model selection" in captured.out


def test_neural_benchmark_ood_cli_persists_separate_artifacts(tmp_path, capsys) -> None:
    workspace = tmp_path / "artifacts" / "neural"
    run_id = "phase6-ood-cli"
    checkpoint_paths = _train_robustness_checkpoints(tmp_path, workspace=workspace, run_id=run_id)
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
    main_captured = capsys.readouterr()
    assert exit_code == 0
    assert "selection_policy: main benchmark is the only selection benchmark" in main_captured.out

    exit_code = main(
        [
            "neural",
            "benchmark",
            "ood",
            "--workspace",
            str(workspace),
            "--run-id",
            run_id,
        ]
    )

    captured = capsys.readouterr()
    main_dir = workspace / run_id / "benchmark" / "main"
    ood_dir = workspace / run_id / "benchmark" / "ood"
    ood_payload = json.loads((ood_dir / "ood-benchmark.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert (main_dir / "benchmark.json").exists()
    assert (main_dir / "manifest.json").exists()
    assert (main_dir / "benchmark-summary.md").exists()
    assert (ood_dir / "ood-benchmark.json").exists()
    assert (ood_dir / "ood-manifest.json").exists()
    assert (ood_dir / "ood-benchmark-summary.md").exists()
    assert main_dir != ood_dir
    assert ood_payload["benchmark_kind"] == "ood"
    assert ood_payload["scenario_set_key"] == OOD_ROBUSTNESS_SCENARIO_SET_KEY
    assert ood_payload["checkpoint_paths"] == {key: str(path) for key, path in checkpoint_paths.items()}
    assert "selection_policy: OOD is separate and must not be used for tuning or model selection" in captured.out


def test_ood_battery_is_explicit_and_distinct_from_main_splits() -> None:
    scenarios = build_ood_robustness_scenarios()

    assert len(scenarios) == 4
    assert {scenario.metadata.name for scenario in scenarios} == {
        "ood-hover-gust",
        "ood-circle-crosswind",
        "ood-spiral-induced-loss",
        "ood-lissajous-noise",
    }
    assert all("ood" in scenario.metadata.tags for scenario in scenarios)
    assert all(scenario.metadata.seed is not None for scenario in scenarios)
    assert all(scenario.trajectory.kind in {"hover", "circle", "spiral", "lissajous"} for scenario in scenarios)


def test_ood_benchmark_persists_separate_traceable_artifacts(tmp_path) -> None:
    episodes = _training_episodes(tmp_path, (11, 12, 13))
    mlp_result = train_mlp_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "mlp.pt",
        config=MLPTrainingConfig(
            seed=21,
            feature_mode="observation_plus_tracking_errors",
            window_size=30,
            stride=10,
            hidden_layers=(16, 8),
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )
    gru_result = train_gru_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "gru.pt",
        config=RecurrentTrainingConfig(
            architecture="gru",
            seed=31,
            feature_mode="observation_plus_tracking_errors",
            hidden_size=16,
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )
    lstm_result = train_lstm_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "lstm.pt",
        config=RecurrentTrainingConfig(
            architecture="lstm",
            seed=41,
            feature_mode="observation_plus_tracking_errors",
            hidden_size=16,
            epochs=2,
            batch_size=4,
            learning_rate=1e-3,
        ),
    )

    output_path = tmp_path / "ood-benchmark.json"
    benchmark = run_ood_robustness_benchmark(
        mlp_checkpoint_path=mlp_result.checkpoint_path,
        gru_checkpoint_path=gru_result.checkpoint_path,
        lstm_checkpoint_path=lstm_result.checkpoint_path,
        output_path=output_path,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert benchmark.output_path == output_path
    assert payload["benchmark_kind"] == "ood"
    assert payload["scenario_set_key"] == OOD_ROBUSTNESS_SCENARIO_SET_KEY
    assert len(payload["results"]) == 4
    assert all("ood" in result["scenario"]["metadata"]["tags"] for result in payload["results"])
    assert set(payload["results"][0]["comparisons"]) == {"mlp", "gru", "lstm"}


def test_ood_reporting_keeps_selection_separate(tmp_path) -> None:
    episodes = _training_episodes(tmp_path, (51, 52, 53))
    mlp_result = train_mlp_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "mlp-report.pt",
        config=MLPTrainingConfig(seed=61, epochs=2, batch_size=4, hidden_layers=(16, 8)),
    )
    gru_result = train_gru_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "gru-report.pt",
        config=RecurrentTrainingConfig(architecture="gru", seed=71, hidden_size=16, epochs=2, batch_size=4),
    )
    lstm_result = train_lstm_checkpoint(
        episodes,
        checkpoint_path=tmp_path / "lstm-report.pt",
        config=RecurrentTrainingConfig(architecture="lstm", seed=81, hidden_size=16, epochs=2, batch_size=4),
    )

    benchmark = run_ood_robustness_benchmark(
        build_ood_robustness_scenarios(),
        mlp_checkpoint_path=mlp_result.checkpoint_path,
        gru_checkpoint_path=gru_result.checkpoint_path,
        lstm_checkpoint_path=lstm_result.checkpoint_path,
        output_path=tmp_path / "ood-benchmark.json",
    )
    report_dir = tmp_path / "ood-report"
    bundle = generate_ood_report(benchmark.output_path, report_dir)
    report_text = bundle.report_path.read_text(encoding="utf-8")
    table_text = bundle.table_path.read_text(encoding="utf-8")

    assert bundle.table_path.exists()
    assert bundle.report_path.exists()
    assert not (report_dir / "selection.json").exists()
    assert "not used for model selection" in report_text
    assert "ood" in table_text.lower()
    assert set(bundle.figure_paths) == {
        "ood-hover-gust",
        "ood-circle-crosswind",
        "ood-spiral-induced-loss",
        "ood-lissajous-noise",
    }
