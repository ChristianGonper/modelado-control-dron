"""Sliding-window builders for Phase 2 dataset episodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .contract import PHASE2_DATASET_CONTRACT, DatasetEpisode, DatasetSample, DatasetSplitContext
from .features import build_feature_matrix, build_target_matrix, feature_dimension_for_mode
from .split import DatasetSplitAssignment


MLP_DEFAULT_WINDOW_SIZE = 30
MLP_DEFAULT_STRIDE = 10
RECURRENT_DEFAULT_STRIDE = 10
RECURRENT_DEFAULT_WINDOW_SIZES: dict[str, int] = {"gru": 100, "lstm": 150}


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _resolve_episode_and_split(
    source: DatasetEpisode | DatasetSplitAssignment,
) -> tuple[DatasetEpisode, DatasetSplitContext | None]:
    if isinstance(source, DatasetSplitAssignment):
        return source.episode, source.split_context
    if isinstance(source, DatasetEpisode):
        return source, None
    raise TypeError("source must be a DatasetEpisode or DatasetSplitAssignment")


@dataclass(frozen=True, slots=True)
class DatasetWindow:
    """One temporal training window built from a complete episode."""

    episode_id: str
    window_index: int
    start_index: int
    end_index: int
    window_size: int
    stride: int
    feature_dimension: int
    feature_mode: str
    architecture: str
    flattened: bool
    samples: tuple[DatasetSample, ...]
    features: np.ndarray
    target: np.ndarray
    split_context: DatasetSplitContext | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "episode_id", str(self.episode_id).strip())
        object.__setattr__(self, "window_index", int(self.window_index))
        object.__setattr__(self, "start_index", int(self.start_index))
        object.__setattr__(self, "end_index", int(self.end_index))
        object.__setattr__(self, "window_size", int(self.window_size))
        object.__setattr__(self, "stride", int(self.stride))
        object.__setattr__(self, "feature_dimension", int(self.feature_dimension))
        object.__setattr__(self, "feature_mode", str(self.feature_mode).strip().lower())
        object.__setattr__(self, "architecture", str(self.architecture).strip().lower())
        object.__setattr__(self, "flattened", bool(self.flattened))
        object.__setattr__(self, "samples", tuple(self.samples))
        object.__setattr__(self, "features", np.asarray(self.features, dtype=np.float64))
        object.__setattr__(self, "target", np.asarray(self.target, dtype=np.float64))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if self.stride <= 0:
            raise ValueError("stride must be positive")
        if self.start_index < 0:
            raise ValueError("start_index must be non-negative")
        if self.end_index <= self.start_index:
            raise ValueError("end_index must be greater than start_index")
        if self.end_index - self.start_index != self.window_size:
            raise ValueError("end_index and start_index must match window_size")
        if len(self.samples) != self.window_size:
            raise ValueError("samples must contain exactly window_size elements")
        if self.feature_dimension <= 0:
            raise ValueError("feature_dimension must be positive")
        if self.split_context is not None and self.split_context.episode_id != self.episode_id:
            raise ValueError("split_context episode_id must match the window episode")
        actual_indices = tuple(sample.index for sample in self.samples)
        if tuple(sorted(actual_indices)) != actual_indices:
            raise ValueError("window samples must be ordered")
        if len(set(actual_indices)) != len(actual_indices):
            raise ValueError("window samples must not repeat indices")
        if self.flattened:
            expected_feature_shape = (self.window_size * self.feature_dimension,)
            if self.features.shape != expected_feature_shape:
                raise ValueError("flattened window features have an unexpected shape")
        else:
            expected_feature_shape = (self.window_size, self.feature_dimension)
            if self.features.shape != expected_feature_shape:
                raise ValueError("window features have an unexpected temporal shape")
        target_dimension = PHASE2_DATASET_CONTRACT.target_dimension
        if self.target.shape != (target_dimension,):
            raise ValueError("window target must have the canonical target dimension")

    @property
    def split_name(self) -> str | None:
        return None if self.split_context is None else self.split_context.split_name

    @property
    def split_seed(self) -> int | None:
        return None if self.split_context is None else self.split_context.split_seed

    @property
    def is_temporal(self) -> bool:
        return not self.flattened

    def as_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "window_index": self.window_index,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "window_size": self.window_size,
            "stride": self.stride,
            "feature_dimension": self.feature_dimension,
            "feature_mode": self.feature_mode,
            "architecture": self.architecture,
            "flattened": self.flattened,
            "split_name": self.split_name,
            "split_seed": self.split_seed,
            "metadata": dict(self.metadata),
        }


def _window_metadata(
    *,
    episode: DatasetEpisode,
    split_context: DatasetSplitContext | None,
    architecture: str,
    feature_mode: str,
    flattened: bool,
    window_index: int,
    start_index: int,
    end_index: int,
    window_size: int,
    stride: int,
    feature_dimension: int,
) -> Mapping[str, object]:
    metadata: dict[str, object] = {
        "architecture": architecture,
        "feature_dimension": feature_dimension,
        "feature_mode": feature_mode,
        "flattened": flattened,
        "source_episode_id": episode.episode_id,
        "start_index": start_index,
        "end_index": end_index,
        "window_index": window_index,
        "window_size": window_size,
        "stride": stride,
        "target_alignment": "last_sample",
    }
    if split_context is not None:
        metadata.update(
            {
                "split_name": split_context.split_name,
                "split_regime": split_context.split_regime,
                "split_seed": split_context.split_seed,
                "split_bucket_key": split_context.metadata.get("bucket_key"),
                "split_bucket_rank": split_context.metadata.get("bucket_rank"),
            }
        )
    return _freeze_mapping(metadata)


def _build_windowed_samples(
    source: DatasetEpisode | DatasetSplitAssignment,
    *,
    window_size: int,
    stride: int,
    feature_mode: str,
    architecture: str,
    flattened: bool,
) -> tuple[DatasetWindow, ...]:
    episode, split_context = _resolve_episode_and_split(source)
    normalized_mode = str(feature_mode).strip().lower()
    feature_matrix = build_feature_matrix(episode, normalized_mode)
    target_matrix = build_target_matrix(episode)
    if feature_matrix.size == 0 or episode.sample_count < window_size:
        return ()

    feature_dimension = feature_dimension_for_mode(normalized_mode)
    windows: list[DatasetWindow] = []
    for window_index, start_index in enumerate(range(0, episode.sample_count - window_size + 1, stride)):
        end_index = start_index + window_size
        window_features = feature_matrix[start_index:end_index]
        if flattened:
            features = window_features.reshape(-1).copy()
        else:
            features = window_features.copy()
        target = target_matrix[end_index - 1].copy()
        window_samples = episode.samples[start_index:end_index]
        windows.append(
            DatasetWindow(
                episode_id=episode.episode_id,
                window_index=window_index,
                start_index=start_index,
                end_index=end_index,
                window_size=window_size,
                stride=stride,
                feature_dimension=feature_dimension,
                feature_mode=normalized_mode,
                architecture=architecture,
                flattened=flattened,
                samples=window_samples,
                features=features,
                target=target,
                split_context=split_context,
                metadata=_window_metadata(
                    episode=episode,
                    split_context=split_context,
                    architecture=architecture,
                    feature_mode=normalized_mode,
                    flattened=flattened,
                    window_index=window_index,
                    start_index=start_index,
                    end_index=end_index,
                    window_size=window_size,
                    stride=stride,
                    feature_dimension=feature_dimension,
                ),
            )
        )
    return tuple(windows)


def build_mlp_windows(
    source: DatasetEpisode | DatasetSplitAssignment,
    *,
    window_size: int = MLP_DEFAULT_WINDOW_SIZE,
    stride: int = MLP_DEFAULT_STRIDE,
    feature_mode: str = "observation_plus_tracking_errors",
) -> tuple[DatasetWindow, ...]:
    return _build_windowed_samples(
        source,
        window_size=window_size,
        stride=stride,
        feature_mode=feature_mode,
        architecture="mlp",
        flattened=True,
    )


def build_recurrent_windows(
    source: DatasetEpisode | DatasetSplitAssignment,
    *,
    architecture: str,
    window_size: int | None = None,
    stride: int = RECURRENT_DEFAULT_STRIDE,
    feature_mode: str = "observation_plus_tracking_errors",
) -> tuple[DatasetWindow, ...]:
    normalized_architecture = str(architecture).strip().lower()
    if normalized_architecture not in RECURRENT_DEFAULT_WINDOW_SIZES:
        raise ValueError(f"unsupported recurrent architecture: {architecture}")
    resolved_window_size = (
        RECURRENT_DEFAULT_WINDOW_SIZES[normalized_architecture]
        if window_size is None
        else int(window_size)
    )
    return _build_windowed_samples(
        source,
        window_size=resolved_window_size,
        stride=stride,
        feature_mode=feature_mode,
        architecture=normalized_architecture,
        flattened=False,
    )
