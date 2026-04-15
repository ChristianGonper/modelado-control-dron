"""Load persisted telemetry exports into reusable dataset episodes."""

from __future__ import annotations

from collections.abc import Sequence
import json
from pathlib import Path
from typing import Mapping

from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleState
from ..visualization import TelemetryArchive, TelemetrySample, load_telemetry_archive
from .contract import DatasetEpisode, DatasetSample, _disturbance_regime_from_metadata


class DatasetExtractionError(ValueError):
    """Raised when a telemetry export does not satisfy the dataset contract."""


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DatasetExtractionError(f"{field_name} must be a mapping")
    return value


def _require_keys(payload: Mapping[str, object], required_keys: Sequence[str], field_name: str) -> None:
    missing = [key for key in required_keys if key not in payload]
    if missing:
        joined = ", ".join(missing)
        raise DatasetExtractionError(f"{field_name} is missing required keys: {joined}")


def _vehicle_state_from_mapping(payload: Mapping[str, object], *, field_name: str) -> VehicleState:
    _require_keys(payload, ("position_m", "orientation_wxyz", "linear_velocity_m_s", "angular_velocity_rad_s", "time_s"), field_name)
    return VehicleState(
        position_m=payload["position_m"],
        orientation_wxyz=payload["orientation_wxyz"],
        linear_velocity_m_s=payload["linear_velocity_m_s"],
        angular_velocity_rad_s=payload["angular_velocity_rad_s"],
        time_s=payload["time_s"],
    )


def _normalize_state(sample: TelemetrySample, *, observed: bool) -> VehicleState:
    if observed:
        return sample.observed_state
    return sample.state


def _command_from_row(sample: TelemetrySample) -> VehicleCommand:
    return sample.command


def _episode_id_from_payload(
    scenario_payload: Mapping[str, object],
    *,
    controller_metadata: Mapping[str, object],
    disturbance_regime: str,
) -> str:
    metadata = _require_mapping(scenario_payload.get("metadata", {}), "scenario.metadata")
    scenario_name = str(metadata.get("name", "unknown")).strip() or "unknown"
    scenario_seed = metadata.get("seed")
    trajectory = _require_mapping(scenario_payload.get("trajectory", {}), "scenario.trajectory")
    trajectory_kind = str(trajectory.get("kind", "unknown")).strip() or "unknown"
    controller_kind = str(controller_metadata.get("kind", "unknown")).strip() or "unknown"
    controller_source = str(controller_metadata.get("source", "unknown")).strip() or "unknown"
    seed_token = "none" if scenario_seed is None else str(int(scenario_seed))
    return "|".join(
        (
            scenario_name,
            f"seed={seed_token}",
            f"trajectory={trajectory_kind}",
            f"disturbance={disturbance_regime}",
            f"controller={controller_kind}",
            f"source={controller_source}",
        )
    )


def _build_sample(
    archive: TelemetryArchive,
    sample: TelemetrySample,
    *,
    episode_id: str,
) -> DatasetSample:
    metadata = {
        "episode_id": episode_id,
        "source_path": None if archive.source_path is None else str(archive.source_path),
        "step_index": sample.step_index,
        "event_kinds": sample.event_kinds,
        "reference_valid_from_s": sample.reference_valid_from_s,
        "reference_valid_until_s": sample.reference_valid_until_s,
        "tracking_state_source": archive.telemetry_metadata.get("tracking_state_source", "true_state"),
    }
    return DatasetSample(
        index=sample.step_index,
        time_s=sample.time_s,
        true_state=_normalize_state(sample, observed=False),
        observed_state=_normalize_state(sample, observed=True),
        reference=TrajectoryReference(
            time_s=sample.time_s,
            position_m=sample.reference_position_m,
            velocity_m_s=sample.reference_velocity_m_s,
            yaw_rad=sample.reference_yaw_rad,
            valid_from_s=sample.reference_valid_from_s or 0.0,
            valid_until_s=sample.reference_valid_until_s,
            acceleration_m_s2=sample.reference_acceleration_m_s2,
        ),
        command=_command_from_row(sample),
        metadata=metadata,
    )


def _build_episode(source: TelemetryArchive) -> DatasetEpisode:
    scenario_payload = source.scenario_metadata
    telemetry_metadata = source.telemetry_metadata
    if not scenario_payload:
        raise DatasetExtractionError(
            "telemetry archive is missing scenario metadata; enable record_scenario_metadata"
        )

    if "metadata" not in scenario_payload:
        raise DatasetExtractionError("scenario.metadata is missing")
    _require_keys(
        _require_mapping(scenario_payload, "scenario"),
        ("trajectory", "controller", "disturbances", "time"),
        "scenario",
    )
    _require_keys(
        _require_mapping(telemetry_metadata, "telemetry"),
        ("detail_level", "sample_count", "tracking_state_source"),
        "telemetry",
    )
    if str(telemetry_metadata.get("tracking_state_source", "true_state")).strip().lower() != "true_state":
        raise DatasetExtractionError("telemetry archive must be anchored to true_state tracking")
    if source.sample_count == 0:
        raise DatasetExtractionError("telemetry archive must contain at least one sample")

    disturbance_regime = _disturbance_regime_from_metadata(scenario_payload)
    episode_id = _episode_id_from_payload(
        scenario_payload,
        controller_metadata=source.controller_metadata,
        disturbance_regime=disturbance_regime,
    )
    samples = tuple(_build_sample(source, sample, episode_id=episode_id) for sample in source.samples)

    initial_state = _vehicle_state_from_mapping(source.initial_state, field_name="initial_state") if source.initial_state else None
    final_state = _vehicle_state_from_mapping(source.final_state, field_name="final_state") if source.final_state else None
    return DatasetEpisode(
        episode_id=episode_id,
        source_path=source.source_path,
        scenario_payload=scenario_payload,
        vehicle_metadata=source.vehicle_metadata,
        controller_metadata=source.controller_metadata,
        telemetry_metadata=source.telemetry_metadata,
        initial_state=initial_state,
        final_state=final_state,
        samples=samples,
    )


def _load_payload(source: str | Path | TelemetryArchive) -> TelemetryArchive:
    if isinstance(source, TelemetryArchive):
        return source
    try:
        return load_telemetry_archive(source)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DatasetExtractionError(f"failed to load telemetry export: {exc}") from exc


def extract_dataset_episode(source: str | Path | TelemetryArchive) -> DatasetEpisode:
    return _build_episode(_load_payload(source))


def extract_dataset_episodes(
    source: str | Path | TelemetryArchive | Sequence[str | Path | TelemetryArchive],
) -> tuple[DatasetEpisode, ...]:
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes, Path, TelemetryArchive)):
        return tuple(extract_dataset_episode(item) for item in source)
    return (extract_dataset_episode(source),)


def load_dataset_episode(source: str | Path | TelemetryArchive) -> DatasetEpisode:
    return extract_dataset_episode(source)


def load_dataset_episodes(
    source: str | Path | TelemetryArchive | Sequence[str | Path | TelemetryArchive],
) -> tuple[DatasetEpisode, ...]:
    return extract_dataset_episodes(source)
