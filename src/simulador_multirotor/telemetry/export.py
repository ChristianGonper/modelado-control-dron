"""Export helpers for structured simulator telemetry."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np

from .memory import SimulationHistory, SimulationStep


_ALLOWED_DETAIL_LEVELS = {"compact", "standard", "full"}


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_detail_level(history: SimulationHistory, detail_level: str | None) -> str:
    resolved = str(detail_level or history.telemetry_metadata.get("detail_level", "standard")).strip().lower()
    if resolved not in _ALLOWED_DETAIL_LEVELS:
        raise ValueError(f"unsupported telemetry detail level: {resolved}")
    return resolved


def _resolve_sample_dt_s(history: SimulationHistory, sample_dt_s: float | None) -> float | None:
    resolved = history.telemetry_metadata.get("sample_dt_s") if sample_dt_s is None else sample_dt_s
    if resolved is None:
        return None
    value = float(resolved)
    if value <= 0.0:
        raise ValueError("sample_dt_s must be positive")
    return value


def _select_steps(history: SimulationHistory, sample_dt_s: float | None) -> tuple[SimulationStep, ...]:
    steps = history.steps
    if not steps or sample_dt_s is None:
        return steps

    selected: list[SimulationStep] = []
    next_sample_time = history.initial_state.time_s
    for step in steps:
        if not selected or step.time_s >= next_sample_time - 1e-12:
            selected.append(step)
            next_sample_time = step.time_s + sample_dt_s
    if selected[-1] is not steps[-1]:
        selected.append(steps[-1])
    return tuple(selected)


def _state_columns(prefix: str, state_mapping: Mapping[str, object]) -> dict[str, object]:
    position_m = state_mapping["position_m"]
    orientation_wxyz = state_mapping["orientation_wxyz"]
    linear_velocity_m_s = state_mapping["linear_velocity_m_s"]
    angular_velocity_rad_s = state_mapping["angular_velocity_rad_s"]
    return {
        f"{prefix}_position_x_m": position_m[0],
        f"{prefix}_position_y_m": position_m[1],
        f"{prefix}_position_z_m": position_m[2],
        f"{prefix}_orientation_w": orientation_wxyz[0],
        f"{prefix}_orientation_x": orientation_wxyz[1],
        f"{prefix}_orientation_y": orientation_wxyz[2],
        f"{prefix}_orientation_z": orientation_wxyz[3],
        f"{prefix}_linear_velocity_x_m_s": linear_velocity_m_s[0],
        f"{prefix}_linear_velocity_y_m_s": linear_velocity_m_s[1],
        f"{prefix}_linear_velocity_z_m_s": linear_velocity_m_s[2],
        f"{prefix}_angular_velocity_x_rad_s": angular_velocity_rad_s[0],
        f"{prefix}_angular_velocity_y_rad_s": angular_velocity_rad_s[1],
        f"{prefix}_angular_velocity_z_rad_s": angular_velocity_rad_s[2],
    }


def _reference_columns(prefix: str, reference_mapping: Mapping[str, object]) -> dict[str, object]:
    position_m = reference_mapping["position_m"]
    velocity_m_s = reference_mapping["velocity_m_s"]
    return {
        f"{prefix}_position_x_m": position_m[0],
        f"{prefix}_position_y_m": position_m[1],
        f"{prefix}_position_z_m": position_m[2],
        f"{prefix}_velocity_x_m_s": velocity_m_s[0],
        f"{prefix}_velocity_y_m_s": velocity_m_s[1],
        f"{prefix}_velocity_z_m_s": velocity_m_s[2],
    }


def _step_row(step: SimulationStep, *, detail_level: str) -> dict[str, object]:
    row: dict[str, object] = {
        "step_index": step.index,
        "time_s": step.time_s,
        "reference_time_s": step.reference.time_s,
        "reference_yaw_rad": step.reference.yaw_rad,
        "reference_valid_from_s": step.reference.valid_from_s,
        "reference_valid_until_s": step.reference.valid_until_s,
        "error_yaw_rad": step.error.yaw_rad,
        "command_collective_thrust_newton": step.command.collective_thrust_newton,
        "command_body_torque_x_nm": step.command.body_torque_nm[0],
        "command_body_torque_y_nm": step.command.body_torque_nm[1],
        "command_body_torque_z_nm": step.command.body_torque_nm[2],
        "event_kinds_json": _json_dump([event.kind for event in step.events]),
    }
    row.update(_state_columns("state", {
        "position_m": step.state.position_m,
        "orientation_wxyz": step.state.orientation_wxyz,
        "linear_velocity_m_s": step.state.linear_velocity_m_s,
        "angular_velocity_rad_s": step.state.angular_velocity_rad_s,
    }))
    row.update(_reference_columns("reference", {
        "position_m": step.reference.position_m,
        "velocity_m_s": step.reference.velocity_m_s,
    }))
    row.update({
        "error_position_x_m": step.error.position_m[0],
        "error_position_y_m": step.error.position_m[1],
        "error_position_z_m": step.error.position_m[2],
        "error_velocity_x_m_s": step.error.velocity_m_s[0],
        "error_velocity_y_m_s": step.error.velocity_m_s[1],
        "error_velocity_z_m_s": step.error.velocity_m_s[2],
    })

    if detail_level != "compact":
        observation_state = step.observation.observed_state
        row.update(_state_columns("observation", {
            "position_m": observation_state.position_m,
            "orientation_wxyz": observation_state.orientation_wxyz,
            "linear_velocity_m_s": observation_state.linear_velocity_m_s,
            "angular_velocity_rad_s": observation_state.angular_velocity_rad_s,
        }))
        row["observation_time_s"] = observation_state.time_s
        row["observation_metadata_json"] = _json_dump(dict(step.observation.metadata))
        row["reference_metadata_json"] = _json_dump(dict(step.reference.metadata))
        row["step_metadata_json"] = _json_dump(dict(step.metadata))
        row["events_json"] = _json_dump([event.to_dict() for event in step.events])

    if detail_level == "full":
        row["state_json"] = _json_dump({
            "state": {
                "position_m": step.state.position_m,
                "orientation_wxyz": step.state.orientation_wxyz,
                "linear_velocity_m_s": step.state.linear_velocity_m_s,
                "angular_velocity_rad_s": step.state.angular_velocity_rad_s,
                "time_s": step.state.time_s,
            },
            "observation": {
                "true_state": {
                    "position_m": step.observation.true_state.position_m,
                    "orientation_wxyz": step.observation.true_state.orientation_wxyz,
                    "linear_velocity_m_s": step.observation.true_state.linear_velocity_m_s,
                    "angular_velocity_rad_s": step.observation.true_state.angular_velocity_rad_s,
                    "time_s": step.observation.true_state.time_s,
                },
                "observed_state": {
                    "position_m": step.observation.observed_state.position_m,
                    "orientation_wxyz": step.observation.observed_state.orientation_wxyz,
                    "linear_velocity_m_s": step.observation.observed_state.linear_velocity_m_s,
                    "angular_velocity_rad_s": step.observation.observed_state.angular_velocity_rad_s,
                    "time_s": step.observation.observed_state.time_s,
                },
                "metadata": dict(step.observation.metadata),
            },
            "reference": {
                "time_s": step.reference.time_s,
                "position_m": step.reference.position_m,
                "velocity_m_s": step.reference.velocity_m_s,
                "yaw_rad": step.reference.yaw_rad,
                "valid_from_s": step.reference.valid_from_s,
                "valid_until_s": step.reference.valid_until_s,
                "acceleration_m_s2": step.reference.acceleration_m_s2,
                "metadata": dict(step.reference.metadata),
            },
            "error": step.error.to_dict(),
            "command": {
                "collective_thrust_newton": step.command.collective_thrust_newton,
                "body_torque_nm": step.command.body_torque_nm,
            },
            "events": [event.to_dict() for event in step.events],
        })
    return row


def _metadata_payload(
    history: SimulationHistory,
    *,
    detail_level: str,
    sample_dt_s: float | None,
    sample_count: int,
) -> dict[str, object]:
    scenario_metadata = dict(history.scenario_metadata)
    vehicle_metadata = dict(history.vehicle_metadata)
    controller_metadata = dict(history.controller_metadata)
    telemetry_metadata = dict(history.telemetry_metadata)
    telemetry_metadata["detail_level"] = detail_level
    telemetry_metadata["sample_dt_s"] = sample_dt_s
    telemetry_metadata["sample_count"] = sample_count
    return {
        "scenario": scenario_metadata,
        "vehicle": vehicle_metadata,
        "controller": controller_metadata,
        "telemetry": telemetry_metadata,
        "initial_state": {
            "position_m": history.initial_state.position_m,
            "orientation_wxyz": history.initial_state.orientation_wxyz,
            "linear_velocity_m_s": history.initial_state.linear_velocity_m_s,
            "angular_velocity_rad_s": history.initial_state.angular_velocity_rad_s,
            "time_s": history.initial_state.time_s,
        },
        "final_state": {
            "position_m": history.final_state.position_m,
            "orientation_wxyz": history.final_state.orientation_wxyz,
            "linear_velocity_m_s": history.final_state.linear_velocity_m_s,
            "angular_velocity_rad_s": history.final_state.angular_velocity_rad_s,
            "time_s": history.final_time_s,
        },
    }


def _export_rows(history: SimulationHistory, *, detail_level: str, sample_dt_s: float | None) -> list[dict[str, object]]:
    selected_steps = _select_steps(history, sample_dt_s)
    return [_step_row(step, detail_level=detail_level) for step in selected_steps]


def export_history_to_json(
    history: SimulationHistory,
    path: str | Path,
    *,
    detail_level: str | None = None,
    sample_dt_s: float | None = None,
) -> Path:
    resolved_detail = _resolve_detail_level(history, detail_level)
    resolved_sample_dt = _resolve_sample_dt_s(history, sample_dt_s)
    rows = _export_rows(history, detail_level=resolved_detail, sample_dt_s=resolved_sample_dt)
    payload = _metadata_payload(
        history,
        detail_level=resolved_detail,
        sample_dt_s=resolved_sample_dt,
        sample_count=len(rows),
    )
    payload["samples"] = rows
    output_path = Path(path)
    output_path.write_text(_json_dump(payload), encoding="utf-8")
    return output_path


def export_history_to_csv(
    history: SimulationHistory,
    path: str | Path,
    *,
    detail_level: str | None = None,
    sample_dt_s: float | None = None,
) -> Path:
    resolved_detail = _resolve_detail_level(history, detail_level)
    resolved_sample_dt = _resolve_sample_dt_s(history, sample_dt_s)
    rows = _export_rows(history, detail_level=resolved_detail, sample_dt_s=resolved_sample_dt)
    output_path = Path(path)
    metadata = _metadata_payload(
        history,
        detail_level=resolved_detail,
        sample_dt_s=resolved_sample_dt,
        sample_count=len(rows),
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"# metadata={_json_dump(metadata)}\n")
        if rows:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return output_path


def _string_array(values: Iterable[object]) -> np.ndarray:
    return np.asarray([_json_dump(value) if not isinstance(value, str) else value for value in values], dtype=np.str_)


def export_history_to_numpy(
    history: SimulationHistory,
    path: str | Path,
    *,
    detail_level: str | None = None,
    sample_dt_s: float | None = None,
) -> Path:
    resolved_detail = _resolve_detail_level(history, detail_level)
    resolved_sample_dt = _resolve_sample_dt_s(history, sample_dt_s)
    rows = _export_rows(history, detail_level=resolved_detail, sample_dt_s=resolved_sample_dt)
    output_path = Path(path)
    arrays: dict[str, np.ndarray] = {
        "metadata_json": np.asarray(
            _json_dump(
                _metadata_payload(
                    history,
                    detail_level=resolved_detail,
                    sample_dt_s=resolved_sample_dt,
                    sample_count=len(rows),
                )
            ),
            dtype=np.str_,
        ),
        "sample_count": np.asarray(len(rows), dtype=np.int64),
    }
    if rows:
        arrays["step_index"] = np.asarray([row["step_index"] for row in rows], dtype=np.int64)
        arrays["time_s"] = np.asarray([row["time_s"] for row in rows], dtype=np.float64)
        arrays["state_position_m"] = np.asarray(
            [[row["state_position_x_m"], row["state_position_y_m"], row["state_position_z_m"]] for row in rows],
            dtype=np.float64,
        )
        arrays["state_orientation_wxyz"] = np.asarray(
            [[row["state_orientation_w"], row["state_orientation_x"], row["state_orientation_y"], row["state_orientation_z"]] for row in rows],
            dtype=np.float64,
        )
        arrays["state_linear_velocity_m_s"] = np.asarray(
            [
                [row["state_linear_velocity_x_m_s"], row["state_linear_velocity_y_m_s"], row["state_linear_velocity_z_m_s"]]
                for row in rows
            ],
            dtype=np.float64,
        )
        arrays["state_angular_velocity_rad_s"] = np.asarray(
            [
                [row["state_angular_velocity_x_rad_s"], row["state_angular_velocity_y_rad_s"], row["state_angular_velocity_z_rad_s"]]
                for row in rows
            ],
            dtype=np.float64,
        )
        arrays["reference_position_m"] = np.asarray(
            [[row["reference_position_x_m"], row["reference_position_y_m"], row["reference_position_z_m"]] for row in rows],
            dtype=np.float64,
        )
        arrays["reference_velocity_m_s"] = np.asarray(
            [
                [row["reference_velocity_x_m_s"], row["reference_velocity_y_m_s"], row["reference_velocity_z_m_s"]]
                for row in rows
            ],
            dtype=np.float64,
        )
        arrays["reference_yaw_rad"] = np.asarray([row["reference_yaw_rad"] for row in rows], dtype=np.float64)
        arrays["error_position_m"] = np.asarray(
            [[row["error_position_x_m"], row["error_position_y_m"], row["error_position_z_m"]] for row in rows],
            dtype=np.float64,
        )
        arrays["error_velocity_m_s"] = np.asarray(
            [[row["error_velocity_x_m_s"], row["error_velocity_y_m_s"], row["error_velocity_z_m_s"]] for row in rows],
            dtype=np.float64,
        )
        arrays["error_yaw_rad"] = np.asarray([row["error_yaw_rad"] for row in rows], dtype=np.float64)
        arrays["command_collective_thrust_newton"] = np.asarray(
            [row["command_collective_thrust_newton"] for row in rows],
            dtype=np.float64,
        )
        arrays["command_body_torque_nm"] = np.asarray(
            [
                [row["command_body_torque_x_nm"], row["command_body_torque_y_nm"], row["command_body_torque_z_nm"]]
                for row in rows
            ],
            dtype=np.float64,
        )
        arrays["event_kinds_json"] = _string_array(row["event_kinds_json"] for row in rows)
        if resolved_detail != "compact":
            arrays["reference_metadata_json"] = _string_array(row["reference_metadata_json"] for row in rows)
            arrays["step_metadata_json"] = _string_array(row["step_metadata_json"] for row in rows)
            arrays["events_json"] = _string_array(row["events_json"] for row in rows)
            arrays["observation_position_m"] = np.asarray(
                [
                    [row["observation_position_x_m"], row["observation_position_y_m"], row["observation_position_z_m"]]
                    for row in rows
                ],
                dtype=np.float64,
            )
            arrays["observation_linear_velocity_m_s"] = np.asarray(
                [
                    [
                        row["observation_linear_velocity_x_m_s"],
                        row["observation_linear_velocity_y_m_s"],
                        row["observation_linear_velocity_z_m_s"],
                    ]
                    for row in rows
                ],
                dtype=np.float64,
            )
            arrays["observation_orientation_wxyz"] = np.asarray(
                [
                    [
                        row["observation_orientation_w"],
                        row["observation_orientation_x"],
                        row["observation_orientation_y"],
                        row["observation_orientation_z"],
                    ]
                    for row in rows
                ],
                dtype=np.float64,
            )
            arrays["observation_time_s"] = np.asarray([row["observation_time_s"] for row in rows], dtype=np.float64)
            arrays["observation_metadata_json"] = _string_array(row["observation_metadata_json"] for row in rows)
        if resolved_detail == "full":
            arrays["state_json"] = _string_array(row["state_json"] for row in rows)
    np.savez_compressed(output_path, **arrays)
    return output_path
