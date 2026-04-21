from __future__ import annotations

def test_package_imports_are_available() -> None:
    import simulador_multirotor
    import simulador_multirotor.app
    import simulador_multirotor.dataset
    import simulador_multirotor.control
    import simulador_multirotor.core
    import simulador_multirotor.dynamics
    import simulador_multirotor.metrics
    import simulador_multirotor.reporting
    import simulador_multirotor.robustness
    import simulador_multirotor.scenarios
    import simulador_multirotor.telemetry
    import simulador_multirotor.validation
    import simulador_multirotor.trajectories
    import simulador_multirotor.visualization

    assert simulador_multirotor.__version__ == "0.1.0"
    assert simulador_multirotor.dataset.PHASE2_DATASET_CONTRACT is not None
    assert simulador_multirotor.control.ControllerContract is not None
    assert simulador_multirotor.core.VehicleState is not None
    assert simulador_multirotor.dynamics.AerodynamicEnvironment is not None
    assert simulador_multirotor.dynamics.RigidBody6DOFDynamics is not None
    assert simulador_multirotor.scenarios.SimulationScenario is not None
    assert simulador_multirotor.metrics.TrackingMetrics is not None
    assert simulador_multirotor.reporting.generate_phase5_report is not None
    assert simulador_multirotor.robustness.build_ood_robustness_scenarios is not None
    assert simulador_multirotor.visualization.TelemetryArchive is not None
    assert simulador_multirotor.validation.build_pd_validation_scenario is not None
