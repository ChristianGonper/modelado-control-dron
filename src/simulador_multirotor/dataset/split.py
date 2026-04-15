"""Deterministic episode-level split utilities for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from math import isclose
from types import MappingProxyType
from typing import Mapping, Sequence

from .contract import DatasetEpisode, DatasetSplitContext


SPLIT_NAMES: tuple[str, ...] = ("train", "validation", "test")
MAIN_SPLIT_REGIME = "main"


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _bucket_key_for_episode(episode: DatasetEpisode) -> tuple[str, str]:
    return (episode.trajectory_kind, episode.disturbance_regime)


def _bucket_signature(bucket_key: Sequence[object]) -> str:
    return "\x1f".join(str(component) for component in bucket_key)


def _rank_token(seed: int, bucket_key: Sequence[object], episode_id: str) -> int:
    payload = f"{int(seed)}|{_bucket_signature(bucket_key)}|{episode_id}".encode("utf-8")
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)


def _largest_remainder_counts(total: int, ratios: Sequence[float]) -> tuple[int, ...]:
    if total < 0:
        raise ValueError("total must be non-negative")
    exact = [total * ratio for ratio in ratios]
    counts = [int(value) for value in exact]
    remainder = total - sum(counts)
    if remainder < 0:
        raise ValueError("split ratios are invalid")
    fractional_parts = [value - int(value) for value in exact]
    order = sorted(range(len(ratios)), key=lambda index: (-fractional_parts[index], index))
    for index in order[:remainder]:
        counts[index] += 1
    return tuple(counts)


@dataclass(frozen=True, slots=True)
class DatasetSplitRatios:
    """Deterministic split ratios for the main Phase 2 dataset."""

    train: float = 0.7
    validation: float = 0.15
    test: float = 0.15

    def __post_init__(self) -> None:
        train = float(self.train)
        validation = float(self.validation)
        test = float(self.test)
        if train < 0.0 or validation < 0.0 or test < 0.0:
            raise ValueError("split ratios must be non-negative")
        if not isclose(train + validation + test, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("split ratios must sum to 1.0")
        object.__setattr__(self, "train", train)
        object.__setattr__(self, "validation", validation)
        object.__setattr__(self, "test", test)

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.train, self.validation, self.test)

    def as_dict(self) -> dict[str, float]:
        return {"train": self.train, "validation": self.validation, "test": self.test}


DEFAULT_SPLIT_RATIOS = DatasetSplitRatios()


@dataclass(frozen=True, slots=True)
class DatasetSplitAssignment:
    """Bind one complete episode to one deterministic split."""

    episode: DatasetEpisode
    split_context: DatasetSplitContext
    bucket_key: tuple[object, ...]
    bucket_rank: int
    bucket_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.episode, DatasetEpisode):
            raise ValueError("episode must be a DatasetEpisode")
        if not isinstance(self.split_context, DatasetSplitContext):
            raise ValueError("split_context must be a DatasetSplitContext")
        if self.split_context.episode_id != self.episode.episode_id:
            raise ValueError("split_context episode_id must match the episode")
        object.__setattr__(self, "bucket_key", tuple(self.bucket_key))
        object.__setattr__(self, "bucket_rank", int(self.bucket_rank))
        object.__setattr__(self, "bucket_size", int(self.bucket_size))
        if self.bucket_rank < 0:
            raise ValueError("bucket_rank must be non-negative")
        if self.bucket_size <= 0:
            raise ValueError("bucket_size must be positive")
        if self.bucket_rank >= self.bucket_size:
            raise ValueError("bucket_rank must be smaller than bucket_size")

    @property
    def episode_id(self) -> str:
        return self.episode.episode_id

    @property
    def split_name(self) -> str | None:
        return self.split_context.split_name

    @property
    def split_seed(self) -> int | None:
        return self.split_context.split_seed

    @property
    def split_regime(self) -> str:
        return self.split_context.split_regime

    @property
    def metadata(self) -> Mapping[str, object]:
        return self.split_context.metadata

    @property
    def traceability(self):
        return self.episode.traceability

    @property
    def sample_count(self) -> int:
        return self.episode.sample_count

    def as_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "split_name": self.split_name,
            "split_seed": self.split_seed,
            "split_regime": self.split_regime,
            "bucket_key": [str(component) for component in self.bucket_key],
            "bucket_rank": self.bucket_rank,
            "bucket_size": self.bucket_size,
            "metadata": dict(self.metadata),
            "traceability": self.traceability.as_dict(),
        }


def _build_split_context(
    episode: DatasetEpisode,
    *,
    split_name: str,
    split_seed: int,
    bucket_key: tuple[object, ...],
    bucket_rank: int,
    bucket_size: int,
    ratios: DatasetSplitRatios,
    counts: tuple[int, int, int],
) -> DatasetSplitContext:
    metadata = _freeze_mapping(
        {
            "allocation_rule": "deterministic_largest_remainder",
            "bucket_components": [str(component) for component in bucket_key],
            "bucket_key": _bucket_signature(bucket_key),
            "bucket_rank": bucket_rank,
            "bucket_size": bucket_size,
            "split_counts": {
                "train": counts[0],
                "validation": counts[1],
                "test": counts[2],
            },
            "split_ratios": ratios.as_dict(),
        }
    )
    return DatasetSplitContext(
        episode_id=episode.episode_id,
        split_key=(bucket_key, split_name, int(split_seed)),
        split_regime=MAIN_SPLIT_REGIME,
        split_name=split_name,
        split_seed=split_seed,
        metadata=metadata,
    )


def split_dataset_episodes(
    episodes: Sequence[DatasetEpisode],
    *,
    seed: int,
    ratios: DatasetSplitRatios = DEFAULT_SPLIT_RATIOS,
) -> tuple[DatasetSplitAssignment, ...]:
    """Assign complete episodes to train/validation/test splits deterministically."""

    normalized_episodes = tuple(episodes)
    if not normalized_episodes:
        return ()

    grouped: dict[tuple[object, ...], list[tuple[int, DatasetEpisode]]] = {}
    for episode in normalized_episodes:
        bucket_key = _bucket_key_for_episode(episode)
        grouped.setdefault(bucket_key, []).append((_rank_token(seed, bucket_key, episode.episode_id), episode))

    assignments: list[DatasetSplitAssignment] = []
    for bucket_key in sorted(grouped, key=_bucket_signature):
        ranked_episodes = sorted(grouped[bucket_key], key=lambda item: (item[0], item[1].episode_id))
        counts = _largest_remainder_counts(len(ranked_episodes), ratios.as_tuple())
        offset = 0
        for split_index, split_name in enumerate(SPLIT_NAMES):
            split_count = counts[split_index]
            for bucket_rank, (_, episode) in enumerate(ranked_episodes[offset : offset + split_count], start=offset):
                split_context = _build_split_context(
                    episode,
                    split_name=split_name,
                    split_seed=seed,
                    bucket_key=bucket_key,
                    bucket_rank=bucket_rank,
                    bucket_size=len(ranked_episodes),
                    ratios=ratios,
                    counts=counts,
                )
                assignments.append(
                    DatasetSplitAssignment(
                        episode=episode,
                        split_context=split_context,
                        bucket_key=bucket_key,
                        bucket_rank=bucket_rank,
                        bucket_size=len(ranked_episodes),
                    )
                )
            offset += split_count

    return tuple(assignments)
