"""PD validation gate for the official generic-drone baseline."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isclose
from pathlib import Path
from typing import Sequence

from ..core.contracts import VehicleState
from ..metrics import TrackingMetrics, compute_tracking_metrics
from ..runner import SimulationRunner
from ..scenarios import (
    BASELINE_PROFILE_ID,
    ScenarioControllerConfig,
    ScenarioMetadata,
    ScenarioTelemetryConfig,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    SimulationScenario,
    build_baseline_vehicle_profile,
    save_simulation_scenario,
)
from ..telemetry import SimulationHistory, export_history_to_json


PD_VALIDATION_GATE_ID = "pd-expert-gate-v1"
PD_VALIDATION_PROFILE_ID = "generic-drone-pd-validation-v1"
PD_VALIDATION_SCENARIO_NAME = "generic-drone-pd-validation-v1"
PD_VALIDATION_SCENARIO_TAGS = ("baseline", "generic-drone", "phase-2", "validation", "pd-gate")
PD_VALIDATION_DURATION_S = 1.0
PD_VALIDATION_PHYSICS_DT_S = 0.02
PD_VALIDATION_CONTROL_DT_S = 0.04
PD_VALIDATION_TELEMETRY_DT_S = 0.04
PD_VALIDATION_DETAIL_LEVEL = "full"
PD_VALIDATION_TRAJECTORY_KIND = "line"
PD_VALIDATION_TRAJECTORY_START_POSITION_M = (0.0, 0.0, 1.0)
PD_VALIDATION_TRAJECTORY_VELOCITY_M_S = (0.1, 0.0, 0.0)
PD_VALIDATION_INITIAL_STATE = VehicleState(
    position_m=PD_VALIDATION_TRAJECTORY_START_POSITION_M,
    orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
    linear_velocity_m_s=(0.0, 0.0, 0.0),
    angular_velocity_rad_s=(0.0, 0.0, 0.0),
    time_s=0.0,
)
PD_VALIDATION_SATURATION_THRESHOLD = 0.98
PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES = {
    "scenario": "scenario.json",
    "telemetry": "telemetry.json",
    "report": "validation-report.json",
    "manifest": "manifest.json",
    "summary": "validation-summary.md",
}


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _controller_parameters() -> dict[str, object]:
    vehicle = build_baseline_vehicle_profile()
    return {
        "position_loop": {
            "mass_kg": vehicle.mass_kg,
            "gravity_m_s2": vehicle.gravity_m_s2,
            "kp_position": (2.0, 2.0, 4.0),
            "kd_velocity": (1.2, 1.2, 2.5),
        },
        "attitude_loop": {
            "mass_kg": vehicle.mass_kg,
            "gravity_m_s2": vehicle.gravity_m_s2,
            "max_collective_thrust_newton": vehicle.max_collective_thrust_newton,
            "max_body_torque_nm": vehicle.max_body_torque_nm,
            "kp_attitude": (4.5, 4.5, 1.8),
            "kd_body_rate": (0.15, 0.15, 0.08),
            "max_tilt_rad": 0.6,
        },
    }


def _trajectory_parameters() -> dict[str, object]:
    return {
        "scenario": PD_VALIDATION_SCENARIO_NAME,
        "validation_profile_id": PD_VALIDATION_PROFILE_ID,
        "baseline_profile_id": BASELINE_PROFILE_ID,
        "validation_gate_id": PD_VALIDATION_GATE_ID,
        "start_position_m": PD_VALIDATION_TRAJECTORY_START_POSITION_M,
        "velocity_m_s": PD_VALIDATION_TRAJECTORY_VELOCITY_M_S,
    }


def _build_pd_controller_config() -> ScenarioControllerConfig:
    return ScenarioControllerConfig(kind="cascade", parameters=_controller_parameters())


def _build_pd_trajectory_config() -> ScenarioTrajectoryConfig:
    return ScenarioTrajectoryConfig(
        kind=PD_VALIDATION_TRAJECTORY_KIND,
        target_position_m=PD_VALIDATION_TRAJECTORY_START_POSITION_M,
        target_velocity_m_s=PD_VALIDATION_TRAJECTORY_VELOCITY_M_S,
        valid_until_s=PD_VALIDATION_DURATION_S,
        source="native",
        parameters=_trajectory_parameters(),
    )


def _build_pd_telemetry_config() -> ScenarioTelemetryConfig:
    return ScenarioTelemetryConfig(record_scenario_metadata=True, detail_level=PD_VALIDATION_DETAIL_LEVEL, sample_dt_s=PD_VALIDATION_TELEMETRY_DT_S)


def build_pd_validation_scenario(*, seed: int | None = None) -> SimulationScenario:
    return SimulationScenario(
        initial_state=PD_VALIDATION_INITIAL_STATE,
        time=ScenarioTimeConfig(
            duration_s=PD_VALIDATION_DURATION_S,
            physics_dt_s=PD_VALIDATION_PHYSICS_DT_S,
            control_dt_s=PD_VALIDATION_CONTROL_DT_S,
            telemetry_dt_s=PD_VALIDATION_TELEMETRY_DT_S,
        ),
        vehicle=build_baseline_vehicle_profile(),
        trajectory=_build_pd_trajectory_config(),
        controller=_build_pd_controller_config(),
        telemetry=_build_pd_telemetry_config(),
        metadata=ScenarioMetadata(
            name=PD_VALIDATION_SCENARIO_NAME,
            description="Minimum validation scenario for the official PD expert baseline.",
            seed=seed,
            tags=PD_VALIDATION_SCENARIO_TAGS,
        ),
    )


def _step_durations(history: SimulationHistory) -> list[float]:
    durations: list[float] = []
    previous_time = history.initial_state.time_s
    for step in history.steps:
        duration = step.time_s - previous_time
        durations.append(duration)
        previous_time = step.time_s
    return durations


@dataclass(frozen=True, slots=True)
class PDValidationCriteria:
    max_position_rmse_m: float = 0.1
    max_final_position_error_m: float = 0.12
    max_velocity_rmse_m_s: float = 0.2
    max_final_velocity_error_m_s: float = 0.2
    max_yaw_rmse_rad: float = 0.01
    max_collective_thrust_fraction: float = 0.8
    max_body_torque_fraction: tuple[float, float, float] = (0.8, 0.8, 0.8)
    max_saturated_sample_fraction: float = 0.0
    max_consecutive_saturated_samples: int = 0
    expected_duration_s: float = PD_VALIDATION_DURATION_S
    expected_sample_count: int = 25
    expected_sample_dt_s: float = PD_VALIDATION_TELEMETRY_DT_S
    require_full_detail_level: bool = True

    def __post_init__(self) -> None:
        torque_fraction = tuple(float(value) for value in self.max_body_torque_fraction)
        if len(torque_fraction) != 3:
            raise ValueError("max_body_torque_fraction must contain exactly 3 values")
        object.__setattr__(self, "max_body_torque_fraction", torque_fraction)


@dataclass(frozen=True, slots=True)
class PDTemporalSummary:
    expected_duration_s: float
    observed_duration_s: float
    expected_sample_count: int
    observed_sample_count: int
    expected_sample_dt_s: float
    observed_sample_dt_s: float
    max_sample_dt_error_s: float
    monotonic_time: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PDSaturationSummary:
    collective_thrust_fraction_max: float
    body_torque_fraction_max: tuple[float, float, float]
    saturated_sample_count: int
    saturated_sample_fraction: float
    max_consecutive_saturated_samples: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PDValidationResult:
    gate_id: str
    passed: bool
    failures: tuple[str, ...]
    criteria: PDValidationCriteria
    metrics: TrackingMetrics
    temporal: PDTemporalSummary
    saturation: PDSaturationSummary
    scenario_name: str
    scenario_seed: int | None
    baseline_profile_id: str
    controller_kind: str
    controller_source: str
    trajectory_kind: str
    telemetry_detail_level: str
    telemetry_tracking_state_source: str
    telemetry_record_scenario_metadata: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "failures": list(self.failures),
            "criteria": asdict(self.criteria),
            "metrics": self.metrics.to_dict(),
            "temporal": self.temporal.to_dict(),
            "saturation": self.saturation.to_dict(),
            "scenario": {
                "name": self.scenario_name,
                "seed": self.scenario_seed,
                "baseline_profile_id": self.baseline_profile_id,
                "controller_kind": self.controller_kind,
                "controller_source": self.controller_source,
                "trajectory_kind": self.trajectory_kind,
            },
            "telemetry": {
                "detail_level": self.telemetry_detail_level,
                "tracking_state_source": self.telemetry_tracking_state_source,
                "record_scenario_metadata": self.telemetry_record_scenario_metadata,
            },
        }


@dataclass(frozen=True, slots=True)
class PDValidationArtifactBundle:
    output_dir: Path
    scenario_path: Path
    telemetry_path: Path
    report_path: Path
    manifest_path: Path
    summary_path: Path
    result: PDValidationResult

    def to_dict(self) -> dict[str, object]:
        return {
            "output_dir": str(self.output_dir),
            "scenario_path": str(self.scenario_path),
            "telemetry_path": str(self.telemetry_path),
            "report_path": str(self.report_path),
            "manifest_path": str(self.manifest_path),
            "summary_path": str(self.summary_path),
            "result": self.result.to_dict(),
        }


def validate_pd_validation_scenario(scenario: SimulationScenario) -> tuple[str, ...]:
    failures: list[str] = []
    if scenario.vehicle != build_baseline_vehicle_profile():
        failures.append("scenario.vehicle must match the official generic-drone baseline profile")
    if scenario.initial_state != PD_VALIDATION_INITIAL_STATE:
        failures.append("scenario.initial_state must match the validation starting state")
    if scenario.time != ScenarioTimeConfig(
        duration_s=PD_VALIDATION_DURATION_S,
        physics_dt_s=PD_VALIDATION_PHYSICS_DT_S,
        control_dt_s=PD_VALIDATION_CONTROL_DT_S,
        telemetry_dt_s=PD_VALIDATION_TELEMETRY_DT_S,
    ):
        failures.append("scenario.time must match the minimum PD validation cadence")
    if scenario.trajectory != _build_pd_trajectory_config():
        failures.append("scenario.trajectory must match the official minimum validation trajectory")
    if scenario.controller != _build_pd_controller_config():
        failures.append("scenario.controller must match the official PD baseline controller")
    if scenario.telemetry != _build_pd_telemetry_config():
        failures.append("scenario.telemetry must keep full-detail, reusable telemetry")
    if scenario.metadata.name != PD_VALIDATION_SCENARIO_NAME:
        failures.append("scenario.metadata.name must identify the PD validation baseline")
    if tuple(scenario.metadata.tags) != PD_VALIDATION_SCENARIO_TAGS:
        failures.append("scenario.metadata.tags must identify the PD validation baseline")
    return tuple(failures)


def _saturation_summary(history: SimulationHistory) -> PDSaturationSummary:
    vehicle = build_baseline_vehicle_profile()
    if not history.steps:
        return PDSaturationSummary(
            collective_thrust_fraction_max=0.0,
            body_torque_fraction_max=(0.0, 0.0, 0.0),
            saturated_sample_count=0,
            saturated_sample_fraction=0.0,
            max_consecutive_saturated_samples=0,
        )

    max_collective_thrust_fraction = 0.0
    max_body_torque_fraction = [0.0, 0.0, 0.0]
    saturated_sample_count = 0
    max_consecutive_saturated_samples = 0
    current_consecutive_saturated_samples = 0

    for step in history.steps:
        collective_thrust_fraction = step.command.collective_thrust_newton / vehicle.max_collective_thrust_newton
        body_torque_fractions = tuple(
            abs(step.command.body_torque_nm[index]) / abs(vehicle.max_body_torque_nm[index])
            if vehicle.max_body_torque_nm[index] != 0.0
            else 0.0
            for index in range(3)
        )
        max_collective_thrust_fraction = max(max_collective_thrust_fraction, collective_thrust_fraction)
        for index, fraction in enumerate(body_torque_fractions):
            max_body_torque_fraction[index] = max(max_body_torque_fraction[index], fraction)
        saturated = collective_thrust_fraction >= PD_VALIDATION_SATURATION_THRESHOLD or any(
            fraction >= PD_VALIDATION_SATURATION_THRESHOLD for fraction in body_torque_fractions
        )
        if saturated:
            saturated_sample_count += 1
            current_consecutive_saturated_samples += 1
            max_consecutive_saturated_samples = max(max_consecutive_saturated_samples, current_consecutive_saturated_samples)
        else:
            current_consecutive_saturated_samples = 0

    return PDSaturationSummary(
        collective_thrust_fraction_max=max_collective_thrust_fraction,
        body_torque_fraction_max=tuple(max_body_torque_fraction),
        saturated_sample_count=saturated_sample_count,
        saturated_sample_fraction=saturated_sample_count / len(history.steps),
        max_consecutive_saturated_samples=max_consecutive_saturated_samples,
    )


def _temporal_summary(history: SimulationHistory, criteria: PDValidationCriteria) -> PDTemporalSummary:
    durations = _step_durations(history)
    observed_sample_count = len(history.steps)
    observed_duration_s = history.final_time_s - history.initial_state.time_s
    max_sample_dt_error_s = 0.0
    observed_sample_dt_s = criteria.expected_sample_dt_s
    if durations:
        observed_sample_dt_s = sum(durations) / len(durations)
        max_sample_dt_error_s = max(abs(duration - criteria.expected_sample_dt_s) for duration in durations)
    monotonic_time = all(duration > 0.0 for duration in durations)
    return PDTemporalSummary(
        expected_duration_s=criteria.expected_duration_s,
        observed_duration_s=observed_duration_s,
        expected_sample_count=criteria.expected_sample_count,
        observed_sample_count=observed_sample_count,
        expected_sample_dt_s=criteria.expected_sample_dt_s,
        observed_sample_dt_s=observed_sample_dt_s,
        max_sample_dt_error_s=max_sample_dt_error_s,
        monotonic_time=monotonic_time,
    )


def _evaluate_failures(
    *,
    scenario: SimulationScenario,
    history: SimulationHistory,
    expected_controller,
    criteria: PDValidationCriteria,
    metrics: TrackingMetrics,
    temporal: PDTemporalSummary,
    saturation: PDSaturationSummary,
) -> tuple[str, ...]:
    failures: list[str] = []
    if not temporal.monotonic_time:
        failures.append("telemetry samples must be strictly increasing in time")
    if not isclose(temporal.observed_duration_s, criteria.expected_duration_s, rel_tol=1e-9, abs_tol=1e-9):
        failures.append("observed duration must match the validation scenario duration")
    if temporal.observed_sample_count != criteria.expected_sample_count:
        failures.append("observed sample count must match the configured telemetry cadence")
    if not isclose(temporal.observed_sample_dt_s, criteria.expected_sample_dt_s, rel_tol=1e-9, abs_tol=1e-9):
        failures.append("observed telemetry cadence must match the configured sample dt")
    if temporal.max_sample_dt_error_s > 1e-9:
        failures.append("telemetry cadence must remain numerically stable")
    if metrics.position_rmse_m > criteria.max_position_rmse_m:
        failures.append("position RMSE exceeds the accepted PD validation threshold")
    if metrics.final_position_error_m > criteria.max_final_position_error_m:
        failures.append("final position error exceeds the accepted PD validation threshold")
    if metrics.velocity_rmse_m_s > criteria.max_velocity_rmse_m_s:
        failures.append("velocity RMSE exceeds the accepted PD validation threshold")
    if metrics.final_velocity_error_m_s > criteria.max_final_velocity_error_m_s:
        failures.append("final velocity error exceeds the accepted PD validation threshold")
    if metrics.yaw_rmse_rad > criteria.max_yaw_rmse_rad:
        failures.append("yaw RMSE exceeds the accepted PD validation threshold")
    if saturation.collective_thrust_fraction_max > criteria.max_collective_thrust_fraction:
        failures.append("collective thrust saturation exceeds the accepted PD validation threshold")
    if any(
        fraction > limit
        for fraction, limit in zip(saturation.body_torque_fraction_max, criteria.max_body_torque_fraction)
    ):
        failures.append("body torque saturation exceeds the accepted PD validation threshold")
    if saturation.saturated_sample_fraction > criteria.max_saturated_sample_fraction:
        failures.append("saturated samples exceed the accepted PD validation threshold")
    if saturation.max_consecutive_saturated_samples > criteria.max_consecutive_saturated_samples:
        failures.append("sustained saturation exceeds the accepted PD validation threshold")
    if criteria.require_full_detail_level and scenario.telemetry.detail_level != PD_VALIDATION_DETAIL_LEVEL:
        failures.append("validation telemetry must be persisted at full detail")
    if history.controller_metadata.get("kind") != expected_controller.kind:
        failures.append("telemetry must preserve the controller kind")
    if history.controller_metadata.get("source") != expected_controller.source:
        failures.append("telemetry must preserve the controller source")
    if history.telemetry_metadata.get("tracking_state_source") != "true_state":
        failures.append("telemetry must use true_state as the tracking state source")
    return tuple(failures)


def evaluate_pd_validation(
    history: SimulationHistory,
    *,
    scenario: SimulationScenario,
    criteria: PDValidationCriteria | None = None,
) -> PDValidationResult:
    criteria = PDValidationCriteria() if criteria is None else criteria
    structural_failures = validate_pd_validation_scenario(scenario)
    expected_controller = scenario.build_controller()
    metrics = compute_tracking_metrics(history)
    saturation = _saturation_summary(history)
    temporal = _temporal_summary(history, criteria)
    failures = list(structural_failures)
    failures.extend(
        _evaluate_failures(
            scenario=scenario,
            history=history,
            expected_controller=expected_controller,
            criteria=criteria,
            metrics=metrics,
            temporal=temporal,
            saturation=saturation,
        )
    )
    return PDValidationResult(
        gate_id=PD_VALIDATION_GATE_ID,
        passed=not failures,
        failures=tuple(failures),
        criteria=criteria,
        metrics=metrics,
        temporal=temporal,
        saturation=saturation,
        scenario_name=scenario.metadata.name,
        scenario_seed=scenario.metadata.seed,
        baseline_profile_id=str(scenario.trajectory.parameters.get("baseline_profile_id", BASELINE_PROFILE_ID)),
        controller_kind=expected_controller.kind,
        controller_source=expected_controller.source,
        trajectory_kind=scenario.trajectory.kind,
        telemetry_detail_level=scenario.telemetry.detail_level,
        telemetry_tracking_state_source=str(history.telemetry_metadata.get("tracking_state_source", "unknown")),
        telemetry_record_scenario_metadata=bool(history.telemetry_metadata.get("record_scenario_metadata", False)),
    )


def _resolve_output_dir(
    *,
    workspace: str | Path,
    run_id: str | None,
    output_dir: str | Path | None,
) -> tuple[Path, str, Path]:
    if output_dir is not None:
        resolved_output_dir = Path(output_dir)
        resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _utc_timestamp().replace(":", "").replace("-", "").replace("Z", "")
        return resolved_output_dir, resolved_run_id, resolved_output_dir.parent
    resolved_workspace = Path(workspace)
    resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _utc_timestamp().replace(":", "").replace("-", "").replace("Z", "")
    return resolved_workspace / resolved_run_id / "validation" / "pd", resolved_run_id, resolved_workspace


def _clear_output_dir(output_dir: Path) -> None:
    for filename in PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES.values():
        file_path = output_dir / filename
        if file_path.exists():
            file_path.unlink()


def _build_summary_markdown(result: PDValidationResult, bundle: PDValidationArtifactBundle) -> str:
    lines = [
        "# PD Validation Gate",
        "",
        f"- `gate_id`: `{result.gate_id}`",
        f"- `passed`: `{result.passed}`",
        f"- `scenario_name`: `{result.scenario_name}`",
        f"- `scenario_seed`: `{result.scenario_seed}`",
        f"- `baseline_profile_id`: `{result.baseline_profile_id}`",
        f"- `controller_kind`: `{result.controller_kind}`",
        f"- `trajectory_kind`: `{result.trajectory_kind}`",
        f"- `telemetry_detail_level`: `{result.telemetry_detail_level}`",
        f"- `telemetry_tracking_state_source`: `{result.telemetry_tracking_state_source}`",
        "",
        "## Criteria And Observations",
        "",
        "| Criterion | Limit | Observed | Status |",
        "| --- | ---: | ---: | --- |",
        f"| position_rmse_m | {result.criteria.max_position_rmse_m} | {result.metrics.position_rmse_m:.6f} | {'pass' if result.metrics.position_rmse_m <= result.criteria.max_position_rmse_m else 'fail'} |",
        f"| final_position_error_m | {result.criteria.max_final_position_error_m} | {result.metrics.final_position_error_m:.6f} | {'pass' if result.metrics.final_position_error_m <= result.criteria.max_final_position_error_m else 'fail'} |",
        f"| velocity_rmse_m_s | {result.criteria.max_velocity_rmse_m_s} | {result.metrics.velocity_rmse_m_s:.6f} | {'pass' if result.metrics.velocity_rmse_m_s <= result.criteria.max_velocity_rmse_m_s else 'fail'} |",
        f"| final_velocity_error_m_s | {result.criteria.max_final_velocity_error_m_s} | {result.metrics.final_velocity_error_m_s:.6f} | {'pass' if result.metrics.final_velocity_error_m_s <= result.criteria.max_final_velocity_error_m_s else 'fail'} |",
        f"| yaw_rmse_rad | {result.criteria.max_yaw_rmse_rad} | {result.metrics.yaw_rmse_rad:.6f} | {'pass' if result.metrics.yaw_rmse_rad <= result.criteria.max_yaw_rmse_rad else 'fail'} |",
        f"| collective_thrust_fraction_max | {result.criteria.max_collective_thrust_fraction} | {result.saturation.collective_thrust_fraction_max:.6f} | {'pass' if result.saturation.collective_thrust_fraction_max <= result.criteria.max_collective_thrust_fraction else 'fail'} |",
        f"| saturated_sample_fraction | {result.criteria.max_saturated_sample_fraction} | {result.saturation.saturated_sample_fraction:.6f} | {'pass' if result.saturation.saturated_sample_fraction <= result.criteria.max_saturated_sample_fraction else 'fail'} |",
        f"| max_consecutive_saturated_samples | {result.criteria.max_consecutive_saturated_samples} | {result.saturation.max_consecutive_saturated_samples} | {'pass' if result.saturation.max_consecutive_saturated_samples <= result.criteria.max_consecutive_saturated_samples else 'fail'} |",
        "",
        "## Artifacts",
        "",
        f"- `scenario`: `{bundle.scenario_path}`",
        f"- `telemetry`: `{bundle.telemetry_path}`",
        f"- `report`: `{bundle.report_path}`",
        f"- `manifest`: `{bundle.manifest_path}`",
        "",
    ]
    if result.failures:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {failure}" for failure in result.failures)
        lines.append("")
    return "\n".join(lines)


def _build_manifest_payload(*, result: PDValidationResult, bundle: PDValidationArtifactBundle, command: str, argv: Sequence[str], run_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "artifact_kind": "pd_validation",
        "stage": "validation",
        "gate_id": result.gate_id,
        "run_id": run_id,
        "created_at": _utc_timestamp(),
        "command": command,
        "argv": list(argv),
        "output_path": str(bundle.output_dir),
        "scenario_path": str(bundle.scenario_path),
        "telemetry_path": str(bundle.telemetry_path),
        "report_path": str(bundle.report_path),
        "summary_path": str(bundle.summary_path),
        "passed": result.passed,
        "failure_count": len(result.failures),
        "failures": list(result.failures),
        "scenario": {
            "name": result.scenario_name,
            "seed": result.scenario_seed,
            "baseline_profile_id": result.baseline_profile_id,
            "controller_kind": result.controller_kind,
            "controller_source": result.controller_source,
            "trajectory_kind": result.trajectory_kind,
        },
        "telemetry": {
            "detail_level": result.telemetry_detail_level,
            "tracking_state_source": result.telemetry_tracking_state_source,
            "record_scenario_metadata": result.telemetry_record_scenario_metadata,
        },
        "criteria": asdict(result.criteria),
        "metrics": result.metrics.to_dict(),
        "temporal": result.temporal.to_dict(),
        "saturation": result.saturation.to_dict(),
    }


def persist_pd_validation_artifacts(
    history: SimulationHistory,
    *,
    scenario: SimulationScenario,
    result: PDValidationResult,
    workspace: str | Path = Path("artifacts/validation"),
    run_id: str | None = None,
    output_dir: str | Path | None = None,
    overwrite: bool = False,
    command: str = "multirotor-sim validation pd",
    argv: Sequence[str] = (),
) -> PDValidationArtifactBundle:
    resolved_output_dir, resolved_run_id, _resolved_workspace = _resolve_output_dir(
        workspace=workspace,
        run_id=run_id,
        output_dir=output_dir,
    )
    resolved_output_dir = resolved_output_dir.resolve()
    if resolved_output_dir.exists():
        if not overwrite:
            raise ValueError(f"output directory already exists: {resolved_output_dir}")
        _clear_output_dir(resolved_output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    bundle = PDValidationArtifactBundle(
        output_dir=resolved_output_dir,
        scenario_path=resolved_output_dir / PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES["scenario"],
        telemetry_path=resolved_output_dir / PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES["telemetry"],
        report_path=resolved_output_dir / PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES["report"],
        manifest_path=resolved_output_dir / PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES["manifest"],
        summary_path=resolved_output_dir / PD_VALIDATION_DEFAULT_OUTPUT_FILENAMES["summary"],
        result=result,
    )

    save_simulation_scenario(scenario, bundle.scenario_path)
    export_history_to_json(
        history,
        bundle.telemetry_path,
        detail_level=scenario.telemetry.detail_level,
        sample_dt_s=scenario.telemetry.sample_dt_s,
    )
    bundle.report_path.write_text(_json_dump(result.to_dict()) + "\n", encoding="utf-8")
    manifest_payload = _build_manifest_payload(result=result, bundle=bundle, command=command, argv=argv, run_id=resolved_run_id)
    bundle.manifest_path.write_text(_json_dump(manifest_payload) + "\n", encoding="utf-8")
    bundle.summary_path.write_text(_build_summary_markdown(result, bundle) + "\n", encoding="utf-8")
    return bundle


def run_pd_validation(
    *,
    seed: int | None = None,
    workspace: str | Path = Path("artifacts/validation"),
    run_id: str | None = None,
    output_dir: str | Path | None = None,
    overwrite: bool = False,
    command: str = "multirotor-sim validation pd",
    argv: Sequence[str] = (),
    criteria: PDValidationCriteria | None = None,
) -> PDValidationArtifactBundle:
    scenario = build_pd_validation_scenario(seed=seed)
    structural_failures = validate_pd_validation_scenario(scenario)
    if structural_failures:
        raise ValueError("; ".join(structural_failures))
    history = SimulationRunner().run(scenario)
    result = evaluate_pd_validation(history, scenario=scenario, criteria=criteria)
    return persist_pd_validation_artifacts(
        history,
        scenario=scenario,
        result=result,
        workspace=workspace,
        run_id=run_id,
        output_dir=output_dir,
        overwrite=overwrite,
        command=command,
        argv=argv,
    )
