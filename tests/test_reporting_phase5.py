from __future__ import annotations

import json

import pytest

from simulador_multirotor.metrics import compare_tracking_metrics, compute_tracking_metrics
from simulador_multirotor.reporting import generate_phase5_report, select_best_neural_model
from simulador_multirotor.core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState
from simulador_multirotor.telemetry import SimulationHistory, SimulationStep, TrackingError


def _make_history(
    *,
    position_targets: list[float],
    velocity_targets: list[float],
    yaw_targets: list[float],
    thrusts: list[float],
    torques: list[tuple[float, float, float]],
    dt: float = 0.1,
) -> SimulationHistory:
    initial_state = VehicleState(
        position_m=(0.0, 0.0, 0.0),
        orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        linear_velocity_m_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_s=(0.0, 0.0, 0.0),
        time_s=0.0,
    )
    steps: list[SimulationStep] = []
    current_time = 0.0
    for index, (position_target, velocity_target, yaw_target, thrust, torque) in enumerate(
        zip(position_targets, velocity_targets, yaw_targets, thrusts, torques, strict=True),
        start=1,
    ):
        current_time += dt
        state = VehicleState(
            position_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_m_s=(0.0, 0.0, 0.0),
            angular_velocity_rad_s=(0.0, 0.0, 0.0),
            time_s=current_time,
        )
        reference = TrajectoryReference(
            time_s=current_time,
            position_m=(position_target, 0.0, 0.0),
            velocity_m_s=(0.0, velocity_target, 0.0),
            yaw_rad=yaw_target,
            valid_from_s=0.0,
        )
        observation = VehicleObservation(true_state=state, observed_state=state, metadata={"sample": index})
        error = TrackingError.from_state_and_reference(state=state, reference=reference)
        command = VehicleCommand(collective_thrust_newton=thrust, body_torque_nm=torque)
        steps.append(
            SimulationStep(
                index=index,
                time_s=current_time,
                state=state,
                observation=observation,
                reference=reference,
                error=error,
                command=command,
                metadata={"step_dt_s": dt},
            )
        )
    return SimulationHistory(initial_state=initial_state, steps=tuple(steps), telemetry_metadata={"detail_level": "full"})


def _controller_payload(
    history: SimulationHistory,
    *,
    model_key: str,
    controller_kind: str,
    controller_source: str,
    cpu_mean: float,
) -> dict[str, object]:
    metrics = compute_tracking_metrics(history).to_dict()
    return {
        "controller_kind": controller_kind,
        "controller_source": controller_source,
        "metrics": {**metrics, "cpu_inference_time_s_mean": cpu_mean},
        "trace": {
            "time_s": [step.time_s for step in history.steps],
            "state_position_m": [step.state.position_m for step in history.steps],
            "reference_position_m": [step.reference.position_m for step in history.steps],
            "position_error_norm_m": [step.position_error_norm_m for step in history.steps],
            "velocity_error_norm_m_s": [step.velocity_error_norm_m_s for step in history.steps],
            "yaw_error_rad": [step.error.yaw_rad for step in history.steps],
            "collective_thrust_newton": [step.command.collective_thrust_newton for step in history.steps],
            "body_torque_nm": [step.command.body_torque_nm for step in history.steps],
        },
    }


def _benchmark_payload() -> dict[str, object]:
    scenario_a = {
        "metadata": {"name": "hover-a"},
        "trajectory": {"kind": "hover"},
    }
    scenario_b = {
        "metadata": {"name": "hover-b"},
        "trajectory": {"kind": "hover"},
    }

    baseline_a = _controller_payload(
        _make_history(
            position_targets=[1.0, 1.0],
            velocity_targets=[1.0, 1.0],
            yaw_targets=[0.3, 0.3],
            thrusts=[1.5, 1.5],
            torques=[(0.2, 0.2, 0.3), (0.3, 0.2, 0.4)],
        ),
        model_key="baseline",
        controller_kind="cascade",
        controller_source="classic",
        cpu_mean=0.004,
    )
    mlp_a = _controller_payload(
        _make_history(
            position_targets=[0.8, 0.8],
            velocity_targets=[0.8, 0.8],
            yaw_targets=[0.2, 0.2],
            thrusts=[1.2, 1.15],
            torques=[(0.15, 0.14, 0.2), (0.16, 0.14, 0.21)],
        ),
        model_key="mlp",
        controller_kind="mlp",
        controller_source="torch",
        cpu_mean=0.0025,
    )
    gru_a = _controller_payload(
        _make_history(
            position_targets=[0.4, 0.4],
            velocity_targets=[0.4, 0.4],
            yaw_targets=[0.1, 0.1],
            thrusts=[1.0, 1.0],
            torques=[(0.08, 0.07, 0.12), (0.08, 0.07, 0.12)],
        ),
        model_key="gru",
        controller_kind="gru",
        controller_source="torch",
        cpu_mean=0.0018,
    )
    lstm_a = _controller_payload(
        _make_history(
            position_targets=[0.6, 0.6],
            velocity_targets=[0.6, 0.6],
            yaw_targets=[0.15, 0.15],
            thrusts=[1.1, 1.05],
            torques=[(0.12, 0.11, 0.17), (0.13, 0.12, 0.19)],
        ),
        model_key="lstm",
        controller_kind="lstm",
        controller_source="torch",
        cpu_mean=0.0030,
    )

    baseline_b = _controller_payload(
        _make_history(
            position_targets=[1.2, 1.2],
            velocity_targets=[1.1, 1.1],
            yaw_targets=[0.35, 0.35],
            thrusts=[1.55, 1.55],
            torques=[(0.22, 0.21, 0.31), (0.33, 0.22, 0.42)],
        ),
        model_key="baseline",
        controller_kind="cascade",
        controller_source="classic",
        cpu_mean=0.0042,
    )
    mlp_b = _controller_payload(
        _make_history(
            position_targets=[0.7, 0.7],
            velocity_targets=[0.7, 0.7],
            yaw_targets=[0.18, 0.18],
            thrusts=[1.18, 1.12],
            torques=[(0.14, 0.13, 0.19), (0.15, 0.13, 0.2)],
        ),
        model_key="mlp",
        controller_kind="mlp",
        controller_source="torch",
        cpu_mean=0.0026,
    )
    gru_b = _controller_payload(
        _make_history(
            position_targets=[0.5, 0.5],
            velocity_targets=[0.5, 0.5],
            yaw_targets=[0.12, 0.12],
            thrusts=[0.98, 0.98],
            torques=[(0.07, 0.07, 0.11), (0.07, 0.07, 0.11)],
        ),
        model_key="gru",
        controller_kind="gru",
        controller_source="torch",
        cpu_mean=0.0017,
    )
    lstm_b = _controller_payload(
        _make_history(
            position_targets=[0.65, 0.65],
            velocity_targets=[0.65, 0.65],
            yaw_targets=[0.16, 0.16],
            thrusts=[1.08, 1.03],
            torques=[(0.11, 0.11, 0.16), (0.12, 0.11, 0.18)],
        ),
        model_key="lstm",
        controller_kind="lstm",
        controller_source="torch",
        cpu_mean=0.0029,
    )

    return {
        "checkpoint_paths": {
            "mlp": "mlp.pt",
            "gru": "gru.pt",
            "lstm": "lstm.pt",
        },
        "output_path": "benchmark.json",
        "results": [
            {
                "scenario": scenario_a,
                "baseline": baseline_a,
                "mlp": mlp_a,
                "gru": gru_a,
                "lstm": lstm_a,
                "comparisons": {},
            },
            {
                "scenario": scenario_b,
                "baseline": baseline_b,
                "mlp": mlp_b,
                "gru": gru_b,
                "lstm": lstm_b,
                "comparisons": {},
            },
        ],
    }


