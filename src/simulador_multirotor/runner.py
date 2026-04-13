"""Minimal end-to-end runner for the Foundation tracer bullet."""

from __future__ import annotations

from dataclasses import dataclass

from .core.contracts import VehicleObservation
from .scenarios import SimulationScenario
from .telemetry import SimulationHistory, SimulationStep, TelemetryEvent, TrackingError


@dataclass(frozen=True, slots=True)
class SimulationRunner:
    def run(self, scenario: SimulationScenario) -> SimulationHistory:
        dynamics = scenario.build_dynamics()
        controller = scenario.build_controller()
        rng = scenario.build_rng()
        trajectory = scenario.build_trajectory()
        state = scenario.initial_state
        time_s = state.time_s
        steps: list[SimulationStep] = []

        step_index = 0
        while time_s < scenario.time.duration_s - 1e-12:
            step_dt = min(scenario.time.dt_s, scenario.time.duration_s - time_s)
            reference = trajectory.reference_at(time_s)
            observed_state = scenario.disturbances.perturb_observation(state, rng)
            observation = VehicleObservation(
                state=observed_state,
                metadata={
                    "step": step_index,
                    "seed": scenario.seed,
                    "trajectory_kind": trajectory.kind,
                },
            )
            command = controller.update(observation, reference)
            state = dynamics.step(state, command, step_dt)
            time_s = state.time_s
            error = TrackingError.from_state_and_reference(state=observation.state, reference=reference)
            events: list[TelemetryEvent] = []
            if step_index == 0:
                events.append(
                    TelemetryEvent(
                        kind="simulation_start",
                        message="simulation started",
                        metadata={
                            "scenario_name": scenario.metadata.name,
                            "seed": scenario.seed,
                        },
                    )
                )
            if reference.metadata.get("trajectory_exhausted"):
                events.append(
                    TelemetryEvent(
                        kind="trajectory_exhausted",
                        message="trajectory horizon reached",
                        metadata={
                            "trajectory_kind": trajectory.kind,
                            "trajectory_source": trajectory.source,
                        },
                    )
                )
            if time_s >= scenario.time.duration_s - 1e-12:
                events.append(
                    TelemetryEvent(
                        kind="simulation_complete",
                        message="simulation completed",
                        metadata={"final_time_s": time_s},
                    )
                )
            steps.append(
                SimulationStep(
                    index=step_index,
                    time_s=time_s,
                    state=state,
                    observation=observation,
                    reference=reference,
                    error=error,
                    command=command,
                    events=tuple(events),
                    metadata={
                        "step_dt_s": step_dt,
                        "trajectory_kind": trajectory.kind,
                    },
                )
            )
            step_index += 1

        return SimulationHistory(
            initial_state=scenario.initial_state,
            steps=tuple(steps),
            scenario_metadata=scenario.describe() if scenario.telemetry.record_scenario_metadata else {},
            telemetry_metadata={
                "record_scenario_metadata": scenario.telemetry.record_scenario_metadata,
                "detail_level": scenario.telemetry.detail_level,
                "sample_dt_s": scenario.telemetry.sample_dt_s,
            },
        )


def run_minimal_simulation() -> SimulationHistory:
    from .scenarios import build_minimal_scenario

    runner = SimulationRunner()
    return runner.run(build_minimal_scenario())
