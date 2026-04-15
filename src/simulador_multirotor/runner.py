"""Minimal end-to-end runner for the Foundation tracer bullet."""

from __future__ import annotations

from dataclasses import dataclass

from .control import ControllerContract
from .core.contracts import VehicleObservation
from .scenarios import SimulationScenario
from .telemetry import SimulationHistory, SimulationStep, TelemetryEvent, TrackingError


@dataclass(frozen=True, slots=True)
class SimulationRunner:
    def run(self, scenario: SimulationScenario, controller: ControllerContract | None = None) -> SimulationHistory:
        dynamics = scenario.build_dynamics()
        controller = scenario.build_controller() if controller is None else controller
        rng = scenario.build_rng()
        trajectory = scenario.build_trajectory()
        scenario_description = scenario.describe()
        state = scenario.initial_state
        time_s = state.time_s
        steps: list[SimulationStep] = []
        physics_dt_s = scenario.physics_dt_s
        control_dt_s = scenario.control_dt_s
        telemetry_dt_s = scenario.telemetry_dt_s
        next_control_time_s = time_s + control_dt_s
        next_telemetry_time_s = time_s + telemetry_dt_s
        pending_events: list[TelemetryEvent] = []

        initial_observed_state = scenario.disturbances.perturb_observation(state, rng)
        initial_observation = VehicleObservation(
            true_state=state,
            observed_state=initial_observed_state,
            metadata={
                "sample": "initial",
                "seed": scenario.seed,
                "trajectory_kind": trajectory.kind,
                "controller_kind": controller.kind,
                "control_time_s": time_s,
            },
        )
        current_command = controller.compute_action(initial_observation, trajectory.reference_at(time_s))
        current_command_time_s = time_s

        step_index = 0
        while time_s < scenario.time.duration_s - 1e-12:
            step_dt = min(physics_dt_s, scenario.time.duration_s - time_s)
            state = dynamics.step(state, current_command, step_dt)
            time_s = state.time_s
            reference = trajectory.reference_at(time_s)
            observed_state = scenario.disturbances.perturb_observation(state, rng)
            observation = VehicleObservation(
                true_state=state,
                observed_state=observed_state,
                metadata={
                    "step": step_index,
                    "seed": scenario.seed,
                    "trajectory_kind": trajectory.kind,
                    "controller_kind": controller.kind,
                    "control_time_s": current_command_time_s,
                },
            )
            error = TrackingError.from_tracking_state_and_reference(tracking_state=state, reference=reference)
            applied_command = dynamics.last_applied_command or current_command
            events: list[TelemetryEvent] = []
            if step_index == 0:
                pending_events.append(
                    TelemetryEvent(
                        kind="simulation_start",
                        message="simulation started",
                        metadata={
                            "scenario_name": scenario.metadata.name,
                            "seed": scenario.seed,
                            "controller_kind": controller.kind,
                            "controller_source": controller.source,
                            "disturbances": scenario.disturbances.physical_flags(),
                        },
                    )
                )
                if scenario.disturbances.enabled:
                    pending_events.append(
                        TelemetryEvent(
                            kind="disturbance_model_configured",
                            message="disturbance model configured from scenario",
                            metadata=scenario.disturbances.physical_flags(),
                        )
                    )
            if reference.metadata.get("trajectory_exhausted"):
                pending_events.append(
                    TelemetryEvent(
                        kind="trajectory_exhausted",
                        message="trajectory horizon reached",
                        metadata={
                            "trajectory_kind": trajectory.kind,
                            "trajectory_source": trajectory.source,
                            "controller_kind": controller.kind,
                        },
                    )
                )
            if time_s >= scenario.time.duration_s - 1e-12:
                pending_events.append(
                    TelemetryEvent(
                        kind="simulation_complete",
                        message="simulation completed",
                        metadata={"final_time_s": time_s},
                    )
                )
            should_log_telemetry = time_s >= next_telemetry_time_s - 1e-12
            if time_s >= scenario.time.duration_s - 1e-12:
                should_log_telemetry = True
            if should_log_telemetry:
                steps.append(
                    SimulationStep(
                        index=step_index,
                        time_s=time_s,
                        state=state,
                        observation=observation,
                        reference=reference,
                        error=error,
                        command=applied_command,
                        events=tuple(pending_events),
                        metadata={
                            "step_dt_s": step_dt,
                            "physics_dt_s": physics_dt_s,
                            "control_dt_s": control_dt_s,
                            "telemetry_dt_s": telemetry_dt_s,
                            "command_time_s": current_command_time_s,
                            "tracking_state_source": "true_state",
                            "trajectory_kind": trajectory.kind,
                            "controller_kind": controller.kind,
                            "controller_source": controller.source,
                        "disturbances": {
                            **scenario.disturbances.physical_flags(),
                            "wind_model": "ornstein_uhlenbeck",
                            "wind_sample_dt_s": step_dt,
                            "wind_base_velocity_m_s": dynamics.aerodynamics.last_wind_base_velocity_m_s,
                            "wind_gust_velocity_m_s": dynamics.aerodynamics.last_wind_gust_velocity_m_s,
                            "wind_sample_m_s": dynamics.aerodynamics.last_wind_velocity_m_s,
                            "parasitic_drag_force_newton": dynamics.aerodynamics.last_parasitic_drag_force_newton,
                            "induced_force_body_newton": dynamics.aerodynamics.last_induced_force_body_newton,
                        },
                    },
                    )
                )
                pending_events.clear()
                next_telemetry_time_s += telemetry_dt_s

            if time_s >= next_control_time_s - 1e-12:
                current_command = controller.compute_action(observation, reference)
                current_command_time_s = time_s
                next_control_time_s += control_dt_s
            step_index += 1

        return SimulationHistory(
            initial_state=scenario.initial_state,
            steps=tuple(steps),
            scenario_metadata=scenario_description if scenario.telemetry.record_scenario_metadata else {},
            vehicle_metadata=scenario_description.get("vehicle", {}),
            controller_metadata={
                "kind": controller.kind,
                "source": controller.source,
                "parameters": dict(controller.parameters),
            },
            telemetry_metadata={
                "record_scenario_metadata": scenario.telemetry.record_scenario_metadata,
                "detail_level": scenario.telemetry.detail_level,
                "sample_dt_s": scenario.telemetry.sample_dt_s,
                "physics_dt_s": physics_dt_s,
                "control_dt_s": control_dt_s,
                "telemetry_dt_s": telemetry_dt_s,
                "tracking_state_source": "true_state",
            },
        )


def run_minimal_simulation() -> SimulationHistory:
    from .scenarios import build_minimal_scenario

    runner = SimulationRunner()
    return runner.run(build_minimal_scenario())
