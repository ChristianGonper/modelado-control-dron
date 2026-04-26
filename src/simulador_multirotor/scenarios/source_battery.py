"""Phase 3 source telemetry battery built from the official baseline and PD controller."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

from ..core.contracts import VehicleState
from .minimal import BASELINE_MASS_KG, BASELINE_MAX_BODY_TORQUE_NM, BASELINE_MAX_COLLECTIVE_THRUST_NEWTON, BASELINE_PROFILE_ID, build_minimal_scenario
from .schema import (
    ScenarioControllerConfig,
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTelemetryConfig,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    SimulationScenario,
)


SOURCE_BATTERY_KEY = "source-telemetry-battery-v1"
SOURCE_BATTERY_NAME = "source-telemetry-battery-v1"
SOURCE_BATTERY_DESCRIPTION = (
    "Small reproducible source battery for Phase 3 dataset generation, derived from the official baseline and PD controller."
)
SOURCE_BATTERY_TAGS = ("baseline", "generic-drone", "phase-3", "source-battery", "pd")
SOURCE_BATTERY_GATE_ID = "pd-expert-gate-v1"
SOURCE_BATTERY_DURATION_S = 6.0
SOURCE_BATTERY_PHYSICS_DT_S = 0.02
SOURCE_BATTERY_CONTROL_DT_S = 0.04
SOURCE_BATTERY_TELEMETRY_DT_S = 0.02
SOURCE_BATTERY_DETAIL_LEVEL = "full"

_SOURCE_BATTERY_CONTROLLER_PARAMETERS: dict[str, object] = {
    "position_loop": {
        "mass_kg": BASELINE_MASS_KG,
        "gravity_m_s2": 9.81,
        "kp_position": (2.0, 2.0, 4.0),
        "kd_velocity": (1.2, 1.2, 2.5),
    },
    "attitude_loop": {
        "mass_kg": BASELINE_MASS_KG,
        "gravity_m_s2": 9.81,
        "max_collective_thrust_newton": BASELINE_MAX_COLLECTIVE_THRUST_NEWTON,
        "max_body_torque_nm": BASELINE_MAX_BODY_TORQUE_NM,
        "kp_attitude": (4.5, 4.5, 1.8),
        "kd_body_rate": (0.15, 0.15, 0.08),
        "max_tilt_rad": 0.6,
    },
}


@dataclass(frozen=True, slots=True)
class SourceBatteryScenarioSpec:
    episode_id: str
    scenario_name: str
    description: str
    seed: int
    trajectory: ScenarioTrajectoryConfig
    disturbances: ScenarioDisturbanceConfig
    initial_state: VehicleState
    tags: tuple[str, ...]


def _build_pd_controller_config() -> ScenarioControllerConfig:
    return ScenarioControllerConfig(kind="cascade", parameters=_SOURCE_BATTERY_CONTROLLER_PARAMETERS)


def _vehicle_state(
    position_m: tuple[float, float, float],
    *,
    linear_velocity_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0),
    angular_velocity_rad_s: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> VehicleState:
    return VehicleState(
        position_m=position_m,
        orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        linear_velocity_m_s=linear_velocity_m_s,
        angular_velocity_rad_s=angular_velocity_rad_s,
        time_s=0.0,
    )


def _circle_initial_state(*, center_m: tuple[float, float, float], radius_m: float, start_phase_rad: float) -> VehicleState:
    from math import cos, sin

    return _vehicle_state(
        (
            center_m[0] + radius_m * cos(start_phase_rad),
            center_m[1] + radius_m * sin(start_phase_rad),
            center_m[2],
        )
    )


def _lissajous_initial_state(
    *,
    center_m: tuple[float, float, float],
    amplitude_m: tuple[float, float, float],
    phase_rad: tuple[float, float, float],
) -> VehicleState:
    from math import sin

    return _vehicle_state(
        tuple(center + amplitude * sin(phase) for center, amplitude, phase in zip(center_m, amplitude_m, phase_rad))  # type: ignore[arg-type]
    )


def _source_battery_specifications() -> tuple[SourceBatteryScenarioSpec, ...]:
    circle_center = (0.0, 0.0, 1.05)
    lissajous_center = (0.0, 0.0, 1.1)
    circle_specs = (
        {
            "episode_id": "circle-wind-01",
            "scenario_name": "source-battery-circle-wind-01",
            "description": "Circle tracking under light wind and gusts.",
            "seed": 801,
            "trajectory": ScenarioTrajectoryConfig(
                kind="circle",
                target_position_m=circle_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": circle_center,
                    "radius_m": 0.8,
                    "angular_speed_rad_s": 0.75,
                    "start_phase_rad": 0.0,
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(1.0, 0.4, 0.0),
                wind_gust_std_m_s=(0.25, 0.25, 0.08),
                wind_gust_time_constant_s=0.18,
                observation_position_noise_std_m=0.01,
                observation_velocity_noise_std_m_s=0.015,
            ),
            "initial_state": _circle_initial_state(center_m=circle_center, radius_m=0.8, start_phase_rad=0.0),
            "tags": ("circle", "wind", "gusts", "source"),
        },
        {
            "episode_id": "circle-wind-02",
            "scenario_name": "source-battery-circle-wind-02",
            "description": "Circle tracking with faster angular motion.",
            "seed": 802,
            "trajectory": ScenarioTrajectoryConfig(
                kind="circle",
                target_position_m=circle_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": circle_center,
                    "radius_m": 1.0,
                    "angular_speed_rad_s": 0.95,
                    "start_phase_rad": 0.4,
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(0.8, -0.6, 0.05),
                wind_gust_std_m_s=(0.2, 0.2, 0.07),
                wind_gust_time_constant_s=0.18,
                observation_position_noise_std_m=0.01,
                observation_velocity_noise_std_m_s=0.015,
            ),
            "initial_state": _circle_initial_state(center_m=circle_center, radius_m=1.0, start_phase_rad=0.4),
            "tags": ("circle", "wind", "gusts", "source"),
        },
        {
            "episode_id": "circle-wind-03",
            "scenario_name": "source-battery-circle-wind-03",
            "description": "Circle tracking with a larger radius and phase offset.",
            "seed": 803,
            "trajectory": ScenarioTrajectoryConfig(
                kind="circle",
                target_position_m=circle_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": circle_center,
                    "radius_m": 1.2,
                    "angular_speed_rad_s": 0.85,
                    "start_phase_rad": 0.8,
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(1.2, 0.2, 0.0),
                wind_gust_std_m_s=(0.3, 0.22, 0.08),
                wind_gust_time_constant_s=0.18,
                observation_position_noise_std_m=0.01,
                observation_velocity_noise_std_m_s=0.015,
            ),
            "initial_state": _circle_initial_state(center_m=circle_center, radius_m=1.2, start_phase_rad=0.8),
            "tags": ("circle", "wind", "gusts", "source"),
        },
        {
            "episode_id": "circle-wind-04",
            "scenario_name": "source-battery-circle-wind-04",
            "description": "Circle tracking with a compact orbit and crosswind.",
            "seed": 804,
            "trajectory": ScenarioTrajectoryConfig(
                kind="circle",
                target_position_m=circle_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": circle_center,
                    "radius_m": 0.65,
                    "angular_speed_rad_s": 1.05,
                    "start_phase_rad": 1.1,
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(0.6, 0.9, 0.0),
                wind_gust_std_m_s=(0.22, 0.28, 0.08),
                wind_gust_time_constant_s=0.18,
                observation_position_noise_std_m=0.01,
                observation_velocity_noise_std_m_s=0.015,
            ),
            "initial_state": _circle_initial_state(center_m=circle_center, radius_m=0.65, start_phase_rad=1.1),
            "tags": ("circle", "wind", "gusts", "source"),
        },
        {
            "episode_id": "circle-wind-05",
            "scenario_name": "source-battery-circle-wind-05",
            "description": "Circle tracking with the most aggressive angular rate in the battery.",
            "seed": 805,
            "trajectory": ScenarioTrajectoryConfig(
                kind="circle",
                target_position_m=circle_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": circle_center,
                    "radius_m": 1.4,
                    "angular_speed_rad_s": 1.1,
                    "start_phase_rad": 1.35,
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(1.1, -0.5, 0.1),
                wind_gust_std_m_s=(0.28, 0.25, 0.09),
                wind_gust_time_constant_s=0.18,
                observation_position_noise_std_m=0.01,
                observation_velocity_noise_std_m_s=0.015,
            ),
            "initial_state": _circle_initial_state(center_m=circle_center, radius_m=1.4, start_phase_rad=1.35),
            "tags": ("circle", "wind", "gusts", "source"),
        },
    )
    lissajous_specs = (
        {
            "episode_id": "lissajous-noise-01",
            "scenario_name": "source-battery-lissajous-noise-01",
            "description": "Lissajous tracking with observation noise and lift losses.",
            "seed": 811,
            "trajectory": ScenarioTrajectoryConfig(
                kind="lissajous",
                target_position_m=lissajous_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": lissajous_center,
                    "amplitude_m": (0.8, 0.6, 0.35),
                    "frequency_rad_s": (1.0, 1.7, 2.8),
                    "phase_rad": (0.0, 0.9, 0.2),
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                induced_hover_enabled=True,
                induced_hover_loss_ratio=0.12,
                wind_velocity_m_s=(-0.7, 0.8, 0.15),
                wind_gust_std_m_s=(0.28, 0.28, 0.12),
                wind_gust_time_constant_s=0.2,
                observation_position_noise_std_m=0.015,
                observation_velocity_noise_std_m_s=0.02,
            ),
            "initial_state": _lissajous_initial_state(
                center_m=lissajous_center,
                amplitude_m=(0.8, 0.6, 0.35),
                phase_rad=(0.0, 0.9, 0.2),
            ),
            "tags": ("lissajous", "noise", "aerodynamic", "source"),
        },
        {
            "episode_id": "lissajous-noise-02",
            "scenario_name": "source-battery-lissajous-noise-02",
            "description": "Lissajous tracking with stronger lateral motion.",
            "seed": 812,
            "trajectory": ScenarioTrajectoryConfig(
                kind="lissajous",
                target_position_m=lissajous_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": lissajous_center,
                    "amplitude_m": (0.95, 0.7, 0.4),
                    "frequency_rad_s": (1.15, 1.9, 3.1),
                    "phase_rad": (0.2, 1.1, 0.4),
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                induced_hover_enabled=True,
                induced_hover_loss_ratio=0.14,
                wind_velocity_m_s=(-0.9, 0.6, 0.15),
                wind_gust_std_m_s=(0.3, 0.28, 0.12),
                wind_gust_time_constant_s=0.2,
                observation_position_noise_std_m=0.015,
                observation_velocity_noise_std_m_s=0.02,
            ),
            "initial_state": _lissajous_initial_state(
                center_m=lissajous_center,
                amplitude_m=(0.95, 0.7, 0.4),
                phase_rad=(0.2, 1.1, 0.4),
            ),
            "tags": ("lissajous", "noise", "aerodynamic", "source"),
        },
        {
            "episode_id": "lissajous-noise-03",
            "scenario_name": "source-battery-lissajous-noise-03",
            "description": "Lissajous tracking with a slightly more aggressive vertical component.",
            "seed": 813,
            "trajectory": ScenarioTrajectoryConfig(
                kind="lissajous",
                target_position_m=lissajous_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": lissajous_center,
                    "amplitude_m": (0.9, 0.75, 0.5),
                    "frequency_rad_s": (1.0, 1.8, 3.2),
                    "phase_rad": (0.35, 0.8, 0.5),
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                induced_hover_enabled=True,
                induced_hover_loss_ratio=0.14,
                wind_velocity_m_s=(-0.8, 0.7, 0.2),
                wind_gust_std_m_s=(0.28, 0.32, 0.14),
                wind_gust_time_constant_s=0.2,
                observation_position_noise_std_m=0.015,
                observation_velocity_noise_std_m_s=0.02,
            ),
            "initial_state": _lissajous_initial_state(
                center_m=lissajous_center,
                amplitude_m=(0.9, 0.75, 0.5),
                phase_rad=(0.35, 0.8, 0.5),
            ),
            "tags": ("lissajous", "noise", "aerodynamic", "source"),
        },
        {
            "episode_id": "lissajous-noise-04",
            "scenario_name": "source-battery-lissajous-noise-04",
            "description": "Lissajous tracking with balanced lateral amplitudes.",
            "seed": 814,
            "trajectory": ScenarioTrajectoryConfig(
                kind="lissajous",
                target_position_m=lissajous_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": lissajous_center,
                    "amplitude_m": (0.75, 0.8, 0.45),
                    "frequency_rad_s": (1.25, 2.0, 3.0),
                    "phase_rad": (0.5, 1.0, 0.6),
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                induced_hover_enabled=True,
                induced_hover_loss_ratio=0.12,
                wind_velocity_m_s=(-1.0, 0.5, 0.15),
                wind_gust_std_m_s=(0.3, 0.28, 0.12),
                wind_gust_time_constant_s=0.2,
                observation_position_noise_std_m=0.015,
                observation_velocity_noise_std_m_s=0.02,
            ),
            "initial_state": _lissajous_initial_state(
                center_m=lissajous_center,
                amplitude_m=(0.75, 0.8, 0.45),
                phase_rad=(0.5, 1.0, 0.6),
            ),
            "tags": ("lissajous", "noise", "aerodynamic", "source"),
        },
        {
            "episode_id": "lissajous-noise-05",
            "scenario_name": "source-battery-lissajous-noise-05",
            "description": "Lissajous tracking with the broadest envelope in the battery.",
            "seed": 815,
            "trajectory": ScenarioTrajectoryConfig(
                kind="lissajous",
                target_position_m=lissajous_center,
                valid_until_s=SOURCE_BATTERY_DURATION_S,
                source="native",
                parameters={
                    "center_m": lissajous_center,
                    "amplitude_m": (1.05, 0.7, 0.5),
                    "frequency_rad_s": (1.35, 2.1, 3.3),
                    "phase_rad": (0.6, 1.2, 0.75),
                    "source_battery_key": SOURCE_BATTERY_KEY,
                },
            ),
            "disturbances": ScenarioDisturbanceConfig(
                enabled=True,
                induced_hover_enabled=True,
                induced_hover_loss_ratio=0.15,
                wind_velocity_m_s=(-0.85, 0.65, 0.2),
                wind_gust_std_m_s=(0.32, 0.3, 0.14),
                wind_gust_time_constant_s=0.2,
                observation_position_noise_std_m=0.015,
                observation_velocity_noise_std_m_s=0.02,
            ),
            "initial_state": _lissajous_initial_state(
                center_m=lissajous_center,
                amplitude_m=(1.05, 0.7, 0.5),
                phase_rad=(0.6, 1.2, 0.75),
            ),
            "tags": ("lissajous", "noise", "aerodynamic", "source"),
        },
    )
    return tuple(SourceBatteryScenarioSpec(**spec) for spec in circle_specs + lissajous_specs)


def build_source_battery_scenarios() -> tuple[SimulationScenario, ...]:
    """Build the reproducible Phase 3 source battery from the official baseline and PD controller."""

    scenarios: list[SimulationScenario] = []
    for spec in _source_battery_specifications():
        scenario = replace(
            build_minimal_scenario(seed=spec.seed),
            initial_state=spec.initial_state,
            time=ScenarioTimeConfig(
                duration_s=SOURCE_BATTERY_DURATION_S,
                physics_dt_s=SOURCE_BATTERY_PHYSICS_DT_S,
                control_dt_s=SOURCE_BATTERY_CONTROL_DT_S,
                telemetry_dt_s=SOURCE_BATTERY_TELEMETRY_DT_S,
            ),
            trajectory=spec.trajectory,
            controller=_build_pd_controller_config(),
            disturbances=spec.disturbances,
            telemetry=ScenarioTelemetryConfig(
                record_scenario_metadata=True,
                detail_level=SOURCE_BATTERY_DETAIL_LEVEL,
                sample_dt_s=SOURCE_BATTERY_TELEMETRY_DT_S,
            ),
            metadata=ScenarioMetadata(
                name=spec.scenario_name,
                description=spec.description,
                seed=spec.seed,
                tags=SOURCE_BATTERY_TAGS + spec.tags,
            ),
        )
        scenarios.append(scenario)
    return tuple(scenarios)


def source_battery_protocol_summary() -> dict[str, object]:
    """Describe the documented protocol used to generate the source battery."""

    scenarios = build_source_battery_scenarios()
    return {
        "source_battery_key": SOURCE_BATTERY_KEY,
        "source_battery_name": SOURCE_BATTERY_NAME,
        "related_validation_gate_id": SOURCE_BATTERY_GATE_ID,
        "baseline_profile_id": BASELINE_PROFILE_ID,
        "controller_kind": "cascade",
        "controller_source": "pid",
        "duration_s": SOURCE_BATTERY_DURATION_S,
        "physics_dt_s": SOURCE_BATTERY_PHYSICS_DT_S,
        "control_dt_s": SOURCE_BATTERY_CONTROL_DT_S,
        "telemetry_dt_s": SOURCE_BATTERY_TELEMETRY_DT_S,
        "scenario_count": len(scenarios),
        "trajectory_kinds": sorted({scenario.trajectory.kind for scenario in scenarios}),
        "scenario_names": [scenario.metadata.name for scenario in scenarios],
    }
