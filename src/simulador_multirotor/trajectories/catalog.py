"""Trajectory registry and scenario integration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any, Mapping

from ..core.contracts import VehicleState
from .contract import TrajectoryContract
from .native import (
    CircleTrajectory,
    HoldTrajectory,
    LissajousTrajectory,
    ParametricCurveTrajectory,
    SpiralTrajectory,
    StraightTrajectory,
)


def _parameters(config: object) -> Mapping[str, object]:
    value = getattr(config, "parameters", {})
    if isinstance(value, Mapping):
        return value
    return dict(value)


def _duration(config: object, default: float) -> float:
    value = getattr(config, "valid_until_s", None)
    if value is None:
        return default
    return float(value)


def _initial_position(initial_state: VehicleState | None) -> tuple[float, float, float]:
    if initial_state is None:
        return (0.0, 0.0, 0.0)
    return initial_state.position_m


def _coerce_vector(value: object | None, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise ValueError("trajectory parameter must contain exactly 3 values")


def _build_hold_trajectory(config: object, initial_state: VehicleState | None) -> TrajectoryContract:
    parameters = _parameters(config)
    position = _coerce_vector(
        getattr(config, "target_position_m", None) or parameters.get("target_position_m"),
        default=_initial_position(initial_state) if initial_state is not None else (0.0, 0.0, 1.0),
    )
    velocity = _coerce_vector(
        getattr(config, "target_velocity_m_s", None) or parameters.get("target_velocity_m_s"),
        default=(0.0, 0.0, 0.0),
    )
    yaw = getattr(config, "target_yaw_rad", None)
    if yaw is None:
        yaw = parameters.get("target_yaw_rad", 0.0)
    acceleration = getattr(config, "target_acceleration_m_s2", None)
    if acceleration is None:
        acceleration = parameters.get("target_acceleration_m_s2")
    return HoldTrajectory(
        kind=getattr(config, "kind", "hover"),
        duration_s=_duration(config, 1.0),
        source=getattr(config, "source", "native"),
        parameters=parameters,
        position_m=position,
        velocity_m_s=velocity,
        yaw_rad=float(yaw),
        acceleration_m_s2=_coerce_vector(acceleration, default=(0.0, 0.0, 0.0)) if acceleration is not None else None,
    )


def _build_straight_trajectory(config: object, initial_state: VehicleState | None) -> TrajectoryContract:
    parameters = _parameters(config)
    start_position = _coerce_vector(parameters.get("start_position_m"), default=_initial_position(initial_state))
    velocity = _coerce_vector(parameters.get("velocity_m_s"), default=(1.0, 0.0, 0.0))
    yaw = parameters.get("yaw_rad")
    return StraightTrajectory(
        kind=getattr(config, "kind", "line"),
        duration_s=_duration(config, 1.0),
        source=getattr(config, "source", "native"),
        parameters=parameters,
        start_position_m=start_position,
        velocity_m_s=velocity,
        yaw_rad=float(yaw) if yaw is not None else None,
    )


def _build_circle_trajectory(config: object, initial_state: VehicleState | None) -> TrajectoryContract:
    parameters = _parameters(config)
    center = _coerce_vector(parameters.get("center_m"), default=_initial_position(initial_state))
    radius = float(parameters.get("radius_m", 1.0))
    angular_speed = float(parameters.get("angular_speed_rad_s", 1.0))
    phase = float(parameters.get("start_phase_rad", 0.0))
    return CircleTrajectory(
        kind=getattr(config, "kind", "circle"),
        duration_s=_duration(config, 1.0),
        source=getattr(config, "source", "native"),
        parameters=parameters,
        center_m=center,
        radius_m=radius,
        angular_speed_rad_s=angular_speed,
        start_phase_rad=phase,
    )


def _build_spiral_trajectory(config: object, initial_state: VehicleState | None) -> TrajectoryContract:
    parameters = _parameters(config)
    center = _coerce_vector(parameters.get("center_m"), default=_initial_position(initial_state))
    return SpiralTrajectory(
        kind=getattr(config, "kind", "spiral"),
        duration_s=_duration(config, 1.0),
        source=getattr(config, "source", "native"),
        parameters=parameters,
        center_m=center,
        initial_radius_m=float(parameters.get("initial_radius_m", 0.25)),
        radial_rate_m_s=float(parameters.get("radial_rate_m_s", 0.1)),
        angular_speed_rad_s=float(parameters.get("angular_speed_rad_s", 1.0)),
        vertical_speed_m_s=float(parameters.get("vertical_speed_m_s", 0.1)),
        start_phase_rad=float(parameters.get("start_phase_rad", 0.0)),
    )


def _build_parametric_curve_trajectory(config: object, initial_state: VehicleState | None) -> TrajectoryContract:
    parameters = _parameters(config)
    origin = _coerce_vector(parameters.get("origin_m"), default=_initial_position(initial_state))
    return ParametricCurveTrajectory(
        kind=getattr(config, "kind", "parametric"),
        duration_s=_duration(config, 1.0),
        source=getattr(config, "source", "native"),
        parameters=parameters,
        origin_m=origin,
        forward_speed_m_s=float(parameters.get("forward_speed_m_s", 1.0)),
        lateral_amplitude_m=float(parameters.get("lateral_amplitude_m", 0.5)),
        lateral_frequency_rad_s=float(parameters.get("lateral_frequency_rad_s", 1.0)),
        vertical_amplitude_m=float(parameters.get("vertical_amplitude_m", 0.0)),
        vertical_frequency_rad_s=float(parameters.get("vertical_frequency_rad_s", 1.0)),
        lateral_phase_rad=float(parameters.get("lateral_phase_rad", 0.0)),
        vertical_phase_rad=float(parameters.get("vertical_phase_rad", 0.0)),
    )


def _build_lissajous_trajectory(config: object, initial_state: VehicleState | None) -> TrajectoryContract:
    parameters = _parameters(config)
    center = _coerce_vector(parameters.get("center_m"), default=_initial_position(initial_state))
    return LissajousTrajectory(
        kind=getattr(config, "kind", "lissajous"),
        duration_s=_duration(config, 1.0),
        source=getattr(config, "source", "native"),
        parameters=parameters,
        center_m=center,
        amplitude_m=_coerce_vector(parameters.get("amplitude_m"), default=(1.0, 1.0, 0.5)),
        frequency_rad_s=_coerce_vector(parameters.get("frequency_rad_s"), default=(1.0, 2.0, 3.0)),
        phase_rad=_coerce_vector(parameters.get("phase_rad"), default=(0.0, pi / 2.0, 0.0)),
    )


TRAJECTORY_FACTORIES: dict[str, Any] = {
    "hover": _build_hold_trajectory,
    "static": _build_hold_trajectory,
    "line": _build_straight_trajectory,
    "circle": _build_circle_trajectory,
    "spiral": _build_spiral_trajectory,
    "parametric": _build_parametric_curve_trajectory,
    "parametric-curve": _build_parametric_curve_trajectory,
    "curve": _build_parametric_curve_trajectory,
    "lissajous": _build_lissajous_trajectory,
}


def build_trajectory_from_config(config: object, *, initial_state: VehicleState | None = None) -> TrajectoryContract:
    kind = str(getattr(config, "kind", "")).strip().lower()
    if not kind:
        raise ValueError("kind must be a non-empty string")
    try:
        factory = TRAJECTORY_FACTORIES[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported trajectory kind: {kind}") from exc
    trajectory = factory(config, initial_state)
    if not isinstance(trajectory, TrajectoryContract):
        raise TypeError("trajectory factory must return a trajectory contract")
    return trajectory


@dataclass(frozen=True, slots=True)
class TrajectorySelection:
    kind: str
    trajectory: TrajectoryContract
