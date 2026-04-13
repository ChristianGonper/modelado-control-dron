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


def _coerce_vector(
    value: Sequence[object],
    *,
    length: int,
    field_name: str,
) -> tuple[float, ...]:
    if len(value) != length:
        raise ValueError(f"{field_name} must contain exactly {length} values")
    return tuple(_coerce_float(component, field_name) for component in value)


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
class VehicleCommand:
    """Decoupled control command: collective thrust and body torques."""

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
class VehicleObservation:
    """Snapshot exposed to controllers, independent from the integrator."""

    state: VehicleState
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.state, VehicleState):
            raise ValueError("state must be a VehicleState")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


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
        if self.valid_until_s is not None and self.time_s > self.valid_until_s:
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
        if self.valid_until_s is not None and time_value > self.valid_until_s:
            return False
        return True
