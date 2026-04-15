"""Minimal comparison helpers for the Phase 3 MLP slice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from time import perf_counter
from typing import Sequence

from .control.cascade import CascadedController
from .control.mlp import load_mlp_controller
from .control.recurrent import load_recurrent_controller
from .control.contract import ControllerContract
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


@dataclass(slots=True)
class _TimedController:
    controller: ControllerContract
    kind: str = ""
    source: str = ""
    parameters: dict[str, object] | None = None
    cpu_inference_time_s_total: float = 0.0
    compute_action_count: int = 0

    def __post_init__(self) -> None:
        self.kind = str(getattr(self.controller, "kind", "")).strip().lower()
        self.source = str(getattr(self.controller, "source", "")).strip().lower()
        self.parameters = dict(getattr(self.controller, "parameters", {}))

    def reset(self) -> None:
        reset = getattr(self.controller, "reset", None)
        if callable(reset):
            reset()
        self.cpu_inference_time_s_total = 0.0
        self.compute_action_count = 0

    def compute_action(self, observation, reference):  # pragma: no cover - delegation wrapper
        start = perf_counter()
        action = self.controller.compute_action(observation, reference)
        self.cpu_inference_time_s_total += perf_counter() - start
        self.compute_action_count += 1
        return action


@dataclass(frozen=True, slots=True)
class NeuralBenchmarkControllerResult:
    controller_kind: str
    controller_source: str
    metrics: dict[str, object]
    cpu_inference_time_s_total: float
    cpu_inference_time_s_mean: float
    compute_action_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "controller_kind": self.controller_kind,
            "controller_source": self.controller_source,
            "metrics": self.metrics,
            "cpu_inference_time_s_total": self.cpu_inference_time_s_total,
            "cpu_inference_time_s_mean": self.cpu_inference_time_s_mean,
            "compute_action_count": self.compute_action_count,
        }


@dataclass(frozen=True, slots=True)
class NeuralBenchmarkScenarioResult:
    scenario: dict[str, object]
    baseline: NeuralBenchmarkControllerResult
    mlp: NeuralBenchmarkControllerResult
    gru: NeuralBenchmarkControllerResult
    lstm: NeuralBenchmarkControllerResult
    comparisons: dict[str, dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "baseline": self.baseline.to_dict(),
            "mlp": self.mlp.to_dict(),
            "gru": self.gru.to_dict(),
            "lstm": self.lstm.to_dict(),
            "comparisons": self.comparisons,
        }


@dataclass(frozen=True, slots=True)
class NeuralBenchmarkResult:
    checkpoint_paths: dict[str, Path]
    output_path: Path
    results: tuple[NeuralBenchmarkScenarioResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "checkpoint_paths": {key: str(value) for key, value in self.checkpoint_paths.items()},
            "output_path": str(self.output_path),
            "results": [result.to_dict() for result in self.results],
        }


def _timed_run(runner: SimulationRunner, scenario: SimulationScenario, controller: ControllerContract) -> tuple[object, _TimedController]:
    timed_controller = _TimedController(controller)
    timed_controller.reset()
    history = runner.run(scenario, controller=timed_controller)
    return history, timed_controller


def _controller_result_from_history(
    *,
    controller: _TimedController,
    history,
    metrics,
) -> NeuralBenchmarkControllerResult:
    step_count = len(history.steps)
    cpu_inference_time_s_mean = 0.0 if controller.compute_action_count == 0 else controller.cpu_inference_time_s_total / controller.compute_action_count
    return NeuralBenchmarkControllerResult(
        controller_kind=controller.kind,
        controller_source=controller.source,
        metrics=metrics.to_dict(),
        cpu_inference_time_s_total=controller.cpu_inference_time_s_total,
        cpu_inference_time_s_mean=cpu_inference_time_s_mean,
        compute_action_count=controller.compute_action_count if controller.compute_action_count else step_count,
    )


def run_homogeneous_neural_benchmark(
    scenarios: Sequence[SimulationScenario],
    *,
    mlp_checkpoint_path: str | Path,
    gru_checkpoint_path: str | Path,
    lstm_checkpoint_path: str | Path,
    output_path: str | Path,
) -> NeuralBenchmarkResult:
    scenarios = tuple(scenarios)
    if not scenarios:
        raise ValueError("scenarios must not be empty")

    resolved_output_path = Path(output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_paths = {
        "mlp": Path(mlp_checkpoint_path),
        "gru": Path(gru_checkpoint_path),
        "lstm": Path(lstm_checkpoint_path),
    }

    mlp_controller = load_mlp_controller(checkpoint_paths["mlp"])
    gru_controller = load_recurrent_controller(checkpoint_paths["gru"])
    lstm_controller = load_recurrent_controller(checkpoint_paths["lstm"])
    runner = SimulationRunner()
    results: list[NeuralBenchmarkScenarioResult] = []
    for scenario in scenarios:
        baseline_history, baseline_timed = _timed_run(runner, scenario, CascadedController())
        mlp_history, mlp_timed = _timed_run(runner, scenario, mlp_controller)
        gru_history, gru_timed = _timed_run(runner, scenario, gru_controller)
        lstm_history, lstm_timed = _timed_run(runner, scenario, lstm_controller)

        baseline_metrics = compute_tracking_metrics(baseline_history)
        mlp_metrics = compute_tracking_metrics(mlp_history)
        gru_metrics = compute_tracking_metrics(gru_history)
        lstm_metrics = compute_tracking_metrics(lstm_history)

        results.append(
            NeuralBenchmarkScenarioResult(
                scenario=scenario.describe(),
                baseline=_controller_result_from_history(
                    controller=baseline_timed,
                    history=baseline_history,
                    metrics=baseline_metrics,
                ),
                mlp=_controller_result_from_history(
                    controller=mlp_timed,
                    history=mlp_history,
                    metrics=mlp_metrics,
                ),
                gru=_controller_result_from_history(
                    controller=gru_timed,
                    history=gru_history,
                    metrics=gru_metrics,
                ),
                lstm=_controller_result_from_history(
                    controller=lstm_timed,
                    history=lstm_history,
                    metrics=lstm_metrics,
                ),
                comparisons={
                    "mlp": compare_tracking_metrics(baseline_metrics, mlp_metrics).to_dict(),
                    "gru": compare_tracking_metrics(baseline_metrics, gru_metrics).to_dict(),
                    "lstm": compare_tracking_metrics(baseline_metrics, lstm_metrics).to_dict(),
                },
            )
        )

    result = NeuralBenchmarkResult(
        checkpoint_paths=checkpoint_paths,
        output_path=resolved_output_path,
        results=tuple(results),
    )
    resolved_output_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
