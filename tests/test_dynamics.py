from __future__ import annotations

import pytest

from simulador_multirotor.core.contracts import VehicleCommand, VehicleState
from simulador_multirotor.dynamics import RigidBody6DOFDynamics, RigidBodyParameters


def make_level_state() -> VehicleState:
    return VehicleState(
        position_m=(0.0, 0.0, 0.0),
        orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        linear_velocity_m_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_s=(0.0, 0.0, 0.0),
    )


def test_free_fall_matches_gravity() -> None:
    dynamics = RigidBody6DOFDynamics()

    next_state = dynamics.step(
        make_level_state(),
        VehicleCommand(collective_thrust_newton=0.0, body_torque_nm=(0.0, 0.0, 0.0)),
        0.1,
    )

    assert next_state.linear_velocity_m_s[2] == pytest.approx(-0.981, rel=1e-6)
    assert next_state.position_m[2] == pytest.approx(-0.04905, rel=1e-6)


def test_hover_thrust_keeps_state_nearly_stationary() -> None:
    parameters = RigidBodyParameters(mass_kg=1.0, gravity_m_s2=9.81)
    dynamics = RigidBody6DOFDynamics(parameters=parameters)

    next_state = dynamics.step(
        make_level_state(),
        VehicleCommand(collective_thrust_newton=9.81, body_torque_nm=(0.0, 0.0, 0.0)),
        0.1,
    )

    assert next_state.linear_velocity_m_s[2] == pytest.approx(0.0, abs=1e-9)
    assert next_state.position_m[2] == pytest.approx(0.0, abs=1e-9)


def test_dynamics_clamps_thrust_to_limits() -> None:
    parameters = RigidBodyParameters(mass_kg=1.0, gravity_m_s2=9.81, max_collective_thrust_newton=15.0)
    dynamics = RigidBody6DOFDynamics(parameters=parameters)

    next_state = dynamics.step(
        make_level_state(),
        VehicleCommand(collective_thrust_newton=100.0, body_torque_nm=(0.0, 0.0, 0.0)),
        0.1,
    )

    assert next_state.linear_velocity_m_s[2] == pytest.approx((15.0 - 9.81) * 0.1, rel=1e-6)


def test_dynamics_rejects_non_positive_dt() -> None:
    with pytest.raises(ValueError, match="positive finite number"):
        RigidBody6DOFDynamics().step(
            make_level_state(),
            VehicleCommand(collective_thrust_newton=0.0, body_torque_nm=(0.0, 0.0, 0.0)),
            0.0,
        )

