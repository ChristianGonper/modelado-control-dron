"""Feature and target builders for Phase 2 dataset episodes."""

from __future__ import annotations

from math import cos, sin

import numpy as np

from .contract import PHASE2_DATASET_CONTRACT, DatasetEpisode, DatasetSample, _observed_yaw_rad, _reference_acceleration


def feature_names_for_mode(mode: str) -> tuple[str, ...]:
    return PHASE2_DATASET_CONTRACT.feature_names(mode)


def feature_dimension_for_mode(mode: str) -> int:
    return PHASE2_DATASET_CONTRACT.feature_dimension(mode)


def target_names() -> tuple[str, ...]:
    return PHASE2_DATASET_CONTRACT.target_names


def target_dimension() -> int:
    return PHASE2_DATASET_CONTRACT.target_dimension


def _base_feature_values(sample: DatasetSample) -> tuple[float, ...]:
    reference_acceleration = _reference_acceleration(sample.reference)
    yaw_sin = sin(sample.reference.yaw_rad)
    yaw_cos = cos(sample.reference.yaw_rad)
    return (
        sample.observed_state.position_m[0],
        sample.observed_state.position_m[1],
        sample.observed_state.position_m[2],
        sample.observed_state.linear_velocity_m_s[0],
        sample.observed_state.linear_velocity_m_s[1],
        sample.observed_state.linear_velocity_m_s[2],
        sample.observed_state.orientation_wxyz[0],
        sample.observed_state.orientation_wxyz[1],
        sample.observed_state.orientation_wxyz[2],
        sample.observed_state.orientation_wxyz[3],
        sample.observed_state.angular_velocity_rad_s[0],
        sample.observed_state.angular_velocity_rad_s[1],
        sample.observed_state.angular_velocity_rad_s[2],
        sample.reference.position_m[0],
        sample.reference.position_m[1],
        sample.reference.position_m[2],
        sample.reference.velocity_m_s[0],
        sample.reference.velocity_m_s[1],
        sample.reference.velocity_m_s[2],
        reference_acceleration[0],
        reference_acceleration[1],
        reference_acceleration[2],
        yaw_sin,
        yaw_cos,
    )


def _error_feature_values(sample: DatasetSample) -> tuple[float, ...]:
    position_error, velocity_error, yaw_error = sample.tracking_error_observed
    return (
        position_error[0],
        position_error[1],
        position_error[2],
        velocity_error[0],
        velocity_error[1],
        velocity_error[2],
        sin(yaw_error),
        cos(yaw_error),
    )


def build_feature_vector(sample: DatasetSample, mode: str) -> tuple[float, ...]:
    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in PHASE2_DATASET_CONTRACT.feature_modes:
        raise ValueError(f"unsupported feature mode: {mode}")
    base_values = _base_feature_values(sample)
    if normalized_mode == "raw_observation":
        return base_values
    return base_values + _error_feature_values(sample)


def build_feature_matrix(episode: DatasetEpisode, mode: str) -> np.ndarray:
    if not episode.samples:
        return np.empty((0, feature_dimension_for_mode(mode)), dtype=np.float64)
    return np.asarray([build_feature_vector(sample, mode) for sample in episode.samples], dtype=np.float64)


def build_target_vector(sample: DatasetSample) -> tuple[float, ...]:
    return (
        sample.command.collective_thrust_newton,
        sample.command.body_torque_nm[0],
        sample.command.body_torque_nm[1],
        sample.command.body_torque_nm[2],
    )


def build_target_matrix(episode: DatasetEpisode) -> np.ndarray:
    if not episode.samples:
        return np.empty((0, target_dimension()), dtype=np.float64)
    return np.asarray([build_target_vector(sample) for sample in episode.samples], dtype=np.float64)
