"""Punto de entrada mínimo para validar el esqueleto del proyecto."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .metrics import compute_tracking_metrics
from .runner import SimulationRunner
from .scenarios import build_minimal_scenario, load_simulation_scenario
from .benchmark import (
    MAIN_BENCHMARK_OUTPUT_NAME,
    OOD_BENCHMARK_OUTPUT_NAME,
    build_main_benchmark_scenarios,
    persist_main_benchmark_artifacts,
    persist_ood_benchmark_artifacts,
    run_homogeneous_neural_benchmark,
    run_ood_robustness_benchmark,
)
from .dataset.artifacts import DatasetArtifactError, load_dataset_preparation_artifact, prepare_dataset_artifacts
from .dataset import load_dataset_episodes
from .control import (
    MLPTrainingConfig,
    RecurrentTrainingConfig,
    load_mlp_checkpoint,
    load_recurrent_checkpoint,
    train_gru_checkpoint,
    train_lstm_checkpoint,
    train_mlp_checkpoint,
)
from .control.mlp import checkpoint_summary_payload as mlp_checkpoint_summary_payload, dump_checkpoint_summary as dump_mlp_checkpoint_summary
from .control.recurrent import (
    checkpoint_summary_payload as recurrent_checkpoint_summary_payload,
    dump_checkpoint_summary as dump_recurrent_checkpoint_summary,
)
from .reporting import generate_phase5_report
from .telemetry import export_history_to_json
from .visualization import load_telemetry_archive, render_analysis_outputs


def build_scenario_demo(scenario) -> dict[str, object]:
    """Run a scenario and return its history."""
    history = SimulationRunner().run(scenario)
    return {"scenario": scenario, "history": history}


def build_minimal_demo(*, seed: int | None = None) -> dict[str, object]:
    """Run the minimum validated demo and return its history."""
    return build_scenario_demo(build_minimal_scenario(seed=seed))


def _print_run_summary(*, history, scenario) -> None:
    print("simulador-multirotor run")
    metrics = compute_tracking_metrics(history)
    print(f"steps: {len(history.steps)}")
    print(f"final_time_s: {history.final_time_s:.3f}")
    print(f"scenario_name: {scenario.metadata.name}")
    print(f"scenario_seed: {scenario.metadata.seed}")
    print(f"position_rmse_m: {metrics.position_rmse_m:.4f}")
    print(f"velocity_rmse_m_s: {metrics.velocity_rmse_m_s:.4f}")
    print(f"mean_collective_thrust_newton: {metrics.mean_collective_thrust_newton:.4f}")
    print(f"final_state: {history.final_state}")


def run_scenario_demo(scenario) -> int:
    demo = build_scenario_demo(scenario)
    _print_run_summary(history=demo["history"], scenario=demo["scenario"])
    return 0


def run_minimal_demo(*, seed: int | None = None) -> int:
    return run_scenario_demo(build_minimal_scenario(seed=seed))


def run_scenario_analysis(*, scenario, analysis_dir: str | Path) -> int:
    demo = build_scenario_demo(scenario)
    history = demo["history"]
    scenario = demo["scenario"]
    _print_run_summary(history=history, scenario=scenario)
    output_dir = Path(analysis_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    telemetry_path = export_history_to_json(
        history,
        output_dir / "telemetry.json",
        detail_level=scenario.telemetry.detail_level,
        sample_dt_s=scenario.telemetry.sample_dt_s,
    )
    archive = load_telemetry_archive(telemetry_path)
    bundle = render_analysis_outputs(archive, output_dir)
    print(f"analysis_telemetry: {bundle.telemetry_path}")
    print(f"analysis_trajectory_2d: {bundle.trajectory_2d_path}")
    print(f"analysis_tracking_errors: {bundle.tracking_errors_path}")
    print(f"analysis_trajectory_3d: {bundle.trajectory_3d_path}")
    return 0


def run_minimal_analysis(*, seed: int | None = None, analysis_dir: str | Path) -> int:
    return run_scenario_analysis(scenario=build_minimal_scenario(seed=seed), analysis_dir=analysis_dir)


def _parse_hidden_layers(value: str) -> tuple[int, ...]:
    parts = [part.strip() for part in str(value).split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("hidden layers must contain at least one integer")
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:  # pragma: no cover - argparse translates the error
        raise argparse.ArgumentTypeError("hidden layers must be a comma-separated list of integers") from exc


def _generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def _resolve_training_output_dir(*, workspace: Path, run_id: str | None, output_dir: Path | None, architecture: str) -> tuple[Path, str]:
    resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _generate_run_id()
    if output_dir is not None:
        return Path(output_dir), resolved_run_id
    return workspace / resolved_run_id / "train" / architecture, resolved_run_id


def _resolve_benchmark_output_dir(*, workspace: Path, run_id: str | None, output_dir: Path | None, benchmark_kind: str) -> tuple[Path, str]:
    resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _generate_run_id()
    if output_dir is not None:
        return Path(output_dir), resolved_run_id
    return workspace / resolved_run_id / "benchmark" / benchmark_kind, resolved_run_id


def _resolve_benchmark_checkpoint_paths(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    *,
    benchmark_label: str,
) -> dict[str, Path]:
    explicit_paths = {
        "mlp": getattr(args, "mlp_checkpoint", None),
        "gru": getattr(args, "gru_checkpoint", None),
        "lstm": getattr(args, "lstm_checkpoint", None),
    }
    provided_explicit_paths = [path for path in explicit_paths.values() if path is not None]
    if provided_explicit_paths and len(provided_explicit_paths) != len(explicit_paths):
        parser.error(f"benchmark {benchmark_label} must use either all explicit checkpoint paths or resolve all three by convention")

    if provided_explicit_paths:
        resolved_paths = {key: Path(path) for key, path in explicit_paths.items()}
    else:
        if args.run_id is None or not str(args.run_id).strip():
            parser.error(f"benchmark {benchmark_label} requires --run-id when checkpoints are resolved by convention")
        workspace = Path(args.workspace)
        run_id = str(args.run_id).strip()
        resolved_paths = {
            "mlp": workspace / run_id / "train" / "mlp" / "checkpoint.pt",
            "gru": workspace / run_id / "train" / "gru" / "checkpoint.pt",
            "lstm": workspace / run_id / "train" / "lstm" / "checkpoint.pt",
        }

    missing_paths = [f"{key}: {path}" for key, path in resolved_paths.items() if not path.exists()]
    if missing_paths:
        parser.error(f"benchmark {benchmark_label} checkpoint does not exist: " + "; ".join(missing_paths))

    if len({path.resolve() for path in resolved_paths.values()}) != len(resolved_paths):
        parser.error(f"benchmark {benchmark_label} requires distinct checkpoints for mlp, gru, and lstm")

    return resolved_paths


def _resolve_report_output_dir(*, benchmark_path: Path, output_dir: Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir)

    resolved_benchmark_path = Path(benchmark_path)
    benchmark_parent = resolved_benchmark_path.parent
    if benchmark_parent.name in {"main", "ood"} and benchmark_parent.parent.name == "benchmark":
        return benchmark_parent.parent.parent / "report" / "final"
    return benchmark_parent / "report" / "final"


def _load_benchmark_payload(benchmark_path: Path) -> dict[str, object]:
    if not benchmark_path.exists():
        raise ValueError(f"benchmark does not exist: {benchmark_path}")
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"benchmark payload must be a JSON object: {benchmark_path}")
    return payload


def _load_dataset_artifact_for_training(dataset_path: Path) -> DatasetPreparationResult:
    try:
        return load_dataset_preparation_artifact(dataset_path)
    except DatasetArtifactError as exc:
        raise ValueError(str(exc)) from exc


def _json_dump(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_dump(payload), encoding="utf-8")
    return path


def _training_manifest_payload(
    *,
    architecture: str,
    dataset_result: DatasetPreparationResult,
    checkpoint_path: Path,
    summary_path: Path,
    output_dir: Path,
    run_id: str,
    command: str,
    argv: Sequence[str],
    config: object,
    training_result: object,
) -> dict[str, object]:
    if hasattr(config, "as_dict"):
        config_payload = config.as_dict()
    else:  # pragma: no cover - defensive fallback
        config_payload = dict(config)
    if hasattr(training_result, "train_loss"):
        metrics_payload = {
            "train_loss": training_result.train_loss,
            "validation_loss": training_result.validation_loss,
            "train_window_count": training_result.train_window_count,
            "validation_window_count": training_result.validation_window_count,
        }
    else:  # pragma: no cover - defensive fallback
        metrics_payload = {}
    return {
        "schema_version": 1,
        "artifact_kind": "training",
        "stage": "train",
        "run_id": run_id,
        "command": command,
        "argv": list(argv),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "architecture": architecture,
        "checkpoint_kind": architecture,
        "input_paths": [str(dataset_result.dataset_path)],
        "dataset_artifact_path": str(dataset_result.output_dir),
        "dataset_path": str(dataset_result.dataset_path),
        "dataset_manifest_path": str(dataset_result.manifest_path),
        "dataset_summary_path": str(dataset_result.summary_path),
        "source_telemetry_paths": [str(path) for path in dataset_result.dataset_payload["source_telemetry_paths"]],
        "feature_mode": config_payload.get("feature_mode"),
        "seed": config_payload.get("seed"),
        "split_seed": config_payload.get("split_seed"),
        "output_path": str(output_dir),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_summary_path": str(summary_path),
        "effective_configuration": config_payload,
        "metrics": metrics_payload,
    }


def _checkpoint_summary_path(checkpoint_path: Path) -> Path:
    return checkpoint_path.with_name("checkpoint-summary.json")


def _training_manifest_path(checkpoint_path: Path) -> Path:
    return checkpoint_path.with_name("training-manifest.json")


def _format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _render_checkpoint_summary_text(summary: dict[str, object], manifest: dict[str, object] | None = None) -> str:
    training = summary.get("training", {})
    normalization = summary.get("normalization", {})
    metrics = summary.get("metrics", {})
    architecture_config = summary.get("architecture", {})
    if not isinstance(architecture_config, dict) or not architecture_config:
        architecture_config = training if isinstance(training, dict) else {}
    lines = [
        "checkpoint summary",
        f"checkpoint_kind: {summary.get('checkpoint_kind', 'unknown')}",
        f"architecture: {training.get('architecture', summary.get('checkpoint_kind', 'unknown'))}",
        f"feature_mode: {training.get('feature_mode', 'unknown')}",
        f"window_size: {training.get('window_size', 'unknown')}",
        f"stride: {training.get('stride', 'unknown')}",
        f"seed: {training.get('seed', 'unknown')}",
        f"split_seed: {training.get('split_seed', summary.get('split_seed', 'unknown'))}",
        f"normalization_feature_dimension: {normalization.get('feature_dimension', 'unknown')}",
        f"normalization_window_size: {normalization.get('window_size', 'unknown')}",
        f"train_loss: {_format_metric(metrics.get('train_loss'))}",
        f"validation_loss: {_format_metric(metrics.get('validation_loss'))}",
        f"train_window_count: {_format_metric(metrics.get('train_window_count'))}",
        f"validation_window_count: {_format_metric(metrics.get('validation_window_count'))}",
    ]
    if isinstance(architecture_config, dict):
        if "hidden_layers" in architecture_config:
            lines.append(f"hidden_layers: {architecture_config.get('hidden_layers')}")
        if "input_dimension" in architecture_config:
            lines.append(f"input_dimension: {architecture_config.get('input_dimension')}")
        if "hidden_size" in architecture_config:
            lines.append(f"hidden_size: {architecture_config.get('hidden_size')}")
        if "num_layers" in architecture_config:
            lines.append(f"num_layers: {architecture_config.get('num_layers')}")
        if "dropout" in architecture_config:
            lines.append(f"dropout: {architecture_config.get('dropout')}")
    if manifest is not None:
        lines.extend(
            [
                f"run_id: {manifest.get('run_id', 'unknown')}",
                f"dataset_artifact_path: {manifest.get('dataset_artifact_path', 'unknown')}",
                f"checkpoint_path: {manifest.get('checkpoint_path', summary.get('checkpoint_path', 'unknown'))}",
            ]
        )
    return "\n".join(lines)


def _render_checkpoint_inspection_text(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {})
    manifest = payload.get("manifest", {})
    architecture_config = payload.get("architecture_config", {})
    lines = [
        "checkpoint inspection",
        f"checkpoint_path: {payload.get('checkpoint_path', 'unknown')}",
        f"checkpoint_kind: {payload.get('checkpoint_kind', 'unknown')}",
        f"architecture: {payload.get('architecture', 'unknown')}",
        f"feature_mode: {payload.get('feature_mode', 'unknown')}",
        f"window_size: {payload.get('window_size', 'unknown')}",
        f"stride: {payload.get('stride', 'unknown')}",
        f"seed: {payload.get('seed', 'unknown')}",
        f"split_seed: {payload.get('split_seed', 'unknown')}",
        f"normalization_feature_dimension: {payload.get('normalization_feature_dimension', 'unknown')}",
        f"train_loss: {_format_metric(payload.get('train_loss'))}",
        f"validation_loss: {_format_metric(payload.get('validation_loss'))}",
    ]
    if isinstance(architecture_config, dict):
        if "hidden_layers" in architecture_config:
            lines.append(f"hidden_layers: {architecture_config.get('hidden_layers')}")
        if "input_dimension" in architecture_config:
            lines.append(f"input_dimension: {architecture_config.get('input_dimension')}")
        if "hidden_size" in architecture_config:
            lines.append(f"hidden_size: {architecture_config.get('hidden_size')}")
        if "num_layers" in architecture_config:
            lines.append(f"num_layers: {architecture_config.get('num_layers')}")
        if "dropout" in architecture_config:
            lines.append(f"dropout: {architecture_config.get('dropout')}")
    source_paths = payload.get("source_telemetry_paths", ())
    if source_paths:
        lines.append("source_telemetry_paths:")
        for path in source_paths:
            lines.append(f"  - {path}")
    if manifest:
        lines.extend(
            [
                f"run_id: {manifest.get('run_id', 'unknown')}",
                f"command: {manifest.get('command', 'unknown')}",
                f"dataset_artifact_path: {manifest.get('dataset_artifact_path', 'unknown')}",
            ]
        )
    if summary:
        lines.append(f"summary_path: {payload.get('summary_path', 'unknown')}")
    return "\n".join(lines)


def _load_checkpoint_bundle(checkpoint_path: Path) -> dict[str, object]:
    summary_path = _checkpoint_summary_path(checkpoint_path)
    manifest_path = _training_manifest_path(checkpoint_path)
    summary_payload: dict[str, object] | None = None
    manifest_payload: dict[str, object] | None = None
    if summary_path.exists():
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(summary_payload, dict):
            raise ValueError("checkpoint summary must be a JSON object")
    if manifest_path.exists():
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest_payload, dict):
            raise ValueError("training manifest must be a JSON object")

    errors: list[str] = []
    checkpoint_kind = "unknown"
    checkpoint = None
    try:
        checkpoint = load_mlp_checkpoint(checkpoint_path)
        checkpoint_kind = "mlp"
    except Exception as exc:  # pragma: no cover - controlled by inspect tests
        errors.append(f"mlp: {exc}")
    if checkpoint is None:
        try:
            checkpoint = load_recurrent_checkpoint(checkpoint_path)
            checkpoint_kind = checkpoint.training.architecture
        except Exception as exc:
            errors.append(f"recurrent: {exc}")
    if checkpoint is None:
        joined = "; ".join(errors) if errors else "unsupported checkpoint payload"
        raise ValueError(f"invalid or incompatible checkpoint: {joined}")

    resolved_checkpoint_architecture = getattr(checkpoint.training, "architecture", checkpoint_kind)

    if summary_payload is not None:
        summary_kind = summary_payload.get("checkpoint_kind")
        summary_architecture = summary_payload.get("training", {}).get("architecture") if isinstance(summary_payload.get("training"), dict) else None
        if summary_kind not in (None, checkpoint_kind, resolved_checkpoint_architecture):
            raise ValueError("checkpoint summary is not compatible with the checkpoint payload")
        if checkpoint_kind != "mlp" and summary_architecture not in (None, resolved_checkpoint_architecture):
            raise ValueError("checkpoint summary is not compatible with the checkpoint payload")

    if manifest_payload is not None:
        manifest_kind = manifest_payload.get("checkpoint_kind")
        manifest_architecture = manifest_payload.get("architecture")
        if manifest_kind not in (None, checkpoint_kind, resolved_checkpoint_architecture):
            raise ValueError("training manifest is not compatible with the checkpoint payload")
        if manifest_architecture not in (None, checkpoint_kind, resolved_checkpoint_architecture):
            raise ValueError("training manifest is not compatible with the checkpoint payload")

    if checkpoint_kind == "mlp":
        summary = mlp_checkpoint_summary_payload(checkpoint, checkpoint_path=checkpoint_path)
    else:
        summary = recurrent_checkpoint_summary_payload(checkpoint, checkpoint_path=checkpoint_path)
    if summary_payload is not None:
        summary = summary_payload
    architecture_config = summary.get("architecture") if isinstance(summary.get("architecture"), dict) else summary.get("training", {})
    if manifest_payload is None:
        manifest_payload = {}
    return {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_kind": checkpoint_kind,
        "architecture": resolved_checkpoint_architecture,
        "architecture_config": architecture_config,
        "feature_mode": summary.get("training", {}).get("feature_mode"),
        "window_size": summary.get("training", {}).get("window_size"),
        "stride": summary.get("training", {}).get("stride"),
        "seed": summary.get("training", {}).get("seed"),
        "split_seed": summary.get("training", {}).get("split_seed", summary.get("split_seed")),
        "normalization_feature_dimension": summary.get("normalization", {}).get("feature_dimension"),
        "train_loss": summary.get("metrics", {}).get("train_loss"),
        "validation_loss": summary.get("metrics", {}).get("validation_loss"),
        "summary_path": str(summary_path),
        "source_telemetry_paths": manifest_payload.get("source_telemetry_paths", []),
        "summary": summary,
        "manifest": manifest_payload,
    }


def _run_train_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    *,
    architecture: str,
) -> int:
    try:
        dataset_result = _load_dataset_artifact_for_training(args.dataset)
        episodes = load_dataset_episodes(dataset_result.dataset_payload["source_telemetry_paths"])
        if not episodes:
            raise ValueError("prepared dataset did not yield any episodes")

        default_seed = int(dataset_result.dataset_payload.get("seed", 7))
        default_split_seed = int(dataset_result.dataset_payload.get("split_seed", default_seed))
        default_feature_mode = str(dataset_result.dataset_payload.get("feature_mode", "observation_plus_tracking_errors"))
        seed = default_seed if args.seed is None else int(args.seed)
        split_seed = default_split_seed if args.split_seed is None else int(args.split_seed)
        feature_mode = default_feature_mode if args.feature_mode is None else str(args.feature_mode)

        workspace = Path(args.workspace)
        output_dir, run_id = _resolve_training_output_dir(
            workspace=workspace,
            run_id=args.run_id,
            output_dir=args.output_dir,
            architecture=architecture,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = output_dir / "checkpoint.pt"
        summary_path = _checkpoint_summary_path(checkpoint_path)
        manifest_path = _training_manifest_path(checkpoint_path)

        if architecture == "mlp":
            default_config = MLPTrainingConfig()
            config = MLPTrainingConfig(
                seed=seed,
                split_seed=split_seed,
                feature_mode=feature_mode,
                window_size=args.window_size if args.window_size is not None else default_config.window_size,
                stride=args.stride if args.stride is not None else default_config.stride,
                hidden_layers=args.hidden_layers if args.hidden_layers is not None else default_config.hidden_layers,
                epochs=args.epochs if args.epochs is not None else default_config.epochs,
                batch_size=args.batch_size if args.batch_size is not None else default_config.batch_size,
                learning_rate=args.learning_rate if args.learning_rate is not None else default_config.learning_rate,
                weight_decay=args.weight_decay if args.weight_decay is not None else default_config.weight_decay,
            )
            training_result = train_mlp_checkpoint(episodes, checkpoint_path=checkpoint_path, config=config)
            summary = mlp_checkpoint_summary_payload(
                training_result.checkpoint,
                training_result=training_result,
                checkpoint_path=checkpoint_path,
            )
            dump_mlp_checkpoint_summary(summary_path, training_result.checkpoint, training_result=training_result, checkpoint_path=checkpoint_path)
        elif architecture in {"gru", "lstm"}:
            default_config = RecurrentTrainingConfig(architecture=architecture)
            config = RecurrentTrainingConfig(
                architecture=architecture,
                seed=seed,
                split_seed=split_seed,
                feature_mode=feature_mode,
                window_size=args.window_size if args.window_size is not None else default_config.window_size,
                stride=args.stride if args.stride is not None else default_config.stride,
                hidden_size=args.hidden_size if args.hidden_size is not None else default_config.hidden_size,
                num_layers=args.num_layers if args.num_layers is not None else default_config.num_layers,
                epochs=args.epochs if args.epochs is not None else default_config.epochs,
                batch_size=args.batch_size if args.batch_size is not None else default_config.batch_size,
                learning_rate=args.learning_rate if args.learning_rate is not None else default_config.learning_rate,
                weight_decay=args.weight_decay if args.weight_decay is not None else default_config.weight_decay,
                dropout=args.dropout if args.dropout is not None else default_config.dropout,
            )
            training_result = train_gru_checkpoint(episodes, checkpoint_path=checkpoint_path, config=config) if architecture == "gru" else train_lstm_checkpoint(episodes, checkpoint_path=checkpoint_path, config=config)
            summary = recurrent_checkpoint_summary_payload(
                training_result.checkpoint,
                training_result=training_result,
                checkpoint_path=checkpoint_path,
            )
            dump_recurrent_checkpoint_summary(summary_path, training_result.checkpoint, training_result=training_result, checkpoint_path=checkpoint_path)
        else:  # pragma: no cover - parser prevents this
            raise ValueError(f"unsupported architecture: {architecture}")

        manifest = _training_manifest_payload(
            architecture=architecture,
            dataset_result=dataset_result,
            checkpoint_path=checkpoint_path,
            summary_path=summary_path,
            output_dir=output_dir,
            run_id=run_id,
            command=f"multirotor-sim neural train {architecture}",
            argv=getattr(args, "argv", ()),
            config=config,
            training_result=training_result,
        )
        _write_json(manifest_path, manifest)
    except (DatasetArtifactError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(f"checkpoint_path: {checkpoint_path}")
    print(f"checkpoint_summary: {summary_path}")
    print(f"training_manifest: {manifest_path}")
    print(f"run_id: {run_id}")
    print(_render_checkpoint_summary_text(summary, manifest))
    return 0


def _run_inspect_checkpoint_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        checkpoint_path = Path(args.checkpoint)
        if not checkpoint_path.exists():
            raise ValueError(f"checkpoint does not exist: {checkpoint_path}")
        payload = _load_checkpoint_bundle(checkpoint_path)
    except (DatasetArtifactError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_checkpoint_inspection_text(payload))
    return 0


def _run_main_benchmark_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        checkpoint_paths = _resolve_benchmark_checkpoint_paths(args, parser, benchmark_label="main")
        workspace = Path(args.workspace)
        output_dir, run_id = _resolve_benchmark_output_dir(
            workspace=workspace,
            run_id=args.run_id,
            output_dir=args.output_dir,
            benchmark_kind="main",
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        benchmark_path = output_dir / MAIN_BENCHMARK_OUTPUT_NAME
        scenarios = build_main_benchmark_scenarios()
        benchmark = run_homogeneous_neural_benchmark(
            scenarios,
            mlp_checkpoint_path=checkpoint_paths["mlp"],
            gru_checkpoint_path=checkpoint_paths["gru"],
            lstm_checkpoint_path=checkpoint_paths["lstm"],
            output_path=benchmark_path,
            command="multirotor-sim neural benchmark main",
            argv=getattr(args, "argv", ()),
        )
        artifact_paths = persist_main_benchmark_artifacts(
            benchmark,
            output_dir=output_dir,
            command="multirotor-sim neural benchmark main",
            argv=getattr(args, "argv", ()),
            run_id=run_id,
        )
    except (DatasetArtifactError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(f"benchmark_path: {artifact_paths['benchmark_path']}")
    print(f"benchmark_manifest: {artifact_paths['manifest_path']}")
    print(f"benchmark_summary: {artifact_paths['summary_path']}")
    print(f"benchmark_run_id: {run_id}")
    print(f"mlp_checkpoint: {checkpoint_paths['mlp']}")
    print(f"gru_checkpoint: {checkpoint_paths['gru']}")
    print(f"lstm_checkpoint: {checkpoint_paths['lstm']}")
    print(f"scenario_set_key: {benchmark.scenario_set_key}")
    print("methodology_policy: control=observed_state; evaluation=true_state")
    print("selection_policy: main benchmark is the only selection benchmark")
    return 0


def _run_ood_benchmark_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        checkpoint_paths = _resolve_benchmark_checkpoint_paths(args, parser, benchmark_label="ood")
        workspace = Path(args.workspace)
        output_dir, run_id = _resolve_benchmark_output_dir(
            workspace=workspace,
            run_id=args.run_id,
            output_dir=args.output_dir,
            benchmark_kind="ood",
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        benchmark_path = output_dir / OOD_BENCHMARK_OUTPUT_NAME
        benchmark = run_ood_robustness_benchmark(
            mlp_checkpoint_path=checkpoint_paths["mlp"],
            gru_checkpoint_path=checkpoint_paths["gru"],
            lstm_checkpoint_path=checkpoint_paths["lstm"],
            output_path=benchmark_path,
            command="multirotor-sim neural benchmark ood",
            argv=getattr(args, "argv", ()),
        )
        artifact_paths = persist_ood_benchmark_artifacts(
            benchmark,
            output_dir=output_dir,
            command="multirotor-sim neural benchmark ood",
            argv=getattr(args, "argv", ()),
            run_id=run_id,
        )
    except (DatasetArtifactError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(f"benchmark_path: {artifact_paths['benchmark_path']}")
    print(f"benchmark_manifest: {artifact_paths['manifest_path']}")
    print(f"benchmark_summary: {artifact_paths['summary_path']}")
    print(f"benchmark_run_id: {run_id}")
    print(f"mlp_checkpoint: {checkpoint_paths['mlp']}")
    print(f"gru_checkpoint: {checkpoint_paths['gru']}")
    print(f"lstm_checkpoint: {checkpoint_paths['lstm']}")
    print(f"scenario_set_key: {benchmark.scenario_set_key}")
    print("methodology_policy: control=observed_state; evaluation=true_state")
    print("selection_policy: OOD is separate and must not be used for tuning or model selection")
    return 0


def _run_final_report_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        benchmark_path = Path(args.benchmark_path)
        payload = _load_benchmark_payload(benchmark_path)
        if payload.get("benchmark_kind") != "main":
            raise ValueError("final report requires a persisted main benchmark; OOD artifacts are not eligible")
        output_dir = _resolve_report_output_dir(benchmark_path=benchmark_path, output_dir=args.output_dir)
        bundle = generate_phase5_report(benchmark_path, output_dir)
    except (DatasetArtifactError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    print(f"benchmark_path: {bundle.benchmark_path}")
    print(f"report_output_dir: {bundle.output_dir}")
    print(f"report_table: {bundle.table_path}")
    print(f"report_selection: {bundle.selection_path}")
    print(f"report_summary: {bundle.report_path}")
    print(f"report_figures_dir: {bundle.output_dir / 'figures'}")
    print(f"selection_model: {json.loads(bundle.selection_path.read_text(encoding='utf-8'))['selected_model_key']}")
    print("methodology_policy: control=observed_state; evaluation=true_state")
    print("selection_policy: report generated from the persisted main benchmark only")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multirotor-sim",
        description="Execution entry point for the multirotor simulator skeleton.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run the minimum validated demo and exit.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed the nominal scenario run.",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        default=None,
        help="Load and execute an external scenario JSON artifact.",
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=None,
        help="Export telemetry and generate static analysis outputs in the given directory.",
    )

    subparsers = parser.add_subparsers(dest="command")
    neural_parser = subparsers.add_parser("neural", help="Expose the neural-control workflow.")
    neural_subparsers = neural_parser.add_subparsers(dest="neural_command", required=True)
    dataset_parser = neural_subparsers.add_parser("dataset", help="Dataset preparation and registration.")
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command", required=True)
    prepare_parser = dataset_subparsers.add_parser("prepare", help="Prepare a dataset from persisted telemetry.")
    prepare_parser.add_argument(
        "--telemetry",
        nargs="+",
        type=Path,
        required=True,
        help="One or more persisted telemetry artifacts to ingest.",
    )
    prepare_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("artifacts/neural"),
        help="Root directory for neural-control artifacts.",
    )
    prepare_parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Explicit run identifier to use for the dataset artifact tree.",
    )
    prepare_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the dataset output directory.",
    )
    prepare_parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Primary experiment seed.",
    )
    prepare_parser.add_argument(
        "--split-seed",
        type=int,
        default=None,
        help="Deterministic split seed; defaults to --seed.",
    )
    prepare_parser.add_argument(
        "--feature-mode",
        choices=("raw_observation", "observation_plus_tracking_errors"),
        default="observation_plus_tracking_errors",
        help="Dataset feature contract to record in the artifact.",
    )
    prepare_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output directory if it already exists.",
    )
    prepare_parser.set_defaults(func=_run_dataset_prepare_command)

    train_parser = neural_subparsers.add_parser("train", help="Train a neural controller from a prepared dataset.")
    train_subparsers = train_parser.add_subparsers(dest="train_command", required=True)
    for architecture in ("mlp", "gru", "lstm"):
        architecture_parser = train_subparsers.add_parser(architecture, help=f"Train a {architecture.upper()} controller.")
        architecture_parser.add_argument("--dataset", type=Path, required=True, help="Prepared dataset artifact directory or dataset.json file.")
        architecture_parser.add_argument("--workspace", type=Path, default=Path("artifacts/neural"), help="Root directory for neural-control artifacts.")
        architecture_parser.add_argument("--run-id", type=str, default=None, help="Explicit run identifier for the training run.")
        architecture_parser.add_argument("--output-dir", type=Path, default=None, help="Override the training output directory.")
        architecture_parser.add_argument("--seed", type=int, default=None, help="Primary experiment seed.")
        architecture_parser.add_argument("--split-seed", type=int, default=None, help="Deterministic split seed; defaults to the dataset seed or artifact value.")
        architecture_parser.add_argument("--feature-mode", choices=("raw_observation", "observation_plus_tracking_errors"), default=None, help="Feature mode to use for training.")
        architecture_parser.add_argument("--epochs", type=int, default=None, help="Number of training epochs.")
        architecture_parser.add_argument("--batch-size", type=int, default=None, help="Training batch size.")
        architecture_parser.add_argument("--learning-rate", type=float, default=None, help="Optimizer learning rate.")
        architecture_parser.add_argument("--weight-decay", type=float, default=None, help="Optimizer weight decay.")
        architecture_parser.add_argument("--window-size", type=int, default=None, help="Temporal window size.")
        architecture_parser.add_argument("--stride", type=int, default=None, help="Window stride.")
        if architecture == "mlp":
            architecture_parser.add_argument("--hidden-layers", type=_parse_hidden_layers, default=None, help="Comma-separated MLP hidden layer sizes.")
        else:
            architecture_parser.add_argument("--hidden-size", type=int, default=None, help="Recurrent hidden size.")
            architecture_parser.add_argument("--num-layers", type=int, default=None, help="Recurrent layer count.")
            architecture_parser.add_argument("--dropout", type=float, default=None, help="Recurrent dropout rate.")
        architecture_parser.set_defaults(func=lambda args, parser, architecture=architecture: _run_train_command(args, parser, architecture=architecture))

    benchmark_parser = neural_subparsers.add_parser("benchmark", help="Run benchmark slices for trained neural controllers.")
    benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
    main_benchmark_parser = benchmark_subparsers.add_parser(
        "main",
        help="Run the main benchmark used for model selection.",
        description="Run the main benchmark used for model selection.",
    )
    main_benchmark_parser.add_argument("--workspace", type=Path, default=Path("artifacts/neural"), help="Root directory for neural-control artifacts.")
    main_benchmark_parser.add_argument("--run-id", type=str, default=None, help="Execution identifier for convention-based checkpoint resolution.")
    main_benchmark_parser.add_argument("--output-dir", type=Path, default=None, help="Override the benchmark output directory.")
    main_benchmark_parser.add_argument("--mlp-checkpoint", type=Path, default=None, help="Explicit path to the trained MLP checkpoint.")
    main_benchmark_parser.add_argument("--gru-checkpoint", type=Path, default=None, help="Explicit path to the trained GRU checkpoint.")
    main_benchmark_parser.add_argument("--lstm-checkpoint", type=Path, default=None, help="Explicit path to the trained LSTM checkpoint.")
    main_benchmark_parser.set_defaults(func=_run_main_benchmark_command)
    ood_benchmark_parser = benchmark_subparsers.add_parser(
        "ood",
        help="Run the OOD robustness benchmark. Not for tuning or model selection.",
        description="Run the OOD robustness benchmark. OOD is separate from the main benchmark and must not be used for tuning or model selection.",
    )
    ood_benchmark_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("artifacts/neural"),
        help="Root directory for neural-control artifacts. OOD is not for tuning or model selection.",
    )
    ood_benchmark_parser.add_argument("--run-id", type=str, default=None, help="Execution identifier for convention-based checkpoint resolution.")
    ood_benchmark_parser.add_argument("--output-dir", type=Path, default=None, help="Override the OOD benchmark output directory.")
    ood_benchmark_parser.add_argument("--mlp-checkpoint", type=Path, default=None, help="Explicit path to the trained MLP checkpoint.")
    ood_benchmark_parser.add_argument("--gru-checkpoint", type=Path, default=None, help="Explicit path to the trained GRU checkpoint.")
    ood_benchmark_parser.add_argument("--lstm-checkpoint", type=Path, default=None, help="Explicit path to the trained LSTM checkpoint.")
    ood_benchmark_parser.set_defaults(func=_run_ood_benchmark_command)

    report_parser = neural_subparsers.add_parser("report", help="Generate reports from persisted benchmark artifacts.")
    report_subparsers = report_parser.add_subparsers(dest="report_command", required=True)
    final_report_parser = report_subparsers.add_parser(
        "final",
        help="Generate the final report from a persisted main benchmark. OOD is excluded.",
        description="Generate the final report from a persisted main benchmark. OOD is excluded from selection.",
    )
    final_report_parser.add_argument(
        "--benchmark-path",
        type=Path,
        required=True,
        help="Path to the persisted main benchmark.json artifact. OOD is excluded from selection.",
    )
    final_report_parser.add_argument("--output-dir", type=Path, default=None, help="Override the final report output directory.")
    final_report_parser.set_defaults(func=_run_final_report_command)

    inspect_parser = neural_subparsers.add_parser("inspect", help="Inspect a checkpoint artifact.")
    inspect_subparsers = inspect_parser.add_subparsers(dest="inspect_command", required=True)
    checkpoint_parser = inspect_subparsers.add_parser("checkpoint", help="Inspect a single checkpoint.")
    checkpoint_parser.add_argument("--checkpoint", type=Path, required=True, help="Path to the checkpoint file to inspect.")
    checkpoint_parser.add_argument("--format", choices=("text", "json"), default="text", help="Inspection output format.")
    checkpoint_parser.set_defaults(func=_run_inspect_checkpoint_command)
    return parser


def _run_dataset_prepare_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        result = prepare_dataset_artifacts(
            args.telemetry,
            workspace=args.workspace,
            run_id=args.run_id,
            output_dir=args.output_dir,
            seed=args.seed,
            split_seed=args.split_seed,
            feature_mode=args.feature_mode,
            overwrite=args.overwrite,
            command="multirotor-sim neural dataset prepare",
            argv=getattr(args, "argv", ()),
        )
    except (DatasetArtifactError, ValueError) as exc:
        parser.error(str(exc))
    print(f"dataset_artifact: {result.dataset_path}")
    print(f"dataset_manifest: {result.manifest_path}")
    print(f"dataset_summary: {result.summary_path}")
    print(f"dataset_run_id: {result.manifest_payload['run_id']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.argv = tuple(argv if argv is not None else sys.argv[1:])
    if getattr(args, "command", None) == "neural":
        if args.neural_command == "dataset" and args.dataset_command == "prepare":
            return args.func(args, parser)
        if args.neural_command == "train" and args.train_command in {"mlp", "gru", "lstm"}:
            return args.func(args, parser)
        if args.neural_command == "benchmark" and args.benchmark_command in {"main", "ood"}:
            return args.func(args, parser)
        if args.neural_command == "report" and args.report_command == "final":
            return args.func(args, parser)
        if args.neural_command == "inspect" and args.inspect_command == "checkpoint":
            return args.func(args, parser)
        parser.error("unsupported neural command")
    if args.analysis_dir is not None:
        scenario = load_simulation_scenario(args.scenario) if args.scenario is not None else build_minimal_scenario(seed=args.seed)
        return run_scenario_analysis(scenario=scenario, analysis_dir=args.analysis_dir)
    if args.scenario is not None:
        return run_scenario_demo(load_simulation_scenario(args.scenario))
    return run_minimal_demo(seed=args.seed)
