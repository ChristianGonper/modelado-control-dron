"""Shared simulator contracts.

The first phase keeps all cross-cutting data types here to avoid circular
imports between control, trajectories, telemetry, and the future runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose, isfinite, sqrt
from types import MappingProxyType
from typing import Mapping, Sequence


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_optional_float(value: object | None, field_name: str) -> float | None:
    if value is None:
        return None
    return _coerce_float(value, field_name)


def _coerce_vector(
    value: Sequence[object],
    *,
    length: int,
    field_name: str,
) -> tuple[float, ...]:
    if len(value) != length:
        raise ValueError(f"{field_name} must contain exactly {length} values")
    return tuple(_coerce_float(component, field_name) for component in value)


def _coerce_unit_vector(value: Sequence[object], *, field_name: str) -> tuple[float, float, float]:
    vector = _coerce_vector(value, length=3, field_name=field_name)
    norm = sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        raise ValueError(f"{field_name} must be non-zero")
    if not isclose(norm, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError(f"{field_name} must be a unit vector")
    return tuple(component / norm for component in vector)


def _freeze_metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class VehicleState:
    """Rigid-body state of the vehicle in world/body coordinates.

    Position and linear velocity live in the inertial/world frame. Orientation
    is stored as a unit quaternion in `w, x, y, z` order. Angular velocity is
    expressed in body axes.
    """

    position_m: tuple[float, float, float]
    orientation_wxyz: tuple[float, float, float, float]
    linear_velocity_m_s: tuple[float, float, float]
    angular_velocity_rad_s: tuple[float, float, float]
    time_s: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "position_m", _coerce_vector(self.position_m, length=3, field_name="position_m"))
        object.__setattr__(
            self,
            "orientation_wxyz",
            _coerce_vector(self.orientation_wxyz, length=4, field_name="orientation_wxyz"),
        )
        object.__setattr__(
            self,
            "linear_velocity_m_s",
            _coerce_vector(self.linear_velocity_m_s, length=3, field_name="linear_velocity_m_s"),
        )
        object.__setattr__(
            self,
            "angular_velocity_rad_s",
            _coerce_vector(self.angular_velocity_rad_s, length=3, field_name="angular_velocity_rad_s"),
        )
        object.__setattr__(self, "time_s", _coerce_float(self.time_s, "time_s"))
        norm = sqrt(sum(component * component for component in self.orientation_wxyz))
        if not isclose(norm, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError("orientation_wxyz must be a unit quaternion")


@dataclass(frozen=True, slots=True)
class RotorGeometry:
    """Geometry and actuator constants for an individual rotor."""

    name: str
    position_m: tuple[float, float, float]
    axis_body: tuple[float, float, float] = (0.0, 0.0, 1.0)
    spin_direction: int = 1
    thrust_coefficient_newton_per_rad_s2: float = 0.0
    reaction_torque_coefficient_nm_per_newton: float = 0.0
    motor_inertia_kg_m2: float = 0.0
    time_constant_s: float | None = None
    max_angular_speed_rad_s: float | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("name must be a non-empty string")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "position_m", _coerce_vector(self.position_m, length=3, field_name="position_m"))
        object.__setattr__(self, "axis_body", _coerce_unit_vector(self.axis_body, field_name="axis_body"))
        spin_direction = int(self.spin_direction)
        if spin_direction not in (-1, 1):
            raise ValueError("spin_direction must be -1 or 1")
        object.__setattr__(self, "spin_direction", spin_direction)
        thrust_coefficient = _coerce_float(
            self.thrust_coefficient_newton_per_rad_s2,
            "thrust_coefficient_newton_per_rad_s2",
        )
        reaction_coefficient = _coerce_float(
            self.reaction_torque_coefficient_nm_per_newton,
            "reaction_torque_coefficient_nm_per_newton",
        )
        motor_inertia = _coerce_float(self.motor_inertia_kg_m2, "motor_inertia_kg_m2")
        if thrust_coefficient <= 0.0:
            raise ValueError("thrust_coefficient_newton_per_rad_s2 must be positive")
        if reaction_coefficient < 0.0:
            raise ValueError("reaction_torque_coefficient_nm_per_newton must be non-negative")
        if motor_inertia < 0.0:
            raise ValueError("motor_inertia_kg_m2 must be non-negative")
        object.__setattr__(self, "thrust_coefficient_newton_per_rad_s2", thrust_coefficient)
        object.__setattr__(self, "reaction_torque_coefficient_nm_per_newton", reaction_coefficient)
        object.__setattr__(self, "motor_inertia_kg_m2", motor_inertia)
        time_constant = _coerce_optional_float(self.time_constant_s, "time_constant_s")
        if time_constant is not None and time_constant <= 0.0:
            raise ValueError("time_constant_s must be positive")
        object.__setattr__(self, "time_constant_s", time_constant)
        max_angular_speed = _coerce_optional_float(self.max_angular_speed_rad_s, "max_angular_speed_rad_s")
        if max_angular_speed is not None and max_angular_speed <= 0.0:
            raise ValueError("max_angular_speed_rad_s must be positive")
        object.__setattr__(self, "max_angular_speed_rad_s", max_angular_speed)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class VehicleIntent:
    """High-level wrench intent produced by the controller."""

    collective_thrust_newton: float
    body_torque_nm: tuple[float, float, float]

    def __post_init__(self) -> None:
        thrust = _coerce_float(self.collective_thrust_newton, "collective_thrust_newton")
        if thrust < 0.0:
            raise ValueError("collective_thrust_newton must be non-negative")
        object.__setattr__(self, "collective_thrust_newton", thrust)
        object.__setattr__(
            self,
            "body_torque_nm",
            _coerce_vector(self.body_torque_nm, length=3, field_name="body_torque_nm"),
        )


@dataclass(frozen=True, slots=True)
class RotorCommand:
    """Per-rotor signal emitted by a mixer or actuator layer."""

    rotor_name: str
    thrust_newton: float = 0.0
    motor_speed_rad_s: float | None = None
    reaction_torque_nm: float | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        rotor_name = str(self.rotor_name).strip()
        if not rotor_name:
            raise ValueError("rotor_name must be a non-empty string")
        object.__setattr__(self, "rotor_name", rotor_name)
        thrust = _coerce_float(self.thrust_newton, "thrust_newton")
        if thrust < 0.0:
            raise ValueError("thrust_newton must be non-negative")
        object.__setattr__(self, "thrust_newton", thrust)
        if self.motor_speed_rad_s is not None:
            object.__setattr__(self, "motor_speed_rad_s", _coerce_float(self.motor_speed_rad_s, "motor_speed_rad_s"))
        if self.reaction_torque_nm is not None:
            object.__setattr__(self, "reaction_torque_nm", _coerce_float(self.reaction_torque_nm, "reaction_torque_nm"))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, init=False)
class VehicleCommand:
    """Decoupled control command with optional per-motor signals."""

    intent: VehicleIntent
    rotor_commands: tuple[RotorCommand, ...]
    metadata: Mapping[str, object]

    def __init__(
        self,
        collective_thrust_newton: float | None = None,
        body_torque_nm: Sequence[object] | None = None,
        *,
        intent: VehicleIntent | None = None,
        rotor_commands: Sequence[RotorCommand] = (),
        metadata: Mapping[str, object] = (),
    ) -> None:
        if intent is None:
            if collective_thrust_newton is None or body_torque_nm is None:
                raise ValueError(
                    "collective_thrust_newton and body_torque_nm are required when intent is not provided"
                )
            intent = VehicleIntent(
                collective_thrust_newton=collective_thrust_newton,
                body_torque_nm=_coerce_vector(body_torque_nm, length=3, field_name="body_torque_nm"),
            )
        else:
            if collective_thrust_newton is not None:
                expected = _coerce_float(collective_thrust_newton, "collective_thrust_newton")
                if not isclose(expected, intent.collective_thrust_newton, rel_tol=1e-9, abs_tol=1e-9):
                    raise ValueError("collective_thrust_newton does not match intent")
            if body_torque_nm is not None:
                expected_torque = _coerce_vector(body_torque_nm, length=3, field_name="body_torque_nm")
                if expected_torque != intent.body_torque_nm:
                    raise ValueError("body_torque_nm does not match intent")

        rotor_command_tuple = tuple(rotor_commands)
        seen_names: set[str] = set()
        for rotor_command in rotor_command_tuple:
            if not isinstance(rotor_command, RotorCommand):
                raise ValueError("rotor_commands must contain RotorCommand instances")
            if rotor_command.rotor_name in seen_names:
                raise ValueError("rotor_commands must not contain duplicate rotor_name values")
            seen_names.add(rotor_command.rotor_name)

        object.__setattr__(self, "intent", intent)
        object.__setattr__(self, "rotor_commands", rotor_command_tuple)
        object.__setattr__(self, "metadata", _freeze_metadata(metadata))

    @property
    def collective_thrust_newton(self) -> float:
        return self.intent.collective_thrust_newton

    @property
    def body_torque_nm(self) -> tuple[float, float, float]:
        return self.intent.body_torque_nm

    @property
    def has_motor_signals(self) -> bool:
        return bool(self.rotor_commands)


@dataclass(frozen=True, slots=True, init=False)
class VehicleObservation:
    """Snapshot exposed to controllers, independent from the integrator."""

    true_state: VehicleState
    observed_state: VehicleState
    metadata: Mapping[str, object]

    def __init__(
        self,
        state: VehicleState | None = None,
        *,
        true_state: VehicleState | None = None,
        observed_state: VehicleState | None = None,
        metadata: Mapping[str, object] = (),
    ) -> None:
        if observed_state is None:
            if true_state is not None:
                observed_state = true_state
            elif state is not None:
                observed_state = state
            else:
                raise ValueError("observed_state must be provided")
        if state is not None and state != observed_state:
            raise ValueError("state and observed_state must match when both are provided")
        if true_state is None:
            true_state = observed_state
        if not isinstance(true_state, VehicleState):
            raise ValueError("true_state must be a VehicleState")
        if not isinstance(observed_state, VehicleState):
            raise ValueError("observed_state must be a VehicleState")
        if not isclose(true_state.time_s, observed_state.time_s, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("true_state and observed_state must refer to the same time")
        object.__setattr__(self, "true_state", true_state)
        object.__setattr__(self, "observed_state", observed_state)
        object.__setattr__(self, "metadata", _freeze_metadata(metadata))

    @property
    def state(self) -> VehicleState:
        """Backward-compatible alias for the observed state."""

        return self.observed_state


@dataclass(frozen=True, slots=True)
class TrajectoryReference:
    """Common reference sample shared by trajectories and controllers.

    `time_s` is the sample timestamp. `valid_from_s` and `valid_until_s`
    define the window in which the reference is usable. `None` means open-ended.
    """

    time_s: float
    position_m: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float]
    yaw_rad: float
    valid_from_s: float
    valid_until_s: float | None = None
    acceleration_m_s2: tuple[float, float, float] | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "time_s", _coerce_float(self.time_s, "time_s"))
        object.__setattr__(self, "position_m", _coerce_vector(self.position_m, length=3, field_name="position_m"))
        object.__setattr__(
            self,
            "velocity_m_s",
            _coerce_vector(self.velocity_m_s, length=3, field_name="velocity_m_s"),
        )
        object.__setattr__(self, "yaw_rad", _coerce_float(self.yaw_rad, "yaw_rad"))
        object.__setattr__(self, "valid_from_s", _coerce_float(self.valid_from_s, "valid_from_s"))
        if self.valid_until_s is not None:
            valid_until = _coerce_float(self.valid_until_s, "valid_until_s")
            if valid_until < self.valid_from_s:
                raise ValueError("valid_until_s must be greater than or equal to valid_from_s")
            object.__setattr__(self, "valid_until_s", valid_until)
        if self.time_s < self.valid_from_s:
            raise ValueError("time_s must be greater than or equal to valid_from_s")
        if self.valid_until_s is not None and self.time_s > self.valid_until_s + 1e-9:
            raise ValueError("time_s must be less than or equal to valid_until_s")
        if self.acceleration_m_s2 is not None:
            object.__setattr__(
                self,
                "acceleration_m_s2",
                _coerce_vector(self.acceleration_m_s2, length=3, field_name="acceleration_m_s2"),
            )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def is_valid_at(self, time_s: float) -> bool:
        """Return whether the reference is valid at a given simulation time."""

        time_value = _coerce_float(time_s, "time_s")
        if time_value < self.valid_from_s:
            return False
        if self.valid_until_s is not None and time_value > self.valid_until_s + 1e-9:
            return False
        return True
