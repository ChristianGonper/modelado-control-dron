"""Minimal comparison helpers for the Phase 3 MLP slice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Sequence

from .control.cascade import CascadedController
from .control.mlp import load_mlp_controller
from .metrics import compare_tracking_metrics, compute_tracking_metrics
from .runner import SimulationRunner
from .scenarios import SimulationScenario


@dataclass(frozen=True, slots=True)
class BenchmarkScenarioResult:
    scenario: dict[str, object]
    baseline_metrics: dict[str, object]
    mlp_metrics: dict[str, object]
    comparison: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "baseline_metrics": self.baseline_metrics,
            "mlp_metrics": self.mlp_metrics,
            "comparison": self.comparison,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    checkpoint_path: Path
    output_path: Path
    results: tuple[BenchmarkScenarioResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "checkpoint_path": str(self.checkpoint_path),
            "output_path": str(self.output_path),
            "results": [result.to_dict() for result in self.results],
        }


def run_homogeneous_mlp_benchmark(
    scenarios: Sequence[SimulationScenario],
    *,
    checkpoint_path: str | Path,
    output_path: str | Path,
) -> BenchmarkResult:
    scenarios = tuple(scenarios)
    if not scenarios:
        raise ValueError("scenarios must not be empty")

    resolved_checkpoint_path = Path(checkpoint_path)
    resolved_output_path = Path(output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    mlp_controller = load_mlp_controller(resolved_checkpoint_path)
    runner = SimulationRunner()
    results: list[BenchmarkScenarioResult] = []
    for scenario in scenarios:
        mlp_controller.reset()
        baseline_history = runner.run(scenario, controller=CascadedController())
        mlp_history = runner.run(scenario, controller=mlp_controller)
        baseline_metrics = compute_tracking_metrics(baseline_history)
        mlp_metrics = compute_tracking_metrics(mlp_history)
        comparison = compare_tracking_metrics(baseline_metrics, mlp_metrics)
        results.append(
            BenchmarkScenarioResult(
                scenario=scenario.describe(),
                baseline_metrics=baseline_metrics.to_dict(),
                mlp_metrics=mlp_metrics.to_dict(),
                comparison=comparison.to_dict(),
            )
        )

    result = BenchmarkResult(
        checkpoint_path=resolved_checkpoint_path,
        output_path=resolved_output_path,
        results=tuple(results),
    )
    resolved_output_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
