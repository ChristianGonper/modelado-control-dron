"""Tracking metrics derived from telemetry histories."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt

from ..telemetry import SimulationHistory


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _rms(values: list[float]) -> float:
    return sqrt(sum(value * value for value in values) / len(values))


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
    tracking_state_source: str
    position_rmse_m: float
    velocity_rmse_m_s: float
    yaw_rmse_rad: float
    mean_position_error_m: float
    mean_velocity_error_m_s: float
    mean_collective_thrust_newton: float
    thrust_integral_newton_s: float
    torque_integral_nm_s: tuple[float, float, float]
    torque_rms_nm: tuple[float, float, float]
    final_position_error_m: float
    final_velocity_error_m_s: float
    final_yaw_error_rad: float

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "duration_s": self.duration_s,
            "tracking_state_source": self.tracking_state_source,
            "position_rmse_m": self.position_rmse_m,
            "velocity_rmse_m_s": self.velocity_rmse_m_s,
            "yaw_rmse_rad": self.yaw_rmse_rad,
            "mean_position_error_m": self.mean_position_error_m,
            "mean_velocity_error_m_s": self.mean_velocity_error_m_s,
            "mean_collective_thrust_newton": self.mean_collective_thrust_newton,
            "thrust_integral_newton_s": self.thrust_integral_newton_s,
            "torque_integral_nm_s": self.torque_integral_nm_s,
            "torque_rms_nm": self.torque_rms_nm,
            "final_position_error_m": self.final_position_error_m,
            "final_velocity_error_m_s": self.final_velocity_error_m_s,
            "final_yaw_error_rad": self.final_yaw_error_rad,
        }


@dataclass(frozen=True, slots=True)
class MetricComparison:
    sample_count: int
    duration_s: float
    tracking_state_source: str
    position_rmse_delta_m: float
    velocity_rmse_delta_m_s: float
    yaw_rmse_delta_rad: float
    mean_collective_thrust_delta_newton: float
    thrust_integral_delta_newton_s: float
    torque_integral_delta_nm_s: tuple[float, float, float]
    torque_rms_delta_nm: tuple[float, float, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "duration_s": self.duration_s,
            "tracking_state_source": self.tracking_state_source,
            "position_rmse_delta_m": self.position_rmse_delta_m,
            "velocity_rmse_delta_m_s": self.velocity_rmse_delta_m_s,
            "yaw_rmse_delta_rad": self.yaw_rmse_delta_rad,
            "mean_collective_thrust_delta_newton": self.mean_collective_thrust_delta_newton,
            "thrust_integral_delta_newton_s": self.thrust_integral_delta_newton_s,
            "torque_integral_delta_nm_s": self.torque_integral_delta_nm_s,
            "torque_rms_delta_nm": self.torque_rms_delta_nm,
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

    thrust_integral = sum(thrust * dt for thrust, dt in zip(thrusts, durations))
    torque_integrals = tuple(
        sum(abs(step_torque[index]) * dt for step_torque, dt in zip(torques, durations))
        for index in range(3)
    )
    torque_rms = tuple(
        sqrt(sum(step_torque[index] * step_torque[index] for step_torque in torques) / len(torques))
        for index in range(3)
    )

    return TrackingMetrics(
        sample_count=len(history.steps),
        duration_s=history.final_time_s - history.initial_state.time_s,
        tracking_state_source="true_state",
        position_rmse_m=_rms(position_norms),
        velocity_rmse_m_s=_rms(velocity_norms),
        yaw_rmse_rad=_rms(yaw_errors),
        mean_position_error_m=_mean(position_norms),
        mean_velocity_error_m_s=_mean(velocity_norms),
        mean_collective_thrust_newton=_mean(thrusts),
        thrust_integral_newton_s=thrust_integral,
        torque_integral_nm_s=torque_integrals,
        torque_rms_nm=torque_rms,
        final_position_error_m=position_norms[-1],
        final_velocity_error_m_s=velocity_norms[-1],
        final_yaw_error_rad=abs(history.steps[-1].error.yaw_rad),
    )


def compare_tracking_metrics(baseline: TrackingMetrics, candidate: TrackingMetrics) -> MetricComparison:
    if baseline.sample_count != candidate.sample_count or not isclose(baseline.duration_s, candidate.duration_s, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("metrics can only be compared for homogeneous executions")
    if baseline.tracking_state_source != candidate.tracking_state_source:
        raise ValueError("metrics can only be compared when they use the same tracking state source")
    return MetricComparison(
        sample_count=baseline.sample_count,
        duration_s=baseline.duration_s,
        tracking_state_source=baseline.tracking_state_source,
        position_rmse_delta_m=candidate.position_rmse_m - baseline.position_rmse_m,
        velocity_rmse_delta_m_s=candidate.velocity_rmse_m_s - baseline.velocity_rmse_m_s,
        yaw_rmse_delta_rad=candidate.yaw_rmse_rad - baseline.yaw_rmse_rad,
        mean_collective_thrust_delta_newton=candidate.mean_collective_thrust_newton - baseline.mean_collective_thrust_newton,
        thrust_integral_delta_newton_s=candidate.thrust_integral_newton_s - baseline.thrust_integral_newton_s,
        torque_integral_delta_nm_s=tuple(
            candidate_value - baseline_value
            for candidate_value, baseline_value in zip(candidate.torque_integral_nm_s, baseline.torque_integral_nm_s)
        ),
        torque_rms_delta_nm=tuple(
            candidate_value - baseline_value
            for candidate_value, baseline_value in zip(candidate.torque_rms_nm, baseline.torque_rms_nm)
        ),
    )
