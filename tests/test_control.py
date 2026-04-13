from __future__ import annotations

import pytest

from simulador_multirotor.control import AttitudeLoopController, CascadedController, ControlTarget, PositionLoopController
from simulador_multirotor.core.contracts import TrajectoryReference, VehicleObservation, VehicleState


def make_observation(z_m: float = 0.0) -> VehicleObservation:
    return VehicleObservation(
        state=VehicleState(
            position_m=(0.0, 0.0, z_m),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
        )
    )


def make_reference(x_m: float = 0.0, y_m: float = 0.0, z_m: float = 1.0) -> TrajectoryReference:
    return TrajectoryReference(
        time_s=0.0,
        position_m=(x_m, y_m, z_m),
        velocity_m_s=(0.0, 0.0, 0.0),
        yaw_rad=0.0,
        valid_from_s=0.0,
    )


def test_cascaded_controller_consumes_observation_and_reference() -> None:
    controller = CascadedController()

    command = controller.update(make_observation(), make_reference())

    assert 0.0 <= command.collective_thrust_newton <= 20.0
    assert len(command.body_torque_nm) == 3


def test_outer_and_inner_loops_are_separable() -> None:
    position_loop = PositionLoopController()
    attitude_loop = AttitudeLoopController(
        mass_kg=1.0,
        gravity_m_s2=9.81,
        max_collective_thrust_newton=20.0,
        max_body_torque_nm=(0.3, 0.3, 0.2),
    )

    target = position_loop.compute_target(make_observation(), make_reference())
    command = attitude_loop.compute_command(make_observation().state, target)

    assert isinstance(target, ControlTarget)
    assert command.collective_thrust_newton <= 20.0
    assert all(abs(component) <= limit for component, limit in zip(command.body_torque_nm, (0.3, 0.3, 0.2)))


def test_controller_saturates_on_large_errors() -> None:
    controller = CascadedController()

    command = controller.update(make_observation(), make_reference(50.0, 50.0, 50.0))

    assert command.collective_thrust_newton == pytest.approx(20.0)
    assert all(abs(component) <= limit for component, limit in zip(command.body_torque_nm, (0.3, 0.3, 0.2)))

