"""GRU and LSTM training, checkpointing, and inference adapters for Phase 4."""

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
    RECURRENT_DEFAULT_STRIDE,
    RECURRENT_DEFAULT_WINDOW_SIZES,
    build_feature_vector_from_observation,
    build_recurrent_windows,
    feature_dimension_for_mode,
    feature_names_for_mode,
    split_dataset_episodes,
    target_names,
)
from .contract import ControllerContract
from .mlp import FeatureNormalizationStats


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


def _normalize_feature_mode(mode: str) -> str:
    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in ("raw_observation", "observation_plus_tracking_errors"):
        raise ValueError(f"unsupported feature mode: {mode}")
    return normalized_mode


def _normalize_architecture(architecture: str) -> str:
    normalized_architecture = str(architecture).strip().lower()
    if normalized_architecture not in RECURRENT_DEFAULT_WINDOW_SIZES:
        raise ValueError(f"unsupported recurrent architecture: {architecture}")
    return normalized_architecture


def _seed_everything(seed: int) -> None:
    normalized_seed = int(seed)
    random.seed(normalized_seed)
    np.random.seed(normalized_seed)
    torch.manual_seed(normalized_seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass


def _window_step_features(window: DatasetWindow) -> np.ndarray:
    if window.features.ndim == 1:
        return window.features.reshape(window.window_size, window.feature_dimension)
    return np.asarray(window.features, dtype=np.float64)


def _stack_training_features(windows: Sequence[DatasetWindow]) -> np.ndarray:
    if not windows:
        raise ValueError("at least one training window is required")
    stacked = np.concatenate([_window_step_features(window) for window in windows], axis=0)
    return np.asarray(stacked, dtype=np.float64)


def _window_sequences(windows: Sequence[DatasetWindow]) -> tuple[np.ndarray, np.ndarray]:
    if not windows:
        raise ValueError("windows must not be empty")
    features = np.asarray([_window_step_features(window) for window in windows], dtype=np.float32)
    targets = np.asarray([window.target for window in windows], dtype=np.float32)
    return features, targets


@dataclass(frozen=True, slots=True)
class RecurrentTrainingConfig:
    """Reproducible training configuration for GRU and LSTM slices."""

    architecture: str = "gru"
    seed: int = 7
    split_seed: int | None = None
    feature_mode: str = "observation_plus_tracking_errors"
    window_size: int | None = None
    stride: int = RECURRENT_DEFAULT_STRIDE
    hidden_size: int = 64
    num_layers: int = 1
    epochs: int = 6
    batch_size: int = 16
    learning_rate: float = 1e-3
    weight_decay: float = 0.0
    dropout: float = 0.0

    def __post_init__(self) -> None:
        architecture = _normalize_architecture(self.architecture)
        object.__setattr__(self, "architecture", architecture)
        object.__setattr__(self, "seed", _coerce_int(self.seed, "seed"))
        object.__setattr__(self, "split_seed", None if self.split_seed is None else _coerce_int(self.split_seed, "split_seed"))
        object.__setattr__(self, "feature_mode", _normalize_feature_mode(self.feature_mode))
        resolved_window_size = RECURRENT_DEFAULT_WINDOW_SIZES[architecture] if self.window_size is None else _coerce_int(self.window_size, "window_size")
        object.__setattr__(self, "window_size", resolved_window_size)
        object.__setattr__(self, "stride", _coerce_int(self.stride, "stride"))
        object.__setattr__(self, "hidden_size", _coerce_int(self.hidden_size, "hidden_size"))
        object.__setattr__(self, "num_layers", _coerce_int(self.num_layers, "num_layers"))
        object.__setattr__(self, "epochs", _coerce_int(self.epochs, "epochs"))
        object.__setattr__(self, "batch_size", _coerce_int(self.batch_size, "batch_size"))
        object.__setattr__(self, "learning_rate", _coerce_float(self.learning_rate, "learning_rate"))
        object.__setattr__(self, "weight_decay", _coerce_float(self.weight_decay, "weight_decay"))
        object.__setattr__(self, "dropout", _coerce_float(self.dropout, "dropout"))
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if self.stride <= 0:
            raise ValueError("stride must be positive")
        if self.hidden_size <= 0:
            raise ValueError("hidden_size must be positive")
        if self.num_layers <= 0:
            raise ValueError("num_layers must be positive")
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")
        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must be non-negative")
        if self.dropout < 0.0:
            raise ValueError("dropout must be non-negative")

    @property
    def effective_split_seed(self) -> int:
        return self.seed if self.split_seed is None else self.split_seed

    def as_dict(self) -> dict[str, object]:
        return {
            "architecture": self.architecture,
            "seed": self.seed,
            "split_seed": self.split_seed,
            "feature_mode": self.feature_mode,
            "window_size": self.window_size,
            "stride": self.stride,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "dropout": self.dropout,
        }


@dataclass(frozen=True, slots=True)
class RecurrentTrainingHistoryEntry:
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


class _RecurrentRegressor(nn.Module):
    def __init__(
        self,
        *,
        architecture: str,
        input_dimension: int,
        hidden_size: int,
        num_layers: int,
        output_dimension: int,
        dropout: float,
    ) -> None:
        super().__init__()
        normalized_architecture = _normalize_architecture(architecture)
        self.architecture = normalized_architecture
        recurrent_dropout = dropout if num_layers > 1 else 0.0
        recurrent_kwargs = {
            "input_size": input_dimension,
            "hidden_size": hidden_size,
            "num_layers": num_layers,
            "batch_first": True,
            "dropout": recurrent_dropout,
        }
        if normalized_architecture == "gru":
            self.recurrent = nn.GRU(**recurrent_kwargs)
        else:
            self.recurrent = nn.LSTM(**recurrent_kwargs)
        self.head = nn.Linear(hidden_size, output_dimension)

    def forward(self, features: torch.Tensor) -> torch.Tensor:  # pragma: no cover - tiny adapter
        if features.ndim != 3:
            raise ValueError("recurrent features must have shape (batch, sequence, feature)")
        outputs, hidden_state = self.recurrent(features)
        del outputs
        if self.architecture == "lstm":
            hidden_state = hidden_state[0]
        return self.head(hidden_state[-1])


@dataclass(frozen=True, slots=True)
class RecurrentCheckpoint:
    """Auditable artifact for a recurrent controller."""

    format_version: int
    training: RecurrentTrainingConfig
    normalization: FeatureNormalizationStats
    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]
    split_seed: int
    split_ratios: dict[str, float]
    model_state_dict: Mapping[str, torch.Tensor]
    history: tuple[RecurrentTrainingHistoryEntry, ...] = ()

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
        return feature_dimension_for_mode(self.training.feature_mode)

    @property
    def output_dimension(self) -> int:
        return len(self.target_names)

    def to_payload(self) -> dict[str, object]:
        return {
            "format_version": self.format_version,
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
    def from_payload(cls, payload: Mapping[str, object]) -> "RecurrentCheckpoint":
        training = RecurrentTrainingConfig(**payload["training"])
        normalization = FeatureNormalizationStats(**payload["normalization"])
        history = tuple(RecurrentTrainingHistoryEntry(**entry) for entry in payload.get("history", ()))
        return cls(
            format_version=payload["format_version"],
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
    def load(cls, path: str | Path) -> "RecurrentCheckpoint":
        resolved_path = Path(path)
        try:
            payload = torch.load(resolved_path, map_location="cpu", weights_only=False)
        except TypeError:
            payload = torch.load(resolved_path, map_location="cpu")
        if not isinstance(payload, Mapping):
            raise ValueError("checkpoint payload must be a mapping")
        return cls.from_payload(payload)

    def build_model(self) -> nn.Module:
        model = _RecurrentRegressor(
            architecture=self.training.architecture,
            input_dimension=self.input_dimension,
            hidden_size=self.training.hidden_size,
            num_layers=self.training.num_layers,
            output_dimension=self.output_dimension,
            dropout=self.training.dropout,
        )
        state_dict = dict(self.model_state_dict)
        if state_dict and all(key.startswith("network.") for key in state_dict):
            state_dict = {key.removeprefix("network."): value for key, value in state_dict.items()}
        model.load_state_dict(state_dict)
        model.eval()
        return model


@dataclass(frozen=True, slots=True)
class RecurrentTrainingResult:
    checkpoint: RecurrentCheckpoint
    checkpoint_path: Path | None
    train_loss: float
    validation_loss: float
    history: tuple[RecurrentTrainingHistoryEntry, ...]
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


def _select_windows(
    assignments: Sequence[DatasetSplitAssignment],
    *,
    architecture: str,
    feature_mode: str,
    window_size: int,
    stride: int,
) -> tuple[list[DatasetWindow], list[DatasetWindow], list[DatasetWindow]]:
    train_windows: list[DatasetWindow] = []
    validation_windows: list[DatasetWindow] = []
    test_windows: list[DatasetWindow] = []
    for assignment in assignments:
        windows = build_recurrent_windows(
            assignment,
            architecture=architecture,
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


def train_recurrent_checkpoint(
    episodes: Sequence[DatasetEpisode],
    *,
    architecture: str,
    checkpoint_path: str | Path | None = None,
    config: RecurrentTrainingConfig | None = None,
) -> RecurrentTrainingResult:
    episodes = tuple(episodes)
    if not episodes:
        raise ValueError("episodes must not be empty")
    resolved_config = RecurrentTrainingConfig(architecture=architecture) if config is None else config
    if resolved_config.architecture != _normalize_architecture(architecture):
        raise ValueError("config architecture does not match the requested architecture")

    _seed_everything(resolved_config.seed)
    assignments = split_dataset_episodes(episodes, seed=resolved_config.effective_split_seed)
    train_windows, validation_windows, _ = _select_windows(
        assignments,
        architecture=resolved_config.architecture,
        feature_mode=resolved_config.feature_mode,
        window_size=resolved_config.window_size,
        stride=resolved_config.stride,
    )
    if not train_windows:
        raise ValueError("train split produced no windows")
    if not validation_windows:
        raise ValueError("validation split produced no windows")

    normalization = FeatureNormalizationStats.from_windows(
        train_windows,
        feature_mode=resolved_config.feature_mode,
        window_size=resolved_config.window_size,
    )
    train_features, train_targets = _window_sequences(train_windows)
    validation_features, validation_targets = _window_sequences(validation_windows)

    model = _RecurrentRegressor(
        architecture=resolved_config.architecture,
        input_dimension=feature_dimension_for_mode(resolved_config.feature_mode),
        hidden_size=resolved_config.hidden_size,
        num_layers=resolved_config.num_layers,
        output_dimension=len(target_names()),
        dropout=resolved_config.dropout,
    )
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=resolved_config.learning_rate,
        weight_decay=resolved_config.weight_decay,
    )
    loss_fn = nn.MSELoss()
    validation_targets_tensor = torch.from_numpy(validation_targets)

    train_dataset = TensorDataset(torch.from_numpy(train_features), torch.from_numpy(train_targets))
    generator = torch.Generator().manual_seed(resolved_config.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=resolved_config.batch_size,
        shuffle=True,
        generator=generator,
        drop_last=False,
    )

    history: list[RecurrentTrainingHistoryEntry] = []
    for epoch in range(1, resolved_config.epochs + 1):
        model.train()
        epoch_loss = 0.0
        sample_count = 0
        for batch_features, batch_targets in train_loader:
            normalized_batch = normalization.normalize_window(batch_features.numpy())
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
            validation_inputs = normalization.normalize_window(validation_features)
            validation_predictions = model(torch.from_numpy(np.asarray(validation_inputs, dtype=np.float32)))
            validation_loss = float(loss_fn(validation_predictions, validation_targets_tensor).item())
        history.append(
            RecurrentTrainingHistoryEntry(
                epoch=epoch,
                train_loss=train_loss,
                validation_loss=validation_loss,
            )
        )

    checkpoint = RecurrentCheckpoint(
        format_version=1,
        training=resolved_config,
        normalization=normalization,
        feature_names=feature_names_for_mode(resolved_config.feature_mode),
        target_names=target_names(),
        split_seed=resolved_config.effective_split_seed,
        split_ratios={"train": 0.7, "validation": 0.15, "test": 0.15},
        model_state_dict=model.state_dict(),
        history=tuple(history),
    )
    saved_checkpoint_path = None if checkpoint_path is None else checkpoint.save(checkpoint_path)
    return RecurrentTrainingResult(
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
class RecurrentController(ControllerContract):
    checkpoint: RecurrentCheckpoint
    model: nn.Module = field(repr=False)
    kind: str = "gru"
    source: str = "torch"
    parameters: Mapping[str, object] = field(default_factory=dict)
    _feature_history: deque[np.ndarray] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        kind = self.checkpoint.training.architecture
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source", str(self.source).strip().lower() or "torch")
        if not self.parameters:
            object.__setattr__(
                self,
                "parameters",
                {
                    "checkpoint_format_version": self.checkpoint.format_version,
                    "architecture": self.checkpoint.training.architecture,
                    "feature_mode": self.checkpoint.training.feature_mode,
                    "window_size": self.checkpoint.training.window_size,
                    "stride": self.checkpoint.training.stride,
                    "hidden_size": self.checkpoint.training.hidden_size,
                    "num_layers": self.checkpoint.training.num_layers,
                },
            )
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))
        self._feature_history = deque(maxlen=self.checkpoint.training.window_size)
        self.model.eval()

    @classmethod
    def from_checkpoint(cls, checkpoint: RecurrentCheckpoint) -> "RecurrentController":
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
        inputs = torch.from_numpy(np.asarray(normalized_window.reshape(1, *normalized_window.shape), dtype=np.float32))
        with torch.no_grad():
            predictions = self.model(inputs).squeeze(0).cpu().numpy()
        if not np.all(np.isfinite(predictions)):
            raise ValueError("recurrent checkpoint produced non-finite command values")
        thrust = max(0.0, float(predictions[0]))
        torque = (float(predictions[1]), float(predictions[2]), float(predictions[3]))
        return VehicleCommand(
            intent=VehicleIntent(
                collective_thrust_newton=thrust,
                body_torque_nm=torque,
            ),
        )


def load_recurrent_checkpoint(path: str | Path) -> RecurrentCheckpoint:
    return RecurrentCheckpoint.load(path)


def load_recurrent_controller(path: str | Path) -> RecurrentController:
    return RecurrentController.from_checkpoint(load_recurrent_checkpoint(path))


def train_gru_checkpoint(
    episodes: Sequence[DatasetEpisode],
    *,
    checkpoint_path: str | Path | None = None,
    config: RecurrentTrainingConfig = RecurrentTrainingConfig(architecture="gru"),
) -> RecurrentTrainingResult:
    if config.architecture != "gru":
        raise ValueError("config architecture must be gru")
    return train_recurrent_checkpoint(
        episodes,
        architecture="gru",
        checkpoint_path=checkpoint_path,
        config=config,
    )


def train_lstm_checkpoint(
    episodes: Sequence[DatasetEpisode],
    *,
    checkpoint_path: str | Path | None = None,
    config: RecurrentTrainingConfig = RecurrentTrainingConfig(architecture="lstm"),
) -> RecurrentTrainingResult:
    if config.architecture != "lstm":
        raise ValueError("config architecture must be lstm")
    return train_recurrent_checkpoint(
        episodes,
        architecture="lstm",
        checkpoint_path=checkpoint_path,
        config=config,
    )


def load_gru_controller(path: str | Path) -> RecurrentController:
    controller = load_recurrent_controller(path)
    if controller.kind != "gru":
        raise ValueError("checkpoint does not contain a GRU controller")
    return controller


def load_lstm_controller(path: str | Path) -> RecurrentController:
    controller = load_recurrent_controller(path)
    if controller.kind != "lstm":
        raise ValueError("checkpoint does not contain an LSTM controller")
    return controller


def checkpoint_summary_payload(
    checkpoint: RecurrentCheckpoint,
    *,
    training_result: RecurrentTrainingResult | None = None,
    checkpoint_path: str | Path | None = None,
) -> dict[str, object]:
    history = training_result.history if training_result is not None else checkpoint.history
    if training_result is not None:
        train_loss = training_result.train_loss
        validation_loss = training_result.validation_loss
        train_window_count = training_result.train_window_count
        validation_window_count = training_result.validation_window_count
    elif history:
        last_entry = history[-1]
        train_loss = last_entry.train_loss
        validation_loss = last_entry.validation_loss
        train_window_count = None
        validation_window_count = None
    else:
        train_loss = None
        validation_loss = None
        train_window_count = None
        validation_window_count = None
    return {
        "format_version": checkpoint.format_version,
        "checkpoint_kind": checkpoint.training.architecture,
        "checkpoint_path": None if checkpoint_path is None else str(checkpoint_path),
        "training": checkpoint.training.as_dict(),
        "normalization": checkpoint.normalization.as_dict(),
        "feature_names": list(checkpoint.feature_names),
        "target_names": list(checkpoint.target_names),
        "split_seed": checkpoint.split_seed,
        "split_ratios": dict(checkpoint.split_ratios),
        "metrics": {
            "train_loss": train_loss,
            "validation_loss": validation_loss,
            "train_window_count": train_window_count,
            "validation_window_count": validation_window_count,
        },
        "history": [entry.as_dict() for entry in history],
    }


def dump_checkpoint_summary(
    path: str | Path,
    checkpoint: RecurrentCheckpoint,
    *,
    training_result: RecurrentTrainingResult | None = None,
    checkpoint_path: str | Path | None = None,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = checkpoint_summary_payload(
        checkpoint,
        training_result=training_result,
        checkpoint_path=checkpoint_path,
    )
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
