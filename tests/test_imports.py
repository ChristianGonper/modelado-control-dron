from __future__ import annotations

def test_package_imports_are_available() -> None:
    import simulador_multirotor
    import simulador_multirotor.app
    import simulador_multirotor.control
    import simulador_multirotor.core
    import simulador_multirotor.metrics
    import simulador_multirotor.scenarios
    import simulador_multirotor.telemetry
    import simulador_multirotor.trajectories
    import simulador_multirotor.visualization

    assert simulador_multirotor.__version__ == "0.1.0"
    assert simulador_multirotor.core.VehicleState is not None
    assert simulador_multirotor.scenarios.SimulationScenario is not None
    assert simulador_multirotor.metrics.TrackingMetrics is not None
