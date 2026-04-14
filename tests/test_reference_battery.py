from __future__ import annotations

import pytest

from simulador_multirotor.metrics import compare_tracking_metrics, compute_tracking_metrics
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import load_simulation_scenario, reference_scenario_path


def _run_reference(name: str):
    scenario = load_simulation_scenario(reference_scenario_path(name))
    history = SimulationRunner().run(scenario)
    metrics = compute_tracking_metrics(history)
    return history, metrics


def test_reference_hover_regression() -> None:
    history, metrics = _run_reference("hover")

    assert metrics.sample_count == 40
    assert metrics.duration_s == pytest.approx(1.6, abs=1e-12)
    assert metrics.position_rmse_m < 1.0
    assert metrics.final_position_error_m < 0.1
    assert metrics.mean_collective_thrust_newton == pytest.approx(9.81, abs=0.5)
    assert history.steps[0].reference.metadata["trajectory_kind"] == "hover"


def test_reference_angular_maneuver_regression() -> None:
    history, metrics = _run_reference("angular_maneuver")

    assert metrics.sample_count == 40
    assert metrics.duration_s == pytest.approx(1.6, abs=1e-12)
    assert metrics.position_rmse_m > 4.0
    assert metrics.yaw_rmse_rad > 1.0
    assert metrics.final_yaw_error_rad > 2.0
    assert max(abs(step.command.body_torque_nm[2]) for step in history.steps) > 1e-6
    assert history.steps[0].reference.metadata["trajectory_kind"] == "circle"


def test_reference_perturbation_regression() -> None:
    _, hover_metrics = _run_reference("hover")
    perturb_history, perturb_metrics = _run_reference("perturbation")

    comparison = compare_tracking_metrics(hover_metrics, perturb_metrics)

    assert perturb_metrics.position_rmse_m > hover_metrics.position_rmse_m
    assert comparison.position_rmse_delta_m > 1.0
    assert perturb_history.steps[0].metadata["disturbances"]["wind_model"] == "ornstein_uhlenbeck"
    assert perturb_history.steps[0].metadata["disturbances"]["wind_base_velocity_m_s"] == (0.25, -0.12, 0.0)


def test_reference_dt_comparison_regression() -> None:
    coarse_history, coarse_metrics = _run_reference("dt_comparison_coarse")
    fine_history, fine_metrics = _run_reference("dt_comparison_fine")

    comparison = compare_tracking_metrics(coarse_metrics, fine_metrics)

    assert coarse_metrics.sample_count == fine_metrics.sample_count == 40
    assert coarse_metrics.duration_s == pytest.approx(fine_metrics.duration_s, abs=1e-12)
    assert fine_metrics.position_rmse_m < coarse_metrics.position_rmse_m
    assert comparison.position_rmse_delta_m < 0.0
    assert abs(comparison.position_rmse_delta_m) < 2.0
    assert coarse_history.steps[0].reference.metadata["trajectory_kind"] == "hover"
    assert fine_history.steps[0].reference.metadata["trajectory_kind"] == "hover"
