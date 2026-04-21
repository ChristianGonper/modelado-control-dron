"""Dataset artifact persistence helpers for the Phase 2 CLI slice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from pathlib import Path
from typing import Mapping, Sequence

from .contract import DatasetEpisode, PHASE2_DATASET_CONTRACT
from .extract import load_dataset_episodes
from .split import DEFAULT_SPLIT_RATIOS, DatasetSplitAssignment, DatasetSplitRatios, split_dataset_episodes
from .windowing import (
    MLP_DEFAULT_STRIDE,
    MLP_DEFAULT_WINDOW_SIZE,
    RECURRENT_DEFAULT_STRIDE,
    RECURRENT_DEFAULT_WINDOW_SIZES,
    build_mlp_windows,
    build_recurrent_windows,
)


DATASET_STAGE = "dataset"
DATASET_ARTIFACT_KIND = "dataset"
DATASET_MANIFEST_SCHEMA_VERSION = 1
DATASET_ARTIFACT_FILENAMES = ("dataset.json", "manifest.json", "dataset-summary.md")


class DatasetArtifactError(ValueError):
    """Raised when dataset artifact persistence cannot proceed."""


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generate_run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def _resolve_path_list(paths: Sequence[str | Path]) -> tuple[Path, ...]:
    if not paths:
        raise DatasetArtifactError("telemetry inputs must not be empty")

    resolved_paths: list[Path] = []
    seen: set[str] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise DatasetArtifactError(f"telemetry path does not exist: {path}")
        resolved = path.resolve()
        resolved_key = str(resolved).casefold()
        if resolved_key in seen:
            raise DatasetArtifactError(f"telemetry inputs must be unique: {resolved}")
        seen.add(resolved_key)
        resolved_paths.append(resolved)
    return tuple(resolved_paths)


def _resolve_output_dir(
    *,
    workspace: str | Path,
    run_id: str | None,
    output_dir: str | Path | None,
) -> tuple[Path, str, Path]:
    if output_dir is not None:
        resolved_output_dir = Path(output_dir)
        resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _generate_run_id()
        resolved_workspace = resolved_output_dir.parent
        return resolved_output_dir, resolved_run_id, resolved_workspace

    resolved_workspace = Path(workspace)
    resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _generate_run_id()
    return resolved_workspace / resolved_run_id / DATASET_STAGE, resolved_run_id, resolved_workspace


def _load_existing_dataset_manifest(output_dir: Path) -> Mapping[str, object]:
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        ) from exc
    if not isinstance(payload, dict):
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        )
    if payload.get("stage") != DATASET_STAGE or payload.get("artifact_kind") != DATASET_ARTIFACT_KIND:
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        )
    if int(payload.get("schema_version", -1)) != DATASET_MANIFEST_SCHEMA_VERSION:
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        )
    dataset_path_value = payload.get("dataset_path")
    if not isinstance(dataset_path_value, str) or not dataset_path_value.strip():
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        )
    if Path(dataset_path_value).resolve().parent != output_dir.resolve():
        raise DatasetArtifactError(
            f"output directory is not a managed dataset artifact directory: {output_dir}"
        )
    return payload


def _clear_managed_dataset_outputs(output_dir: Path) -> None:
    _load_existing_dataset_manifest(output_dir)
    for filename in DATASET_ARTIFACT_FILENAMES:
        file_path = output_dir / filename
        if file_path.exists():
            file_path.unlink()


def _split_counts(assignments: Sequence[DatasetSplitAssignment]) -> dict[str, int]:
    counts = {name: 0 for name in ("train", "validation", "test", "unassigned")}
    for assignment in assignments:
        counts[assignment.split_name or "unassigned"] += 1
    return counts


def _window_counts(
    assignments: Sequence[DatasetSplitAssignment],
    *,
    feature_mode: str,
) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}

    def _collect(
        architecture: str,
        *,
        window_size: int | None,
        stride: int,
    ) -> None:
        per_split = {name: 0 for name in ("train", "validation", "test")}
        total = 0
        for assignment in assignments:
            if architecture == "mlp":
                windows = build_mlp_windows(
                    assignment,
                    feature_mode=feature_mode,
                    window_size=window_size or MLP_DEFAULT_WINDOW_SIZE,
                    stride=stride,
                )
            else:
                windows = build_recurrent_windows(
                    assignment,
                    architecture=architecture,
                    feature_mode=feature_mode,
                    window_size=window_size,
                    stride=stride,
                )
            count = len(windows)
            total += count
            if assignment.split_name in per_split:
                per_split[assignment.split_name] += count
        summary[architecture] = {
            "window_size": window_size if window_size is not None else RECURRENT_DEFAULT_WINDOW_SIZES[architecture],
            "stride": stride,
            "total_window_count": total,
            "split_window_counts": per_split,
        }

    _collect("mlp", window_size=MLP_DEFAULT_WINDOW_SIZE, stride=MLP_DEFAULT_STRIDE)
    _collect("gru", window_size=None, stride=RECURRENT_DEFAULT_STRIDE)
    _collect("lstm", window_size=None, stride=RECURRENT_DEFAULT_STRIDE)
    return summary


def _episode_payload(
    episode: DatasetEpisode,
    assignment: DatasetSplitAssignment,
    *,
    feature_mode: str,
) -> dict[str, object]:
    window_info: dict[str, object] = {
        "mlp": len(
            build_mlp_windows(
                assignment,
                feature_mode=feature_mode,
                window_size=MLP_DEFAULT_WINDOW_SIZE,
                stride=MLP_DEFAULT_STRIDE,
            )
        ),
        "gru": len(
            build_recurrent_windows(
                assignment,
                architecture="gru",
                feature_mode=feature_mode,
                window_size=None,
                stride=RECURRENT_DEFAULT_STRIDE,
            )
        ),
        "lstm": len(
            build_recurrent_windows(
                assignment,
                architecture="lstm",
                feature_mode=feature_mode,
                window_size=None,
                stride=RECURRENT_DEFAULT_STRIDE,
            )
        ),
    }
    return {
        "episode_id": episode.episode_id,
        "source_path": None if episode.source_path is None else str(episode.source_path),
        "scenario_name": episode.scenario_name,
        "scenario_seed": episode.scenario_seed,
        "controller_kind": episode.controller_kind,
        "controller_source": episode.controller_source,
        "trajectory_kind": episode.trajectory_kind,
        "disturbance_regime": episode.disturbance_regime,
        "sample_count": episode.sample_count,
        "split_name": assignment.split_name,
        "split_seed": assignment.split_seed,
        "split_regime": assignment.split_regime,
        "bucket_key": [str(component) for component in assignment.bucket_key],
        "bucket_rank": assignment.bucket_rank,
        "bucket_size": assignment.bucket_size,
        "traceability": episode.traceability.as_dict(),
        "window_counts": window_info,
    }


def _build_dataset_payload(
    *,
    episodes: Sequence[DatasetEpisode],
    assignments: Sequence[DatasetSplitAssignment],
    source_paths: Sequence[Path],
    run_id: str,
    workspace: Path,
    output_dir: Path,
    dataset_path: Path,
    manifest_path: Path,
    summary_path: Path,
    feature_mode: str,
    seed: int,
    split_seed: int,
    split_ratios: DatasetSplitRatios,
    created_at: str,
    command: str,
    argv: Sequence[str],
) -> dict[str, object]:
    assignment_by_episode_id = {assignment.episode_id: assignment for assignment in assignments}
    return {
        "schema_version": DATASET_MANIFEST_SCHEMA_VERSION,
        "artifact_kind": DATASET_ARTIFACT_KIND,
        "stage": DATASET_STAGE,
        "run_id": run_id,
        "created_at": created_at,
        "command": command,
        "argv": list(argv),
        "workspace": str(workspace),
        "output_path": str(output_dir),
        "dataset_path": str(dataset_path),
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "seed": seed,
        "split_seed": split_seed,
        "feature_mode": feature_mode,
        "dataset_contract_version": PHASE2_DATASET_CONTRACT.schema_version,
        "traceability_policy": "observed_state_with_true_state_tracking",
        "split_policy": "episode_level_deterministic_largest_remainder",
        "source_telemetry_paths": [str(path) for path in source_paths],
        "input_paths": [str(path) for path in source_paths],
        "episode_count": len(episodes),
        "split_ratios": split_ratios.as_dict(),
        "split_counts": _split_counts(assignments),
        "window_counts": _window_counts(assignments, feature_mode=feature_mode),
        "episodes": [
            _episode_payload(
                episode,
                assignment_by_episode_id[episode.episode_id],
                feature_mode=feature_mode,
            )
            for episode in episodes
        ],
    }


def _build_manifest_payload(
    *,
    dataset_payload: Mapping[str, object],
    manifest_path: Path,
) -> dict[str, object]:
    return {
        "schema_version": DATASET_MANIFEST_SCHEMA_VERSION,
        "stage": DATASET_STAGE,
        "artifact_kind": DATASET_ARTIFACT_KIND,
        "run_id": dataset_payload["run_id"],
        "created_at": dataset_payload["created_at"],
        "command": dataset_payload["command"],
        "argv": list(dataset_payload["argv"]),
        "seed": dataset_payload["seed"],
        "split_seed": dataset_payload["split_seed"],
        "feature_mode": dataset_payload["feature_mode"],
        "input_paths": list(dataset_payload["input_paths"]),
        "output_path": str(manifest_path),
        "dataset_path": dataset_payload["dataset_path"],
        "dataset_output_dir": dataset_payload["output_path"],
        "dataset_contract_version": dataset_payload["dataset_contract_version"],
        "source_telemetry_paths": list(dataset_payload["source_telemetry_paths"]),
        "episode_count": dataset_payload["episode_count"],
        "split_ratios": dict(dataset_payload["split_ratios"]),
        "traceability_policy": dataset_payload["traceability_policy"],
        "split_policy": dataset_payload["split_policy"],
        "window_counts": dataset_payload["window_counts"],
    }


def _build_summary_markdown(dataset_payload: Mapping[str, object], manifest_payload: Mapping[str, object]) -> str:
    lines: list[str] = [
        "# Dataset Preparation Summary",
        "",
        f"- `run_id`: `{dataset_payload['run_id']}`",
        f"- `created_at`: `{dataset_payload['created_at']}`",
        f"- `feature_mode`: `{dataset_payload['feature_mode']}`",
        f"- `seed`: `{dataset_payload['seed']}`",
        f"- `split_seed`: `{dataset_payload['split_seed']}`",
        f"- `episode_count`: `{dataset_payload['episode_count']}`",
        f"- `output_path`: `{dataset_payload['dataset_path']}`",
        "",
        "## Inputs",
    ]
    for path in dataset_payload["source_telemetry_paths"]:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Split Counts",
            "",
            "| Split | Count |",
            "| --- | ---: |",
        ]
    )
    for name in ("train", "validation", "test", "unassigned"):
        lines.append(f"| {name} | {dataset_payload['split_counts'].get(name, 0)} |")

    lines.extend(
        [
            "",
            "## Window Counts",
            "",
            "| Architecture | Window Size | Stride | Total | Train | Validation | Test |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for architecture in ("mlp", "gru", "lstm"):
        info = dataset_payload["window_counts"][architecture]
        split_counts = info["split_window_counts"]
        lines.append(
            "| {arch} | {window_size} | {stride} | {total} | {train} | {validation} | {test} |".format(
                arch=architecture,
                window_size=info["window_size"],
                stride=info["stride"],
                total=info["total_window_count"],
                train=split_counts["train"],
                validation=split_counts["validation"],
                test=split_counts["test"],
            )
        )

    lines.extend(
        [
            "",
            "## Manifest",
            "",
            f"- `manifest_path`: `{manifest_payload['output_path']}`",
            f"- `dataset_contract_version`: `{manifest_payload['dataset_contract_version']}`",
            f"- `traceability_policy`: `{manifest_payload['traceability_policy']}`",
            f"- `split_policy`: `{manifest_payload['split_policy']}`",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class DatasetPreparationResult:
    output_dir: Path
    dataset_path: Path
    manifest_path: Path
    summary_path: Path
    dataset_payload: Mapping[str, object]
    manifest_payload: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "output_dir": str(self.output_dir),
            "dataset_path": str(self.dataset_path),
            "manifest_path": str(self.manifest_path),
            "summary_path": str(self.summary_path),
            "dataset_payload": dict(self.dataset_payload),
            "manifest_payload": dict(self.manifest_payload),
        }


def prepare_dataset_artifacts(
    telemetry_paths: Sequence[str | Path],
    *,
    workspace: str | Path = Path("artifacts/neural"),
    run_id: str | None = None,
    output_dir: str | Path | None = None,
    seed: int = 7,
    split_seed: int | None = None,
    feature_mode: str = "observation_plus_tracking_errors",
    overwrite: bool = False,
    command: str = "multirotor-sim neural dataset prepare",
    argv: Sequence[str] = (),
) -> DatasetPreparationResult:
    resolved_telemetry_paths = _resolve_path_list(telemetry_paths)
    episodes = load_dataset_episodes(resolved_telemetry_paths)
    if not episodes:
        raise DatasetArtifactError("telemetry inputs did not produce any dataset episodes")

    resolved_seed = int(seed)
    resolved_split_seed = resolved_seed if split_seed is None else int(split_seed)
    split_ratios = DEFAULT_SPLIT_RATIOS
    assignments = split_dataset_episodes(episodes, seed=resolved_split_seed, ratios=split_ratios)
    if not assignments:
        raise DatasetArtifactError("dataset split did not produce any assignments")

    resolved_output_dir, resolved_run_id, resolved_workspace = _resolve_output_dir(
        workspace=workspace,
        run_id=run_id,
        output_dir=output_dir,
    )
    resolved_output_dir = resolved_output_dir.resolve()
    resolved_workspace = resolved_workspace.resolve()
    if resolved_output_dir.exists():
        if not overwrite:
            raise DatasetArtifactError(f"output directory already exists: {resolved_output_dir}")
        _clear_managed_dataset_outputs(resolved_output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = resolved_output_dir / "dataset.json"
    manifest_path = resolved_output_dir / "manifest.json"
    summary_path = resolved_output_dir / "dataset-summary.md"
    created_at = _utc_timestamp()
    dataset_payload = _build_dataset_payload(
        episodes=episodes,
        assignments=assignments,
        source_paths=resolved_telemetry_paths,
        run_id=resolved_run_id,
        workspace=resolved_workspace,
        output_dir=resolved_output_dir,
        dataset_path=dataset_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        feature_mode=feature_mode,
        seed=resolved_seed,
        split_seed=resolved_split_seed,
        split_ratios=split_ratios,
        created_at=created_at,
        command=command,
        argv=argv,
    )
    manifest_payload = _build_manifest_payload(dataset_payload=dataset_payload, manifest_path=manifest_path)
    summary_text = _build_summary_markdown(dataset_payload, manifest_payload)

    dataset_path.write_text(_json_dump(dataset_payload) + "\n", encoding="utf-8")
    manifest_path.write_text(_json_dump(manifest_payload) + "\n", encoding="utf-8")
    summary_path.write_text(summary_text + "\n", encoding="utf-8")

    return DatasetPreparationResult(
        output_dir=resolved_output_dir,
        dataset_path=dataset_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        dataset_payload=dataset_payload,
        manifest_payload=manifest_payload,
    )
