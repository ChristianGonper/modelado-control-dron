from __future__ import annotations

import pytest

from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import (
    BASELINE_ARM_LENGTH_M,
    BASELINE_INERTIA_KG_M2,
    BASELINE_MAX_BODY_TORQUE_NM,
    BASELINE_MAX_COLLECTIVE_THRUST_NEWTON,
    BASELINE_MASS_KG,
    BASELINE_PROFILE_ID,
    BASELINE_PROFILE_NAME,
    BASELINE_PROFILE_TAGS,
    BASELINE_ROTOR_MAX_ANGULAR_SPEED_RAD_S,
    BASELINE_ROTOR_REACTION_TORQUE_COEFFICIENT_NM_PER_NEWTON,
    BASELINE_ROTOR_THRUST_COEFFICIENT_NEWTON_PER_RAD_S2,
    build_baseline_scenario,
)
from simulador_multirotor.dynamics import RigidBodyParameters


def test_baseline_profile_fixes_physical_parameters() -> None:
    scenario = build_baseline_scenario()
    vehicle = scenario.vehicle

    assert scenario.metadata.name == BASELINE_PROFILE_NAME
    assert scenario.metadata.tags == BASELINE_PROFILE_TAGS
    assert scenario.trajectory.parameters["baseline_profile_id"] == BASELINE_PROFILE_ID
    assert vehicle.mass_kg == pytest.approx(BASELINE_MASS_KG)
    assert vehicle.inertia_kg_m2 == pytest.approx(BASELINE_INERTIA_KG_M2)
    assert vehicle.max_collective_thrust_newton == pytest.approx(BASELINE_MAX_COLLECTIVE_THRUST_NEWTON)
    assert vehicle.max_body_torque_nm == pytest.approx(BASELINE_MAX_BODY_TORQUE_NM)
    assert len(vehicle.rotors) == 4

    rotor_thrust_capacities = []
    for rotor in vehicle.rotors:
        assert rotor.axis_body == (0.0, 0.0, 1.0)
        assert rotor.thrust_coefficient_newton_per_rad_s2 == pytest.approx(
            BASELINE_ROTOR_THRUST_COEFFICIENT_NEWTON_PER_RAD_S2
        )
        assert rotor.reaction_torque_coefficient_nm_per_newton == pytest.approx(
            BASELINE_ROTOR_REACTION_TORQUE_COEFFICIENT_NM_PER_NEWTON
        )
        assert rotor.max_angular_speed_rad_s == pytest.approx(BASELINE_ROTOR_MAX_ANGULAR_SPEED_RAD_S)
        rotor_thrust_capacities.append(
            rotor.thrust_coefficient_newton_per_rad_s2 * rotor.max_angular_speed_rad_s * rotor.max_angular_speed_rad_s
        )

    assert sum(rotor_thrust_capacities) >= vehicle.max_collective_thrust_newton
    assert vehicle.rotors[0].position_m == pytest.approx((BASELINE_ARM_LENGTH_M, BASELINE_ARM_LENGTH_M, 0.0))
    assert vehicle.rotors[1].position_m == pytest.approx((BASELINE_ARM_LENGTH_M, -BASELINE_ARM_LENGTH_M, 0.0))
    assert vehicle.rotors[2].position_m == pytest.approx((-BASELINE_ARM_LENGTH_M, BASELINE_ARM_LENGTH_M, 0.0))
    assert vehicle.rotors[3].position_m == pytest.approx((-BASELINE_ARM_LENGTH_M, -BASELINE_ARM_LENGTH_M, 0.0))


def test_baseline_profile_runs_nominal_simulation_without_extra_configuration() -> None:
    history = SimulationRunner().run(build_baseline_scenario())

    assert history.final_time_s == pytest.approx(1.0)
    assert history.scenario_metadata["metadata"]["name"] == BASELINE_PROFILE_NAME
    assert history.scenario_metadata["trajectory"]["parameters"]["baseline_profile_id"] == BASELINE_PROFILE_ID
    assert history.vehicle_metadata["mass_kg"] == pytest.approx(BASELINE_MASS_KG)


def test_incoherent_vehicle_profile_reports_clear_rotor_capacity_error() -> None:
    baseline_vehicle = build_baseline_scenario().vehicle

    with pytest.raises(ValueError, match="sum of rotor maximum thrusts must cover max_collective_thrust_newton"):
        RigidBodyParameters(
            mass_kg=baseline_vehicle.mass_kg,
            gravity_m_s2=baseline_vehicle.gravity_m_s2,
            inertia_kg_m2=baseline_vehicle.inertia_kg_m2,
            max_collective_thrust_newton=baseline_vehicle.max_collective_thrust_newton * 2.0,
            max_body_torque_nm=baseline_vehicle.max_body_torque_nm,
            motor_time_constant_s=baseline_vehicle.motor_time_constant_s,
            aerodynamic_force_model=baseline_vehicle.aerodynamic_force_model,
            parasitic_drag_area_m2=baseline_vehicle.parasitic_drag_area_m2,
            air_density_kg_m3=baseline_vehicle.air_density_kg_m3,
            induced_hover_loss_ratio=baseline_vehicle.induced_hover_loss_ratio,
            rotors=baseline_vehicle.rotors,
        )
