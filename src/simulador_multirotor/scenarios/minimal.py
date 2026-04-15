"""Nominal scenario helpers for the simulator."""

from __future__ import annotations

from ..core.contracts import RotorGeometry, VehicleState
from ..dynamics import RigidBodyParameters
from .schema import (
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    SimulationScenario,
)

MinimalScenario = SimulationScenario


def build_minimal_scenario(*, seed: int | None = None) -> SimulationScenario:
    arm_length_m = 0.11
    return SimulationScenario(
        initial_state=VehicleState(
            position_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            time_s=0.0,
        ),
        time=ScenarioTimeConfig(duration_s=1.0, physics_dt_s=0.02, control_dt_s=0.04, telemetry_dt_s=0.04),
        vehicle=RigidBodyParameters(
            rotors=(
                RotorGeometry(
                    name="front_left",
                    position_m=(arm_length_m, arm_length_m, 0.0),
                    axis_body=(0.0, 0.0, 1.0),
                    spin_direction=1,
                    thrust_coefficient_newton_per_rad_s2=2.5e-6,
                    reaction_torque_coefficient_nm_per_newton=1.0e-7,
                    motor_inertia_kg_m2=1.0e-5,
                    time_constant_s=0.05,
                    max_angular_speed_rad_s=2200.0,
                ),
                RotorGeometry(
                    name="front_right",
                    position_m=(arm_length_m, -arm_length_m, 0.0),
                    axis_body=(0.0, 0.0, 1.0),
                    spin_direction=-1,
                    thrust_coefficient_newton_per_rad_s2=2.5e-6,
                    reaction_torque_coefficient_nm_per_newton=1.0e-7,
                    motor_inertia_kg_m2=1.0e-5,
                    time_constant_s=0.05,
                    max_angular_speed_rad_s=2200.0,
                ),
                RotorGeometry(
                    name="rear_left",
                    position_m=(-arm_length_m, arm_length_m, 0.0),
                    axis_body=(0.0, 0.0, 1.0),
                    spin_direction=-1,
                    thrust_coefficient_newton_per_rad_s2=2.5e-6,
                    reaction_torque_coefficient_nm_per_newton=1.0e-7,
                    motor_inertia_kg_m2=1.0e-5,
                    time_constant_s=0.05,
                    max_angular_speed_rad_s=2200.0,
                ),
                RotorGeometry(
                    name="rear_right",
                    position_m=(-arm_length_m, -arm_length_m, 0.0),
                    axis_body=(0.0, 0.0, 1.0),
                    spin_direction=1,
                    thrust_coefficient_newton_per_rad_s2=2.5e-6,
                    reaction_torque_coefficient_nm_per_newton=1.0e-7,
                    motor_inertia_kg_m2=1.0e-5,
                    time_constant_s=0.05,
                    max_angular_speed_rad_s=2200.0,
                ),
            ),
        ),
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
