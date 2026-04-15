"""Benchmark reporting and model selection for Phase 5."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg", force=True)

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def _slugify(value: object) -> str:
    text = str(value).strip().lower()
    cleaned = [character if character.isalnum() else "-" for character in text]
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "scenario"


def _save_figure(fig: Figure, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _style_axis(axis: plt.Axes) -> None:
    axis.grid(True, alpha=0.25)
    axis.set_facecolor("#fcfcfd")


def _load_payload(source: str | Path | Mapping[str, object]) -> dict[str, object]:
    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    return json.loads(path.read_text(encoding="utf-8"))


def _metric(mapping: Mapping[str, object], key: str, default: float = 0.0) -> float:
    value = mapping.get(key, default)
    if isinstance(value, (list, tuple)):
        raise ValueError(f"metric {key} must be scalar")
    return float(value)


def _vector_metric(mapping: Mapping[str, object], key: str, length: int) -> tuple[float, ...]:
    value = mapping.get(key)
    if not isinstance(value, Sequence):
        raise ValueError(f"metric {key} must be a sequence")
    if len(value) != length:
        raise ValueError(f"metric {key} must contain exactly {length} values")
    return tuple(float(component) for component in value)


def _series_from_trace(trace: Mapping[str, object], key: str) -> np.ndarray:
    value = trace.get(key)
    if value is None:
        raise ValueError(f"trace is missing {key}")
    return np.asarray(value, dtype=np.float64)


def _scenario_label(scenario: Mapping[str, object]) -> str:
    metadata = scenario.get("metadata", {})
    if isinstance(metadata, Mapping):
        name = metadata.get("name")
        if name:
            return str(name)
    trajectory = scenario.get("trajectory", {})
    if isinstance(trajectory, Mapping):
        kind = trajectory.get("kind")
        if kind:
            return str(kind)
    return "scenario"


def _collect_controller_rows(payload: Mapping[str, object]) -> list[dict[str, object]]:
    results = payload.get("results", [])
    if not isinstance(results, Sequence):
        raise ValueError("benchmark payload must contain a results sequence")

    rows: list[dict[str, object]] = []
    for result in results:
        if not isinstance(result, Mapping):
            raise ValueError("benchmark result entries must be mappings")
        scenario = result.get("scenario", {})
        scenario_label = _scenario_label(scenario if isinstance(scenario, Mapping) else {})
        for model_key in ("baseline", "mlp", "gru", "lstm"):
            controller = result.get(model_key)
            if not isinstance(controller, Mapping):
                raise ValueError(f"benchmark result is missing {model_key}")
            metrics = controller.get("metrics", {})
            trace = controller.get("trace", {})
            if not isinstance(metrics, Mapping) or not isinstance(trace, Mapping):
                raise ValueError(f"{model_key} result must contain metrics and trace mappings")
            rows.append(
                {
                    "scenario_label": scenario_label,
                    "model_key": model_key,
                    "controller_kind": str(controller.get("controller_kind", model_key)),
                    "controller_source": str(controller.get("controller_source", "")),
                    "cpu_inference_time_s_total": float(controller.get("cpu_inference_time_s_total", 0.0)),
                    "cpu_inference_time_s_mean": float(controller.get("cpu_inference_time_s_mean", 0.0)),
                    "compute_action_count": int(controller.get("compute_action_count", 0)),
                    "metrics": dict(metrics),
                    "trace": dict(trace),
                }
            )
    return rows


def _smoothness_scalar(metrics: Mapping[str, object]) -> float:
    thrust_total_variation = _metric(metrics, "collective_thrust_total_variation_newton")
    torque_total_variation = _vector_metric(metrics, "torque_total_variation_nm", 3)
    return thrust_total_variation + sum(abs(component) for component in torque_total_variation)


def _precision_scalar(metrics: Mapping[str, object]) -> float:
    return (
        _metric(metrics, "position_rmse_m")
        + 0.25 * _metric(metrics, "velocity_rmse_m_s")
        + 0.5 * _metric(metrics, "yaw_rmse_rad")
    )


def _robustness_scalar(metrics: Mapping[str, object]) -> float:
    return _metric(metrics, "position_rmse_m") + 0.5 * _metric(metrics, "yaw_rmse_rad")


def _inference_scalar(metrics: Mapping[str, object], controller: Mapping[str, object]) -> float:
    cpu_time = controller.get("cpu_inference_time_s_mean")
    if cpu_time is not None:
        return float(cpu_time)
    return _metric(metrics, "cpu_inference_time_s_mean", 0.0)


@dataclass(frozen=True, slots=True)
class ConsolidatedModelSummary:
    model_key: str
    controller_kind: str
    controller_source: str
    scenario_count: int
    control_observation_source: str
    tracking_state_source: str
    mean_position_rmse_m: float
    mean_position_mae_m: float
    mean_velocity_rmse_m_s: float
    mean_yaw_rmse_rad: float
    mean_collective_thrust_total_variation_newton: float
    mean_cpu_inference_time_s_mean: float
    worst_position_rmse_m: float
    worst_yaw_rmse_rad: float
    precision_score: float
    smoothness_score: float
    robustness_score: float
    inference_score: float
    total_score: float
    baseline_position_rmse_ratio: float | None = None
    baseline_smoothness_ratio: float | None = None
    baseline_inference_ratio: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "model_key": self.model_key,
            "controller_kind": self.controller_kind,
            "controller_source": self.controller_source,
            "scenario_count": self.scenario_count,
            "control_observation_source": self.control_observation_source,
            "tracking_state_source": self.tracking_state_source,
            "mean_position_rmse_m": self.mean_position_rmse_m,
            "mean_position_mae_m": self.mean_position_mae_m,
            "mean_velocity_rmse_m_s": self.mean_velocity_rmse_m_s,
            "mean_yaw_rmse_rad": self.mean_yaw_rmse_rad,
            "mean_collective_thrust_total_variation_newton": self.mean_collective_thrust_total_variation_newton,
            "mean_cpu_inference_time_s_mean": self.mean_cpu_inference_time_s_mean,
            "worst_position_rmse_m": self.worst_position_rmse_m,
            "worst_yaw_rmse_rad": self.worst_yaw_rmse_rad,
            "precision_score": self.precision_score,
            "smoothness_score": self.smoothness_score,
            "robustness_score": self.robustness_score,
            "inference_score": self.inference_score,
            "total_score": self.total_score,
            "baseline_position_rmse_ratio": self.baseline_position_rmse_ratio,
            "baseline_smoothness_ratio": self.baseline_smoothness_ratio,
            "baseline_inference_ratio": self.baseline_inference_ratio,
        }


@dataclass(frozen=True, slots=True)
class SelectionResult:
    selected_model_key: str
    selected_controller_kind: str
    selected_score: float
    score_breakdown: dict[str, float]
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_model_key": self.selected_model_key,
            "selected_controller_kind": self.selected_controller_kind,
            "selected_score": self.selected_score,
            "score_breakdown": self.score_breakdown,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ReportArtifactBundle:
    benchmark_path: Path
    output_dir: Path
    table_path: Path
    report_path: Path
    selection_path: Path
    figure_paths: dict[str, dict[str, Path]]

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_path": str(self.benchmark_path),
            "output_dir": str(self.output_dir),
            "table_path": str(self.table_path),
            "report_path": str(self.report_path),
            "selection_path": str(self.selection_path),
            "figure_paths": {
                scenario: {kind: str(path) for kind, path in paths.items()}
                for scenario, paths in self.figure_paths.items()
            },
        }


def build_consolidated_model_summaries(
    source: str | Path | Mapping[str, object],
    *,
    candidate_models: Sequence[str] = ("mlp", "gru", "lstm"),
) -> list[ConsolidatedModelSummary]:
    payload = _load_payload(source)
    rows = _collect_controller_rows(payload)
    if not rows:
        raise ValueError("benchmark payload must contain at least one scenario")

    aggregated: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        aggregated.setdefault(str(row["model_key"]), []).append(row)

    summaries: list[ConsolidatedModelSummary] = []
    baseline_rows = aggregated.get("baseline", [])
    baseline_position_rmse = np.mean([_metric(row["metrics"], "position_rmse_m") for row in baseline_rows]) if baseline_rows else None
    baseline_smoothness = np.mean([_smoothness_scalar(row["metrics"]) for row in baseline_rows]) if baseline_rows else None
    baseline_inference = np.mean([_inference_scalar(row["metrics"], row) for row in baseline_rows]) if baseline_rows else None

    for model_key in ("baseline", *candidate_models):
        model_rows = aggregated.get(model_key, [])
        if not model_rows:
            continue
        metrics_list = [row["metrics"] for row in model_rows]
        controller = model_rows[0]
        precision_components = [_precision_scalar(metrics) for metrics in metrics_list]
        smoothness_components = [_smoothness_scalar(metrics) for metrics in metrics_list]
        robustness_components = [_robustness_scalar(metrics) for metrics in metrics_list]
        inference_components = [_inference_scalar(row["metrics"], row) for row in model_rows]
        total_score = 0.45 * float(np.mean(precision_components)) + 0.20 * float(np.mean(smoothness_components)) + 0.25 * float(np.mean(robustness_components)) + 0.10 * float(np.mean(inference_components))
        summaries.append(
            ConsolidatedModelSummary(
                model_key=model_key,
                controller_kind=str(controller["controller_kind"]),
                controller_source=str(controller["controller_source"]),
                scenario_count=len(model_rows),
                control_observation_source=str(metrics_list[0].get("control_observation_source", "observed_state")),
                tracking_state_source=str(metrics_list[0].get("tracking_state_source", "true_state")),
                mean_position_rmse_m=float(np.mean([_metric(metrics, "position_rmse_m") for metrics in metrics_list])),
                mean_position_mae_m=float(np.mean([_metric(metrics, "position_mae_m") for metrics in metrics_list])),
                mean_velocity_rmse_m_s=float(np.mean([_metric(metrics, "velocity_rmse_m_s") for metrics in metrics_list])),
                mean_yaw_rmse_rad=float(np.mean([_metric(metrics, "yaw_rmse_rad") for metrics in metrics_list])),
                mean_collective_thrust_total_variation_newton=float(np.mean([_metric(metrics, "collective_thrust_total_variation_newton") for metrics in metrics_list])),
                mean_cpu_inference_time_s_mean=float(np.mean(inference_components)),
                worst_position_rmse_m=float(np.max([_metric(metrics, "position_rmse_m") for metrics in metrics_list])),
                worst_yaw_rmse_rad=float(np.max([_metric(metrics, "yaw_rmse_rad") for metrics in metrics_list])),
                precision_score=float(np.mean(precision_components)),
                smoothness_score=float(np.mean(smoothness_components)),
                robustness_score=float(np.mean(robustness_components)),
                inference_score=float(np.mean(inference_components)),
                total_score=total_score,
                baseline_position_rmse_ratio=None if baseline_position_rmse is None else float(np.mean([_metric(metrics, "position_rmse_m") for metrics in metrics_list]) / max(baseline_position_rmse, 1e-12)),
                baseline_smoothness_ratio=None if baseline_smoothness is None else float(np.mean(smoothness_components) / max(baseline_smoothness, 1e-12)),
                baseline_inference_ratio=None if baseline_inference is None else float(np.mean(inference_components) / max(baseline_inference, 1e-12)),
            )
        )
    return summaries


def build_consolidated_table_markdown(
    source: str | Path | Mapping[str, object],
    *,
    candidate_models: Sequence[str] = ("mlp", "gru", "lstm"),
) -> str:
    summaries = build_consolidated_model_summaries(source, candidate_models=candidate_models)
    if not summaries:
        raise ValueError("benchmark payload did not produce any summaries")

    lines = [
        "# Phase 5 Benchmark Summary",
        "",
        "Control is computed from `observed_state` and tracking is evaluated on `true_state`.",
        "",
        "| Model | Controller | Scenarios | Position RMSE [m] | Position MAE [m] | Yaw RMSE [rad] | Smoothness score | CPU inference [s] | Total score |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        lines.append(
            "| {model} | {kind} / {source} | {count} | {rmse:.4f} | {mae:.4f} | {yaw:.4f} | {smoothness:.4f} | {cpu:.6f} | {score:.4f} |".format(
                model=summary.model_key,
                kind=summary.controller_kind,
                source=summary.controller_source,
                count=summary.scenario_count,
                rmse=summary.mean_position_rmse_m,
                mae=summary.mean_position_mae_m,
                yaw=summary.mean_yaw_rmse_rad,
                smoothness=summary.smoothness_score,
                cpu=summary.mean_cpu_inference_time_s_mean,
                score=summary.total_score,
            )
        )
    return "\n".join(lines) + "\n"


def _render_trajectory_comparison_figure(scenario_label: str, controllers: Sequence[Mapping[str, object]]) -> Figure:
    fig, axis = plt.subplots(figsize=(9.5, 7.5), constrained_layout=True)
    for controller in controllers:
        trace = controller["trace"]
        state_positions = _series_from_trace(trace, "state_position_m")
        reference_positions = _series_from_trace(trace, "reference_position_m")
        model_key = str(controller["model_key"])
        axis.plot(reference_positions[:, 0], reference_positions[:, 1], linestyle="--", linewidth=2.0, alpha=0.5, label=f"ref-{model_key}")
        axis.plot(state_positions[:, 0], state_positions[:, 1], linewidth=2.0, label=model_key)
    axis.set_title(f"Trajectory comparison - {scenario_label}")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_aspect("equal", adjustable="box")
    _style_axis(axis)
    axis.legend(loc="best", frameon=False, ncol=2)
    return fig


def _render_temporal_error_comparison_figure(scenario_label: str, controllers: Sequence[Mapping[str, object]]) -> Figure:
    fig, axes = plt.subplots(3, 1, figsize=(10.0, 9.0), sharex=True, constrained_layout=True)
    series = (
        ("position_error_norm_m", "Position error |e_p| [m]", axes[0], "#d62728"),
        ("velocity_error_norm_m_s", "Velocity error |e_v| [m/s]", axes[1], "#9467bd"),
        ("yaw_error_rad", "Yaw error [rad]", axes[2], "#ff7f0e"),
    )
    for key, ylabel, axis, color in series:
        for controller in controllers:
            trace = controller["trace"]
            times = _series_from_trace(trace, "time_s")
            values = _series_from_trace(trace, key)
            axis.plot(times, values, linewidth=1.6, label=str(controller["model_key"]))
        axis.set_ylabel(ylabel)
        _style_axis(axis)
        axis.legend(loc="best", frameon=False, ncol=2)
    axes[0].set_title(f"Temporal error comparison - {scenario_label}")
    axes[-1].set_xlabel("t [s]")
    return fig


def _render_control_behavior_comparison_figure(scenario_label: str, controllers: Sequence[Mapping[str, object]]) -> Figure:
    fig, axes = plt.subplots(4, 1, figsize=(10.0, 10.5), sharex=True, constrained_layout=True)
    panel_specs = (
        ("collective_thrust_newton", "Collective thrust [N]", "#1f77b4"),
        ("body_torque_nm", "Torque x [Nm]", "#2ca02c"),
        ("body_torque_nm", "Torque y [Nm]", "#ff7f0e"),
        ("body_torque_nm", "Torque z [Nm]", "#d62728"),
    )
    for index, (key, ylabel, color) in enumerate(panel_specs):
        axis = axes[index]
        for controller in controllers:
            trace = controller["trace"]
            times = _series_from_trace(trace, "time_s")
            if key == "collective_thrust_newton":
                values = _series_from_trace(trace, key)
            else:
                values = np.asarray(trace[key], dtype=np.float64)[:, index - 1]
            axis.plot(times, values, linewidth=1.6, label=str(controller["model_key"]))
        axis.set_ylabel(ylabel)
        _style_axis(axis)
        axis.legend(loc="best", frameon=False, ncol=2)
    axes[0].set_title(f"Control behavior comparison - {scenario_label}")
    axes[-1].set_xlabel("t [s]")
    return fig


def render_benchmark_figures(
    source: str | Path | Mapping[str, object],
    output_dir: str | Path,
) -> dict[str, dict[str, Path]]:
    payload = _load_payload(source)
    rows = _collect_controller_rows(payload)
    if not rows:
        raise ValueError("benchmark payload must contain at least one scenario")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["scenario_label"]), []).append(row)

    figure_paths: dict[str, dict[str, Path]] = {}
    for scenario_label, controllers in grouped.items():
        safe_label = _slugify(scenario_label)
        figure_paths[scenario_label] = {
            "trajectory": _save_figure(
                _render_trajectory_comparison_figure(scenario_label, controllers),
                output_path / f"{safe_label}_trajectory_comparison.png",
            ),
            "temporal_error": _save_figure(
                _render_temporal_error_comparison_figure(scenario_label, controllers),
                output_path / f"{safe_label}_temporal_error_comparison.png",
            ),
            "control_behavior": _save_figure(
                _render_control_behavior_comparison_figure(scenario_label, controllers),
                output_path / f"{safe_label}_control_behavior_comparison.png",
            ),
        }
    return figure_paths


def select_best_neural_model(
    source: str | Path | Mapping[str, object],
    *,
    candidate_models: Sequence[str] = ("mlp", "gru", "lstm"),
) -> SelectionResult:
    summaries = build_consolidated_model_summaries(source, candidate_models=candidate_models)
    summary_by_model = {summary.model_key: summary for summary in summaries}
    candidates = [summary_by_model[model_key] for model_key in candidate_models if model_key in summary_by_model]
    if not candidates:
        raise ValueError("benchmark payload did not include any candidate models")

    precision_best = min(summary.precision_score for summary in candidates)
    smoothness_best = min(summary.smoothness_score for summary in candidates)
    robustness_best = min(summary.robustness_score for summary in candidates)
    inference_best = min(summary.inference_score for summary in candidates)

    ranked: list[tuple[float, str, ConsolidatedModelSummary, dict[str, float]]] = []
    weights = {
        "precision": 0.45,
        "smoothness": 0.20,
        "robustness": 0.25,
        "inference": 0.10,
    }
    for summary in candidates:
        breakdown = {
            "precision": summary.precision_score / max(precision_best, 1e-12),
            "smoothness": summary.smoothness_score / max(smoothness_best, 1e-12),
            "robustness": summary.robustness_score / max(robustness_best, 1e-12),
            "inference": summary.inference_score / max(inference_best, 1e-12),
        }
        score = sum(weights[name] * breakdown[name] for name in weights)
        ranked.append((score, summary.model_key, summary, breakdown))

    ranked.sort(key=lambda item: (item[0], item[1]))
    selected_score, _, selected_summary, breakdown = ranked[0]
    baseline = summary_by_model.get("baseline")
    rationale_parts = [
        f"selected {selected_summary.model_key} with the lowest weighted score",
        f"precision={breakdown['precision']:.3f}",
        f"smoothness={breakdown['smoothness']:.3f}",
        f"robustness={breakdown['robustness']:.3f}",
        f"inference={breakdown['inference']:.3f}",
    ]
    if baseline is not None:
        rationale_parts.append(
            f"baseline_rmse_ratio={selected_summary.baseline_position_rmse_ratio:.3f}" if selected_summary.baseline_position_rmse_ratio is not None else "baseline_rmse_ratio=n/a"
        )
    rationale = "; ".join(rationale_parts)
    return SelectionResult(
        selected_model_key=selected_summary.model_key,
        selected_controller_kind=selected_summary.controller_kind,
        selected_score=selected_score,
        score_breakdown=breakdown,
        rationale=rationale,
    )


def generate_phase5_report(
    benchmark_source: str | Path | Mapping[str, object],
    output_dir: str | Path,
) -> ReportArtifactBundle:
    payload = _load_payload(benchmark_source)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    table_markdown = build_consolidated_table_markdown(payload)
    table_path = output_path / "comparison_table.md"
    table_path.write_text(table_markdown, encoding="utf-8")

    figure_paths = render_benchmark_figures(payload, output_path / "figures")

    selection = select_best_neural_model(payload)
    selection_path = output_path / "selection.json"
    selection_path.write_text(json.dumps(selection.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_lines = [
        "# Phase 5 Metrics and Reporting",
        "",
        "Control is computed from `observed_state` and tracking is evaluated on `true_state`.",
        "",
        "## Consolidated Table",
        "",
        table_markdown.rstrip(),
        "",
        "## Selected Model",
        "",
        f"- Model: `{selection.selected_model_key}`",
        f"- Controller: `{selection.selected_controller_kind}`",
        f"- Score: `{selection.selected_score:.4f}`",
        f"- Rationale: {selection.rationale}",
        "",
        "## Figures",
        "",
    ]
    for scenario_label, paths in figure_paths.items():
        report_lines.append(f"### {scenario_label}")
        for kind, path in paths.items():
            report_lines.append(f"- {kind}: [{path.name}]({path})")
        report_lines.append("")

    report_path = output_path / "report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return ReportArtifactBundle(
        benchmark_path=Path(benchmark_source) if isinstance(benchmark_source, (str, Path)) else output_path / "benchmark.json",
        output_dir=output_path,
        table_path=table_path,
        report_path=report_path,
        selection_path=selection_path,
        figure_paths=figure_paths,
    )