def test_phase5_metrics_include_provenance_and_error_integrals() -> None:
    history = _make_history(
        position_targets=[1.0, 2.0],
        velocity_targets=[1.0, 2.0],
        yaw_targets=[0.2, 0.4],
        thrusts=[1.0, 1.5],
        torques=[(0.1, 0.2, 0.3), (0.4, 0.5, 0.6)],
    )

    metrics = compute_tracking_metrics(history)

    assert metrics.control_observation_source == "observed_state"
    assert metrics.tracking_state_source == "true_state"
    assert metrics.position_mae_m == pytest.approx(1.5)
    assert metrics.position_iae_m_s == pytest.approx(0.3)
    assert metrics.position_ise_m2_s == pytest.approx(0.5)
    assert metrics.velocity_mae_m_s == pytest.approx(1.5)
    assert metrics.yaw_mae_rad == pytest.approx(0.3)
    assert metrics.collective_thrust_total_variation_newton == pytest.approx(0.5)
    assert metrics.torque_step_rms_nm[0] > 0.0


def test_phase5_metric_comparison_keeps_provenance_and_deltas() -> None:
    baseline = compute_tracking_metrics(
        _make_history(
            position_targets=[1.0, 1.0],
            velocity_targets=[1.0, 1.0],
            yaw_targets=[0.2, 0.2],
            thrusts=[1.0, 1.0],
            torques=[(0.1, 0.1, 0.1), (0.1, 0.1, 0.1)],
        )
    )
    candidate = compute_tracking_metrics(
        _make_history(
            position_targets=[0.5, 0.5],
            velocity_targets=[0.5, 0.5],
            yaw_targets=[0.1, 0.1],
            thrusts=[0.9, 0.95],
            torques=[(0.08, 0.08, 0.08), (0.09, 0.09, 0.09)],
        )
    )

    comparison = compare_tracking_metrics(baseline, candidate)

    assert comparison.control_observation_source == "observed_state"
    assert comparison.tracking_state_source == "true_state"
    assert comparison.position_mae_delta_m < 0.0
    assert comparison.position_iae_delta_m_s < 0.0
    assert comparison.collective_thrust_total_variation_delta_newton > 0.0


def test_phase5_reporting_generates_table_figures_and_selection(tmp_path) -> None:
    payload = _benchmark_payload()
    report_dir = tmp_path / "phase5-report"

    bundle = generate_phase5_report(payload, report_dir)
    selection = json.loads(bundle.selection_path.read_text(encoding="utf-8"))
    table_text = bundle.table_path.read_text(encoding="utf-8")
    report_text = bundle.report_path.read_text(encoding="utf-8")

    assert bundle.table_path.exists()
    assert bundle.report_path.exists()
    assert bundle.selection_path.exists()
    assert selection["selected_model_key"] == "gru"
    assert "precision" in selection["score_breakdown"]
    assert "observed_state" in table_text
    assert "true_state" in report_text
    assert "baseline" in table_text
    assert "mlp" in table_text
    assert "gru" in table_text
    assert "lstm" in table_text
    assert set(bundle.figure_paths) == {"hover-a", "hover-b"}
    for scenario_paths in bundle.figure_paths.values():
        assert set(scenario_paths) == {"trajectory", "temporal_error", "control_behavior"}
        for path in scenario_paths.values():
            assert path.exists()
            assert path.stat().st_size > 0
