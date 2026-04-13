"""Punto de entrada mínimo para validar el esqueleto del proyecto."""

from __future__ import annotations

import argparse
from typing import Sequence

from .runner import SimulationRunner
from .scenarios import build_minimal_scenario


def build_minimal_demo(*, seed: int | None = None) -> dict[str, object]:
    """Run the minimum validated demo and return its history."""
    scenario = build_minimal_scenario(seed=seed)
    history = SimulationRunner().run(scenario)
    return {"scenario": scenario, "history": history}


def run_minimal_demo() -> int:
    demo = build_minimal_demo()
    print("simulador-multirotor minimal run")
    history = demo["history"]
    scenario = demo["scenario"]
    print(f"steps: {len(history.steps)}")
    print(f"final_time_s: {history.final_time_s:.3f}")
    print(f"scenario_name: {scenario.metadata.name}")
    print(f"scenario_seed: {scenario.metadata.seed}")
    print(f"final_state: {history.final_state}")
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
    args = parser.parse_args(argv)
    if args.seed is not None:
        demo = build_minimal_demo(seed=args.seed)
        history = demo["history"]
        scenario = demo["scenario"]
        print("simulador-multirotor minimal run")
        print(f"steps: {len(history.steps)}")
        print(f"final_time_s: {history.final_time_s:.3f}")
        print(f"scenario_name: {scenario.metadata.name}")
        print(f"scenario_seed: {scenario.metadata.seed}")
        print(f"final_state: {history.final_state}")
        return 0
    return run_minimal_demo()
