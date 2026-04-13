"""Nominal scenario helpers for the simulator."""

from __future__ import annotations

from ..core.contracts import VehicleState
from .schema import (
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    SimulationScenario,
)

MinimalScenario = SimulationScenario


def build_minimal_scenario(*, seed: int | None = None) -> SimulationScenario:
    return SimulationScenario(
        initial_state=VehicleState(
            position_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            time_s=0.0,
        ),
        time=ScenarioTimeConfig(duration_s=1.0, dt_s=0.02),
        trajectory=ScenarioTrajectoryConfig(
            kind="hover",
            target_position_m=(0.0, 0.0, 1.0),
            valid_until_s=1.0,
            source="native",
            parameters={"scenario": "minimal-tracer-bullet"},
        ),
        metadata=ScenarioMetadata(
            name="minimal-tracer-bullet",
            description="Nominal hover used by the foundation tracer bullet.",
            seed=seed,
            tags=("foundation", "nominal"),
        ),
    )
