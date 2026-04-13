"""Scenario schema for reproducible simulator runs.

The scenario is the main configuration entry point for the runner. It groups
the vehicle, initial conditions, timing, trajectory, disturbances, controller,
telemetry, and experiment metadata into a single extensible contract.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import ClassVar, Mapping, Sequence

from ..control import CascadedController, AttitudeLoopController, PositionLoopController
from ..core.contracts import TrajectoryReference, VehicleState
from ..dynamics import AerodynamicEnvironment, RigidBody6DOFDynamics, RigidBodyParameters
from ..trajectories import TrajectoryContract, build_trajectory_from_config


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_optional_float(value: object | None, field_name: str) -> float | None:
    if value is None:
        return None
    return _coerce_float(value, field_name)


def _coerce_vector(value: Sequence[object], *, length: int, field_name: str) -> tuple[float, ...]:
    if len(value) != length:
        raise ValueError(f"{field_name} must contain exactly {length} values")
    return tuple(_coerce_float(component, field_name) for component in value)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _state_to_summary(state: VehicleState) -> dict[str, object]:
    return {
        "position_m": state.position_m,
        "orientation_wxyz": state.orientation_wxyz,
        "linear_velocity_m_s": state.linear_velocity_m_s,
        "angular_velocity_rad_s": state.angular_velocity_rad_s,
        "time_s": state.time_s,
    }


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    name: str = "nominal-hover"
    description: str | None = None
    seed: int | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name).strip() or "nominal-hover")
        if self.description is not None:
            object.__setattr__(self, "description", str(self.description).strip() or None)
        if self.seed is not None:
            object.__setattr__(self, "seed", int(self.seed))
        object.__setattr__(self, "tags", tuple(str(tag).strip() for tag in self.tags if str(tag).strip()))


@dataclass(frozen=True, slots=True)
class ScenarioTimeConfig:
    duration_s: float
    dt_s: float
    telemetry_dt_s: float | None = None

    def __post_init__(self) -> None:
        duration_s = _coerce_float(self.duration_s, "duration_s")
        dt_s = _coerce_float(self.dt_s, "dt_s")
        if duration_s <= 0.0:
            raise ValueError("duration_s must be positive")
        if dt_s <= 0.0:
            raise ValueError("dt_s must be positive")
        telemetry_dt_s = _coerce_optional_float(self.telemetry_dt_s, "telemetry_dt_s")
        if telemetry_dt_s is not None and telemetry_dt_s <= 0.0:
            raise ValueError("telemetry_dt_s must be positive")
        object.__setattr__(self, "duration_s", duration_s)
        object.__setattr__(self, "dt_s", dt_s)
        object.__setattr__(self, "telemetry_dt_s", telemetry_dt_s)


@dataclass(frozen=True, slots=True)
class ScenarioTrajectoryConfig:
    kind: str = "hover"
    target_position_m: tuple[float, float, float] = (0.0, 0.0, 1.0)
    target_velocity_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_yaw_rad: float = 0.0
    valid_until_s: float | None = None
    target_acceleration_m_s2: tuple[float, float, float] | None = None
    source: str = "native"
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind).strip().lower()
        if not kind:
            raise ValueError("kind must be a non-empty string")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "target_position_m", _coerce_vector(self.target_position_m, length=3, field_name="target_position_m"))
        object.__setattr__(self, "target_velocity_m_s", _coerce_vector(self.target_velocity_m_s, length=3, field_name="target_velocity_m_s"))
        object.__setattr__(self, "target_yaw_rad", _coerce_float(self.target_yaw_rad, "target_yaw_rad"))
        object.__setattr__(self, "valid_until_s", _coerce_optional_float(self.valid_until_s, "valid_until_s"))
        if self.target_acceleration_m_s2 is not None:
            object.__setattr__(
                self,
                "target_acceleration_m_s2",
                _coerce_vector(self.target_acceleration_m_s2, length=3, field_name="target_acceleration_m_s2"),
            )
        source = str(self.source).strip().lower()
        if not source:
            raise ValueError("source must be a non-empty string")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))

    def build_trajectory(self, *, initial_state: VehicleState | None = None) -> TrajectoryContract:
        return build_trajectory_from_config(self, initial_state=initial_state)

    def build_reference(self, time_s: float, *, initial_state: VehicleState | None = None) -> TrajectoryReference:
        return self.build_trajectory(initial_state=initial_state).reference_at(time_s)


@dataclass(frozen=True, slots=True)
class ScenarioDisturbanceConfig:
    enabled: bool = False
    parasitic_drag_enabled: bool = False
    induced_hover_enabled: bool = False
    wind_velocity_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    wind_gust_std_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    parasitic_drag_area_m2: float | None = None
    induced_hover_loss_ratio: float | None = None
    observation_position_noise_std_m: float = 0.0
    observation_velocity_noise_std_m_s: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", bool(self.enabled))
        object.__setattr__(self, "parasitic_drag_enabled", bool(self.parasitic_drag_enabled))
        object.__setattr__(self, "induced_hover_enabled", bool(self.induced_hover_enabled))
        object.__setattr__(self, "wind_velocity_m_s", _coerce_vector(self.wind_velocity_m_s, length=3, field_name="wind_velocity_m_s"))
        object.__setattr__(self, "wind_gust_std_m_s", _coerce_vector(self.wind_gust_std_m_s, length=3, field_name="wind_gust_std_m_s"))
        if self.parasitic_drag_area_m2 is not None:
            object.__setattr__(
                self,
                "parasitic_drag_area_m2",
                _coerce_float(self.parasitic_drag_area_m2, "parasitic_drag_area_m2"),
            )
            if self.parasitic_drag_area_m2 < 0.0:
                raise ValueError("parasitic_drag_area_m2 must be non-negative")
        if self.induced_hover_loss_ratio is not None:
            object.__setattr__(
                self,
                "induced_hover_loss_ratio",
                _coerce_float(self.induced_hover_loss_ratio, "induced_hover_loss_ratio"),
            )
            if self.induced_hover_loss_ratio < 0.0:
                raise ValueError("induced_hover_loss_ratio must be non-negative")
        object.__setattr__(
            self,
            "observation_position_noise_std_m",
            _coerce_float(self.observation_position_noise_std_m, "observation_position_noise_std_m"),
        )
        object.__setattr__(
            self,
            "observation_velocity_noise_std_m_s",
            _coerce_float(self.observation_velocity_noise_std_m_s, "observation_velocity_noise_std_m_s"),
        )
        if self.observation_position_noise_std_m < 0.0:
            raise ValueError("observation_position_noise_std_m must be non-negative")
        if self.observation_velocity_noise_std_m_s < 0.0:
            raise ValueError("observation_velocity_noise_std_m_s must be non-negative")

    def is_active(self) -> bool:
        return self.enabled and (
            self.parasitic_drag_enabled
            or self.induced_hover_enabled
            or any(component != 0.0 for component in self.wind_velocity_m_s)
            or any(component != 0.0 for component in self.wind_gust_std_m_s)
            or self.observation_position_noise_std_m > 0.0
            or self.observation_velocity_noise_std_m_s > 0.0
        )

    def physical_flags(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "parasitic_drag_enabled": self.parasitic_drag_enabled,
            "induced_hover_enabled": self.induced_hover_enabled,
            "wind_velocity_m_s": self.wind_velocity_m_s,
            "wind_gust_std_m_s": self.wind_gust_std_m_s,
            "parasitic_drag_area_m2": self.parasitic_drag_area_m2,
            "induced_hover_loss_ratio": self.induced_hover_loss_ratio,
            "observation_position_noise_std_m": self.observation_position_noise_std_m,
            "observation_velocity_noise_std_m_s": self.observation_velocity_noise_std_m_s,
        }

    def perturb_observation(self, state: VehicleState, rng: random.Random) -> VehicleState:
        if not self.is_active():
            return state
        position = tuple(
            component + rng.gauss(0.0, self.observation_position_noise_std_m)
            for component in state.position_m
        )
        linear_velocity = tuple(
            component + rng.gauss(0.0, self.observation_velocity_noise_std_m_s)
            for component in state.linear_velocity_m_s
        )
        return VehicleState(
            position_m=position,
            orientation_wxyz=state.orientation_wxyz,
            linear_velocity_m_s=linear_velocity,
            angular_velocity_rad_s=state.angular_velocity_rad_s,
            time_s=state.time_s,
        )

    def build_aerodynamic_environment(
        self,
        vehicle: RigidBodyParameters,
        *,
        seed: int | None = None,
    ) -> AerodynamicEnvironment:
        drag_area_m2 = vehicle.parasitic_drag_area_m2
        if self.parasitic_drag_area_m2 is not None:
            drag_area_m2 = self.parasitic_drag_area_m2
        induced_hover_loss_ratio = vehicle.induced_hover_loss_ratio
        if self.induced_hover_loss_ratio is not None:
            induced_hover_loss_ratio = self.induced_hover_loss_ratio
        return AerodynamicEnvironment(
            parasitic_drag_enabled=self.enabled and self.parasitic_drag_enabled,
            induced_hover_enabled=self.enabled and self.induced_hover_enabled,
            wind_velocity_m_s=self.wind_velocity_m_s,
            wind_gust_std_m_s=self.wind_gust_std_m_s,
            parasitic_drag_area_m2=drag_area_m2,
            air_density_kg_m3=vehicle.air_density_kg_m3,
            induced_hover_loss_ratio=induced_hover_loss_ratio,
            seed=seed,
        )


@dataclass(frozen=True, slots=True)
class ScenarioControllerConfig:
    kind: str = "cascade"
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = str(self.kind).strip().lower()
        if not kind:
            raise ValueError("kind must be a non-empty string")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))


@dataclass(frozen=True, slots=True)
class ScenarioTelemetryConfig:
    record_scenario_metadata: bool = True
    detail_level: str = "standard"
    sample_dt_s: float | None = None
    _allowed_detail_levels: ClassVar[tuple[str, ...]] = ("compact", "standard", "full")

    def __post_init__(self) -> None:
        detail_level = str(self.detail_level).strip().lower()
        if not detail_level:
            raise ValueError("detail_level must be a non-empty string")
        if detail_level not in self._allowed_detail_levels:
            raise ValueError(
                "detail_level must be one of: compact, standard, full"
            )
        object.__setattr__(self, "detail_level", detail_level)
        sample_dt_s = _coerce_optional_float(self.sample_dt_s, "sample_dt_s")
        if sample_dt_s is not None and sample_dt_s <= 0.0:
            raise ValueError("sample_dt_s must be positive")
        object.__setattr__(self, "sample_dt_s", sample_dt_s)
        object.__setattr__(self, "record_scenario_metadata", bool(self.record_scenario_metadata))


@dataclass(frozen=True, slots=True)
class SimulationScenario:
    initial_state: VehicleState
    time: ScenarioTimeConfig
    trajectory: ScenarioTrajectoryConfig = field(default_factory=ScenarioTrajectoryConfig)
    vehicle: RigidBodyParameters = field(default_factory=RigidBodyParameters)
    controller: ScenarioControllerConfig = field(default_factory=ScenarioControllerConfig)
    disturbances: ScenarioDisturbanceConfig = field(default_factory=ScenarioDisturbanceConfig)
    telemetry: ScenarioTelemetryConfig = field(default_factory=ScenarioTelemetryConfig)
    metadata: ScenarioMetadata = field(default_factory=ScenarioMetadata)

    def __post_init__(self) -> None:
        if not isinstance(self.initial_state, VehicleState):
            raise ValueError("initial_state must be a VehicleState")
        if not isinstance(self.time, ScenarioTimeConfig):
            raise ValueError("time must be a ScenarioTimeConfig")
        if not isinstance(self.trajectory, ScenarioTrajectoryConfig):
            raise ValueError("trajectory must be a ScenarioTrajectoryConfig")
        if not isinstance(self.vehicle, RigidBodyParameters):
            raise ValueError("vehicle must be a RigidBodyParameters")
        if not isinstance(self.controller, ScenarioControllerConfig):
            raise ValueError("controller must be a ScenarioControllerConfig")
        if not isinstance(self.disturbances, ScenarioDisturbanceConfig):
            raise ValueError("disturbances must be a ScenarioDisturbanceConfig")
        if not isinstance(self.telemetry, ScenarioTelemetryConfig):
            raise ValueError("telemetry must be a ScenarioTelemetryConfig")
        if not isinstance(self.metadata, ScenarioMetadata):
            raise ValueError("metadata must be a ScenarioMetadata")

    @property
    def duration_s(self) -> float:
        return self.time.duration_s

    @property
    def dt_s(self) -> float:
        return self.time.dt_s

    @property
    def seed(self) -> int | None:
        return self.metadata.seed

    def build_rng(self) -> random.Random:
        return random.Random(self.metadata.seed)

    def build_dynamics(self) -> RigidBody6DOFDynamics:
        return RigidBody6DOFDynamics(
            parameters=self.vehicle,
            aerodynamics=self.disturbances.build_aerodynamic_environment(self.vehicle, seed=self.seed),
        )

    def build_controller(self) -> CascadedController:
        if self.controller.kind not in {"cascade", "pid_cascade"}:
            raise ValueError(f"unsupported controller kind: {self.controller.kind}")

        position_defaults = {"kp_position": (2.0, 2.0, 4.0), "kd_velocity": (1.2, 1.2, 2.5)}
        attitude_defaults = {
            "mass_kg": self.vehicle.mass_kg,
            "gravity_m_s2": self.vehicle.gravity_m_s2,
            "max_collective_thrust_newton": self.vehicle.max_collective_thrust_newton,
            "max_body_torque_nm": self.vehicle.max_body_torque_nm,
        }
        position_loop_parameters = dict(self.controller.parameters.get("position_loop", {}))
        attitude_loop_parameters = dict(self.controller.parameters.get("attitude_loop", {}))
        position_loop = PositionLoopController(**{**position_defaults, **position_loop_parameters})
        attitude_loop = AttitudeLoopController(**{**attitude_defaults, **attitude_loop_parameters})
        return CascadedController(position_loop=position_loop, attitude_loop=attitude_loop)

    def reference_at(self, time_s: float) -> TrajectoryReference:
        return self.trajectory.build_reference(time_s, initial_state=self.initial_state)

    def build_trajectory(self) -> TrajectoryContract:
        return self.trajectory.build_trajectory(initial_state=self.initial_state)

    def describe(self) -> dict[str, object]:
        return {
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "seed": self.metadata.seed,
                "tags": self.metadata.tags,
            },
            "vehicle": asdict(self.vehicle),
            "initial_state": _state_to_summary(self.initial_state),
            "time": asdict(self.time),
            "trajectory": {
                "kind": self.trajectory.kind,
                "target_position_m": self.trajectory.target_position_m,
                "target_velocity_m_s": self.trajectory.target_velocity_m_s,
                "target_yaw_rad": self.trajectory.target_yaw_rad,
                "valid_until_s": self.trajectory.valid_until_s,
                "target_acceleration_m_s2": self.trajectory.target_acceleration_m_s2,
                "source": self.trajectory.source,
                "parameters": dict(self.trajectory.parameters),
            },
            "controller": {
                "kind": self.controller.kind,
                "parameters": dict(self.controller.parameters),
            },
            "disturbances": asdict(self.disturbances),
            "telemetry": asdict(self.telemetry),
        }
