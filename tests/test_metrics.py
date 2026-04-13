from __future__ import annotations

import pytest

from simulador_multirotor.core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState
from simulador_multirotor.metrics import compare_tracking_metrics, compute_tracking_metrics
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import build_minimal_scenario
from simulador_multirotor.telemetry import SimulationHistory, SimulationStep, TrackingError


def _make_synthetic_history(position_targets: list[float], thrusts: list[float]) -> SimulationHistory:
    initial_state = VehicleState(
        position_m=(0.0, 0.0, 0.0),
        orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        linear_velocity_m_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_s=(0.0, 0.0, 0.0),
        time_s=0.0,
    )
    steps: list[SimulationStep] = []
    current_time = 0.0
    for index, (target_z, thrust) in enumerate(zip(position_targets, thrusts), start=1):
        current_time += 0.1
        observed_state = VehicleState(
            position_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            time_s=current_time,
        )
        reference = TrajectoryReference(
            time_s=current_time,
            position_m=(0.0, 0.0, target_z),
            velocity_m_s=(0.0, 0.0, 0.0),
            yaw_rad=0.0,
            valid_from_s=0.0,
        )
        observation = VehicleObservation(state=observed_state, metadata={"sample": index})
        error = TrackingError.from_state_and_reference(state=observed_state, reference=reference)
        command = VehicleCommand(collective_thrust_newton=thrust, body_torque_nm=(0.1, 0.2, 0.3))
        steps.append(
            SimulationStep(
                index=index,
                time_s=current_time,
                state=observed_state,
                observation=observation,
                reference=reference,
                error=error,
                command=command,
                metadata={"step_dt_s": 0.1},
            )
        )
    return SimulationHistory(
        initial_state=initial_state,
        steps=tuple(steps),
        telemetry_metadata={"detail_level": "standard"},
    )


def test_metrics_compute_on_real_execution() -> None:
    history = SimulationRunner().run(build_minimal_scenario())

    metrics = compute_tracking_metrics(history)

    assert metrics.sample_count == len(history.steps)
    assert metrics.duration_s == pytest.approx(history.final_time_s - history.initial_state.time_s)
    assert metrics.position_rmse_m >= 0.0
    assert metrics.mean_collective_thrust_newton > 0.0


def test_metrics_compare_homogeneous_synthetic_histories() -> None:
    baseline = _make_synthetic_history([1.0, 1.0], [1.5, 1.5])
    candidate = _make_synthetic_history([2.0, 2.0], [1.8, 1.8])

    baseline_metrics = compute_tracking_metrics(baseline)
    candidate_metrics = compute_tracking_metrics(candidate)
    comparison = compare_tracking_metrics(baseline_metrics, candidate_metrics)

    assert comparison.sample_count == 2
    assert comparison.position_rmse_delta_m > 0.0
    assert comparison.mean_collective_thrust_delta_newton > 0.0
