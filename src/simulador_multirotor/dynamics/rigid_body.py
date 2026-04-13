"""Minimal rigid-body 6DOF dynamics."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from ..core.attitude import normalize_quaternion, quaternion_multiply, rotate_vector_by_quaternion
from ..core.contracts import VehicleCommand, VehicleState


def _coerce_positive(value: object, field_name: str) -> float:
    number = float(value)
    if not isfinite(number) or number <= 0.0:
        raise ValueError(f"{field_name} must be a positive finite number")
    return number


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True, slots=True)
class RigidBodyParameters:
    mass_kg: float = 1.0
    gravity_m_s2: float = 9.81
    inertia_kg_m2: tuple[float, float, float] = (0.02, 0.02, 0.04)
    max_collective_thrust_newton: float = 20.0
    max_body_torque_nm: tuple[float, float, float] = (0.3, 0.3, 0.2)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mass_kg", _coerce_positive(self.mass_kg, "mass_kg"))
        object.__setattr__(self, "gravity_m_s2", _coerce_positive(self.gravity_m_s2, "gravity_m_s2"))
        inertia = tuple(_coerce_positive(component, "inertia_kg_m2") for component in self.inertia_kg_m2)
        object.__setattr__(self, "inertia_kg_m2", inertia)
        object.__setattr__(
            self,
            "max_collective_thrust_newton",
            _coerce_positive(self.max_collective_thrust_newton, "max_collective_thrust_newton"),
        )
        torque_limits = tuple(_coerce_positive(component, "max_body_torque_nm") for component in self.max_body_torque_nm)
        object.__setattr__(self, "max_body_torque_nm", torque_limits)


@dataclass(frozen=True, slots=True)
class RigidBody6DOFDynamics:
    parameters: RigidBodyParameters = field(default_factory=RigidBodyParameters)

    def step(self, state: VehicleState, command: VehicleCommand, dt_s: float) -> VehicleState:
        dt = float(dt_s)
        if not isfinite(dt) or dt <= 0.0:
            raise ValueError("dt_s must be a positive finite number")

        thrust = _clamp(command.collective_thrust_newton, 0.0, self.parameters.max_collective_thrust_newton)
        torque = tuple(
            _clamp(component, -limit, limit)
            for component, limit in zip(command.body_torque_nm, self.parameters.max_body_torque_nm)
        )

        thrust_world = rotate_vector_by_quaternion(state.orientation_wxyz, (0.0, 0.0, thrust))
        gravity_world = (0.0, 0.0, -self.parameters.gravity_m_s2 * self.parameters.mass_kg)
        acceleration = tuple(
            (force + gravity) / self.parameters.mass_kg
            for force, gravity in zip(thrust_world, gravity_world)
        )

        angular_acceleration = tuple(
            torque_component / inertia
            for torque_component, inertia in zip(torque, self.parameters.inertia_kg_m2)
        )

        linear_velocity = tuple(
            velocity + acceleration_component * dt
            for velocity, acceleration_component in zip(state.linear_velocity_m_s, acceleration)
        )
        angular_velocity = tuple(
            omega + alpha * dt
            for omega, alpha in zip(state.angular_velocity_rad_s, angular_acceleration)
        )

        position = tuple(
            coordinate + velocity * dt + 0.5 * acceleration_component * dt * dt
            for coordinate, velocity, acceleration_component in zip(
                state.position_m,
                state.linear_velocity_m_s,
                acceleration,
            )
        )

        omega_avg = tuple(
            0.5 * (omega_before + omega_after)
            for omega_before, omega_after in zip(state.angular_velocity_rad_s, angular_velocity)
        )
        omega_quaternion = (0.0, omega_avg[0], omega_avg[1], omega_avg[2])
        quaternion_delta = quaternion_multiply(normalize_quaternion(state.orientation_wxyz), omega_quaternion)
        orientation = normalize_quaternion(
            tuple(
                component + 0.5 * delta * dt
                for component, delta in zip(state.orientation_wxyz, quaternion_delta)
            )
        )

        return VehicleState(
            position_m=position,
            orientation_wxyz=orientation,
            linear_velocity_m_s=linear_velocity,
            angular_velocity_rad_s=angular_velocity,
            time_s=state.time_s + dt,
        )
