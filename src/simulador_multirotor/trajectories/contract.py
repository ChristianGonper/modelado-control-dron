"""Common trajectory contract and adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Callable, Mapping, Protocol, runtime_checkable

from ..core.contracts import TrajectoryReference


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


@runtime_checkable
class TrajectoryContract(Protocol):
    """Common surface shared by native and adapted trajectories."""

    kind: str
    source: str
    duration_s: float
    parameters: Mapping[str, object]

    def reference_at(self, time_s: float) -> TrajectoryReference:
        """Return a trajectory reference sample at the requested time."""

    def is_complete_at(self, time_s: float) -> bool:
        """Return whether the trajectory horizon has been exhausted."""


@dataclass(frozen=True, slots=True)
class TrajectoryAdapter:
    """Adapt an external sampler to the shared trajectory contract."""

    sample_fn: Callable[[float], TrajectoryReference]
    kind: str = "adapted"
    source: str = "external"
    duration_s: float | None = None
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind).strip().lower()
        if not kind:
            raise ValueError("kind must be a non-empty string")
        source = str(self.source).strip().lower()
        if not source:
            raise ValueError("source must be a non-empty string")
        duration_s = float("inf") if self.duration_s is None else _coerce_float(self.duration_s, "duration_s")
        if duration_s <= 0.0:
            raise ValueError("duration_s must be positive")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "duration_s", duration_s)
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def reference_at(self, time_s: float) -> TrajectoryReference:
        reference = self.sample_fn(time_s)
        if not isinstance(reference, TrajectoryReference):
            raise ValueError("sample_fn must return a TrajectoryReference")
        return reference

    def is_complete_at(self, time_s: float) -> bool:
        return _coerce_float(time_s, "time_s") >= self.duration_s
