"""In-memory telemetry for the minimal runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState


@dataclass(frozen=True, slots=True)
class SimulationStep:
    index: int
    time_s: float
    state: VehicleState
    observation: VehicleObservation
    reference: TrajectoryReference
    command: VehicleCommand


@dataclass(frozen=True, slots=True)
class SimulationHistory:
    initial_state: VehicleState
    steps: tuple[SimulationStep, ...]
    scenario_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_metadata", MappingProxyType(dict(self.scenario_metadata)))

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
