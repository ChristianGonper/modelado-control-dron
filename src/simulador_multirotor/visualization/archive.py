"""Load persisted telemetry into a plotting-friendly archive."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np

from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleObservation, VehicleState


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_optional_float(value: object | None, field_name: str) -> float | None:
    if value is None or value == "":
        return None
    return _coerce_float(value, field_name)


def _coerce_vector(value: Sequence[object], *, length: int, field_name: str) -> tuple[float, ...]:
    if len(value) != length:
        raise ValueError(f"{field_name} must contain exactly {length} values")
    return tuple(_coerce_float(component, field_name) for component in value)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _json_load(value: object, default: object) -> object:
    if value is None or value == "":
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def _vector_from_flat(sample: Mapping[str, object], keys: Sequence[str], fallback_key: str | None = None) -> tuple[object, ...]:
    if all(key in sample for key in keys):
        return tuple(sample[key] for key in keys)
    if fallback_key is not None and fallback_key in sample:
        value = sample[fallback_key]
        if isinstance(value, Sequence):
            return tuple(value)
    raise KeyError(keys[0])


def _vehicle_state(
    position_m: Sequence[object],
    orientation_wxyz: Sequence[object],
    linear_velocity_m_s: Sequence[object],
    angular_velocity_rad_s: Sequence[object],
    *,
    time_s: object,
) -> VehicleState:
    return VehicleState(
        position_m=position_m,
        orientation_wxyz=orientation_wxyz,
        linear_velocity_m_s=linear_velocity_m_s,
        angular_velocity_rad_s=angular_velocity_rad_s,
        time_s=time_s,
    )


def _reference_acceleration_from_payload(payload: object) -> tuple[float, float, float] | None:
    state_payload = _json_load(payload, None)
    if not isinstance(state_payload, Mapping):
        return None
    reference_payload = state_payload.get("reference")
    if not isinstance(reference_payload, Mapping):
        return None
    acceleration = reference_payload.get("acceleration_m_s2")
    if acceleration is None:
        return None
    return _coerce_vector(acceleration, length=3, field_name="reference_acceleration_m_s2")


@dataclass(frozen=True, slots=True)
class TelemetrySample:
    step_index: int
    time_s: float
    state_position_m: tuple[float, float, float]
    state_orientation_wxyz: tuple[float, float, float, float]
    state_linear_velocity_m_s: tuple[float, float, float]
    state_angular_velocity_rad_s: tuple[float, float, float]
    observed_state_position_m: tuple[float, float, float]
    observed_state_orientation_wxyz: tuple[float, float, float, float]
    observed_state_linear_velocity_m_s: tuple[float, float, float]
    observed_state_angular_velocity_rad_s: tuple[float, float, float]
    reference_position_m: tuple[float, float, float]
    reference_velocity_m_s: tuple[float, float, float]
    reference_yaw_rad: float
    error_position_m: tuple[float, float, float]
    error_velocity_m_s: tuple[float, float, float]
    error_yaw_rad: float
    command_collective_thrust_newton: float
    command_body_torque_nm: tuple[float, float, float]
    event_kinds: tuple[str, ...] = ()
    reference_valid_from_s: float | None = None
    reference_valid_until_s: float | None = None
    reference_acceleration_m_s2: tuple[float, float, float] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_index", int(self.step_index))
        object.__setattr__(self, "time_s", _coerce_float(self.time_s, "time_s"))
        object.__setattr__(self, "state_position_m", _coerce_vector(self.state_position_m, length=3, field_name="state_position_m"))
        object.__setattr__(self, "state_orientation_wxyz", _coerce_vector(self.state_orientation_wxyz, length=4, field_name="state_orientation_wxyz"))
        object.__setattr__(self, "state_linear_velocity_m_s", _coerce_vector(self.state_linear_velocity_m_s, length=3, field_name="state_linear_velocity_m_s"))
        object.__setattr__(self, "state_angular_velocity_rad_s", _coerce_vector(self.state_angular_velocity_rad_s, length=3, field_name="state_angular_velocity_rad_s"))
        object.__setattr__(self, "observed_state_position_m", _coerce_vector(self.observed_state_position_m, length=3, field_name="observed_state_position_m"))
        object.__setattr__(self, "observed_state_orientation_wxyz", _coerce_vector(self.observed_state_orientation_wxyz, length=4, field_name="observed_state_orientation_wxyz"))
        object.__setattr__(self, "observed_state_linear_velocity_m_s", _coerce_vector(self.observed_state_linear_velocity_m_s, length=3, field_name="observed_state_linear_velocity_m_s"))
        object.__setattr__(self, "observed_state_angular_velocity_rad_s", _coerce_vector(self.observed_state_angular_velocity_rad_s, length=3, field_name="observed_state_angular_velocity_rad_s"))
        object.__setattr__(self, "reference_position_m", _coerce_vector(self.reference_position_m, length=3, field_name="reference_position_m"))
        object.__setattr__(self, "reference_velocity_m_s", _coerce_vector(self.reference_velocity_m_s, length=3, field_name="reference_velocity_m_s"))
        object.__setattr__(self, "reference_yaw_rad", _coerce_float(self.reference_yaw_rad, "reference_yaw_rad"))
        object.__setattr__(self, "reference_valid_from_s", _coerce_optional_float(self.reference_valid_from_s, "reference_valid_from_s"))
        object.__setattr__(self, "reference_valid_until_s", _coerce_optional_float(self.reference_valid_until_s, "reference_valid_until_s"))
        if self.reference_acceleration_m_s2 is not None:
            object.__setattr__(
                self,
                "reference_acceleration_m_s2",
                _coerce_vector(self.reference_acceleration_m_s2, length=3, field_name="reference_acceleration_m_s2"),
            )
        object.__setattr__(self, "error_position_m", _coerce_vector(self.error_position_m, length=3, field_name="error_position_m"))
        object.__setattr__(self, "error_velocity_m_s", _coerce_vector(self.error_velocity_m_s, length=3, field_name="error_velocity_m_s"))
        object.__setattr__(self, "error_yaw_rad", _coerce_float(self.error_yaw_rad, "error_yaw_rad"))
        object.__setattr__(self, "command_collective_thrust_newton", _coerce_float(self.command_collective_thrust_newton, "command_collective_thrust_newton"))
        object.__setattr__(self, "command_body_torque_nm", _coerce_vector(self.command_body_torque_nm, length=3, field_name="command_body_torque_nm"))
        object.__setattr__(self, "event_kinds", tuple(str(kind).strip() for kind in self.event_kinds if str(kind).strip()))

    @property
    def body_z_axis(self) -> tuple[float, float, float]:
        from ..core.attitude import rotate_vector_by_quaternion

        return rotate_vector_by_quaternion(self.state_orientation_wxyz, (0.0, 0.0, 1.0))

    @property
    def state(self) -> VehicleState:
        return _vehicle_state(
            self.state_position_m,
            self.state_orientation_wxyz,
            self.state_linear_velocity_m_s,
            self.state_angular_velocity_rad_s,
            time_s=self.time_s,
        )

    @property
    def observed_state(self) -> VehicleState:
        return _vehicle_state(
            self.observed_state_position_m,
            self.observed_state_orientation_wxyz,
            self.observed_state_linear_velocity_m_s,
            self.observed_state_angular_velocity_rad_s,
            time_s=self.time_s,
        )

    @property
    def tracking_state(self) -> VehicleState:
        return self.state

    @property
    def reference(self) -> TrajectoryReference:
        return TrajectoryReference(
            time_s=self.time_s,
            position_m=self.reference_position_m,
            velocity_m_s=self.reference_velocity_m_s,
            yaw_rad=self.reference_yaw_rad,
            valid_from_s=self.reference_valid_from_s or 0.0,
            valid_until_s=self.reference_valid_until_s,
            acceleration_m_s2=self.reference_acceleration_m_s2,
        )

    @property
    def command(self) -> VehicleCommand:
        return VehicleCommand(
            collective_thrust_newton=self.command_collective_thrust_newton,
            body_torque_nm=self.command_body_torque_nm,
        )

    @property
    def observation(self) -> VehicleObservation:
        return VehicleObservation(true_state=self.state, observed_state=self.observed_state)


@dataclass(frozen=True, slots=True)
class TelemetryArchive:
    source_path: Path | None
    scenario_metadata: Mapping[str, object] = field(default_factory=dict)
    vehicle_metadata: Mapping[str, object] = field(default_factory=dict)
    controller_metadata: Mapping[str, object] = field(default_factory=dict)
    telemetry_metadata: Mapping[str, object] = field(default_factory=dict)
    initial_state: Mapping[str, object] = field(default_factory=dict)
    final_state: Mapping[str, object] = field(default_factory=dict)
    samples: tuple[TelemetrySample, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_path", None if self.source_path is None else Path(self.source_path))
        object.__setattr__(self, "scenario_metadata", _freeze_mapping(self.scenario_metadata))
        object.__setattr__(self, "vehicle_metadata", _freeze_mapping(self.vehicle_metadata))
        object.__setattr__(self, "controller_metadata", _freeze_mapping(self.controller_metadata))
        object.__setattr__(self, "telemetry_metadata", _freeze_mapping(self.telemetry_metadata))
        object.__setattr__(self, "initial_state", _freeze_mapping(self.initial_state))
        object.__setattr__(self, "final_state", _freeze_mapping(self.final_state))
        object.__setattr__(self, "samples", tuple(self.samples))
        for sample in self.samples:
            if not isinstance(sample, TelemetrySample):
                raise ValueError("samples must contain TelemetrySample instances")

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def times_s(self) -> np.ndarray:
        return np.asarray([sample.time_s for sample in self.samples], dtype=np.float64)

    @property
    def state_positions_m(self) -> np.ndarray:
        return np.asarray([sample.state_position_m for sample in self.samples], dtype=np.float64)

    @property
    def reference_positions_m(self) -> np.ndarray:
        return np.asarray([sample.reference_position_m for sample in self.samples], dtype=np.float64)

    @property
    def error_positions_m(self) -> np.ndarray:
        return np.asarray([sample.error_position_m for sample in self.samples], dtype=np.float64)

    @property
    def error_velocities_m_s(self) -> np.ndarray:
        return np.asarray([sample.error_velocity_m_s for sample in self.samples], dtype=np.float64)

    @property
    def error_yaw_rad(self) -> np.ndarray:
        return np.asarray([sample.error_yaw_rad for sample in self.samples], dtype=np.float64)


@dataclass(frozen=True, slots=True)
class AnalysisArtifactBundle:
    telemetry_path: Path
    trajectory_2d_path: Path
    tracking_errors_path: Path
    trajectory_3d_path: Path


def _sample_from_mapping(sample: Mapping[str, object]) -> TelemetrySample:
    return TelemetrySample(
        step_index=sample["step_index"],
        time_s=sample["time_s"],
        state_position_m=_vector_from_flat(sample, ("state_position_x_m", "state_position_y_m", "state_position_z_m"), "state_position_m"),
        state_orientation_wxyz=_vector_from_flat(sample, ("state_orientation_w", "state_orientation_x", "state_orientation_y", "state_orientation_z"), "state_orientation_wxyz"),
        state_linear_velocity_m_s=_vector_from_flat(sample, ("state_linear_velocity_x_m_s", "state_linear_velocity_y_m_s", "state_linear_velocity_z_m_s"), "state_linear_velocity_m_s"),
        state_angular_velocity_rad_s=_vector_from_flat(sample, ("state_angular_velocity_x_rad_s", "state_angular_velocity_y_rad_s", "state_angular_velocity_z_rad_s"), "state_angular_velocity_rad_s"),
        observed_state_position_m=_vector_from_flat(sample, ("observed_state_position_x_m", "observed_state_position_y_m", "observed_state_position_z_m"), "observed_state_position_m"),
        observed_state_orientation_wxyz=_vector_from_flat(sample, ("observed_state_orientation_w", "observed_state_orientation_x", "observed_state_orientation_y", "observed_state_orientation_z"), "observed_state_orientation_wxyz"),
        observed_state_linear_velocity_m_s=_vector_from_flat(sample, ("observed_state_linear_velocity_x_m_s", "observed_state_linear_velocity_y_m_s", "observed_state_linear_velocity_z_m_s"), "observed_state_linear_velocity_m_s"),
        observed_state_angular_velocity_rad_s=_vector_from_flat(sample, ("observed_state_angular_velocity_x_rad_s", "observed_state_angular_velocity_y_rad_s", "observed_state_angular_velocity_z_rad_s"), "observed_state_angular_velocity_rad_s"),
        reference_position_m=_vector_from_flat(sample, ("reference_position_x_m", "reference_position_y_m", "reference_position_z_m"), "reference_position_m"),
        reference_velocity_m_s=_vector_from_flat(sample, ("reference_velocity_x_m_s", "reference_velocity_y_m_s", "reference_velocity_z_m_s"), "reference_velocity_m_s"),
        reference_yaw_rad=sample["reference_yaw_rad"],
        reference_valid_from_s=sample.get("reference_valid_from_s"),
        error_position_m=_vector_from_flat(sample, ("error_position_x_m", "error_position_y_m", "error_position_z_m"), "error_position_m"),
        error_velocity_m_s=_vector_from_flat(sample, ("error_velocity_x_m_s", "error_velocity_y_m_s", "error_velocity_z_m_s"), "error_velocity_m_s"),
        error_yaw_rad=sample["error_yaw_rad"],
        command_collective_thrust_newton=sample["command_collective_thrust_newton"],
        command_body_torque_nm=_vector_from_flat(sample, ("command_body_torque_x_nm", "command_body_torque_y_nm", "command_body_torque_z_nm"), "command_body_torque_nm"),
        event_kinds=tuple(_json_load(sample.get("event_kinds_json", []), [])),
        reference_valid_until_s=sample.get("reference_valid_until_s"),
        reference_acceleration_m_s2=_reference_acceleration_from_payload(sample.get("state_json")),
    )


def _sample_from_npz(archive: np.lib.npyio.NpzFile, index: int) -> TelemetrySample:
    return TelemetrySample(
        step_index=int(archive["step_index"][index]),
        time_s=float(archive["time_s"][index]),
        state_position_m=tuple(float(value) for value in archive["state_position_m"][index]),
        state_orientation_wxyz=tuple(float(value) for value in archive["state_orientation_wxyz"][index]),
        state_linear_velocity_m_s=tuple(float(value) for value in archive["state_linear_velocity_m_s"][index]),
        state_angular_velocity_rad_s=tuple(float(value) for value in archive["state_angular_velocity_rad_s"][index]),
        observed_state_position_m=tuple(float(value) for value in archive["observed_state_position_m"][index]),
        observed_state_orientation_wxyz=tuple(float(value) for value in archive["observed_state_orientation_wxyz"][index]),
        observed_state_linear_velocity_m_s=tuple(float(value) for value in archive["observed_state_linear_velocity_m_s"][index]),
        observed_state_angular_velocity_rad_s=tuple(float(value) for value in archive["observed_state_angular_velocity_rad_s"][index]),
        reference_position_m=tuple(float(value) for value in archive["reference_position_m"][index]),
        reference_velocity_m_s=tuple(float(value) for value in archive["reference_velocity_m_s"][index]),
        reference_yaw_rad=float(archive["reference_yaw_rad"][index]),
        reference_valid_from_s=float(archive["reference_valid_from_s"][index]) if "reference_valid_from_s" in archive else None,
        reference_valid_until_s=_coerce_optional_float(archive["reference_valid_until_s"][index], "reference_valid_until_s")
        if "reference_valid_until_s" in archive
        else None,
        reference_acceleration_m_s2=
        tuple(float(value) for value in archive["reference_acceleration_m_s2"][index])
        if "reference_acceleration_m_s2" in archive
        else _reference_acceleration_from_payload(archive["state_json"][index]) if "state_json" in archive else None,
        error_position_m=tuple(float(value) for value in archive["error_position_m"][index]),
        error_velocity_m_s=tuple(float(value) for value in archive["error_velocity_m_s"][index]),
        error_yaw_rad=float(archive["error_yaw_rad"][index]),
        command_collective_thrust_newton=float(archive["command_collective_thrust_newton"][index]),
        command_body_torque_nm=tuple(float(value) for value in archive["command_body_torque_nm"][index]),
        event_kinds=tuple(_json_load(archive["event_kinds_json"][index].item(), [])),
    )


def _sample_from_csv_row(row: Mapping[str, object]) -> TelemetrySample:
    return TelemetrySample(
        step_index=row["step_index"],
        time_s=row["time_s"],
        state_position_m=_vector_from_flat(row, ("state_position_x_m", "state_position_y_m", "state_position_z_m"), "state_position_m"),
        state_orientation_wxyz=_vector_from_flat(row, ("state_orientation_w", "state_orientation_x", "state_orientation_y", "state_orientation_z"), "state_orientation_wxyz"),
        state_linear_velocity_m_s=_vector_from_flat(row, ("state_linear_velocity_x_m_s", "state_linear_velocity_y_m_s", "state_linear_velocity_z_m_s"), "state_linear_velocity_m_s"),
        state_angular_velocity_rad_s=_vector_from_flat(row, ("state_angular_velocity_x_rad_s", "state_angular_velocity_y_rad_s", "state_angular_velocity_z_rad_s"), "state_angular_velocity_rad_s"),
        observed_state_position_m=_vector_from_flat(row, ("observed_state_position_x_m", "observed_state_position_y_m", "observed_state_position_z_m"), "observed_state_position_m"),
        observed_state_orientation_wxyz=_vector_from_flat(row, ("observed_state_orientation_w", "observed_state_orientation_x", "observed_state_orientation_y", "observed_state_orientation_z"), "observed_state_orientation_wxyz"),
        observed_state_linear_velocity_m_s=_vector_from_flat(row, ("observed_state_linear_velocity_x_m_s", "observed_state_linear_velocity_y_m_s", "observed_state_linear_velocity_z_m_s"), "observed_state_linear_velocity_m_s"),
        observed_state_angular_velocity_rad_s=_vector_from_flat(row, ("observed_state_angular_velocity_x_rad_s", "observed_state_angular_velocity_y_rad_s", "observed_state_angular_velocity_z_rad_s"), "observed_state_angular_velocity_rad_s"),
        reference_position_m=_vector_from_flat(row, ("reference_position_x_m", "reference_position_y_m", "reference_position_z_m"), "reference_position_m"),
        reference_velocity_m_s=_vector_from_flat(row, ("reference_velocity_x_m_s", "reference_velocity_y_m_s", "reference_velocity_z_m_s"), "reference_velocity_m_s"),
        reference_yaw_rad=row["reference_yaw_rad"],
        reference_valid_from_s=row.get("reference_valid_from_s"),
        error_position_m=_vector_from_flat(row, ("error_position_x_m", "error_position_y_m", "error_position_z_m"), "error_position_m"),
        error_velocity_m_s=_vector_from_flat(row, ("error_velocity_x_m_s", "error_velocity_y_m_s", "error_velocity_z_m_s"), "error_velocity_m_s"),
        error_yaw_rad=row["error_yaw_rad"],
        command_collective_thrust_newton=row["command_collective_thrust_newton"],
        command_body_torque_nm=_vector_from_flat(row, ("command_body_torque_x_nm", "command_body_torque_y_nm", "command_body_torque_z_nm"), "command_body_torque_nm"),
        event_kinds=tuple(_json_load(row.get("event_kinds_json", "[]"), [])),
        reference_valid_until_s=row.get("reference_valid_until_s"),
        reference_acceleration_m_s2=_reference_acceleration_from_payload(row.get("state_json")),
    )


def _load_json_archive(path: Path) -> TelemetryArchive:
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenario_metadata = payload.get("scenario", {})
    return TelemetryArchive(
        source_path=path,
        scenario_metadata=scenario_metadata,
        vehicle_metadata=payload.get("vehicle", scenario_metadata.get("vehicle", {})),
        controller_metadata=payload.get("controller", scenario_metadata.get("controller", {})),
        telemetry_metadata=payload.get("telemetry", {}),
        initial_state=payload.get("initial_state", {}),
        final_state=payload.get("final_state", {}),
        samples=tuple(_sample_from_mapping(sample) for sample in payload.get("samples", [])),
    )


def _load_npz_archive(path: Path) -> TelemetryArchive:
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(archive["metadata_json"].item())
        scenario_metadata = metadata.get("scenario", {})
        sample_count = int(archive["sample_count"].item())
        return TelemetryArchive(
            source_path=path,
            scenario_metadata=scenario_metadata,
            vehicle_metadata=metadata.get("vehicle", scenario_metadata.get("vehicle", {})),
            controller_metadata=metadata.get("controller", scenario_metadata.get("controller", {})),
            telemetry_metadata=metadata.get("telemetry", {}),
            initial_state=metadata.get("initial_state", {}),
            final_state=metadata.get("final_state", {}),
            samples=tuple(_sample_from_npz(archive, index) for index in range(sample_count)),
        )


def _load_csv_archive(path: Path) -> TelemetryArchive:
    metadata: dict[str, object] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        first_line = handle.readline()
        if first_line.startswith("# metadata="):
            metadata = json.loads(first_line.removeprefix("# metadata=").strip())
        else:
            handle.seek(0)
        rows = list(csv.DictReader(line for line in handle if not line.startswith("#")))
    scenario_metadata = metadata.get("scenario", {})
    return TelemetryArchive(
        source_path=path,
        scenario_metadata=scenario_metadata,
        vehicle_metadata=metadata.get("vehicle", scenario_metadata.get("vehicle", {})),
        controller_metadata=metadata.get("controller", scenario_metadata.get("controller", {})),
        telemetry_metadata=metadata.get("telemetry", {}),
        initial_state=metadata.get("initial_state", {}),
        final_state=metadata.get("final_state", {}),
        samples=tuple(_sample_from_csv_row(row) for row in rows),
    )


def load_telemetry_archive(path: str | Path) -> TelemetryArchive:
    resolved_path = Path(path)
    if resolved_path.suffix.lower() == ".json":
        return _load_json_archive(resolved_path)
    if resolved_path.suffix.lower() == ".npz":
        return _load_npz_archive(resolved_path)
    if resolved_path.suffix.lower() == ".csv":
        return _load_csv_archive(resolved_path)
    raise ValueError(f"unsupported telemetry file format: {resolved_path.suffix}")
