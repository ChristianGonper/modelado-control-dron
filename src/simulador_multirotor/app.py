"""Punto de entrada mínimo para validar el esqueleto del proyecto."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .metrics import compute_tracking_metrics
from .runner import SimulationRunner
from .scenarios import build_minimal_scenario, load_simulation_scenario
from .dataset.artifacts import DatasetArtifactError, prepare_dataset_artifacts
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
        parser.error("unsupported neural command")
    if args.analysis_dir is not None:
        scenario = load_simulation_scenario(args.scenario) if args.scenario is not None else build_minimal_scenario(seed=args.seed)
        return run_scenario_analysis(scenario=scenario, analysis_dir=args.analysis_dir)
    if args.scenario is not None:
        return run_scenario_demo(load_simulation_scenario(args.scenario))
    return run_minimal_demo(seed=args.seed)
