"""Minimal rigid-body 6DOF dynamics."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from ..core.attitude import (
    normalize_quaternion,
    quaternion_increment_from_angular_velocity,
    quaternion_derivative,
    quaternion_multiply,
    rotate_vector_by_quaternion,
)
from ..core.contracts import RotorGeometry, VehicleCommand, VehicleState
from .aerodynamics import AerodynamicEnvironment


def _coerce_positive(value: object, field_name: str) -> float:
    number = float(value)
    if not isfinite(number) or number <= 0.0:
        raise ValueError(f"{field_name} must be a positive finite number")
    return number


def _coerce_non_negative(value: object, field_name: str) -> float:
    number = float(value)
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{field_name} must be a non-negative finite number")
    return number


def _coerce_float(value: object, field_name: str) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be a finite number")
    return number


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _vector_add(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(left_component + right_component for left_component, right_component in zip(left, right))


def _vector_sub(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(left_component - right_component for left_component, right_component in zip(left, right))


def _vector_scale(vector: tuple[float, ...], scale: float) -> tuple[float, ...]:
    return tuple(component * scale for component in vector)


def _vector_weighted_sum(*terms: tuple[float, tuple[float, ...]]) -> tuple[float, ...]:
    if not terms:
        raise ValueError("terms must not be empty")
    length = len(terms[0][1])
    total = [0.0] * length
    for weight, vector in terms:
        if len(vector) != length:
            raise ValueError("all vectors must have the same length")
        for index, component in enumerate(vector):
            total[index] += weight * component
    return tuple(total)


def _cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    lx, ly, lz = left
    rx, ry, rz = right
    return (
        ly * rz - lz * ry,
        lz * rx - lx * rz,
        lx * ry - ly * rx,
    )


@dataclass(frozen=True, slots=True)
class RigidBodyStateDerivative:
    position_m_s: tuple[float, float, float]
    linear_velocity_m_s2: tuple[float, float, float]
    orientation_wxyz_s: tuple[float, float, float, float]
    angular_velocity_rad_s2: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class RigidBodyParameters:
    mass_kg: float = 1.0
    gravity_m_s2: float = 9.81
    inertia_kg_m2: tuple[float, float, float] = (0.02, 0.02, 0.04)
    max_collective_thrust_newton: float = 20.0
    max_body_torque_nm: tuple[float, float, float] = (0.3, 0.3, 0.2)
    parasitic_drag_area_m2: float = 0.0
    air_density_kg_m3: float = 1.225
    induced_hover_loss_ratio: float = 0.0
    rotors: tuple[RotorGeometry, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mass_kg", _coerce_positive(self.mass_kg, "mass_kg"))
        object.__setattr__(self, "gravity_m_s2", _coerce_non_negative(self.gravity_m_s2, "gravity_m_s2"))
        inertia = tuple(_coerce_positive(component, "inertia_kg_m2") for component in self.inertia_kg_m2)
        object.__setattr__(self, "inertia_kg_m2", inertia)
        object.__setattr__(
            self,
            "max_collective_thrust_newton",
            _coerce_positive(self.max_collective_thrust_newton, "max_collective_thrust_newton"),
        )
        torque_limits = tuple(_coerce_positive(component, "max_body_torque_nm") for component in self.max_body_torque_nm)
        object.__setattr__(self, "max_body_torque_nm", torque_limits)
        object.__setattr__(
            self,
            "parasitic_drag_area_m2",
            max(0.0, _coerce_float(self.parasitic_drag_area_m2, "parasitic_drag_area_m2")),
        )
        object.__setattr__(self, "air_density_kg_m3", _coerce_positive(self.air_density_kg_m3, "air_density_kg_m3"))
        object.__setattr__(
            self,
            "induced_hover_loss_ratio",
            max(0.0, _coerce_float(self.induced_hover_loss_ratio, "induced_hover_loss_ratio")),
        )
        rotors = tuple(self.rotors)
        seen_names: set[str] = set()
        for rotor in rotors:
            if not isinstance(rotor, RotorGeometry):
                raise ValueError("rotors must contain RotorGeometry instances")
            if rotor.name in seen_names:
                raise ValueError("rotors must not contain duplicate names")
            seen_names.add(rotor.name)
        object.__setattr__(self, "rotors", rotors)

    @property
    def rotor_count(self) -> int:
        return len(self.rotors)

    @property
    def has_rotors(self) -> bool:
        return bool(self.rotors)


@dataclass(frozen=True, slots=True)
class RigidBody6DOFDynamics:
    parameters: RigidBodyParameters = field(default_factory=RigidBodyParameters)
    aerodynamics: AerodynamicEnvironment = field(default_factory=AerodynamicEnvironment)

    def _resolve_forces_and_torques(
        self,
        state: VehicleState,
        command: VehicleCommand,
        wind_world: tuple[float, float, float],
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        thrust = _clamp(command.collective_thrust_newton, 0.0, self.parameters.max_collective_thrust_newton)
        torque = tuple(
            _clamp(component, -limit, limit)
            for component, limit in zip(command.body_torque_nm, self.parameters.max_body_torque_nm)
        )

        relative_air_velocity_world = tuple(
            velocity - wind_component
            for velocity, wind_component in zip(state.linear_velocity_m_s, wind_world)
        )
        drag_world = self.aerodynamics.compute_parasitic_drag_force_newton(relative_air_velocity_world)
        induced_force_body = self.aerodynamics.compute_induced_force_body_newton(
            thrust,
            max_collective_thrust_newton=self.parameters.max_collective_thrust_newton,
        )
        effective_thrust = thrust + induced_force_body[2]
        thrust_world = rotate_vector_by_quaternion(state.orientation_wxyz, (0.0, 0.0, effective_thrust))
        gravity_world = (0.0, 0.0, -self.parameters.gravity_m_s2 * self.parameters.mass_kg)
        acceleration = tuple(
            (force + gravity + drag) / self.parameters.mass_kg
            for force, gravity, drag in zip(thrust_world, gravity_world, drag_world)
        )
        inertia = self.parameters.inertia_kg_m2
        angular_velocity = state.angular_velocity_rad_s
        gyro_coupling = _cross(
            angular_velocity,
            tuple(inertia_component * omega_component for inertia_component, omega_component in zip(inertia, angular_velocity)),
        )
        angular_acceleration = tuple(
            (torque_component - gyro_component) / inertia_component
            for torque_component, gyro_component, inertia_component in zip(torque, gyro_coupling, inertia)
        )
        return acceleration, angular_acceleration

    def evaluate_derivative(
        self,
        state: VehicleState,
        command: VehicleCommand,
        *,
        wind_world: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> RigidBodyStateDerivative:
        acceleration, angular_acceleration = self._resolve_forces_and_torques(state, command, wind_world)
        return RigidBodyStateDerivative(
            position_m_s=state.linear_velocity_m_s,
            linear_velocity_m_s2=acceleration,
            orientation_wxyz_s=quaternion_derivative(state.orientation_wxyz, state.angular_velocity_rad_s),
            angular_velocity_rad_s2=angular_acceleration,
        )

    def derivative(
        self,
        state: VehicleState,
        command: VehicleCommand,
        *,
        wind_world: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> RigidBodyStateDerivative:
        """Backward-compatible alias for the pure derivative path."""

        return self.evaluate_derivative(state, command, wind_world=wind_world)

    def _predict_state(
        self,
        state: VehicleState,
        derivative: RigidBodyStateDerivative,
        dt_s: float,
    ) -> VehicleState:
        next_position = _vector_add(state.position_m, _vector_scale(derivative.position_m_s, dt_s))
        next_linear_velocity = _vector_add(state.linear_velocity_m_s, _vector_scale(derivative.linear_velocity_m_s2, dt_s))
        next_angular_velocity = _vector_add(
            state.angular_velocity_rad_s,
            _vector_scale(derivative.angular_velocity_rad_s2, dt_s),
        )
        average_angular_velocity = tuple(
            0.5 * (before + after)
            for before, after in zip(state.angular_velocity_rad_s, next_angular_velocity)
        )
        orientation_delta = quaternion_increment_from_angular_velocity(average_angular_velocity, dt_s)
        next_orientation = normalize_quaternion(quaternion_multiply(state.orientation_wxyz, orientation_delta))
        return VehicleState(
            position_m=next_position,
            orientation_wxyz=next_orientation,
            linear_velocity_m_s=next_linear_velocity,
            angular_velocity_rad_s=next_angular_velocity,
            time_s=state.time_s + dt_s,
        )

    def step(self, state: VehicleState, command: VehicleCommand, dt_s: float) -> VehicleState:
        dt = float(dt_s)
        if not isfinite(dt) or dt <= 0.0:
            raise ValueError("dt_s must be a positive finite number")

        wind_world = self.aerodynamics.sample_wind_velocity()
        k1 = self.evaluate_derivative(state, command, wind_world=wind_world)
        k2_state = self._predict_state(state, k1, 0.5 * dt)
        k2 = self.evaluate_derivative(k2_state, command, wind_world=wind_world)
        k3_state = self._predict_state(state, k2, 0.5 * dt)
        k3 = self.evaluate_derivative(k3_state, command, wind_world=wind_world)
        k4_state = self._predict_state(state, k3, dt)
        k4 = self.evaluate_derivative(k4_state, command, wind_world=wind_world)

        next_position = tuple(
            component + dt / 6.0 * weighted_sum
            for component, weighted_sum in zip(
                state.position_m,
                _vector_weighted_sum(
                    (1.0, k1.position_m_s),
                    (2.0, k2.position_m_s),
                    (2.0, k3.position_m_s),
                    (1.0, k4.position_m_s),
                ),
            )
        )
        next_linear_velocity = tuple(
            component + dt / 6.0 * weighted_sum
            for component, weighted_sum in zip(
                state.linear_velocity_m_s,
                _vector_weighted_sum(
                    (1.0, k1.linear_velocity_m_s2),
                    (2.0, k2.linear_velocity_m_s2),
                    (2.0, k3.linear_velocity_m_s2),
                    (1.0, k4.linear_velocity_m_s2),
                ),
            )
        )
        next_angular_velocity = tuple(
            component + dt / 6.0 * weighted_sum
            for component, weighted_sum in zip(
                state.angular_velocity_rad_s,
                _vector_weighted_sum(
                    (1.0, k1.angular_velocity_rad_s2),
                    (2.0, k2.angular_velocity_rad_s2),
                    (2.0, k3.angular_velocity_rad_s2),
                    (1.0, k4.angular_velocity_rad_s2),
                ),
            )
        )
        effective_angular_velocity = tuple(
            (
                state.angular_velocity_rad_s[index]
                + 2.0 * k2_state.angular_velocity_rad_s[index]
                + 2.0 * k3_state.angular_velocity_rad_s[index]
                + k4_state.angular_velocity_rad_s[index]
            )
            / 6.0
            for index in range(3)
        )
        orientation_delta = quaternion_increment_from_angular_velocity(effective_angular_velocity, dt)
        next_orientation = normalize_quaternion(quaternion_multiply(state.orientation_wxyz, orientation_delta))

        return VehicleState(
            position_m=next_position,
            orientation_wxyz=next_orientation,
            linear_velocity_m_s=next_linear_velocity,
            angular_velocity_rad_s=next_angular_velocity,
            time_s=state.time_s + dt,
        )
