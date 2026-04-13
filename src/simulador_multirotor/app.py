"""Punto de entrada mínimo para validar el esqueleto del proyecto."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .metrics import compute_tracking_metrics
from .runner import SimulationRunner
from .scenarios import build_minimal_scenario
from .telemetry import export_history_to_json
from .visualization import load_telemetry_archive, render_analysis_outputs


def build_minimal_demo(*, seed: int | None = None) -> dict[str, object]:
    """Run the minimum validated demo and return its history."""
    scenario = build_minimal_scenario(seed=seed)
    history = SimulationRunner().run(scenario)
    return {"scenario": scenario, "history": history}


def _print_demo_summary(*, history, scenario) -> None:
    print("simulador-multirotor minimal run")
    metrics = compute_tracking_metrics(history)
    print(f"steps: {len(history.steps)}")
    print(f"final_time_s: {history.final_time_s:.3f}")
    print(f"scenario_name: {scenario.metadata.name}")
    print(f"scenario_seed: {scenario.metadata.seed}")
    print(f"position_rmse_m: {metrics.position_rmse_m:.4f}")
    print(f"velocity_rmse_m_s: {metrics.velocity_rmse_m_s:.4f}")
    print(f"mean_collective_thrust_newton: {metrics.mean_collective_thrust_newton:.4f}")
    print(f"final_state: {history.final_state}")


def run_minimal_demo(*, seed: int | None = None) -> int:
    demo = build_minimal_demo(seed=seed)
    _print_demo_summary(history=demo["history"], scenario=demo["scenario"])
    return 0


def run_minimal_analysis(*, seed: int | None = None, analysis_dir: str | Path) -> int:
    demo = build_minimal_demo(seed=seed)
    history = demo["history"]
    scenario = demo["scenario"]
    _print_demo_summary(history=history, scenario=scenario)
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


def main(argv: Sequence[str] | None = None) -> int:
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
        "--analysis-dir",
        type=Path,
        default=None,
        help="Export telemetry and generate static analysis outputs in the given directory.",
    )
    args = parser.parse_args(argv)
    if args.analysis_dir is not None:
        return run_minimal_analysis(seed=args.seed, analysis_dir=args.analysis_dir)
    return run_minimal_demo(seed=args.seed)
