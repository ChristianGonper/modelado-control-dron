from __future__ import annotations

import pytest

from simulador_multirotor.core.contracts import TrajectoryReference, VehicleCommand, VehicleState


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

