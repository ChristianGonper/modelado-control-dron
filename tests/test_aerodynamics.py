from __future__ import annotations

from dataclasses import replace
from math import isfinite

import pytest

from simulador_multirotor.core.contracts import VehicleCommand, VehicleState
from simulador_multirotor.dynamics import AerodynamicEnvironment, RigidBody6DOFDynamics, RigidBodyParameters
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import ScenarioDisturbanceConfig, ScenarioMetadata, build_minimal_scenario


def make_level_state(*, velocity_x_m_s: float = 0.0) -> VehicleState:
    return VehicleState(
        position_m=(0.0, 0.0, 0.0),
        orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        linear_velocity_m_s=(velocity_x_m_s, 0.0, 0.0),
        angular_velocity_rad_s=(0.0, 0.0, 0.0),
    )


def _gust_energy(environment: AerodynamicEnvironment, *, dt_s: float, samples: int, burn_in: int = 0) -> float:
    energies: list[float] = []
    for index in range(samples):
        wind = environment.sample_wind_velocity(dt_s)
        if index < burn_in:
            continue
        gust = tuple(component - base for component, base in zip(wind, environment.wind_velocity_m_s))
        energies.append(sum(component * component for component in gust))
    return sum(energies) / len(energies)


def test_parasitic_drag_opposes_motion_and_is_switchable() -> None:
    command = VehicleCommand(collective_thrust_newton=0.0, body_torque_nm=(0.0, 0.0, 0.0))
    state = make_level_state(velocity_x_m_s=5.0)

    nominal = RigidBody6DOFDynamics().step(state, command, 0.1)
    with_drag = RigidBody6DOFDynamics(
        parameters=RigidBodyParameters(parasitic_drag_area_m2=0.25),
        aerodynamics=AerodynamicEnvironment(
            parasitic_drag_enabled=True,
            parasitic_drag_area_m2=0.25,
        ),
    ).step(state, command, 0.1)

    assert with_drag.linear_velocity_m_s[0] < nominal.linear_velocity_m_s[0]
    assert with_drag.linear_velocity_m_s[0] < state.linear_velocity_m_s[0]
    assert with_drag.position_m[0] < nominal.position_m[0]


def test_induced_hover_term_reduces_effective_lift_in_hover() -> None:
    command = VehicleCommand(collective_thrust_newton=9.81, body_torque_nm=(0.0, 0.0, 0.0))
    state = make_level_state()

    nominal = RigidBody6DOFDynamics().step(state, command, 0.1)
    with_induced = RigidBody6DOFDynamics(
        parameters=RigidBodyParameters(induced_hover_loss_ratio=0.25),
        aerodynamics=AerodynamicEnvironment(
            induced_hover_enabled=True,
            induced_hover_loss_ratio=0.25,
        ),
    ).step(state, command, 0.1)

    assert with_induced.linear_velocity_m_s[2] < nominal.linear_velocity_m_s[2]
    assert with_induced.position_m[2] < nominal.position_m[2]


def test_perturbed_runner_is_reproducible_and_respects_basic_bounds() -> None:
    scenario = replace(
        build_minimal_scenario(),
        metadata=ScenarioMetadata(name="gusty-hover", seed=23, tags=("phase-5",)),
        disturbances=ScenarioDisturbanceConfig(
            enabled=True,
            parasitic_drag_enabled=True,
            induced_hover_enabled=True,
            wind_velocity_m_s=(0.5, 0.0, 0.0),
            wind_gust_std_m_s=(0.05, 0.0, 0.0),
            parasitic_drag_area_m2=0.08,
            induced_hover_loss_ratio=0.08,
            observation_position_noise_std_m=0.01,
            observation_velocity_noise_std_m_s=0.01,
        ),
    )

    first = SimulationRunner().run(scenario)
    second = SimulationRunner().run(scenario)
    different = SimulationRunner().run(replace(scenario, metadata=ScenarioMetadata(name="gusty-hover", seed=24)))

    assert first == second
    assert first != different
    assert first.final_time_s == pytest.approx(scenario.duration_s, abs=1e-12)
    assert first.steps[0].events[0].metadata["disturbances"]["parasitic_drag_enabled"] is True
    assert any(event.kind == "disturbance_model_configured" for event in first.steps[0].events)

    for step in first.steps:
        assert all(isfinite(component) for component in step.state.position_m)
        assert all(isfinite(component) for component in step.state.linear_velocity_m_s)
        assert all(isfinite(component) for component in step.state.angular_velocity_rad_s)
        quaternion_norm = sum(component * component for component in step.state.orientation_wxyz)
        assert quaternion_norm == pytest.approx(1.0, abs=1e-9)
        assert step.metadata["disturbances"]["wind_model"] == "ornstein_uhlenbeck"
        assert step.metadata["disturbances"]["wind_sample_dt_s"] == pytest.approx(step.metadata["step_dt_s"])
        assert "wind_base_velocity_m_s" in step.metadata["disturbances"]


def test_wind_process_is_seed_reproducible_and_dt_invariant() -> None:
    base_kwargs = dict(
        wind_velocity_m_s=(0.2, -0.1, 0.05),
        wind_gust_std_m_s=(0.15, 0.15, 0.15),
        wind_gust_time_constant_s=0.2,
        seed=123,
    )
    dt_small = 0.01
    dt_large = 0.04

    first = AerodynamicEnvironment(**base_kwargs)
    second = AerodynamicEnvironment(**base_kwargs)
    assert [first.sample_wind_velocity(dt_small) for _ in range(32)] == [second.sample_wind_velocity(dt_small) for _ in range(32)]

    energy_small = _gust_energy(AerodynamicEnvironment(**base_kwargs), dt_s=dt_small, samples=4000, burn_in=500)
    energy_large = _gust_energy(AerodynamicEnvironment(**base_kwargs), dt_s=dt_large, samples=1000, burn_in=125)
    expected_energy = 3.0 * (0.15**2)

    assert energy_small == pytest.approx(expected_energy, rel=0.2)
    assert energy_large == pytest.approx(expected_energy, rel=0.2)
    assert energy_small == pytest.approx(energy_large, rel=0.15)
