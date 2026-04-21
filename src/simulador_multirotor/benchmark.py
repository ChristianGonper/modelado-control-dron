"""Minimal comparison helpers for the Phase 3 MLP slice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from time import perf_counter
from typing import Mapping, Sequence

from .control.cascade import CascadedController
from .control.mlp import load_mlp_controller
from .control.recurrent import load_gru_controller, load_lstm_controller
from .control.contract import ControllerContract
from .metrics import compare_tracking_metrics, compute_tracking_metrics
from .robustness import OOD_ROBUSTNESS_SCENARIO_SET_KEY, build_ood_robustness_scenarios
from .runner import SimulationRunner
from .scenarios import REFERENCE_SCENARIO_NAMES, SimulationScenario, load_simulation_scenario, reference_scenario_path


BENCHMARK_STAGE = "benchmark"
BENCHMARK_ARTIFACT_KIND = "benchmark"
BENCHMARK_MANIFEST_SCHEMA_VERSION = 1
MAIN_BENCHMARK_OUTPUT_NAME = "benchmark.json"
MAIN_BENCHMARK_SUMMARY_NAME = "benchmark-summary.md"
MAIN_BENCHMARK_MANIFEST_NAME = "manifest.json"


def build_main_benchmark_scenarios() -> tuple[SimulationScenario, ...]:
    return tuple(load_simulation_scenario(reference_scenario_path(name)) for name in REFERENCE_SCENARIO_NAMES)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _load_json_file(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"benchmark sidecar must be a JSON object: {path}")
    return payload


def _checkpoint_artifact_payload(checkpoint_path: Path) -> dict[str, object]:
    summary_path = checkpoint_path.with_name("checkpoint-summary.json")
    manifest_path = checkpoint_path.with_name("training-manifest.json")
    summary_payload = _load_json_file(summary_path)
    manifest_payload = _load_json_file(manifest_path)
    checkpoint_kind = None
    training_payload: dict[str, object] | None = None
    metrics_payload: dict[str, object] | None = None

    if summary_payload is not None:
        checkpoint_kind = summary_payload.get("checkpoint_kind")
        training = summary_payload.get("training")
        if isinstance(training, Mapping):
            training_payload = dict(training)
        metrics = summary_payload.get("metrics")
        if isinstance(metrics, Mapping):
            metrics_payload = dict(metrics)

    return {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_summary_path": str(summary_path) if summary_path.exists() else None,
        "training_manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "checkpoint_kind": checkpoint_kind,
        "training": training_payload,
        "metrics": metrics_payload,
        "training_manifest": manifest_payload,
    }


def _benchmark_summary_markdown(
    result: "NeuralBenchmarkResult",
    *,
    manifest_path: Path,
    summary_path: Path,
    checkpoint_artifacts: Mapping[str, Mapping[str, object]],
) -> str:
    lines = [
        "# Main Benchmark Summary",
        "",
        "Control is computed from `observed_state` and tracking is evaluated on `true_state`.",
        "",
        f"- `benchmark_kind`: `{result.benchmark_kind}`",
        f"- `scenario_set_key`: `{result.scenario_set_key}`",
        f"- `benchmark_path`: `{result.output_path}`",
        f"- `manifest_path`: `{manifest_path}`",
        f"- `summary_path`: `{summary_path}`",
        f"- `scenario_count`: `{len(result.results)}`",
        "",
        "## Checkpoints",
        "",
    ]
    for model_key in ("mlp", "gru", "lstm"):
        checkpoint_info = checkpoint_artifacts[model_key]
        lines.extend(
            [
                f"### {model_key}",
                f"- checkpoint: `{checkpoint_info['checkpoint_path']}`",
                f"- checkpoint_summary: `{checkpoint_info['checkpoint_summary_path'] or 'n/a'}`",
                f"- training_manifest: `{checkpoint_info['training_manifest_path'] or 'n/a'}`",
            ]
        )
        training = checkpoint_info.get("training")
        if isinstance(training, Mapping):
            for field_name in ("architecture", "feature_mode", "window_size", "stride", "seed", "split_seed", "hidden_layers", "hidden_size", "num_layers", "dropout"):
                if field_name in training:
                    lines.append(f"- {field_name}: `{training[field_name]}`")
        metrics = checkpoint_info.get("metrics")
        if isinstance(metrics, Mapping):
            for field_name in ("train_loss", "validation_loss", "train_window_count", "validation_window_count"):
                if field_name in metrics:
                    lines.append(f"- {field_name}: `{metrics[field_name]}`")
        lines.append("")
    lines.extend(
        [
            "## Scenarios",
            "",
        ]
    )
    for index, scenario_result in enumerate(result.results, start=1):
        scenario = scenario_result.scenario
        metadata = scenario.get("metadata", {}) if isinstance(scenario, Mapping) else {}
        scenario_name = metadata.get("name", f"scenario-{index}") if isinstance(metadata, Mapping) else f"scenario-{index}"
        lines.append(f"- `{scenario_name}`")
    return "\n".join(lines) + "\n"


def persist_main_benchmark_artifacts(
    result: "NeuralBenchmarkResult",
    *,
    output_dir: str | Path,
    command: str,
    argv: Sequence[str],
    run_id: str,
) -> dict[str, Path]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = resolved_output_dir / MAIN_BENCHMARK_MANIFEST_NAME
    summary_path = resolved_output_dir / MAIN_BENCHMARK_SUMMARY_NAME
    checkpoint_artifacts = {
        model_key: _checkpoint_artifact_payload(result.checkpoint_paths[model_key])
        for model_key in ("mlp", "gru", "lstm")
    }
    manifest_payload = {
        "schema_version": BENCHMARK_MANIFEST_SCHEMA_VERSION,
        "artifact_kind": BENCHMARK_ARTIFACT_KIND,
        "stage": BENCHMARK_STAGE,
        "benchmark_kind": result.benchmark_kind,
        "scenario_set_key": result.scenario_set_key,
        "run_id": run_id,
        "created_at": result.created_at or _utc_timestamp(),
        "command": command,
        "argv": list(argv),
        "output_path": str(manifest_path),
        "benchmark_path": str(result.output_path),
        "benchmark_output_dir": str(resolved_output_dir),
        "checkpoint_paths": {key: str(value) for key, value in result.checkpoint_paths.items()},
        "checkpoint_artifacts": checkpoint_artifacts,
        "scenario_count": len(result.results),
        "scenario_names": [
            _scenario_name_from_payload(scenario_result.scenario, index=index)
            for index, scenario_result in enumerate(result.results, start=1)
        ],
    }
    manifest_path.write_text(_json_dump(manifest_payload) + "\n", encoding="utf-8")
    summary_path.write_text(
        _benchmark_summary_markdown(
            result,
            manifest_path=manifest_path,
            summary_path=summary_path,
            checkpoint_artifacts=checkpoint_artifacts,
        ),
        encoding="utf-8",
    )
    return {
        "manifest_path": manifest_path,
        "summary_path": summary_path,
        "benchmark_path": result.output_path,
    }


def _scenario_name_from_payload(scenario: Mapping[str, object], *, index: int) -> str:
    metadata = scenario.get("metadata")
    if isinstance(metadata, Mapping):
        name = metadata.get("name")
        if name:
            return str(name)
    return f"scenario-{index}"


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
    trace: dict[str, object]
    cpu_inference_time_s_total: float
    cpu_inference_time_s_mean: float
    compute_action_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "controller_kind": self.controller_kind,
            "controller_source": self.controller_source,
            "metrics": self.metrics,
            "trace": self.trace,
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
    benchmark_kind: str
    scenario_set_key: str
    checkpoint_paths: dict[str, Path]
    output_path: Path
    results: tuple[NeuralBenchmarkScenarioResult, ...]
    created_at: str = ""
    command: str = ""
    argv: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_kind": self.benchmark_kind,
            "scenario_set_key": self.scenario_set_key,
            "checkpoint_paths": {key: str(value) for key, value in self.checkpoint_paths.items()},
            "output_path": str(self.output_path),
            "created_at": self.created_at,
            "command": self.command,
            "argv": list(self.argv),
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
    trace = {
        "time_s": [step.time_s for step in history.steps],
        "state_position_m": [step.state.position_m for step in history.steps],
        "reference_position_m": [step.reference.position_m for step in history.steps],
        "position_error_norm_m": [step.position_error_norm_m for step in history.steps],
        "velocity_error_norm_m_s": [step.velocity_error_norm_m_s for step in history.steps],
        "yaw_error_rad": [step.error.yaw_rad for step in history.steps],
        "collective_thrust_newton": [step.command.collective_thrust_newton for step in history.steps],
        "body_torque_nm": [step.command.body_torque_nm for step in history.steps],
    }
    return NeuralBenchmarkControllerResult(
        controller_kind=controller.kind,
        controller_source=controller.source,
        metrics=metrics.to_dict(),
        trace=trace,
        cpu_inference_time_s_total=controller.cpu_inference_time_s_total,
        cpu_inference_time_s_mean=cpu_inference_time_s_mean,
        compute_action_count=controller.compute_action_count if controller.compute_action_count else step_count,
    )


def _run_neural_benchmark(
    scenarios: Sequence[SimulationScenario],
    *,
    mlp_checkpoint_path: str | Path,
    gru_checkpoint_path: str | Path,
    lstm_checkpoint_path: str | Path,
    output_path: str | Path,
    benchmark_kind: str,
    scenario_set_key: str,
    command: str = "",
    argv: Sequence[str] = (),
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
    gru_controller = load_gru_controller(checkpoint_paths["gru"])
    lstm_controller = load_lstm_controller(checkpoint_paths["lstm"])
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
        benchmark_kind=benchmark_kind,
        scenario_set_key=scenario_set_key,
        checkpoint_paths=checkpoint_paths,
        output_path=resolved_output_path,
        results=tuple(results),
        created_at=_utc_timestamp(),
        command=command,
        argv=tuple(argv),
    )
    resolved_output_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_homogeneous_neural_benchmark(
    scenarios: Sequence[SimulationScenario],
    *,
    mlp_checkpoint_path: str | Path,
    gru_checkpoint_path: str | Path,
    lstm_checkpoint_path: str | Path,
    output_path: str | Path,
    command: str = "",
    argv: Sequence[str] = (),
) -> NeuralBenchmarkResult:
    return _run_neural_benchmark(
        scenarios,
        mlp_checkpoint_path=mlp_checkpoint_path,
        gru_checkpoint_path=gru_checkpoint_path,
        lstm_checkpoint_path=lstm_checkpoint_path,
        output_path=output_path,
        benchmark_kind="main",
        scenario_set_key="main-homogeneous-v1",
        command=command,
        argv=argv,
    )


def run_ood_robustness_benchmark(
    scenarios: Sequence[SimulationScenario] | None = None,
    *,
    mlp_checkpoint_path: str | Path,
    gru_checkpoint_path: str | Path,
    lstm_checkpoint_path: str | Path,
    output_path: str | Path,
) -> NeuralBenchmarkResult:
    resolved_scenarios = build_ood_robustness_scenarios() if scenarios is None else tuple(scenarios)
    return _run_neural_benchmark(
        resolved_scenarios,
        mlp_checkpoint_path=mlp_checkpoint_path,
        gru_checkpoint_path=gru_checkpoint_path,
        lstm_checkpoint_path=lstm_checkpoint_path,
        output_path=output_path,
        benchmark_kind="ood",
        scenario_set_key=OOD_ROBUSTNESS_SCENARIO_SET_KEY,
    )
