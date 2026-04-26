"""Official baseline scenario helpers for the simulator."""

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
BaselineScenario = SimulationScenario

BASELINE_PROFILE_ID = "generic-drone-baseline-v1"
BASELINE_PROFILE_NAME = "generic-drone-baseline-v1"
BASELINE_PROFILE_TAGS = ("baseline", "generic-drone", "phase-1")
BASELINE_ARM_LENGTH_M = 0.11
BASELINE_MASS_KG = 1.0
BASELINE_INERTIA_KG_M2 = (0.02, 0.02, 0.04)
BASELINE_MAX_COLLECTIVE_THRUST_NEWTON = 20.0
BASELINE_MAX_BODY_TORQUE_NM = (0.3, 0.3, 0.2)
BASELINE_MOTOR_TIME_CONSTANT_S = 0.03
BASELINE_ROTOR_THRUST_COEFFICIENT_NEWTON_PER_RAD_S2 = 2.5e-6
BASELINE_ROTOR_REACTION_TORQUE_COEFFICIENT_NM_PER_NEWTON = 1.0e-7
BASELINE_ROTOR_MOTOR_INERTIA_KG_M2 = 1.0e-5
BASELINE_ROTOR_MAX_ANGULAR_SPEED_RAD_S = 1500.0


def _build_baseline_rotor(name: str, position_m: tuple[float, float, float], spin_direction: int) -> RotorGeometry:
    return RotorGeometry(
        name=name,
        position_m=position_m,
        axis_body=(0.0, 0.0, 1.0),
        spin_direction=spin_direction,
        thrust_coefficient_newton_per_rad_s2=BASELINE_ROTOR_THRUST_COEFFICIENT_NEWTON_PER_RAD_S2,
        reaction_torque_coefficient_nm_per_newton=BASELINE_ROTOR_REACTION_TORQUE_COEFFICIENT_NM_PER_NEWTON,
        motor_inertia_kg_m2=BASELINE_ROTOR_MOTOR_INERTIA_KG_M2,
        time_constant_s=BASELINE_MOTOR_TIME_CONSTANT_S,
        max_angular_speed_rad_s=BASELINE_ROTOR_MAX_ANGULAR_SPEED_RAD_S,
    )


def build_baseline_vehicle_profile() -> RigidBodyParameters:
    return RigidBodyParameters(
        mass_kg=BASELINE_MASS_KG,
        gravity_m_s2=9.81,
        inertia_kg_m2=BASELINE_INERTIA_KG_M2,
        max_collective_thrust_newton=BASELINE_MAX_COLLECTIVE_THRUST_NEWTON,
        max_body_torque_nm=BASELINE_MAX_BODY_TORQUE_NM,
        motor_time_constant_s=BASELINE_MOTOR_TIME_CONSTANT_S,
        aerodynamic_force_model="aggregated_body",
        parasitic_drag_area_m2=0.0,
        air_density_kg_m3=1.225,
        induced_hover_loss_ratio=0.0,
        rotors=(
            _build_baseline_rotor("front_left", (BASELINE_ARM_LENGTH_M, BASELINE_ARM_LENGTH_M, 0.0), 1),
            _build_baseline_rotor("front_right", (BASELINE_ARM_LENGTH_M, -BASELINE_ARM_LENGTH_M, 0.0), -1),
            _build_baseline_rotor("rear_left", (-BASELINE_ARM_LENGTH_M, BASELINE_ARM_LENGTH_M, 0.0), -1),
            _build_baseline_rotor("rear_right", (-BASELINE_ARM_LENGTH_M, -BASELINE_ARM_LENGTH_M, 0.0), 1),
        ),
    )


def build_baseline_scenario(*, seed: int | None = None) -> SimulationScenario:
    return SimulationScenario(
        initial_state=VehicleState(
            position_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            time_s=0.0,
        ),
        time=ScenarioTimeConfig(duration_s=1.0, physics_dt_s=0.02, control_dt_s=0.04, telemetry_dt_s=0.04),
        vehicle=build_baseline_vehicle_profile(),
        trajectory=ScenarioTrajectoryConfig(
            kind="hover",
            target_position_m=(0.0, 0.0, 1.0),
            valid_until_s=1.0,
            source="native",
            parameters={
                "scenario": BASELINE_PROFILE_NAME,
                "baseline_profile_id": BASELINE_PROFILE_ID,
            },
        ),
        metadata=ScenarioMetadata(
            name=BASELINE_PROFILE_NAME,
            description="Official baseline for the generic multirotor reference profile.",
            seed=seed,
            tags=BASELINE_PROFILE_TAGS,
        ),
    )


def build_minimal_scenario(*, seed: int | None = None) -> SimulationScenario:
    return build_baseline_scenario(seed=seed)
