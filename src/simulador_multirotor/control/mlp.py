"""MLP training, checkpointing, and inference adapter for Phase 3."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence
import json
import random

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ..core.contracts import TrajectoryReference, VehicleCommand, VehicleIntent, VehicleObservation
from ..dataset import (
    DatasetEpisode,
    DatasetSplitAssignment,
    DatasetWindow,
    MLP_DEFAULT_STRIDE,
    MLP_DEFAULT_WINDOW_SIZE,
    build_feature_vector_from_observation,
    build_mlp_windows,
    feature_dimension_for_mode,
    feature_names_for_mode,
    split_dataset_episodes,
    target_names,
)
from .contract import ControllerContract


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _coerce_float(value: object, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a real number") from exc
    if not np.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _coerce_int(value: object, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc


def _coerce_tuple_of_ints(values: Sequence[object], field_name: str) -> tuple[int, ...]:
    return tuple(_coerce_int(value, field_name) for value in values)


def _window_step_features(window: DatasetWindow) -> np.ndarray:
    if window.features.ndim == 1:
        return window.features.reshape(window.window_size, window.feature_dimension)
    return np.asarray(window.features, dtype=np.float64)


def _stack_training_features(windows: Sequence[DatasetWindow]) -> np.ndarray:
    if not windows:
        raise ValueError("at least one training window is required")
    stacked = np.concatenate([_window_step_features(window) for window in windows], axis=0)
    return np.asarray(stacked, dtype=np.float64)


def _normalize_mode(mode: str) -> str:
    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in ("raw_observation", "observation_plus_tracking_errors"):
        raise ValueError(f"unsupported feature mode: {mode}")
    return normalized_mode


def _seed_everything(seed: int) -> None:
    normalized_seed = int(seed)
    random.seed(normalized_seed)
    np.random.seed(normalized_seed)
    torch.manual_seed(normalized_seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass


@dataclass(frozen=True, slots=True)
class MLPTrainingConfig:
    """Reproducible training configuration for the Phase 3 MLP slice."""

    seed: int = 7
    split_seed: int | None = None
    feature_mode: str = "observation_plus_tracking_errors"
    window_size: int = MLP_DEFAULT_WINDOW_SIZE
    stride: int = MLP_DEFAULT_STRIDE
    hidden_layers: tuple[int, ...] = (128, 64)
    epochs: int = 6
    batch_size: int = 16
    learning_rate: float = 1e-3
    weight_decay: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "seed", _coerce_int(self.seed, "seed"))
        object.__setattr__(self, "split_seed", None if self.split_seed is None else _coerce_int(self.split_seed, "split_seed"))
        object.__setattr__(self, "feature_mode", _normalize_mode(self.feature_mode))
        object.__setattr__(self, "window_size", _coerce_int(self.window_size, "window_size"))
        object.__setattr__(self, "stride", _coerce_int(self.stride, "stride"))
        object.__setattr__(self, "hidden_layers", _coerce_tuple_of_ints(self.hidden_layers, "hidden_layers"))
        object.__setattr__(self, "epochs", _coerce_int(self.epochs, "epochs"))
        object.__setattr__(self, "batch_size", _coerce_int(self.batch_size, "batch_size"))
        object.__setattr__(self, "learning_rate", _coerce_float(self.learning_rate, "learning_rate"))
        object.__setattr__(self, "weight_decay", _coerce_float(self.weight_decay, "weight_decay"))
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if self.stride <= 0:
            raise ValueError("stride must be positive")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")
        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must be non-negative")

    @property
    def effective_split_seed(self) -> int:
        return self.seed if self.split_seed is None else self.split_seed

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "split_seed": self.split_seed,
            "feature_mode": self.feature_mode,
            "window_size": self.window_size,
            "stride": self.stride,
            "hidden_layers": list(self.hidden_layers),
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
        }


@dataclass(frozen=True, slots=True)
class MLPArchitectureConfig:
    """Architecture metadata persisted with the checkpoint."""

    input_dimension: int
    hidden_layers: tuple[int, ...] = (128, 64)
    output_dimension: int = 4
    activation: str = "relu"

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_dimension", _coerce_int(self.input_dimension, "input_dimension"))
        object.__setattr__(self, "hidden_layers", _coerce_tuple_of_ints(self.hidden_layers, "hidden_layers"))
        object.__setattr__(self, "output_dimension", _coerce_int(self.output_dimension, "output_dimension"))
        activation = str(self.activation).strip().lower()
        if activation != "relu":
            raise ValueError("only relu activation is supported in this slice")
        object.__setattr__(self, "activation", activation)
        if self.input_dimension <= 0:
            raise ValueError("input_dimension must be positive")
        if self.output_dimension <= 0:
            raise ValueError("output_dimension must be positive")
        if any(layer <= 0 for layer in self.hidden_layers):
            raise ValueError("hidden_layers must contain positive integers")

    def as_dict(self) -> dict[str, object]:
        return {
            "input_dimension": self.input_dimension,
            "hidden_layers": list(self.hidden_layers),
            "output_dimension": self.output_dimension,
            "activation": self.activation,
        }

    def build_module(self) -> nn.Module:
        layers: list[nn.Module] = []
        dimensions = (self.input_dimension, *self.hidden_layers, self.output_dimension)
        for index in range(len(dimensions) - 1):
            layers.append(nn.Linear(dimensions[index], dimensions[index + 1]))
            if index < len(dimensions) - 2:
                layers.append(nn.ReLU())
        return nn.Sequential(*layers)


@dataclass(frozen=True, slots=True)
class FeatureNormalizationStats:
    """Train-only normalization statistics stored with the checkpoint."""

    feature_mode: str
    feature_dimension: int
    window_size: int
    mean: tuple[float, ...]
    std: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "feature_mode", _normalize_mode(self.feature_mode))
        object.__setattr__(self, "feature_dimension", _coerce_int(self.feature_dimension, "feature_dimension"))
        object.__setattr__(self, "window_size", _coerce_int(self.window_size, "window_size"))
        object.__setattr__(self, "mean", tuple(float(value) for value in self.mean))
        object.__setattr__(self, "std", tuple(float(value) for value in self.std))
        if self.feature_dimension <= 0:
            raise ValueError("feature_dimension must be positive")
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if len(self.mean) != self.feature_dimension or len(self.std) != self.feature_dimension:
            raise ValueError("mean and std must match feature_dimension")
        if any(not np.isfinite(value) for value in self.mean):
            raise ValueError("mean must contain finite values")
        if any(not np.isfinite(value) for value in self.std):
            raise ValueError("std must contain finite values")

    @classmethod
    def from_windows(cls, windows: Sequence[DatasetWindow], *, feature_mode: str, window_size: int) -> "FeatureNormalizationStats":
        if not windows:
            raise ValueError("at least one training window is required to compute normalization")
        feature_dimension = feature_dimension_for_mode(feature_mode)
        stacked = _stack_training_features(windows)
        mean = stacked.mean(axis=0)
        std = stacked.std(axis=0)
        std = np.where(std < 1e-12, 1.0, std)
        return cls(
            feature_mode=feature_mode,
            feature_dimension=feature_dimension,
            window_size=window_size,
            mean=tuple(float(value) for value in mean),
            std=tuple(float(value) for value in std),
        )

    def normalize_window(self, features: np.ndarray) -> np.ndarray:
        array = np.asarray(features, dtype=np.float64)
        mean = np.asarray(self.mean, dtype=np.float64)
        std = np.asarray(self.std, dtype=np.float64)
        if array.ndim == 1:
            if array.shape != (self.feature_dimension,):
                raise ValueError("feature vector has an unexpected dimension")
            return (array - mean) / std
        if array.ndim == 2:
            if array.shape != (self.window_size, self.feature_dimension):
                raise ValueError("feature window has an unexpected shape")
            return (array - mean) / std
        if array.ndim == 3:
            if array.shape[1:] != (self.window_size, self.feature_dimension):
                raise ValueError("feature batch has an unexpected shape")
            return (array - mean.reshape(1, 1, -1)) / std.reshape(1, 1, -1)
        raise ValueError("feature data has an unexpected shape")

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_mode": self.feature_mode,
            "feature_dimension": self.feature_dimension,
            "window_size": self.window_size,
            "mean": list(self.mean),
            "std": list(self.std),
        }


@dataclass(frozen=True, slots=True)
class MLPTrainingHistoryEntry:
    epoch: int
    train_loss: float
    validation_loss: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "epoch", _coerce_int(self.epoch, "epoch"))
        object.__setattr__(self, "train_loss", _coerce_float(self.train_loss, "train_loss"))
        object.__setattr__(self, "validation_loss", _coerce_float(self.validation_loss, "validation_loss"))

    def as_dict(self) -> dict[str, object]:
        return {
            "epoch": self.epoch,
            "train_loss": self.train_loss,
            "validation_loss": self.validation_loss,
        }


@dataclass(frozen=True, slots=True)
class MLPCheckpoint:
    """Auditable artifact for an MLP controller."""

    format_version: int
    architecture: MLPArchitectureConfig
    training: MLPTrainingConfig
    normalization: FeatureNormalizationStats
    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]
    split_seed: int
    split_ratios: dict[str, float]
    model_state_dict: Mapping[str, torch.Tensor]
    history: tuple[MLPTrainingHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "format_version", _coerce_int(self.format_version, "format_version"))
        object.__setattr__(self, "feature_names", tuple(str(name) for name in self.feature_names))
        object.__setattr__(self, "target_names", tuple(str(name) for name in self.target_names))
        object.__setattr__(self, "split_seed", _coerce_int(self.split_seed, "split_seed"))
        object.__setattr__(self, "split_ratios", {str(key): float(value) for key, value in dict(self.split_ratios).items()})
        object.__setattr__(self, "history", tuple(self.history))
        if self.format_version != 1:
            raise ValueError(f"unsupported checkpoint format version: {self.format_version}")
        if not self.feature_names:
            raise ValueError("feature_names must not be empty")
        if not self.target_names:
            raise ValueError("target_names must not be empty")

    @property
    def input_dimension(self) -> int:
        return self.architecture.input_dimension

    @property
    def output_dimension(self) -> int:
        return self.architecture.output_dimension

    def to_payload(self) -> dict[str, object]:
        return {
            "format_version": self.format_version,
            "architecture": self.architecture.as_dict(),
            "training": self.training.as_dict(),
            "normalization": self.normalization.as_dict(),
            "feature_names": list(self.feature_names),
            "target_names": list(self.target_names),
            "split_seed": self.split_seed,
            "split_ratios": dict(self.split_ratios),
            "history": [entry.as_dict() for entry in self.history],
            "model_state_dict": dict(self.model_state_dict),
        }

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.to_payload(), output_path)
        return output_path

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "MLPCheckpoint":
        architecture = MLPArchitectureConfig(**payload["architecture"])
        training = MLPTrainingConfig(**payload["training"])
        normalization = FeatureNormalizationStats(**payload["normalization"])
        history = tuple(MLPTrainingHistoryEntry(**entry) for entry in payload.get("history", ()))
        return cls(
            format_version=payload["format_version"],
            architecture=architecture,
            training=training,
            normalization=normalization,
            feature_names=tuple(payload["feature_names"]),
            target_names=tuple(payload["target_names"]),
            split_seed=payload["split_seed"],
            split_ratios=dict(payload.get("split_ratios", {})),
            model_state_dict=payload["model_state_dict"],
            history=history,
        )

    @classmethod
    def load(cls, path: str | Path) -> "MLPCheckpoint":
        resolved_path = Path(path)
        try:
            payload = torch.load(resolved_path, map_location="cpu", weights_only=False)
        except TypeError:
            payload = torch.load(resolved_path, map_location="cpu")
        if not isinstance(payload, Mapping):
            raise ValueError("checkpoint payload must be a mapping")
        return cls.from_payload(payload)

    def build_model(self) -> nn.Module:
        model = self.architecture.build_module()
        state_dict = dict(self.model_state_dict)
        if state_dict and all(key.startswith("network.") for key in state_dict):
            state_dict = {key.removeprefix("network."): value for key, value in state_dict.items()}
        model.load_state_dict(state_dict)
        model.eval()
        return model


@dataclass(frozen=True, slots=True)
class MLPTrainingResult:
    checkpoint: MLPCheckpoint
    checkpoint_path: Path | None
    train_loss: float
    validation_loss: float
    history: tuple[MLPTrainingHistoryEntry, ...]
    train_window_count: int
    validation_window_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "checkpoint_path": None if self.checkpoint_path is None else str(self.checkpoint_path),
            "train_loss": self.train_loss,
            "validation_loss": self.validation_loss,
            "history": [entry.as_dict() for entry in self.history],
            "train_window_count": self.train_window_count,
            "validation_window_count": self.validation_window_count,
            "checkpoint": self.checkpoint.to_payload(),
        }


def _window_arrays(windows: Sequence[DatasetWindow]) -> tuple[np.ndarray, np.ndarray]:
    if not windows:
        raise ValueError("windows must not be empty")
    feature_dimension = windows[0].feature_dimension
    flattened = np.asarray(
        [
            _window_step_features(window).reshape(window.window_size, feature_dimension).reshape(-1)
            for window in windows
        ],
        dtype=np.float32,
    )
    targets = np.asarray([window.target for window in windows], dtype=np.float32)
    return flattened, targets


class _MLPRegressor(nn.Module):
    def __init__(self, architecture: MLPArchitectureConfig) -> None:
        super().__init__()
        self.network = architecture.build_module()

    def forward(self, features: torch.Tensor) -> torch.Tensor:  # pragma: no cover - tiny adapter
        return self.network(features)


def _select_windows(
    assignments: Sequence[DatasetSplitAssignment],
    *,
    feature_mode: str,
    window_size: int,
    stride: int,
) -> tuple[list[DatasetWindow], list[DatasetWindow], list[DatasetWindow]]:
    train_windows: list[DatasetWindow] = []
    validation_windows: list[DatasetWindow] = []
    test_windows: list[DatasetWindow] = []
    for assignment in assignments:
        windows = build_mlp_windows(
            assignment,
            window_size=window_size,
            stride=stride,
            feature_mode=feature_mode,
        )
        if assignment.split_name == "train":
            train_windows.extend(windows)
        elif assignment.split_name == "validation":
            validation_windows.extend(windows)
        elif assignment.split_name == "test":
            test_windows.extend(windows)
    return train_windows, validation_windows, test_windows


def train_mlp_checkpoint(
    episodes: Sequence[DatasetEpisode],
    *,
    checkpoint_path: str | Path | None = None,
    config: MLPTrainingConfig = MLPTrainingConfig(),
) -> MLPTrainingResult:
    episodes = tuple(episodes)
    if not episodes:
        raise ValueError("episodes must not be empty")
    _seed_everything(config.seed)
    assignments = split_dataset_episodes(episodes, seed=config.effective_split_seed)
    train_windows, validation_windows, _ = _select_windows(
        assignments,
        feature_mode=config.feature_mode,
        window_size=config.window_size,
        stride=config.stride,
    )
    if not train_windows:
        raise ValueError("train split produced no windows")
    if not validation_windows:
        raise ValueError("validation split produced no windows")

    normalization = FeatureNormalizationStats.from_windows(
        train_windows,
        feature_mode=config.feature_mode,
        window_size=config.window_size,
    )
    train_features, train_targets = _window_arrays(train_windows)
    validation_features, validation_targets = _window_arrays(validation_windows)

    feature_dimension = feature_dimension_for_mode(config.feature_mode)
    architecture = MLPArchitectureConfig(
        input_dimension=config.window_size * feature_dimension,
        hidden_layers=config.hidden_layers,
        output_dimension=len(target_names()),
    )
    model = _MLPRegressor(architecture)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    loss_fn = nn.MSELoss()
    validation_targets_tensor = torch.from_numpy(validation_targets)

    train_dataset = TensorDataset(torch.from_numpy(train_features), torch.from_numpy(train_targets))
    generator = torch.Generator().manual_seed(config.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
        drop_last=False,
    )

    history: list[MLPTrainingHistoryEntry] = []
    for epoch in range(1, config.epochs + 1):
        model.train()
        epoch_loss = 0.0
        sample_count = 0
        for batch_features, batch_targets in train_loader:
            normalized_batch = normalization.normalize_window(batch_features.numpy().reshape(-1, config.window_size, feature_dimension)).reshape(
                batch_features.shape[0],
                -1,
            )
            batch_inputs = torch.from_numpy(np.asarray(normalized_batch, dtype=np.float32))
            optimizer.zero_grad()
            predictions = model(batch_inputs)
            loss = loss_fn(predictions, batch_targets)
            loss.backward()
            optimizer.step()
            batch_size = int(batch_features.shape[0])
            epoch_loss += float(loss.item()) * batch_size
            sample_count += batch_size
        train_loss = epoch_loss / sample_count
        model.eval()
        with torch.no_grad():
            validation_inputs = normalization.normalize_window(
                validation_features.reshape(-1, config.window_size, feature_dimension)
            ).reshape(validation_features.shape[0], -1)
            validation_predictions = model(torch.from_numpy(np.asarray(validation_inputs, dtype=np.float32)))
            validation_loss = float(loss_fn(validation_predictions, validation_targets_tensor).item())
        history.append(
            MLPTrainingHistoryEntry(
                epoch=epoch,
                train_loss=train_loss,
                validation_loss=validation_loss,
            )
        )

    checkpoint = MLPCheckpoint(
        format_version=1,
        architecture=architecture,
        training=config,
        normalization=normalization,
        feature_names=feature_names_for_mode(config.feature_mode),
        target_names=target_names(),
        split_seed=config.effective_split_seed,
        split_ratios={"train": 0.7, "validation": 0.15, "test": 0.15},
        model_state_dict=model.network.state_dict(),
        history=tuple(history),
    )
    saved_checkpoint_path = None if checkpoint_path is None else checkpoint.save(checkpoint_path)
    return MLPTrainingResult(
        checkpoint=checkpoint,
        checkpoint_path=saved_checkpoint_path,
        train_loss=history[-1].train_loss,
        validation_loss=history[-1].validation_loss,
        history=tuple(history),
        train_window_count=len(train_windows),
        validation_window_count=len(validation_windows),
    )


def _feature_vector_for_controller(
    observation: VehicleObservation,
    reference: TrajectoryReference,
    *,
    feature_mode: str,
) -> np.ndarray:
    values = build_feature_vector_from_observation(observation, reference, feature_mode)
    return np.asarray(values, dtype=np.float64)


@dataclass(slots=True)
class MLPController(ControllerContract):
    checkpoint: MLPCheckpoint
    model: nn.Module = field(repr=False)
    kind: str = "mlp"
    source: str = "torch"
    parameters: Mapping[str, object] = field(default_factory=dict)
    _feature_history: deque[np.ndarray] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", str(self.kind).strip().lower() or "mlp")
        object.__setattr__(self, "source", str(self.source).strip().lower() or "torch")
        if not self.parameters:
            object.__setattr__(
                self,
                "parameters",
                {
                    "checkpoint_format_version": self.checkpoint.format_version,
                    "feature_mode": self.checkpoint.training.feature_mode,
                    "window_size": self.checkpoint.training.window_size,
                    "stride": self.checkpoint.training.stride,
                    "hidden_layers": list(self.checkpoint.architecture.hidden_layers),
                },
            )
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))
        self._feature_history: deque[np.ndarray] = deque(maxlen=self.checkpoint.training.window_size)
        self.model.eval()

    @classmethod
    def from_checkpoint(cls, checkpoint: MLPCheckpoint) -> "MLPController":
        return cls(checkpoint=checkpoint, model=checkpoint.build_model())

    def reset(self) -> None:
        self._feature_history.clear()

    def compute_action(
        self,
        observation: VehicleObservation,
        reference: TrajectoryReference,
    ) -> VehicleCommand:
        feature_vector = _feature_vector_for_controller(
            observation,
            reference,
            feature_mode=self.checkpoint.training.feature_mode,
        )
        self._feature_history.append(feature_vector)
        history = list(self._feature_history)
        if len(history) < self.checkpoint.training.window_size:
            pad = [history[0]] * (self.checkpoint.training.window_size - len(history))
            history = pad + history
        window = np.asarray(history, dtype=np.float64)
        normalized_window = self.checkpoint.normalization.normalize_window(window)
        inputs = torch.from_numpy(np.asarray(normalized_window.reshape(1, -1), dtype=np.float32))
        with torch.no_grad():
            predictions = self.model(inputs).squeeze(0).cpu().numpy()
        if not np.all(np.isfinite(predictions)):
            raise ValueError("MLP checkpoint produced non-finite command values")
        thrust = max(0.0, float(predictions[0]))
        torque = (float(predictions[1]), float(predictions[2]), float(predictions[3]))
        return VehicleCommand(
            intent=VehicleIntent(
                collective_thrust_newton=thrust,
                body_torque_nm=torque,
            ),
        )


def load_mlp_checkpoint(path: str | Path) -> MLPCheckpoint:
    return MLPCheckpoint.load(path)


def load_mlp_controller(path: str | Path) -> MLPController:
    return MLPController.from_checkpoint(load_mlp_checkpoint(path))


def dump_checkpoint_summary(path: str | Path, checkpoint: MLPCheckpoint) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = checkpoint.to_payload()
    summary.pop("model_state_dict", None)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
