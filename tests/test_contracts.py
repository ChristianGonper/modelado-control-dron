from __future__ import annotations

import pytest

from simulador_multirotor.core.contracts import (
    RotorCommand,
    RotorGeometry,
    TrajectoryReference,
    VehicleCommand,
    VehicleIntent,
    VehicleObservation,
    VehicleState,
)


def test_vehicle_state_normalizes_inputs_to_tuples() -> None:
    state = VehicleState(
        position_m=[1, 2, 3],
        orientation_wxyz=[1, 0, 0, 0],
        linear_velocity_m_s=[0, 0, 0],
        angular_velocity_rad_s=[0, 0, 0],
    )

    assert state.position_m == (1.0, 2.0, 3.0)
    assert state.orientation_wxyz == (1.0, 0.0, 0.0, 0.0)


def test_vehicle_state_rejects_non_unit_quaternion() -> None:
    with pytest.raises(ValueError, match="unit quaternion"):
        VehicleState(
            position_m=(0, 0, 0),
            orientation_wxyz=(2, 0, 0, 0),
            linear_velocity_m_s=(0, 0, 0),
            angular_velocity_rad_s=(0, 0, 0),
        )


def test_vehicle_command_rejects_negative_thrust() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        VehicleCommand(collective_thrust_newton=-1.0, body_torque_nm=(0, 0, 0))


def test_vehicle_command_separates_intent_and_motor_signals() -> None:
    command = VehicleCommand(
        intent=VehicleIntent(collective_thrust_newton=9.81, body_torque_nm=(0.1, 0.0, -0.1)),
        rotor_commands=(
            RotorCommand(rotor_name="front_left", thrust_newton=2.4),
            RotorCommand(rotor_name="front_right", thrust_newton=2.4),
        ),
        metadata={"source": "mixer"},
    )

    assert command.collective_thrust_newton == pytest.approx(9.81)
    assert command.body_torque_nm == pytest.approx((0.1, 0.0, -0.1))
    assert command.has_motor_signals is True
    assert command.rotor_commands[0].rotor_name == "front_left"
    assert command.metadata["source"] == "mixer"


def test_vehicle_observation_keeps_true_and_observed_states_separate() -> None:
    true_state = VehicleState(
        position_m=(0, 0, 0),
        orientation_wxyz=(1, 0, 0, 0),
        linear_velocity_m_s=(0, 0, 0),
        angular_velocity_rad_s=(0, 0, 0),
        time_s=1.0,
    )
    observed_state = VehicleState(
        position_m=(0.1, 0.0, 0.0),
        orientation_wxyz=(1, 0, 0, 0),
        linear_velocity_m_s=(0, 0, 0),
        angular_velocity_rad_s=(0, 0, 0),
        time_s=1.0,
    )

    observation = VehicleObservation(true_state=true_state, observed_state=observed_state, metadata={"sensor": "imu"})

    assert observation.true_state == true_state
    assert observation.observed_state == observed_state
    assert observation.state == observed_state
    assert observation.metadata["sensor"] == "imu"


def test_vehicle_observation_rejects_time_mismatch() -> None:
    true_state = VehicleState(
        position_m=(0, 0, 0),
        orientation_wxyz=(1, 0, 0, 0),
        linear_velocity_m_s=(0, 0, 0),
        angular_velocity_rad_s=(0, 0, 0),
        time_s=1.0,
    )
    observed_state = VehicleState(
        position_m=(0, 0, 0),
        orientation_wxyz=(1, 0, 0, 0),
        linear_velocity_m_s=(0, 0, 0),
        angular_velocity_rad_s=(0, 0, 0),
        time_s=1.1,
    )

    with pytest.raises(ValueError, match="same time"):
        VehicleObservation(true_state=true_state, observed_state=observed_state)


def test_rotor_geometry_validates_axis_and_direction() -> None:
    rotor = RotorGeometry(
        name="front_left",
        position_m=(0.1, 0.1, 0.0),
        axis_body=(0.0, 0.0, 1.0),
        spin_direction=1,
        thrust_coefficient_newton_per_rad_s2=1.0e-6,
        reaction_torque_coefficient_nm_per_newton=1.0e-7,
        motor_inertia_kg_m2=1.0e-5,
        time_constant_s=0.03,
        max_angular_speed_rad_s=2500.0,
        metadata={"motor": "A"},
    )

    assert rotor.axis_body == (0.0, 0.0, 1.0)
    assert rotor.spin_direction == 1
    assert rotor.metadata["motor"] == "A"

    with pytest.raises(ValueError, match="spin_direction"):
        RotorGeometry(
            name="bad",
            position_m=(0.0, 0.0, 0.0),
            axis_body=(0.0, 0.0, 1.0),
            spin_direction=0,
            thrust_coefficient_newton_per_rad_s2=1.0e-6,
        )


def test_trajectory_reference_validity_window_and_metadata() -> None:
    reference = TrajectoryReference(
        time_s=1.0,
        position_m=(0, 0, 1),
        velocity_m_s=(0, 0, 0),
        yaw_rad=0.0,
        valid_from_s=0.5,
        valid_until_s=2.0,
        acceleration_m_s2=[0, 0, 0],
        metadata={"family": "hover"},
    )

    assert reference.is_valid_at(1.5) is True
    assert reference.is_valid_at(2.5) is False
    assert reference.metadata["family"] == "hover"


def test_trajectory_reference_rejects_inverted_window() -> None:
    with pytest.raises(ValueError, match="greater than or equal"):
        TrajectoryReference(
            time_s=1.0,
            position_m=(0, 0, 1),
            velocity_m_s=(0, 0, 0),
            yaw_rad=0.0,
            valid_from_s=2.0,
            valid_until_s=1.0,
        )

