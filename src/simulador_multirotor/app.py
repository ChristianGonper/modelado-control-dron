"""Punto de entrada mínimo para validar el esqueleto del proyecto."""

from __future__ import annotations

import argparse
from typing import Sequence

from .runner import run_minimal_simulation


def build_minimal_demo() -> dict[str, object]:
    """Run the minimum validated demo and return its history."""
    return {"history": run_minimal_simulation()}


def run_minimal_demo() -> int:
    demo = build_minimal_demo()
    print("simulador-multirotor minimal run")
    history = demo["history"]
    print(f"steps: {len(history.steps)}")
    print(f"final_time_s: {history.final_time_s:.3f}")
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
    parser.parse_args(argv)
    return run_minimal_demo()
