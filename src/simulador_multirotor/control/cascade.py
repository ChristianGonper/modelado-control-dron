"""Minimal cascaded controller for the tracer bullet."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, cos, isfinite, sin

from ..core.attitude import euler_from_quaternion
from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _wrap_angle(angle_rad: float) -> float:
    wrapped = (angle_rad + 3.141592653589793) % (2.0 * 3.141592653589793) - 3.141592653589793
    return wrapped


def _coerce_gain(value: object, field_name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _coerce_vector(value: tuple[float, float, float] | list[float], field_name: str) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return (float(value[0]), float(value[1]), float(value[2]))


@dataclass(frozen=True, slots=True)
class ControlTarget:
    desired_acceleration_m_s2: tuple[float, float, float]
    desired_yaw_rad: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "desired_acceleration_m_s2",
            _coerce_vector(self.desired_acceleration_m_s2, "desired_acceleration_m_s2"),
        )
        object.__setattr__(self, "desired_yaw_rad", _coerce_gain(self.desired_yaw_rad, "desired_yaw_rad"))


@dataclass(frozen=True, slots=True)
class PositionLoopController:
    kp_position: tuple[float, float, float] = (2.0, 2.0, 4.0)
    kd_velocity: tuple[float, float, float] = (1.2, 1.2, 2.5)

    def __post_init__(self) -> None:
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
        return ControlTarget(
            desired_acceleration_m_s2=desired_acceleration,
            desired_yaw_rad=reference.yaw_rad,
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
        desired_accel_world = target.desired_acceleration_m_s2
        desired_yaw = target.desired_yaw_rad
        current_roll, current_pitch, current_yaw = euler_from_quaternion(state.orientation_wxyz)

        cos_yaw = cos(desired_yaw)
        sin_yaw = sin(desired_yaw)
        ax_body = cos_yaw * desired_accel_world[0] + sin_yaw * desired_accel_world[1]
        ay_body = -sin_yaw * desired_accel_world[0] + cos_yaw * desired_accel_world[1]

        vertical = max(0.2, self.gravity_m_s2 + desired_accel_world[2])
        desired_pitch = _clamp(atan2(-ax_body, vertical), -self.max_tilt_rad, self.max_tilt_rad)
        desired_roll = _clamp(atan2(ay_body, vertical), -self.max_tilt_rad, self.max_tilt_rad)
        roll_error = _wrap_angle(desired_roll - current_roll)
        pitch_error = _wrap_angle(desired_pitch - current_pitch)
        yaw_error = _wrap_angle(desired_yaw - current_yaw)
        angular_velocity = state.angular_velocity_rad_s
        torque_command = tuple(
            _clamp(
                kp * error - kd * rate,
                -limit,
                limit,
            )
            for kp, error, kd, rate, limit in zip(
                self.kp_attitude,
                (roll_error, pitch_error, yaw_error),
                self.kd_body_rate,
                angular_velocity,
                self.max_body_torque_nm,
            )
        )

        desired_thrust = self.mass_kg * vertical
        thrust_denominator = max(0.25, cos(desired_roll) * cos(desired_pitch))
        collective_thrust = _clamp(
            desired_thrust / thrust_denominator,
            0.0,
            self.max_collective_thrust_newton,
        )

        return VehicleCommand(
            collective_thrust_newton=collective_thrust,
            body_torque_nm=torque_command,
        )


@dataclass(frozen=True, slots=True)
class CascadedController:
    position_loop: PositionLoopController = field(default_factory=PositionLoopController)
    attitude_loop: AttitudeLoopController = field(
        default_factory=lambda: AttitudeLoopController(
            mass_kg=1.0,
            gravity_m_s2=9.81,
            max_collective_thrust_newton=20.0,
            max_body_torque_nm=(0.3, 0.3, 0.2),
        )
    )

    def update(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        target = self.position_loop.compute_target(observation, reference)
        return self.attitude_loop.compute_command(observation.state, target)
