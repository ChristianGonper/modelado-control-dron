"""Out-of-distribution robustness scenarios for Phase 6."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .scenarios import (
    ScenarioDisturbanceConfig,
    ScenarioMetadata,
    ScenarioTimeConfig,
    ScenarioTrajectoryConfig,
    SimulationScenario,
    build_minimal_scenario,
)

OOD_ROBUSTNESS_SCENARIO_SET_KEY = "ood-robustness-v1"


@dataclass(frozen=True, slots=True)
class RobustnessScenarioBundle:
    scenario_set_key: str
    scenarios: tuple[SimulationScenario, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_set_key": self.scenario_set_key,
            "scenarios": [scenario.describe() for scenario in self.scenarios],
        }


def _with_ood_metadata(
    scenario: SimulationScenario,
    *,
    name: str,
    description: str,
    seed: int,
    tags: tuple[str, ...],
) -> SimulationScenario:
    return replace(
        scenario,
        metadata=ScenarioMetadata(
            name=name,
            description=description,
            seed=seed,
            tags=tags,
        ),
    )


def _robustness_template(
    *,
    seed: int,
    duration_s: float,
    trajectory: ScenarioTrajectoryConfig,
    disturbances: ScenarioDisturbanceConfig,
    name: str,
    description: str,
    tags: tuple[str, ...],
) -> SimulationScenario:
    scenario = build_minimal_scenario(seed=seed)
    scenario = replace(
        scenario,
        time=ScenarioTimeConfig(
            duration_s=duration_s,
            physics_dt_s=0.01,
            control_dt_s=0.02,
            telemetry_dt_s=0.02,
        ),
        trajectory=trajectory,
        disturbances=disturbances,
    )
    return _with_ood_metadata(
        scenario,
        name=name,
        description=description,
        seed=seed,
        tags=tags,
    )


def build_ood_robustness_scenarios() -> tuple[SimulationScenario, ...]:
    """Build a small, explicit OOD battery with harder conditions than the main split."""
    scenarios = (
        _robustness_template(
            seed=401,
            duration_s=4.0,
            trajectory=ScenarioTrajectoryConfig(
                kind="hover",
                target_position_m=(0.0, 0.0, 1.2),
                valid_until_s=4.0,
                source="native",
                parameters={"scenario": "ood-hover-gust"},
            ),
            disturbances=ScenarioDisturbanceConfig(
                enabled=True,
                wind_velocity_m_s=(1.8, -1.2, 0.3),
                wind_gust_std_m_s=(0.6, 0.6, 0.25),
                wind_gust_time_constant_s=0.18,
                observation_position_noise_std_m=0.03,
                observation_velocity_noise_std_m_s=0.04,
            ),
            name="ood-hover-gust",
            description="Nominal hover under stronger wind and observation noise.",
            tags=("ood", "robustness", "hover", "wind", "noise"),
        ),
        _robustness_template(
            seed=402,
            duration_s=5.0,
            trajectory=ScenarioTrajectoryConfig(
                kind="circle",
                target_position_m=(0.0, 0.0, 1.0),
                valid_until_s=5.0,
                source="native",
                parameters={
                    "center_m": (0.0, 0.0, 1.0),
                    "radius_m": 1.6,
                    "angular_speed_rad_s": 1.4,
                    "start_phase_rad": 0.35,
                },
            ),
            disturbances=ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(2.2, 0.4, 0.0),
                wind_gust_std_m_s=(0.45, 0.35, 0.2),
                wind_gust_time_constant_s=0.22,
            ),
            name="ood-circle-crosswind",
            description="Circular tracking with crosswind and drag enabled.",
            tags=("ood", "robustness", "circle", "wind", "drag"),
        ),
        _robustness_template(
            seed=403,
            duration_s=5.0,
            trajectory=ScenarioTrajectoryConfig(
                kind="spiral",
                target_position_m=(0.0, 0.0, 1.0),
                valid_until_s=5.0,
                source="native",
                parameters={
                    "center_m": (0.0, 0.0, 1.0),
                    "initial_radius_m": 0.45,
                    "radial_rate_m_s": 0.22,
                    "angular_speed_rad_s": 1.8,
                    "vertical_speed_m_s": 0.18,
                    "start_phase_rad": 0.0,
                },
            ),
            disturbances=ScenarioDisturbanceConfig(
                enabled=True,
                induced_hover_enabled=True,
                induced_hover_loss_ratio=0.18,
                observation_position_noise_std_m=0.02,
                observation_velocity_noise_std_m_s=0.03,
            ),
            name="ood-spiral-induced-loss",
            description="Spiral tracking under induced hover loss and sensor noise.",
            tags=("ood", "robustness", "spiral", "lift-loss", "noise"),
        ),
        _robustness_template(
            seed=404,
            duration_s=5.5,
            trajectory=ScenarioTrajectoryConfig(
                kind="lissajous",
                target_position_m=(0.0, 0.0, 1.0),
                valid_until_s=5.5,
                source="native",
                parameters={
                    "center_m": (0.0, 0.0, 1.0),
                    "amplitude_m": (1.5, 1.1, 0.7),
                    "frequency_rad_s": (1.3, 2.2, 3.4),
                    "phase_rad": (0.0, 1.1, 0.3),
                },
            ),
            disturbances=ScenarioDisturbanceConfig(
                enabled=True,
                parasitic_drag_enabled=True,
                wind_velocity_m_s=(-1.4, 1.3, 0.2),
                wind_gust_std_m_s=(0.5, 0.45, 0.3),
                wind_gust_time_constant_s=0.2,
                observation_position_noise_std_m=0.025,
                observation_velocity_noise_std_m_s=0.03,
            ),
            name="ood-lissajous-noise",
            description="Aggressive lissajous tracking with wind and observation noise.",
            tags=("ood", "robustness", "lissajous", "wind", "noise"),
        ),
    )
    return scenarios

