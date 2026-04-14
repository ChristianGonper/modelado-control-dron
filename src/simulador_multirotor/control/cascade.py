"""Minimal cascaded controller for the tracer bullet."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite, sqrt
from types import MappingProxyType
from typing import Mapping

from ..core.attitude import (
    normalize_quaternion,
    quaternion_error_vector,
    quaternion_from_thrust_direction_and_yaw,
    quaternion_shortest_error,
)
from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleIntent, VehicleObservation, VehicleState
from .contract import ControllerContract


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _coerce_gain(value: object, field_name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _coerce_vector(value: tuple[float, float, float] | list[float], field_name: str) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return (float(value[0]), float(value[1]), float(value[2]))


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class ControlTarget:
    desired_acceleration_m_s2: tuple[float, float, float]
    desired_yaw_rad: float
    desired_collective_thrust_newton: float
    desired_attitude_wxyz: tuple[float, float, float, float]
    desired_body_rate_rad_s: tuple[float, float, float]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "desired_acceleration_m_s2",
            _coerce_vector(self.desired_acceleration_m_s2, "desired_acceleration_m_s2"),
        )
        object.__setattr__(self, "desired_yaw_rad", _coerce_gain(self.desired_yaw_rad, "desired_yaw_rad"))
        object.__setattr__(
            self,
            "desired_collective_thrust_newton",
            _coerce_gain(self.desired_collective_thrust_newton, "desired_collective_thrust_newton"),
        )
        object.__setattr__(
            self,
            "desired_attitude_wxyz",
            normalize_quaternion(self.desired_attitude_wxyz),
        )
        object.__setattr__(
            self,
            "desired_body_rate_rad_s",
            _coerce_vector(self.desired_body_rate_rad_s, "desired_body_rate_rad_s"),
        )


@dataclass(frozen=True, slots=True)
class PositionLoopController:
    mass_kg: float = 1.0
    gravity_m_s2: float = 9.81
    kp_position: tuple[float, float, float] = (2.0, 2.0, 4.0)
    kd_velocity: tuple[float, float, float] = (1.2, 1.2, 2.5)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mass_kg", _coerce_gain(self.mass_kg, "mass_kg"))
        object.__setattr__(self, "gravity_m_s2", _coerce_gain(self.gravity_m_s2, "gravity_m_s2"))
        object.__setattr__(self, "kp_position", _coerce_vector(self.kp_position, "kp_position"))
        object.__setattr__(self, "kd_velocity", _coerce_vector(self.kd_velocity, "kd_velocity"))

    def compute_target(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> ControlTarget:
        state = observation.state
        position_error = tuple(
            reference_coordinate - state_coordinate
            for reference_coordinate, state_coordinate in zip(reference.position_m, state.position_m)
        )
        velocity_error = tuple(
            reference_velocity - state_velocity
            for reference_velocity, state_velocity in zip(reference.velocity_m_s, state.linear_velocity_m_s)
        )
        desired_acceleration = tuple(
            kp * error + kd * vel_error
            for kp, error, kd, vel_error in zip(self.kp_position, position_error, self.kd_velocity, velocity_error)
        )
        if reference.acceleration_m_s2 is not None:
            desired_acceleration = tuple(
                acceleration + feedforward
                for acceleration, feedforward in zip(desired_acceleration, reference.acceleration_m_s2)
            )
        desired_force_world = tuple(
            self.mass_kg * component for component in (
                desired_acceleration[0],
                desired_acceleration[1],
                desired_acceleration[2] + self.gravity_m_s2,
            )
        )
        desired_thrust = sqrt(sum(component * component for component in desired_force_world))
        if desired_thrust <= 1e-9:
            desired_force_world = (0.0, 0.0, self.mass_kg * self.gravity_m_s2)
            desired_thrust = self.mass_kg * self.gravity_m_s2
        desired_body_z_world = tuple(component / desired_thrust for component in desired_force_world)
        desired_attitude = quaternion_from_thrust_direction_and_yaw(desired_body_z_world, reference.yaw_rad)
        return ControlTarget(
            desired_acceleration_m_s2=desired_acceleration,
            desired_yaw_rad=reference.yaw_rad,
            desired_collective_thrust_newton=desired_thrust,
            desired_attitude_wxyz=desired_attitude,
            desired_body_rate_rad_s=(0.0, 0.0, 0.0),
        )


@dataclass(frozen=True, slots=True)
class AttitudeLoopController:
    mass_kg: float
    gravity_m_s2: float
    max_collective_thrust_newton: float
    max_body_torque_nm: tuple[float, float, float]
    kp_attitude: tuple[float, float, float] = (4.5, 4.5, 1.8)
    kd_body_rate: tuple[float, float, float] = (0.15, 0.15, 0.08)
    max_tilt_rad: float = 0.6

    def __post_init__(self) -> None:
        object.__setattr__(self, "mass_kg", _coerce_gain(self.mass_kg, "mass_kg"))
        object.__setattr__(self, "gravity_m_s2", _coerce_gain(self.gravity_m_s2, "gravity_m_s2"))
        object.__setattr__(
            self,
            "max_collective_thrust_newton",
            _coerce_gain(self.max_collective_thrust_newton, "max_collective_thrust_newton"),
        )
        object.__setattr__(self, "max_body_torque_nm", _coerce_vector(self.max_body_torque_nm, "max_body_torque_nm"))
        object.__setattr__(self, "kp_attitude", _coerce_vector(self.kp_attitude, "kp_attitude"))
        object.__setattr__(self, "kd_body_rate", _coerce_vector(self.kd_body_rate, "kd_body_rate"))
        object.__setattr__(self, "max_tilt_rad", _coerce_gain(self.max_tilt_rad, "max_tilt_rad"))

    def compute_command(self, state: VehicleState, target: ControlTarget) -> VehicleCommand:
        attitude_error = quaternion_error_vector(quaternion_shortest_error(target.desired_attitude_wxyz, state.orientation_wxyz))
        angular_velocity = state.angular_velocity_rad_s
        body_rate_error = tuple(
            desired_rate - current_rate
            for desired_rate, current_rate in zip(target.desired_body_rate_rad_s, angular_velocity)
        )
        torque_command = tuple(
            _clamp(
                kp * error + kd * rate,
                -limit,
                limit,
            )
            for kp, error, kd, rate, limit in zip(
                self.kp_attitude,
                attitude_error,
                self.kd_body_rate,
                body_rate_error,
                self.max_body_torque_nm,
            )
        )

        collective_thrust = _clamp(
            target.desired_collective_thrust_newton,
            0.0,
            self.max_collective_thrust_newton,
        )

        return VehicleCommand(
            intent=VehicleIntent(
                collective_thrust_newton=collective_thrust,
                body_torque_nm=torque_command,
            ),
        )


@dataclass(frozen=True, slots=True)
class CascadedController(ControllerContract):
    position_loop: PositionLoopController = field(default_factory=PositionLoopController)
    attitude_loop: AttitudeLoopController = field(
        default_factory=lambda: AttitudeLoopController(
            mass_kg=1.0,
            gravity_m_s2=9.81,
            max_collective_thrust_newton=20.0,
            max_body_torque_nm=(0.3, 0.3, 0.2),
        )
    )
    kind: str = "cascade"
    source: str = "pid"
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", str(self.kind).strip().lower() or "cascade")
        object.__setattr__(self, "source", str(self.source).strip().lower() or "pid")
        if not self.parameters:
            object.__setattr__(
                self,
                "parameters",
                {
                    "position_loop": asdict(self.position_loop),
                    "attitude_loop": asdict(self.attitude_loop),
                },
            )
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def compute_action(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        target = self.position_loop.compute_target(observation, reference)
        return self.attitude_loop.compute_command(observation.state, target)

    def update(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        """Backward-compatible alias used by the tracer bullet."""
        return self.compute_action(observation, reference)
