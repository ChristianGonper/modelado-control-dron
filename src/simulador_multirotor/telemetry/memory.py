"""Structured in-memory telemetry for simulator executions."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from types import MappingProxyType
from typing import Mapping

from ..core.attitude import euler_from_quaternion
from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _wrap_angle(angle_rad: float) -> float:
    return (angle_rad + 3.141592653589793) % (2.0 * 3.141592653589793) - 3.141592653589793


def _vector_norm(vector: tuple[float, ...]) -> float:
    return sqrt(sum(component * component for component in vector))


def _serialize_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return dict(value)


def _serialize_state(state: VehicleState) -> dict[str, object]:
    return {
        "position_m": state.position_m,
        "orientation_wxyz": state.orientation_wxyz,
        "linear_velocity_m_s": state.linear_velocity_m_s,
        "angular_velocity_rad_s": state.angular_velocity_rad_s,
        "time_s": state.time_s,
    }


def _serialize_observation(observation: VehicleObservation) -> dict[str, object]:
    return {
        "true_state": _serialize_state(observation.true_state),
        "observed_state": _serialize_state(observation.observed_state),
        "metadata": _serialize_mapping(observation.metadata),
    }


def _serialize_reference(reference: TrajectoryReference) -> dict[str, object]:
    return {
        "time_s": reference.time_s,
        "position_m": reference.position_m,
        "velocity_m_s": reference.velocity_m_s,
        "yaw_rad": reference.yaw_rad,
        "valid_from_s": reference.valid_from_s,
        "valid_until_s": reference.valid_until_s,
        "acceleration_m_s2": reference.acceleration_m_s2,
        "metadata": _serialize_mapping(reference.metadata),
    }


def _serialize_command(command: VehicleCommand) -> dict[str, object]:
    return {
        "collective_thrust_newton": command.collective_thrust_newton,
        "body_torque_nm": command.body_torque_nm,
    }


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    kind: str
    message: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind).strip().lower()
        if not kind:
            raise ValueError("kind must be a non-empty string")
        object.__setattr__(self, "kind", kind)
        if self.message is not None:
            message = str(self.message).strip()
            object.__setattr__(self, "message", message or None)
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "message": self.message,
            "metadata": _serialize_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class TrackingError:
    position_m: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float]
    yaw_rad: float

    def __post_init__(self) -> None:
        if len(self.position_m) != 3:
            raise ValueError("position_m must contain exactly 3 values")
        if len(self.velocity_m_s) != 3:
            raise ValueError("velocity_m_s must contain exactly 3 values")
        object.__setattr__(self, "position_m", tuple(_coerce_float(value, "position_m") for value in self.position_m))
        object.__setattr__(self, "velocity_m_s", tuple(_coerce_float(value, "velocity_m_s") for value in self.velocity_m_s))
        object.__setattr__(self, "yaw_rad", _coerce_float(self.yaw_rad, "yaw_rad"))

    @classmethod
    def from_state_and_reference(
        cls,
        *,
        state: VehicleState,
        reference: TrajectoryReference,
    ) -> "TrackingError":
        _, _, current_yaw = euler_from_quaternion(state.orientation_wxyz)
        position_error = tuple(
            reference_value - state_value for reference_value, state_value in zip(reference.position_m, state.position_m)
        )
        velocity_error = tuple(
            reference_value - state_value
            for reference_value, state_value in zip(reference.velocity_m_s, state.linear_velocity_m_s)
        )
        yaw_error = _wrap_angle(reference.yaw_rad - current_yaw)
        return cls(position_m=position_error, velocity_m_s=velocity_error, yaw_rad=yaw_error)

    @property
    def position_norm_m(self) -> float:
        return _vector_norm(self.position_m)

    @property
    def velocity_norm_m_s(self) -> float:
        return _vector_norm(self.velocity_m_s)

    @property
    def yaw_abs_rad(self) -> float:
        return abs(self.yaw_rad)

    def to_dict(self) -> dict[str, object]:
        return {
            "position_m": self.position_m,
            "velocity_m_s": self.velocity_m_s,
            "yaw_rad": self.yaw_rad,
        }


@dataclass(frozen=True, slots=True)
class SimulationStep:
    index: int
    time_s: float
    state: VehicleState
    observation: VehicleObservation
    reference: TrajectoryReference
    error: TrackingError
    command: VehicleCommand
    events: tuple[TelemetryEvent, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "index", int(self.index))
        object.__setattr__(self, "time_s", _coerce_float(self.time_s, "time_s"))
        if not isinstance(self.state, VehicleState):
            raise ValueError("state must be a VehicleState")
        if not isinstance(self.observation, VehicleObservation):
            raise ValueError("observation must be a VehicleObservation")
        if not isinstance(self.reference, TrajectoryReference):
            raise ValueError("reference must be a TrajectoryReference")
        if not isinstance(self.error, TrackingError):
            raise ValueError("error must be a TrackingError")
        if not isinstance(self.command, VehicleCommand):
            raise ValueError("command must be a VehicleCommand")
        object.__setattr__(self, "events", tuple(self.events))
        for event in self.events:
            if not isinstance(event, TelemetryEvent):
                raise ValueError("events must contain TelemetryEvent instances")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @property
    def position_error_norm_m(self) -> float:
        return self.error.position_norm_m

    @property
    def velocity_error_norm_m_s(self) -> float:
        return self.error.velocity_norm_m_s

    def to_dict(self, *, detail_level: str = "standard") -> dict[str, object]:
        record = {
            "index": self.index,
            "time_s": self.time_s,
            "state": _serialize_state(self.state),
            "true_state": _serialize_state(self.state),
            "reference": _serialize_reference(self.reference),
            "error": self.error.to_dict(),
            "command": _serialize_command(self.command),
            "events": [event.to_dict() for event in self.events],
            "metadata": _serialize_mapping(self.metadata),
        }
        if detail_level == "compact":
            record.pop("metadata")
            record.pop("events")
            record["observation"] = None
            record["observed_state"] = _serialize_state(self.observation.observed_state)
        else:
            record["observation"] = _serialize_observation(self.observation)
            record["observed_state"] = _serialize_state(self.observation.observed_state)
            if detail_level != "full":
                record["observation"] = {
                    "true_state": {
                        "position_m": self.observation.true_state.position_m,
                        "linear_velocity_m_s": self.observation.true_state.linear_velocity_m_s,
                        "time_s": self.observation.true_state.time_s,
                    },
                    "observed_state": {
                        "position_m": self.observation.observed_state.position_m,
                        "linear_velocity_m_s": self.observation.observed_state.linear_velocity_m_s,
                        "time_s": self.observation.observed_state.time_s,
                    },
                    "metadata": _serialize_mapping(self.observation.metadata),
                }
        return record


@dataclass(frozen=True, slots=True)
class SimulationHistory:
    initial_state: VehicleState
    steps: tuple[SimulationStep, ...]
    scenario_metadata: Mapping[str, object] = field(default_factory=dict)
    vehicle_metadata: Mapping[str, object] = field(default_factory=dict)
    controller_metadata: Mapping[str, object] = field(default_factory=dict)
    telemetry_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_metadata", MappingProxyType(dict(self.scenario_metadata)))
        object.__setattr__(self, "vehicle_metadata", MappingProxyType(dict(self.vehicle_metadata)))
        object.__setattr__(self, "controller_metadata", MappingProxyType(dict(self.controller_metadata)))
        object.__setattr__(self, "telemetry_metadata", MappingProxyType(dict(self.telemetry_metadata)))

    @property
    def final_state(self) -> VehicleState:
        if not self.steps:
            return self.initial_state
        return self.steps[-1].state

    @property
    def final_time_s(self) -> float:
        if not self.steps:
            return self.initial_state.time_s
        return self.steps[-1].time_s

    @property
    def sample_count(self) -> int:
        return len(self.steps)
