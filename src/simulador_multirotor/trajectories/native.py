"""Native trajectory families used by the simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, cos, isfinite, sin
from types import MappingProxyType
from typing import Mapping, Sequence

from ..core.contracts import TrajectoryReference


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_vector(value: Sequence[object], *, length: int, field_name: str) -> tuple[float, ...]:
    if len(value) != length:
        raise ValueError(f"{field_name} must contain exactly {length} values")
    return tuple(_coerce_float(component, field_name) for component in value)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _yaw_from_velocity(velocity_m_s: Sequence[float]) -> float:
    return atan2(float(velocity_m_s[1]), float(velocity_m_s[0]))


@dataclass(frozen=True, slots=True)
class BaseTrajectory:
    kind: str
    duration_s: float
    source: str = "native"
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind).strip().lower()
        source = str(self.source).strip().lower()
        if not kind:
            raise ValueError("kind must be a non-empty string")
        if not source:
            raise ValueError("source must be a non-empty string")
        duration_s = _coerce_float(self.duration_s, "duration_s")
        if duration_s <= 0.0:
            raise ValueError("duration_s must be positive")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "duration_s", duration_s)
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def reference_at(self, time_s: float) -> TrajectoryReference:
        query_time = _coerce_float(time_s, "time_s")
        if query_time < 0.0:
            raise ValueError("time_s must be non-negative")
        sample_time = min(query_time, self.duration_s)
        sample = self._evaluate(sample_time)
        metadata = {
            "trajectory_kind": self.kind,
            "trajectory_source": self.source,
            "trajectory_parameters": dict(self.parameters),
            "trajectory_query_time_s": query_time,
            "trajectory_horizon_s": self.duration_s,
            "trajectory_exhausted": query_time > self.duration_s,
        }
        return TrajectoryReference(
            time_s=sample_time,
            position_m=sample["position_m"],
            velocity_m_s=sample["velocity_m_s"],
            yaw_rad=sample["yaw_rad"],
            valid_from_s=0.0,
            valid_until_s=self.duration_s,
            acceleration_m_s2=sample.get("acceleration_m_s2"),
            metadata=metadata,
        )

    def is_complete_at(self, time_s: float) -> bool:
        return _coerce_float(time_s, "time_s") >= self.duration_s

    def _evaluate(self, time_s: float) -> dict[str, object]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class HoldTrajectory(BaseTrajectory):
    position_m: tuple[float, float, float] = (0.0, 0.0, 1.0)
    velocity_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw_rad: float = 0.0
    acceleration_m_s2: tuple[float, float, float] | None = None

    def __post_init__(self) -> None:
        BaseTrajectory.__post_init__(self)
        object.__setattr__(self, "position_m", _coerce_vector(self.position_m, length=3, field_name="position_m"))
        object.__setattr__(self, "velocity_m_s", _coerce_vector(self.velocity_m_s, length=3, field_name="velocity_m_s"))
        object.__setattr__(self, "yaw_rad", _coerce_float(self.yaw_rad, "yaw_rad"))
        if self.acceleration_m_s2 is not None:
            object.__setattr__(
                self,
                "acceleration_m_s2",
                _coerce_vector(self.acceleration_m_s2, length=3, field_name="acceleration_m_s2"),
            )

    def _evaluate(self, time_s: float) -> dict[str, object]:
        sample = {
            "position_m": self.position_m,
            "velocity_m_s": self.velocity_m_s,
            "yaw_rad": self.yaw_rad,
        }
        if self.acceleration_m_s2 is not None:
            sample["acceleration_m_s2"] = self.acceleration_m_s2
        return sample


@dataclass(frozen=True, slots=True)
class StraightTrajectory(BaseTrajectory):
    start_position_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity_m_s: tuple[float, float, float] = (1.0, 0.0, 0.0)
    yaw_rad: float | None = None

    def __post_init__(self) -> None:
        BaseTrajectory.__post_init__(self)
        object.__setattr__(self, "start_position_m", _coerce_vector(self.start_position_m, length=3, field_name="start_position_m"))
        object.__setattr__(self, "velocity_m_s", _coerce_vector(self.velocity_m_s, length=3, field_name="velocity_m_s"))
        if self.yaw_rad is not None:
            object.__setattr__(self, "yaw_rad", _coerce_float(self.yaw_rad, "yaw_rad"))

    def _evaluate(self, time_s: float) -> dict[str, object]:
        position = tuple(
            start + velocity * time_s for start, velocity in zip(self.start_position_m, self.velocity_m_s)
        )
        yaw = self.yaw_rad if self.yaw_rad is not None else _yaw_from_velocity(self.velocity_m_s)
        return {
            "position_m": position,
            "velocity_m_s": self.velocity_m_s,
            "yaw_rad": yaw,
        }


@dataclass(frozen=True, slots=True)
class CircleTrajectory(BaseTrajectory):
    center_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    radius_m: float = 1.0
    angular_speed_rad_s: float = 1.0
    start_phase_rad: float = 0.0

    def __post_init__(self) -> None:
        BaseTrajectory.__post_init__(self)
        object.__setattr__(self, "center_m", _coerce_vector(self.center_m, length=3, field_name="center_m"))
        radius_m = _coerce_float(self.radius_m, "radius_m")
        angular_speed_rad_s = _coerce_float(self.angular_speed_rad_s, "angular_speed_rad_s")
        if radius_m <= 0.0:
            raise ValueError("radius_m must be positive")
        if angular_speed_rad_s == 0.0:
            raise ValueError("angular_speed_rad_s must be non-zero")
        object.__setattr__(self, "radius_m", radius_m)
        object.__setattr__(self, "angular_speed_rad_s", angular_speed_rad_s)
        object.__setattr__(self, "start_phase_rad", _coerce_float(self.start_phase_rad, "start_phase_rad"))

    def _evaluate(self, time_s: float) -> dict[str, object]:
        theta = self.start_phase_rad + self.angular_speed_rad_s * time_s
        position = (
            self.center_m[0] + self.radius_m * cos(theta),
            self.center_m[1] + self.radius_m * sin(theta),
            self.center_m[2],
        )
        velocity = (
            -self.radius_m * self.angular_speed_rad_s * sin(theta),
            self.radius_m * self.angular_speed_rad_s * cos(theta),
            0.0,
        )
        return {
            "position_m": position,
            "velocity_m_s": velocity,
            "yaw_rad": _yaw_from_velocity(velocity),
        }


@dataclass(frozen=True, slots=True)
class SpiralTrajectory(BaseTrajectory):
    center_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    initial_radius_m: float = 0.25
    radial_rate_m_s: float = 0.1
    angular_speed_rad_s: float = 1.0
    vertical_speed_m_s: float = 0.1
    start_phase_rad: float = 0.0

    def __post_init__(self) -> None:
        BaseTrajectory.__post_init__(self)
        object.__setattr__(self, "center_m", _coerce_vector(self.center_m, length=3, field_name="center_m"))
        initial_radius_m = _coerce_float(self.initial_radius_m, "initial_radius_m")
        angular_speed_rad_s = _coerce_float(self.angular_speed_rad_s, "angular_speed_rad_s")
        if initial_radius_m <= 0.0:
            raise ValueError("initial_radius_m must be positive")
        if angular_speed_rad_s == 0.0:
            raise ValueError("angular_speed_rad_s must be non-zero")
        object.__setattr__(self, "initial_radius_m", initial_radius_m)
        object.__setattr__(self, "radial_rate_m_s", _coerce_float(self.radial_rate_m_s, "radial_rate_m_s"))
        object.__setattr__(self, "angular_speed_rad_s", angular_speed_rad_s)
        object.__setattr__(self, "vertical_speed_m_s", _coerce_float(self.vertical_speed_m_s, "vertical_speed_m_s"))
        object.__setattr__(self, "start_phase_rad", _coerce_float(self.start_phase_rad, "start_phase_rad"))

    def _evaluate(self, time_s: float) -> dict[str, object]:
        radius = self.initial_radius_m + self.radial_rate_m_s * time_s
        theta = self.start_phase_rad + self.angular_speed_rad_s * time_s
        position = (
            self.center_m[0] + radius * cos(theta),
            self.center_m[1] + radius * sin(theta),
            self.center_m[2] + self.vertical_speed_m_s * time_s,
        )
        velocity = (
            self.radial_rate_m_s * cos(theta) - radius * self.angular_speed_rad_s * sin(theta),
            self.radial_rate_m_s * sin(theta) + radius * self.angular_speed_rad_s * cos(theta),
            self.vertical_speed_m_s,
        )
        return {
            "position_m": position,
            "velocity_m_s": velocity,
            "yaw_rad": _yaw_from_velocity(velocity),
        }


@dataclass(frozen=True, slots=True)
class ParametricCurveTrajectory(BaseTrajectory):
    origin_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    forward_speed_m_s: float = 1.0
    lateral_amplitude_m: float = 0.5
    lateral_frequency_rad_s: float = 1.0
    vertical_amplitude_m: float = 0.0
    vertical_frequency_rad_s: float = 1.0
    lateral_phase_rad: float = 0.0
    vertical_phase_rad: float = 0.0

    def __post_init__(self) -> None:
        BaseTrajectory.__post_init__(self)
        object.__setattr__(self, "origin_m", _coerce_vector(self.origin_m, length=3, field_name="origin_m"))
        object.__setattr__(self, "forward_speed_m_s", _coerce_float(self.forward_speed_m_s, "forward_speed_m_s"))
        object.__setattr__(self, "lateral_amplitude_m", _coerce_float(self.lateral_amplitude_m, "lateral_amplitude_m"))
        object.__setattr__(self, "lateral_frequency_rad_s", _coerce_float(self.lateral_frequency_rad_s, "lateral_frequency_rad_s"))
        object.__setattr__(self, "vertical_amplitude_m", _coerce_float(self.vertical_amplitude_m, "vertical_amplitude_m"))
        object.__setattr__(self, "vertical_frequency_rad_s", _coerce_float(self.vertical_frequency_rad_s, "vertical_frequency_rad_s"))
        object.__setattr__(self, "lateral_phase_rad", _coerce_float(self.lateral_phase_rad, "lateral_phase_rad"))
        object.__setattr__(self, "vertical_phase_rad", _coerce_float(self.vertical_phase_rad, "vertical_phase_rad"))

    def _evaluate(self, time_s: float) -> dict[str, object]:
        lateral_angle = self.lateral_phase_rad + self.lateral_frequency_rad_s * time_s
        vertical_angle = self.vertical_phase_rad + self.vertical_frequency_rad_s * time_s
        position = (
            self.origin_m[0] + self.forward_speed_m_s * time_s,
            self.origin_m[1] + self.lateral_amplitude_m * sin(lateral_angle),
            self.origin_m[2] + self.vertical_amplitude_m * sin(vertical_angle),
        )
        velocity = (
            self.forward_speed_m_s,
            self.lateral_amplitude_m * self.lateral_frequency_rad_s * cos(lateral_angle),
            self.vertical_amplitude_m * self.vertical_frequency_rad_s * cos(vertical_angle),
        )
        return {
            "position_m": position,
            "velocity_m_s": velocity,
            "yaw_rad": _yaw_from_velocity(velocity),
        }


@dataclass(frozen=True, slots=True)
class LissajousTrajectory(BaseTrajectory):
    center_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    amplitude_m: tuple[float, float, float] = (1.0, 1.0, 0.5)
    frequency_rad_s: tuple[float, float, float] = (1.0, 2.0, 3.0)
    phase_rad: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        BaseTrajectory.__post_init__(self)
        object.__setattr__(self, "center_m", _coerce_vector(self.center_m, length=3, field_name="center_m"))
        object.__setattr__(self, "amplitude_m", _coerce_vector(self.amplitude_m, length=3, field_name="amplitude_m"))
        object.__setattr__(
            self,
            "frequency_rad_s",
            _coerce_vector(self.frequency_rad_s, length=3, field_name="frequency_rad_s"),
        )
        object.__setattr__(self, "phase_rad", _coerce_vector(self.phase_rad, length=3, field_name="phase_rad"))

    def _evaluate(self, time_s: float) -> dict[str, object]:
        angles = tuple(phase + frequency * time_s for phase, frequency in zip(self.phase_rad, self.frequency_rad_s))
        position = tuple(
            center + amplitude * sin(angle)
            for center, amplitude, angle in zip(self.center_m, self.amplitude_m, angles)
        )
        velocity = tuple(
            amplitude * frequency * cos(angle)
            for amplitude, frequency, angle in zip(self.amplitude_m, self.frequency_rad_s, angles)
        )
        return {
            "position_m": position,
            "velocity_m_s": velocity,
            "yaw_rad": _yaw_from_velocity(velocity),
        }
