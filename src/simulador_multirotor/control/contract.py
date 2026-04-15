"""Shared controller contract and adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Callable, Mapping, Protocol, runtime_checkable

from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleIntent, VehicleObservation


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_vector(value: tuple[float, float, float] | list[float], field_name: str) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return (float(value[0]), float(value[1]), float(value[2]))


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@runtime_checkable
class ControllerContract(Protocol):
    """Common controller surface shared by PID and future smart controllers."""

    kind: str
    source: str
    parameters: Mapping[str, object]

    def compute_action(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        """Return the action to apply for the given observation and reference."""


@dataclass(frozen=True, slots=True)
class ControllerAdapter:
    """Adapt an external control callable to the simulator contract."""

    compute_fn: Callable[[VehicleObservation, TrajectoryReference], VehicleCommand]
    kind: str = "adapted"
    source: str = "external"
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind).strip().lower()
        if not kind:
            raise ValueError("kind must be a non-empty string")
        source = str(self.source).strip().lower()
        if not source:
            raise ValueError("source must be a non-empty string")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def compute_action(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        action = self.compute_fn(observation, reference)
        if not isinstance(action, VehicleCommand):
            raise ValueError("compute_fn must return a VehicleCommand")
        return action


@dataclass(frozen=True, slots=True)
class NullController:
    """Minimal stub controller used to validate the replacement boundary."""

    collective_thrust_newton: float = 0.0
    body_torque_nm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    kind: str = "stub"
    source: str = "internal"
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        thrust = _coerce_float(self.collective_thrust_newton, "collective_thrust_newton")
        if thrust < 0.0:
            raise ValueError("collective_thrust_newton must be non-negative")
        object.__setattr__(self, "collective_thrust_newton", thrust)
        object.__setattr__(self, "body_torque_nm", _coerce_vector(self.body_torque_nm, "body_torque_nm"))
        object.__setattr__(self, "kind", str(self.kind).strip().lower() or "stub")
        object.__setattr__(self, "source", str(self.source).strip().lower() or "internal")
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def compute_action(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        return VehicleCommand(
            intent=VehicleIntent(
                collective_thrust_newton=self.collective_thrust_newton,
                body_torque_nm=self.body_torque_nm,
            ),
        )
