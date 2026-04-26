"""Phase 3 source telemetry battery persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
import shutil
import uuid
from pathlib import Path
from typing import Sequence

from ..runner import SimulationRunner
from ..scenarios import (
    BASELINE_PROFILE_ID,
    SOURCE_BATTERY_GATE_ID,
    build_baseline_vehicle_profile,
    build_source_battery_scenarios,
    source_battery_protocol_summary,
    save_simulation_scenario,
)
from ..telemetry import SimulationHistory, export_history_to_json


SOURCE_BATTERY_ARTIFACT_KIND = "source_battery"
SOURCE_BATTERY_STAGE = "source"
SOURCE_BATTERY_MANIFEST_SCHEMA_VERSION = 1
SOURCE_BATTERY_DEFAULT_OUTPUT_FILENAMES = {
    "battery": "source-battery.json",
    "manifest": "manifest.json",
    "summary": "source-battery-summary.md",
}


class SourceBatteryArtifactError(ValueError):
    """Raised when the source battery artifact cannot be produced."""


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generate_run_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def _resolve_output_dir(
    *,
    workspace: str | Path,
    run_id: str | None,
    output_dir: str | Path | None,
) -> tuple[Path, str, Path]:
    if output_dir is not None:
        resolved_output_dir = Path(output_dir)
        resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _generate_run_id()
        return resolved_output_dir, resolved_run_id, resolved_output_dir.parent

    resolved_workspace = Path(workspace)
    resolved_run_id = str(run_id).strip() if run_id is not None and str(run_id).strip() else _generate_run_id()
    return resolved_workspace / resolved_run_id / SOURCE_BATTERY_STAGE / "battery", resolved_run_id, resolved_workspace


def _load_existing_battery_manifest(output_dir: Path) -> dict[str, object]:
    manifest_path = output_dir / SOURCE_BATTERY_DEFAULT_OUTPUT_FILENAMES["manifest"]
    if not manifest_path.exists():
        raise SourceBatteryArtifactError(f"output directory is not a managed source battery artifact directory: {output_dir}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceBatteryArtifactError(f"output directory is not a managed source battery artifact directory: {output_dir}") from exc
    if not isinstance(payload, dict):
        raise SourceBatteryArtifactError(f"output directory is not a managed source battery artifact directory: {output_dir}")
    if payload.get("stage") != SOURCE_BATTERY_STAGE or payload.get("artifact_kind") != SOURCE_BATTERY_ARTIFACT_KIND:
        raise SourceBatteryArtifactError(f"output directory is not a managed source battery artifact directory: {output_dir}")
    if int(payload.get("schema_version", -1)) != SOURCE_BATTERY_MANIFEST_SCHEMA_VERSION:
        raise SourceBatteryArtifactError(f"output directory is not a managed source battery artifact directory: {output_dir}")
    return payload


def _clear_output_dir(output_dir: Path) -> None:
    manifest = _load_existing_battery_manifest(output_dir)
    for filename in SOURCE_BATTERY_DEFAULT_OUTPUT_FILENAMES.values():
        path = output_dir / filename
        if path.exists():
            path.unlink()
    for episode in manifest.get("episodes", []):
        if not isinstance(episode, dict):
            continue
        episode_dir = episode.get("episode_dir")
        if isinstance(episode_dir, str) and episode_dir.strip():
            shutil.rmtree(Path(episode_dir), ignore_errors=True)


def _slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in str(value).strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "episode"


def _episode_dir(output_dir: Path, index: int, episode_id: str) -> Path:
    return output_dir / "episodes" / f"{index:02d}-{_slugify(episode_id)}"


def validate_source_battery_scenario(scenario: object) -> tuple[str, ...]:
    failures: list[str] = []
    if getattr(scenario, "vehicle", None) != build_baseline_vehicle_profile():
        failures.append("scenario.vehicle must match the official generic-drone baseline profile")
    if getattr(getattr(scenario, "controller", None), "kind", None) != "cascade":
        failures.append("scenario.controller must use the official cascaded PD controller")
    telemetry = getattr(scenario, "telemetry", None)
    if getattr(telemetry, "record_scenario_metadata", False) is not True:
        failures.append("scenario.telemetry must record scenario metadata")
    if getattr(telemetry, "detail_level", None) != "full":
        failures.append("scenario.telemetry must use full detail")
    if getattr(telemetry, "sample_dt_s", None) != 0.02:
        failures.append("scenario.telemetry must use the source battery sampling cadence")
    time = getattr(scenario, "time", None)
    if getattr(time, "duration_s", None) != 6.0:
        failures.append("scenario.time.duration_s must match the source battery protocol")
    if getattr(time, "physics_dt_s", None) != 0.02:
        failures.append("scenario.time.physics_dt_s must match the source battery protocol")
    if getattr(time, "control_dt_s", None) != 0.04:
        failures.append("scenario.time.control_dt_s must match the source battery protocol")
    if getattr(time, "telemetry_dt_s", None) != 0.02:
        failures.append("scenario.time.telemetry_dt_s must match the source battery protocol")
    trajectory = getattr(scenario, "trajectory", None)
    if getattr(trajectory, "valid_until_s", None) != 6.0:
        failures.append("scenario.trajectory.valid_until_s must match the source battery protocol")
    trajectory_parameters = dict(getattr(trajectory, "parameters", {}))
    if trajectory_parameters.get("source_battery_key") != "source-telemetry-battery-v1":
        failures.append("scenario.trajectory.parameters must identify the source battery protocol")
    metadata = getattr(scenario, "metadata", None)
    if getattr(metadata, "seed", None) is None:
        failures.append("scenario.metadata.seed must be fixed for reproducibility")
    return tuple(failures)


def _disturbance_regime(scenario: object) -> str:
    disturbances = getattr(scenario, "disturbances", None)
    if disturbances is None:
        return "unknown"
    flags: list[str] = []
    if getattr(disturbances, "observation_position_noise_std_m", 0.0) or getattr(
        disturbances, "observation_velocity_noise_std_m_s", 0.0
    ):
        flags.append("observation_noise")
    if any(float(component) != 0.0 for component in getattr(disturbances, "wind_velocity_m_s", (0.0, 0.0, 0.0))):
        flags.append("wind")
    if any(float(component) != 0.0 for component in getattr(disturbances, "wind_gust_std_m_s", (0.0, 0.0, 0.0))):
        flags.append("gusts")
    if getattr(disturbances, "parasitic_drag_enabled", False) or getattr(disturbances, "induced_hover_enabled", False):
        flags.append("aerodynamic")
    if not flags:
        return "nominal" if getattr(disturbances, "enabled", False) or disturbances else "unknown"
    return "+".join(flags)


def _summarize_step_count(history: SimulationHistory) -> int:
    return len(history.steps)


@dataclass(frozen=True, slots=True)
class SourceBatteryEpisodeArtifact:
    episode_id: str
    episode_dir: Path
    scenario_path: Path
    telemetry_path: Path
    scenario_name: str
    scenario_seed: int | None
    baseline_profile_id: str
    trajectory_kind: str
    controller_kind: str
    controller_source: str
    controller_parameters: dict[str, object]
    disturbance_regime: str
    sample_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "episode_dir": str(self.episode_dir),
            "scenario_path": str(self.scenario_path),
            "telemetry_path": str(self.telemetry_path),
            "scenario_name": self.scenario_name,
            "scenario_seed": self.scenario_seed,
            "baseline_profile_id": self.baseline_profile_id,
            "trajectory_kind": self.trajectory_kind,
            "controller_kind": self.controller_kind,
            "controller_source": self.controller_source,
            "controller_parameters": self.controller_parameters,
            "disturbance_regime": self.disturbance_regime,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True, slots=True)
class SourceBatteryArtifactBundle:
    output_dir: Path
    battery_path: Path
    manifest_path: Path
    summary_path: Path
    episodes: tuple[SourceBatteryEpisodeArtifact, ...]
    battery_payload: dict[str, object]
    manifest_payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "output_dir": str(self.output_dir),
            "battery_path": str(self.battery_path),
            "manifest_path": str(self.manifest_path),
            "summary_path": str(self.summary_path),
            "episodes": [episode.to_dict() for episode in self.episodes],
            "battery_payload": self.battery_payload,
            "manifest_payload": self.manifest_payload,
        }


def _episode_payload(episode: SourceBatteryEpisodeArtifact) -> dict[str, object]:
    return {
        "episode_id": episode.episode_id,
        "episode_dir": str(episode.episode_dir),
        "scenario_path": str(episode.scenario_path),
        "telemetry_path": str(episode.telemetry_path),
        "scenario_name": episode.scenario_name,
        "scenario_seed": episode.scenario_seed,
        "baseline_profile_id": episode.baseline_profile_id,
        "trajectory_kind": episode.trajectory_kind,
        "controller_kind": episode.controller_kind,
        "controller_source": episode.controller_source,
        "controller_parameters": episode.controller_parameters,
        "disturbance_regime": episode.disturbance_regime,
        "sample_count": episode.sample_count,
    }


def _build_battery_payload(
    *,
    episodes: Sequence[SourceBatteryEpisodeArtifact],
    run_id: str,
    workspace: Path,
    output_dir: Path,
    battery_path: Path,
    manifest_path: Path,
    summary_path: Path,
    command: str,
    argv: Sequence[str],
) -> dict[str, object]:
    protocol = source_battery_protocol_summary()
    return {
        "schema_version": SOURCE_BATTERY_MANIFEST_SCHEMA_VERSION,
        "artifact_kind": SOURCE_BATTERY_ARTIFACT_KIND,
        "stage": SOURCE_BATTERY_STAGE,
        "run_id": run_id,
        "created_at": _utc_timestamp(),
        "command": command,
        "argv": list(argv),
        "workspace": str(workspace),
        "output_path": str(output_dir),
        "battery_path": str(battery_path),
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
        "protocol": protocol,
        "related_validation_gate_id": SOURCE_BATTERY_GATE_ID,
        "baseline_profile_id": BASELINE_PROFILE_ID,
        "episode_count": len(episodes),
        "episodes": [_episode_payload(episode) for episode in episodes],
        "source_telemetry_paths": [str(episode.telemetry_path) for episode in episodes],
        "seed_list": [episode.scenario_seed for episode in episodes],
    }


def _build_manifest_payload(*, battery_payload: dict[str, object], manifest_path: Path) -> dict[str, object]:
    return {
        "schema_version": SOURCE_BATTERY_MANIFEST_SCHEMA_VERSION,
        "artifact_kind": SOURCE_BATTERY_ARTIFACT_KIND,
        "stage": SOURCE_BATTERY_STAGE,
        "run_id": battery_payload["run_id"],
        "created_at": battery_payload["created_at"],
        "command": battery_payload["command"],
        "argv": list(battery_payload["argv"]),
        "output_path": str(manifest_path),
        "battery_path": battery_payload["battery_path"],
        "summary_path": battery_payload["summary_path"],
        "baseline_profile_id": battery_payload["baseline_profile_id"],
        "related_validation_gate_id": battery_payload["related_validation_gate_id"],
        "episode_count": battery_payload["episode_count"],
        "source_telemetry_paths": list(battery_payload["source_telemetry_paths"]),
        "seed_list": list(battery_payload["seed_list"]),
    }


def _build_summary_markdown(battery_payload: dict[str, object]) -> str:
    lines: list[str] = [
        "# Source Telemetry Battery",
        "",
        f"- `source_battery_key`: `{battery_payload['protocol']['source_battery_key']}`",
        f"- `related_validation_gate_id`: `{battery_payload['related_validation_gate_id']}`",
        f"- `baseline_profile_id`: `{battery_payload['baseline_profile_id']}`",
        f"- `episode_count`: `{battery_payload['episode_count']}`",
        f"- `seed_list`: `{battery_payload['seed_list']}`",
        "",
        "## Protocol",
        "",
        f"- `duration_s`: `{battery_payload['protocol']['duration_s']}`",
        f"- `physics_dt_s`: `{battery_payload['protocol']['physics_dt_s']}`",
        f"- `control_dt_s`: `{battery_payload['protocol']['control_dt_s']}`",
        f"- `telemetry_dt_s`: `{battery_payload['protocol']['telemetry_dt_s']}`",
        f"- `trajectory_kinds`: `{battery_payload['protocol']['trajectory_kinds']}`",
        "",
        "## Episodes",
        "",
        "| Episode | Seed | Trajectory | Disturbance Regime | Samples | Telemetry |",
        "| --- | ---: | --- | --- | ---: | --- |",
    ]
    for episode in battery_payload["episodes"]:
        lines.append(
            "| {episode_id} | {scenario_seed} | {trajectory_kind} | {disturbance_regime} | {sample_count} | `{telemetry_path}` |".format(
                **episode
            )
        )
    lines.extend(
        [
            "",
            "## Downstream Use",
            "",
            "Prepare a dataset from the persisted telemetry paths with:",
            "",
            "```bash",
            "uv run multirotor-sim neural dataset prepare --telemetry <telemetry-paths...>",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def persist_source_battery_artifacts(
    *,
    workspace: str | Path = Path("artifacts/validation"),
    run_id: str | None = None,
    output_dir: str | Path | None = None,
    overwrite: bool = False,
    command: str = "multirotor-sim validation source-battery",
    argv: Sequence[str] = (),
) -> SourceBatteryArtifactBundle:
    scenarios = build_source_battery_scenarios()
    structural_failures: list[str] = []
    for scenario in scenarios:
        structural_failures.extend(validate_source_battery_scenario(scenario))
    if structural_failures:
        raise SourceBatteryArtifactError("; ".join(structural_failures))

    resolved_output_dir, resolved_run_id, resolved_workspace = _resolve_output_dir(
        workspace=workspace,
        run_id=run_id,
        output_dir=output_dir,
    )
    resolved_output_dir = resolved_output_dir.resolve()
    resolved_workspace = resolved_workspace.resolve()
    if resolved_output_dir.exists():
        if not overwrite:
            raise SourceBatteryArtifactError(f"output directory already exists: {resolved_output_dir}")
        _clear_output_dir(resolved_output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    episode_artifacts: list[SourceBatteryEpisodeArtifact] = []
    for index, scenario in enumerate(scenarios, start=1):
        episode_dir = _episode_dir(resolved_output_dir, index, scenario.metadata.name)
        episode_dir.mkdir(parents=True, exist_ok=True)
        scenario_path = episode_dir / "scenario.json"
        telemetry_path = episode_dir / "telemetry.json"
        history = SimulationRunner().run(scenario)
        save_simulation_scenario(scenario, scenario_path)
        export_history_to_json(
            history,
            telemetry_path,
            detail_level=scenario.telemetry.detail_level,
            sample_dt_s=scenario.telemetry.sample_dt_s,
        )
        episode_artifacts.append(
            SourceBatteryEpisodeArtifact(
                episode_id=scenario.metadata.name,
                episode_dir=episode_dir,
                scenario_path=scenario_path,
                telemetry_path=telemetry_path,
                scenario_name=scenario.metadata.name,
                scenario_seed=scenario.metadata.seed,
                baseline_profile_id=str(scenario.trajectory.parameters.get("baseline_profile_id", BASELINE_PROFILE_ID)),
                trajectory_kind=scenario.trajectory.kind,
                controller_kind=scenario.controller.kind,
                controller_source="pid",
                controller_parameters=dict(scenario.controller.parameters),
                disturbance_regime=_disturbance_regime(scenario),
                sample_count=_summarize_step_count(history),
            )
        )

    battery_path = resolved_output_dir / SOURCE_BATTERY_DEFAULT_OUTPUT_FILENAMES["battery"]
    manifest_path = resolved_output_dir / SOURCE_BATTERY_DEFAULT_OUTPUT_FILENAMES["manifest"]
    summary_path = resolved_output_dir / SOURCE_BATTERY_DEFAULT_OUTPUT_FILENAMES["summary"]
    battery_payload = _build_battery_payload(
        episodes=episode_artifacts,
        run_id=resolved_run_id,
        workspace=resolved_workspace,
        output_dir=resolved_output_dir,
        battery_path=battery_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        command=command,
        argv=argv,
    )
    manifest_payload = _build_manifest_payload(battery_payload=battery_payload, manifest_path=manifest_path)

    battery_path.write_text(_json_dump(battery_payload) + "\n", encoding="utf-8")
    manifest_path.write_text(_json_dump(manifest_payload) + "\n", encoding="utf-8")
    summary_path.write_text(_build_summary_markdown(battery_payload) + "\n", encoding="utf-8")

    return SourceBatteryArtifactBundle(
        output_dir=resolved_output_dir,
        battery_path=battery_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        episodes=tuple(episode_artifacts),
        battery_payload=battery_payload,
        manifest_payload=manifest_payload,
    )


def run_source_battery(
    *,
    workspace: str | Path = Path("artifacts/validation"),
    run_id: str | None = None,
    output_dir: str | Path | None = None,
    overwrite: bool = False,
    command: str = "multirotor-sim validation source-battery",
    argv: Sequence[str] = (),
) -> SourceBatteryArtifactBundle:
    return persist_source_battery_artifacts(
        workspace=workspace,
        run_id=run_id,
        output_dir=output_dir,
        overwrite=overwrite,
        command=command,
        argv=argv,
    )
