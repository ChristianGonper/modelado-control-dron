"""Tracking metrics derived from telemetry histories."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt

from ..telemetry import SimulationHistory


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _rms(values: list[float]) -> float:
    return sqrt(sum(value * value for value in values) / len(values))


def _integral(values: list[float], durations: list[float]) -> float:
    return sum(value * dt for value, dt in zip(values, durations))


def _integral_of_squares(values: list[float], durations: list[float]) -> float:
    return sum(value * value * dt for value, dt in zip(values, durations))


def _step_deltas(values: list[float]) -> list[float]:
    if len(values) < 2:
        return []
    return [abs(current - previous) for previous, current in zip(values, values[1:])]


def _vector_deltas(values: list[tuple[float, float, float]]) -> tuple[list[float], list[float], list[float]]:
    deltas_x: list[float] = []
    deltas_y: list[float] = []
    deltas_z: list[float] = []
    for previous, current in zip(values, values[1:]):
        deltas_x.append(abs(current[0] - previous[0]))
        deltas_y.append(abs(current[1] - previous[1]))
        deltas_z.append(abs(current[2] - previous[2]))
    return deltas_x, deltas_y, deltas_z


def _step_durations(history: SimulationHistory) -> list[float]:
    durations: list[float] = []
    previous_time = history.initial_state.time_s
    for step in history.steps:
        dt = step.time_s - previous_time
        if dt <= 0.0:
            raise ValueError("telemetry samples must be strictly increasing in time")
        durations.append(dt)
        previous_time = step.time_s
    return durations


@dataclass(frozen=True, slots=True)
class TrackingMetrics:
    sample_count: int
    duration_s: float
    control_observation_source: str
    tracking_state_source: str
    position_rmse_m: float
    position_mae_m: float
    position_iae_m_s: float
    position_ise_m2_s: float
    velocity_rmse_m_s: float
    velocity_mae_m_s: float
    velocity_iae_m_s: float
    velocity_ise_m2_s: float
    yaw_rmse_rad: float
    yaw_mae_rad: float
    yaw_iae_rad_s: float
    yaw_ise_rad2_s: float
    mean_position_error_m: float
    mean_velocity_error_m_s: float
    mean_collective_thrust_newton: float
    thrust_integral_newton_s: float
    collective_thrust_step_rms_newton: float
    collective_thrust_total_variation_newton: float
    torque_integral_nm_s: tuple[float, float, float]
    torque_rms_nm: tuple[float, float, float]
    torque_step_rms_nm: tuple[float, float, float]
    torque_total_variation_nm: tuple[float, float, float]
    final_position_error_m: float
    final_velocity_error_m_s: float
    final_yaw_error_rad: float

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "duration_s": self.duration_s,
            "control_observation_source": self.control_observation_source,
            "tracking_state_source": self.tracking_state_source,
            "position_rmse_m": self.position_rmse_m,
            "position_mae_m": self.position_mae_m,
            "position_iae_m_s": self.position_iae_m_s,
            "position_ise_m2_s": self.position_ise_m2_s,
            "velocity_rmse_m_s": self.velocity_rmse_m_s,
            "velocity_mae_m_s": self.velocity_mae_m_s,
            "velocity_iae_m_s": self.velocity_iae_m_s,
            "velocity_ise_m2_s": self.velocity_ise_m2_s,
            "yaw_rmse_rad": self.yaw_rmse_rad,
            "yaw_mae_rad": self.yaw_mae_rad,
            "yaw_iae_rad_s": self.yaw_iae_rad_s,
            "yaw_ise_rad2_s": self.yaw_ise_rad2_s,
            "mean_position_error_m": self.mean_position_error_m,
            "mean_velocity_error_m_s": self.mean_velocity_error_m_s,
            "mean_collective_thrust_newton": self.mean_collective_thrust_newton,
            "thrust_integral_newton_s": self.thrust_integral_newton_s,
            "collective_thrust_step_rms_newton": self.collective_thrust_step_rms_newton,
            "collective_thrust_total_variation_newton": self.collective_thrust_total_variation_newton,
            "torque_integral_nm_s": self.torque_integral_nm_s,
            "torque_rms_nm": self.torque_rms_nm,
            "torque_step_rms_nm": self.torque_step_rms_nm,
            "torque_total_variation_nm": self.torque_total_variation_nm,
            "final_position_error_m": self.final_position_error_m,
            "final_velocity_error_m_s": self.final_velocity_error_m_s,
            "final_yaw_error_rad": self.final_yaw_error_rad,
        }


@dataclass(frozen=True, slots=True)
class MetricComparison:
    sample_count: int
    duration_s: float
    control_observation_source: str
    tracking_state_source: str
    position_rmse_delta_m: float
    position_mae_delta_m: float
    position_iae_delta_m_s: float
    position_ise_delta_m2_s: float
    velocity_rmse_delta_m_s: float
    velocity_mae_delta_m_s: float
    velocity_iae_delta_m_s: float
    velocity_ise_delta_m2_s: float
    yaw_rmse_delta_rad: float
    yaw_mae_delta_rad: float
    yaw_iae_delta_rad_s: float
    yaw_ise_delta_rad2_s: float
    mean_collective_thrust_delta_newton: float
    thrust_integral_delta_newton_s: float
    collective_thrust_step_rms_delta_newton: float
    collective_thrust_total_variation_delta_newton: float
    torque_integral_delta_nm_s: tuple[float, float, float]
    torque_rms_delta_nm: tuple[float, float, float]
    torque_step_rms_delta_nm: tuple[float, float, float]
    torque_total_variation_delta_nm: tuple[float, float, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "duration_s": self.duration_s,
            "control_observation_source": self.control_observation_source,
            "tracking_state_source": self.tracking_state_source,
            "position_rmse_delta_m": self.position_rmse_delta_m,
            "position_mae_delta_m": self.position_mae_delta_m,
            "position_iae_delta_m_s": self.position_iae_delta_m_s,
            "position_ise_delta_m2_s": self.position_ise_delta_m2_s,
            "velocity_rmse_delta_m_s": self.velocity_rmse_delta_m_s,
            "velocity_mae_delta_m_s": self.velocity_mae_delta_m_s,
            "velocity_iae_delta_m_s": self.velocity_iae_delta_m_s,
            "velocity_ise_delta_m2_s": self.velocity_ise_delta_m2_s,
            "yaw_rmse_delta_rad": self.yaw_rmse_delta_rad,
            "yaw_mae_delta_rad": self.yaw_mae_delta_rad,
            "yaw_iae_delta_rad_s": self.yaw_iae_delta_rad_s,
            "yaw_ise_delta_rad2_s": self.yaw_ise_delta_rad2_s,
            "mean_collective_thrust_delta_newton": self.mean_collective_thrust_delta_newton,
            "thrust_integral_delta_newton_s": self.thrust_integral_delta_newton_s,
            "collective_thrust_step_rms_delta_newton": self.collective_thrust_step_rms_delta_newton,
            "collective_thrust_total_variation_delta_newton": self.collective_thrust_total_variation_delta_newton,
            "torque_integral_delta_nm_s": self.torque_integral_delta_nm_s,
            "torque_rms_delta_nm": self.torque_rms_delta_nm,
            "torque_step_rms_delta_nm": self.torque_step_rms_delta_nm,
            "torque_total_variation_delta_nm": self.torque_total_variation_delta_nm,
        }


def compute_tracking_metrics(history: SimulationHistory) -> TrackingMetrics:
    if not history.steps:
        raise ValueError("telemetry history must contain at least one sample")

    durations = _step_durations(history)
    position_norms = [step.position_error_norm_m for step in history.steps]
    velocity_norms = [step.velocity_error_norm_m_s for step in history.steps]
    yaw_errors = [abs(step.error.yaw_rad) for step in history.steps]
    thrusts = [step.command.collective_thrust_newton for step in history.steps]
    torques = [step.command.body_torque_nm for step in history.steps]
    thrust_deltas = _step_deltas(thrusts)
    torque_delta_x, torque_delta_y, torque_delta_z = _vector_deltas(torques)

    thrust_integral = _integral(thrusts, durations)
    torque_integrals = tuple(
        _integral([abs(step_torque[index]) for step_torque in torques], durations)
        for index in range(3)
    )
    torque_rms = tuple(
        sqrt(sum(step_torque[index] * step_torque[index] for step_torque in torques) / len(torques))
        for index in range(3)
    )
    torque_step_rms = tuple(
        sqrt(sum(delta * delta for delta in axis_deltas) / len(axis_deltas)) if axis_deltas else 0.0
        for axis_deltas in (torque_delta_x, torque_delta_y, torque_delta_z)
    )
    torque_total_variation = tuple(sum(axis_deltas) for axis_deltas in (torque_delta_x, torque_delta_y, torque_delta_z))

    return TrackingMetrics(
        sample_count=len(history.steps),
        duration_s=history.final_time_s - history.initial_state.time_s,
        control_observation_source="observed_state",
        tracking_state_source="true_state",
        position_rmse_m=_rms(position_norms),
        position_mae_m=_mean(position_norms),
        position_iae_m_s=_integral(position_norms, durations),
        position_ise_m2_s=_integral_of_squares(position_norms, durations),
        velocity_rmse_m_s=_rms(velocity_norms),
        velocity_mae_m_s=_mean(velocity_norms),
        velocity_iae_m_s=_integral(velocity_norms, durations),
        velocity_ise_m2_s=_integral_of_squares(velocity_norms, durations),
        yaw_rmse_rad=_rms(yaw_errors),
        yaw_mae_rad=_mean(yaw_errors),
        yaw_iae_rad_s=_integral(yaw_errors, durations),
        yaw_ise_rad2_s=_integral_of_squares(yaw_errors, durations),
        mean_position_error_m=_mean(position_norms),
        mean_velocity_error_m_s=_mean(velocity_norms),
        mean_collective_thrust_newton=_mean(thrusts),
        thrust_integral_newton_s=thrust_integral,
        collective_thrust_step_rms_newton=_rms(thrust_deltas) if thrust_deltas else 0.0,
        collective_thrust_total_variation_newton=sum(thrust_deltas),
        torque_integral_nm_s=torque_integrals,
        torque_rms_nm=torque_rms,
        torque_step_rms_nm=torque_step_rms,
        torque_total_variation_nm=torque_total_variation,
        final_position_error_m=position_norms[-1],
        final_velocity_error_m_s=velocity_norms[-1],
        final_yaw_error_rad=abs(history.steps[-1].error.yaw_rad),
    )


def compare_tracking_metrics(baseline: TrackingMetrics, candidate: TrackingMetrics) -> MetricComparison:
    if baseline.sample_count != candidate.sample_count or not isclose(baseline.duration_s, candidate.duration_s, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("metrics can only be compared for homogeneous executions")
    if baseline.control_observation_source != candidate.control_observation_source:
        raise ValueError("metrics can only be compared when they use the same control observation source")
    if baseline.tracking_state_source != candidate.tracking_state_source:
        raise ValueError("metrics can only be compared when they use the same tracking state source")
    return MetricComparison(
        sample_count=baseline.sample_count,
        duration_s=baseline.duration_s,
        control_observation_source=baseline.control_observation_source,
        tracking_state_source=baseline.tracking_state_source,
        position_rmse_delta_m=candidate.position_rmse_m - baseline.position_rmse_m,
        position_mae_delta_m=candidate.position_mae_m - baseline.position_mae_m,
        position_iae_delta_m_s=candidate.position_iae_m_s - baseline.position_iae_m_s,
        position_ise_delta_m2_s=candidate.position_ise_m2_s - baseline.position_ise_m2_s,
        velocity_rmse_delta_m_s=candidate.velocity_rmse_m_s - baseline.velocity_rmse_m_s,
        velocity_mae_delta_m_s=candidate.velocity_mae_m_s - baseline.velocity_mae_m_s,
        velocity_iae_delta_m_s=candidate.velocity_iae_m_s - baseline.velocity_iae_m_s,
        velocity_ise_delta_m2_s=candidate.velocity_ise_m2_s - baseline.velocity_ise_m2_s,
        yaw_rmse_delta_rad=candidate.yaw_rmse_rad - baseline.yaw_rmse_rad,
        yaw_mae_delta_rad=candidate.yaw_mae_rad - baseline.yaw_mae_rad,
        yaw_iae_delta_rad_s=candidate.yaw_iae_rad_s - baseline.yaw_iae_rad_s,
        yaw_ise_delta_rad2_s=candidate.yaw_ise_rad2_s - baseline.yaw_ise_rad2_s,
        mean_collective_thrust_delta_newton=candidate.mean_collective_thrust_newton - baseline.mean_collective_thrust_newton,
        thrust_integral_delta_newton_s=candidate.thrust_integral_newton_s - baseline.thrust_integral_newton_s,
        collective_thrust_step_rms_delta_newton=candidate.collective_thrust_step_rms_newton - baseline.collective_thrust_step_rms_newton,
        collective_thrust_total_variation_delta_newton=candidate.collective_thrust_total_variation_newton - baseline.collective_thrust_total_variation_newton,
        torque_integral_delta_nm_s=tuple(
            candidate_value - baseline_value
            for candidate_value, baseline_value in zip(candidate.torque_integral_nm_s, baseline.torque_integral_nm_s)
        ),
        torque_rms_delta_nm=tuple(
            candidate_value - baseline_value
            for candidate_value, baseline_value in zip(candidate.torque_rms_nm, baseline.torque_rms_nm)
        ),
        torque_step_rms_delta_nm=tuple(
            candidate_value - baseline_value
            for candidate_value, baseline_value in zip(candidate.torque_step_rms_nm, baseline.torque_step_rms_nm)
        ),
        torque_total_variation_delta_nm=tuple(
            candidate_value - baseline_value
            for candidate_value, baseline_value in zip(candidate.torque_total_variation_nm, baseline.torque_total_variation_nm)
        ),
    )
