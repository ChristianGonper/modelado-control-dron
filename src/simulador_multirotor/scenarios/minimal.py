"""Ad hoc scenario used for the Foundation tracer bullet."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..control import CascadedController
from ..core.contracts import TrajectoryReference, VehicleState
from ..dynamics import RigidBody6DOFDynamics, RigidBodyParameters


@dataclass(frozen=True, slots=True)
class MinimalScenario:
    initial_state: VehicleState
    target_position_m: tuple[float, float, float]
    target_velocity_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_yaw_rad: float = 0.0
    duration_s: float = 1.0
    dt_s: float = 0.02
    reference_valid_until_s: float | None = None
    dynamics: RigidBodyParameters = field(default_factory=RigidBodyParameters)
    controller: CascadedController = field(default_factory=CascadedController)

    def reference_at(self, time_s: float) -> TrajectoryReference:
        return TrajectoryReference(
            time_s=time_s,
            position_m=self.target_position_m,
            velocity_m_s=self.target_velocity_m_s,
            yaw_rad=self.target_yaw_rad,
            valid_from_s=0.0,
            valid_until_s=self.reference_valid_until_s,
            metadata={"scenario": "minimal-tracer-bullet"},
        )

    def build_dynamics(self) -> RigidBody6DOFDynamics:
        return RigidBody6DOFDynamics(parameters=self.dynamics)

    def build_controller(self) -> CascadedController:
        return self.controller


def build_minimal_scenario() -> MinimalScenario:
    return MinimalScenario(
        initial_state=VehicleState(
            position_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            time_s=0.0,
        ),
        target_position_m=(0.0, 0.0, 1.0),
        duration_s=1.0,
        dt_s=0.02,
        reference_valid_until_s=1.0,
    )
