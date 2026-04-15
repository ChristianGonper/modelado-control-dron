"""Canonical dataset contract for Phase 2 control neuronal work."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose, isfinite, pi
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np

from ..core.attitude import euler_from_quaternion
from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState


FEATURE_MODES: tuple[str, ...] = ("raw_observation", "observation_plus_tracking_errors")
BASE_FEATURE_NAMES: tuple[str, ...] = (
    "observed_position_x_m",
    "observed_position_y_m",
    "observed_position_z_m",
    "observed_linear_velocity_x_m_s",
    "observed_linear_velocity_y_m_s",
    "observed_linear_velocity_z_m_s",
    "observed_orientation_w",
    "observed_orientation_x",
    "observed_orientation_y",
    "observed_orientation_z",
    "observed_angular_velocity_x_rad_s",
    "observed_angular_velocity_y_rad_s",
    "observed_angular_velocity_z_rad_s",
    "reference_position_x_m",
    "reference_position_y_m",
    "reference_position_z_m",
    "reference_velocity_x_m_s",
    "reference_velocity_y_m_s",
    "reference_velocity_z_m_s",
    "reference_acceleration_x_m_s2",
    "reference_acceleration_y_m_s2",
    "reference_acceleration_z_m_s2",
    "reference_yaw_sin",
    "reference_yaw_cos",
)
ERROR_FEATURE_NAMES: tuple[str, ...] = (
    "tracking_position_error_x_m",
    "tracking_position_error_y_m",
    "tracking_position_error_z_m",
    "tracking_velocity_error_x_m_s",
    "tracking_velocity_error_y_m_s",
    "tracking_velocity_error_z_m_s",
    "tracking_yaw_error_sin",
    "tracking_yaw_error_cos",
)
DATASET_TARGET_NAMES: tuple[str, ...] = (
    "collective_thrust_newton",
    "body_torque_x_nm",
    "body_torque_y_nm",
    "body_torque_z_nm",
)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_vector(value: Sequence[object], *, length: int, field_name: str) -> tuple[float, ...]:
    if len(value) != length:
        raise ValueError(f"{field_name} must contain exactly {length} values")
    return tuple(_coerce_float(component, field_name) for component in value)


def _wrap_angle(angle_rad: float) -> float:
    return (angle_rad + pi) % (2.0 * pi) - pi


def _reference_acceleration(reference: TrajectoryReference) -> tuple[float, float, float]:
    if reference.acceleration_m_s2 is None:
        return (0.0, 0.0, 0.0)
    return _coerce_vector(reference.acceleration_m_s2, length=3, field_name="reference.acceleration_m_s2")


def _observed_yaw_rad(observed_state: VehicleState) -> float:
    return euler_from_quaternion(observed_state.orientation_wxyz)[2]


@dataclass(frozen=True, slots=True)
class DatasetContract:
    """Closed Phase 2 dataset contract."""

    schema_version: int = 1
    feature_modes: tuple[str, ...] = FEATURE_MODES
    base_feature_names: tuple[str, ...] = BASE_FEATURE_NAMES
    error_feature_names: tuple[str, ...] = ERROR_FEATURE_NAMES
    target_names: tuple[str, ...] = DATASET_TARGET_NAMES

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", int(self.schema_version))
        object.__setattr__(self, "feature_modes", tuple(str(mode).strip().lower() for mode in self.feature_modes if str(mode).strip()))
        object.__setattr__(self, "base_feature_names", tuple(str(name).strip() for name in self.base_feature_names if str(name).strip()))
        object.__setattr__(self, "error_feature_names", tuple(str(name).strip() for name in self.error_feature_names if str(name).strip()))
        object.__setattr__(self, "target_names", tuple(str(name).strip() for name in self.target_names if str(name).strip()))

    def feature_names(self, mode: str) -> tuple[str, ...]:
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in self.feature_modes:
            raise ValueError(f"unsupported feature mode: {mode}")
        if normalized_mode == "raw_observation":
            return self.base_feature_names
        return self.base_feature_names + self.error_feature_names

    def feature_dimension(self, mode: str) -> int:
        return len(self.feature_names(mode))

    @property
    def target_dimension(self) -> int:
        return len(self.target_names)


PHASE2_DATASET_CONTRACT = DatasetContract()


@dataclass(frozen=True, slots=True)
class DatasetTraceability:
    source_path: Path | None
    episode_id: str
    scenario_name: str
    scenario_seed: int | None
    controller_kind: str
    controller_source: str
    trajectory_kind: str
    disturbance_regime: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "episode_id", str(self.episode_id).strip())
        object.__setattr__(self, "scenario_name", str(self.scenario_name).strip() or "unknown")
        object.__setattr__(self, "controller_kind", str(self.controller_kind).strip() or "unknown")
        object.__setattr__(self, "controller_source", str(self.controller_source).strip() or "unknown")
        object.__setattr__(self, "trajectory_kind", str(self.trajectory_kind).strip() or "unknown")
        object.__setattr__(self, "disturbance_regime", str(self.disturbance_regime).strip() or "unknown")
        if self.scenario_seed is not None:
            object.__setattr__(self, "scenario_seed", int(self.scenario_seed))
        object.__setattr__(self, "source_path", None if self.source_path is None else Path(self.source_path))

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_name": self.scenario_name,
            "scenario_seed": self.scenario_seed,
            "controller_kind": self.controller_kind,
            "controller_source": self.controller_source,
            "trajectory_kind": self.trajectory_kind,
            "disturbance_regime": self.disturbance_regime,
            "source_path": None if self.source_path is None else str(self.source_path),
            "episode_id": self.episode_id,
        }


@dataclass(frozen=True, slots=True)
class DatasetSplitContext:
    episode_id: str
    split_key: tuple[object, ...] = field(default_factory=tuple)
    split_regime: str = "unassigned"
    split_name: str | None = None
    split_seed: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "episode_id", str(self.episode_id).strip())
        object.__setattr__(self, "split_key", tuple(self.split_key))
        object.__setattr__(self, "split_regime", str(self.split_regime).strip().lower() or "unassigned")
        if self.split_name is not None:
            object.__setattr__(self, "split_name", str(self.split_name).strip() or None)
        if self.split_seed is not None:
            object.__setattr__(self, "split_seed", int(self.split_seed))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


def _disturbance_regime_from_metadata(scenario_payload: Mapping[str, object]) -> str:
    disturbances = scenario_payload.get("disturbances")
    if not isinstance(disturbances, Mapping):
        return "unknown"

    flags: list[str] = []
    if bool(disturbances.get("observation_position_noise_std_m", 0.0)) or bool(
        disturbances.get("observation_velocity_noise_std_m_s", 0.0)
    ):
        flags.append("observation_noise")

    if any(float(component) != 0.0 for component in disturbances.get("wind_velocity_m_s", (0.0, 0.0, 0.0))):
        flags.append("wind")
    if any(float(component) != 0.0 for component in disturbances.get("wind_gust_std_m_s", (0.0, 0.0, 0.0))):
        flags.append("gusts")

    if bool(disturbances.get("parasitic_drag_enabled")) or bool(disturbances.get("induced_hover_enabled")):
        flags.append("aerodynamic")

    if not flags:
        return "nominal" if bool(disturbances.get("enabled", False)) or disturbances else "unknown"
    return "+".join(flags)


@dataclass(frozen=True, slots=True)
class DatasetSample:
    index: int
    time_s: float
    true_state: VehicleState
    observed_state: VehicleState
    reference: TrajectoryReference
    command: VehicleCommand
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "index", int(self.index))
        object.__setattr__(self, "time_s", _coerce_float(self.time_s, "time_s"))
        if not isinstance(self.true_state, VehicleState):
            raise ValueError("true_state must be a VehicleState")
        if not isinstance(self.observed_state, VehicleState):
            raise ValueError("observed_state must be a VehicleState")
        if not isinstance(self.reference, TrajectoryReference):
            raise ValueError("reference must be a TrajectoryReference")
        if not isinstance(self.command, VehicleCommand):
            raise ValueError("command must be a VehicleCommand")
        if not isclose(self.true_state.time_s, self.time_s, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("true_state time must match the sample time")
        if not isclose(self.observed_state.time_s, self.time_s, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("observed_state time must match the sample time")
        if not isclose(self.reference.time_s, self.time_s, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("reference time must match the sample time")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @property
    def observation(self) -> VehicleObservation:
        return VehicleObservation(true_state=self.true_state, observed_state=self.observed_state, metadata=self.metadata)

    @property
    def tracking_state(self) -> VehicleState:
        return self.true_state

    @property
    def tracking_error_observed(self) -> tuple[tuple[float, float, float], tuple[float, float, float], float]:
        position_error = tuple(
            reference_value - observed_value
            for reference_value, observed_value in zip(self.reference.position_m, self.observed_state.position_m)
        )
        velocity_error = tuple(
            reference_value - observed_value
            for reference_value, observed_value in zip(self.reference.velocity_m_s, self.observed_state.linear_velocity_m_s)
        )
        yaw_error = _wrap_angle(self.reference.yaw_rad - _observed_yaw_rad(self.observed_state))
        return position_error, velocity_error, yaw_error

    def feature_vector(self, mode: str) -> tuple[float, ...]:
        from .features import build_feature_vector

        return build_feature_vector(self, mode)

    @property
    def target_vector(self) -> tuple[float, ...]:
        from .features import build_target_vector

        return build_target_vector(self)


@dataclass(frozen=True, slots=True)
class DatasetEpisode:
    episode_id: str
    source_path: Path | None = None
    scenario_payload: Mapping[str, object] = field(default_factory=dict)
    vehicle_metadata: Mapping[str, object] = field(default_factory=dict)
    controller_metadata: Mapping[str, object] = field(default_factory=dict)
    telemetry_metadata: Mapping[str, object] = field(default_factory=dict)
    initial_state: VehicleState | None = None
    final_state: VehicleState | None = None
    samples: tuple[DatasetSample, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "episode_id", str(self.episode_id).strip())
        object.__setattr__(self, "source_path", None if self.source_path is None else Path(self.source_path))
        object.__setattr__(self, "scenario_payload", _freeze_mapping(self.scenario_payload))
        object.__setattr__(self, "vehicle_metadata", _freeze_mapping(self.vehicle_metadata))
        object.__setattr__(self, "controller_metadata", _freeze_mapping(self.controller_metadata))
        object.__setattr__(self, "telemetry_metadata", _freeze_mapping(self.telemetry_metadata))
        object.__setattr__(self, "samples", tuple(self.samples))
        if not self.episode_id:
            raise ValueError("episode_id must be a non-empty string")
        if self.initial_state is not None and not isinstance(self.initial_state, VehicleState):
            raise ValueError("initial_state must be a VehicleState")
        if self.final_state is not None and not isinstance(self.final_state, VehicleState):
            raise ValueError("final_state must be a VehicleState")
        for sample in self.samples:
            if not isinstance(sample, DatasetSample):
                raise ValueError("samples must contain DatasetSample instances")

    @property
    def scenario_metadata(self) -> Mapping[str, object]:
        metadata = self.scenario_payload.get("metadata", {})
        if not isinstance(metadata, Mapping):
            return MappingProxyType({})
        return _freeze_mapping(metadata)

    @property
    def scenario_name(self) -> str:
        return str(self.scenario_metadata.get("name", "unknown")).strip() or "unknown"

    @property
    def scenario_seed(self) -> int | None:
        seed = self.scenario_metadata.get("seed")
        if seed is None:
            return None
        return int(seed)

    @property
    def trajectory_kind(self) -> str:
        trajectory = self.scenario_payload.get("trajectory", {})
        if not isinstance(trajectory, Mapping):
            return "unknown"
        return str(trajectory.get("kind", "unknown")).strip() or "unknown"

    @property
    def controller_kind(self) -> str:
        return str(self.controller_metadata.get("kind", "unknown")).strip() or "unknown"

    @property
    def controller_source(self) -> str:
        return str(self.controller_metadata.get("source", "unknown")).strip() or "unknown"

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def disturbance_regime(self) -> str:
        return _disturbance_regime_from_metadata(self.scenario_payload)

    @property
    def traceability(self) -> DatasetTraceability:
        return DatasetTraceability(
            source_path=self.source_path,
            episode_id=self.episode_id,
            scenario_name=self.scenario_name,
            scenario_seed=self.scenario_seed,
            controller_kind=self.controller_kind,
            controller_source=self.controller_source,
            trajectory_kind=self.trajectory_kind,
            disturbance_regime=self.disturbance_regime,
        )

    @property
    def split_key(self) -> tuple[object, ...]:
        return (
            self.trajectory_kind,
            self.disturbance_regime,
            self.scenario_name,
            self.scenario_seed,
            self.controller_kind,
            self.controller_source,
        )

    def feature_matrix(self, mode: str) -> np.ndarray:
        from .features import build_feature_matrix

        return build_feature_matrix(self, mode)

    @property
    def target_matrix(self) -> np.ndarray:
        from .features import build_target_matrix

        return build_target_matrix(self)
