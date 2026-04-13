"""Static figure generation for telemetry archives."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .archive import AnalysisArtifactBundle, TelemetryArchive, load_telemetry_archive


def _require_samples(archive: TelemetryArchive) -> None:
    if not archive.samples:
        raise ValueError("telemetry archive must contain at least one sample")


def _save_figure(fig: Figure, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _style_axis(axis: plt.Axes) -> None:
    axis.grid(True, alpha=0.25)
    axis.set_facecolor("#fcfcfd")


def _xy_limits(state_positions: np.ndarray, reference_positions: np.ndarray) -> tuple[float, float, float, float]:
    combined = np.concatenate([state_positions[:, :2], reference_positions[:, :2]], axis=0)
    x_min, y_min = np.min(combined, axis=0)
    x_max, y_max = np.max(combined, axis=0)
    span = max(x_max - x_min, y_max - y_min, 1e-6)
    pad = span * 0.08
    center_x = (x_min + x_max) * 0.5
    center_y = (y_min + y_max) * 0.5
    half = span * 0.5 + pad
    return center_x - half, center_x + half, center_y - half, center_y + half


def _xyz_limits(state_positions: np.ndarray, reference_positions: np.ndarray) -> tuple[np.ndarray, float]:
    combined = np.concatenate([state_positions, reference_positions], axis=0)
    mins = np.min(combined, axis=0)
    maxs = np.max(combined, axis=0)
    center = (mins + maxs) * 0.5
    span = max(float(np.max(maxs - mins)), 1e-6)
    return center, span


def render_trajectory_2d_figure(archive: TelemetryArchive) -> Figure:
    _require_samples(archive)
    state_positions = archive.state_positions_m
    reference_positions = archive.reference_positions_m
    times = archive.times_s
    position_error_norm = np.linalg.norm(archive.error_positions_m, axis=1)
    velocity_error_norm = np.linalg.norm(archive.error_velocities_m_s, axis=1)
    yaw_error_abs = np.abs(archive.error_yaw_rad)

    fig = plt.figure(figsize=(12.5, 9.0), constrained_layout=True)
    grid = fig.add_gridspec(2, 2)
    ax_xy = fig.add_subplot(grid[:, 0])
    ax_position = fig.add_subplot(grid[0, 1])
    ax_velocity = fig.add_subplot(grid[1, 1], sharex=ax_position)

    ax_xy.plot(reference_positions[:, 0], reference_positions[:, 1], linestyle="--", color="#6c757d", linewidth=2.0, label="Referencia")
    ax_xy.plot(state_positions[:, 0], state_positions[:, 1], color="#1f77b4", linewidth=2.2, label="Estado")
    ax_xy.scatter(state_positions[0, 0], state_positions[0, 1], color="#2ca02c", s=42, label="Inicio")
    ax_xy.scatter(state_positions[-1, 0], state_positions[-1, 1], color="#d62728", s=42, label="Fin")
    ax_xy.set_title("Trayectoria 2D")
    ax_xy.set_xlabel("x [m]")
    ax_xy.set_ylabel("y [m]")
    ax_xy.set_aspect("equal", adjustable="box")
    _style_axis(ax_xy)
    x_min, x_max, y_min, y_max = _xy_limits(state_positions, reference_positions)
    ax_xy.set_xlim(x_min, x_max)
    ax_xy.set_ylim(y_min, y_max)
    ax_xy.legend(loc="best", frameon=False)

    ax_position.plot(times, position_error_norm, color="#d62728", linewidth=1.9)
    ax_position.set_title("Error de posición")
    ax_position.set_ylabel("|e_p| [m]")
    _style_axis(ax_position)

    ax_velocity.plot(times, velocity_error_norm, color="#9467bd", linewidth=1.9, label="|e_v|")
    ax_velocity.plot(times, yaw_error_abs, color="#ff7f0e", linewidth=1.6, label="|e_yaw|")
    ax_velocity.set_title("Error de velocidad y yaw")
    ax_velocity.set_xlabel("t [s]")
    ax_velocity.set_ylabel("Error")
    _style_axis(ax_velocity)
    ax_velocity.legend(loc="best", frameon=False)

    return fig


def render_tracking_error_figure(archive: TelemetryArchive) -> Figure:
    _require_samples(archive)
    times = archive.times_s
    position_error_components = archive.error_positions_m
    velocity_error_components = archive.error_velocities_m_s
    yaw_error_abs = np.abs(archive.error_yaw_rad)

    fig, axes = plt.subplots(3, 1, figsize=(10.0, 8.5), sharex=True, constrained_layout=True)
    labels = ("x", "y", "z")
    colors = ("#1f77b4", "#ff7f0e", "#2ca02c")

    for axis, values, title, ylabel in (
        (axes[0], position_error_components, "Error de posición por eje", "e_p [m]"),
        (axes[1], velocity_error_components, "Error de velocidad por eje", "e_v [m/s]"),
    ):
        for idx, (label, color) in enumerate(zip(labels, colors, strict=True)):
            axis.plot(times, values[:, idx], label=label, color=color, linewidth=1.5)
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        _style_axis(axis)
        axis.legend(loc="best", ncol=3, frameon=False)

    axes[2].plot(times, yaw_error_abs, color="#d62728", linewidth=1.7)
    axes[2].set_title("Error absoluto de yaw")
    axes[2].set_ylabel("|e_yaw| [rad]")
    axes[2].set_xlabel("t [s]")
    _style_axis(axes[2])

    return fig


def render_trajectory_3d_figure(archive: TelemetryArchive) -> Figure:
    _require_samples(archive)
    state_positions = archive.state_positions_m
    reference_positions = archive.reference_positions_m
    times = archive.times_s
    center, span = _xyz_limits(state_positions, reference_positions)

    fig = plt.figure(figsize=(10.5, 8.5), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")

    scatter = ax.scatter(
        state_positions[:, 0],
        state_positions[:, 1],
        state_positions[:, 2],
        c=times,
        cmap="viridis",
        s=14,
        alpha=0.85,
        label="Estado",
    )
    ax.plot(
        reference_positions[:, 0],
        reference_positions[:, 1],
        reference_positions[:, 2],
        linestyle="--",
        color="#6c757d",
        linewidth=2.0,
        label="Referencia",
    )
    ax.plot(state_positions[:, 0], state_positions[:, 1], state_positions[:, 2], color="#1f77b4", linewidth=2.0)

    stride = max(1, len(archive.samples) // 12)
    quiver_length = max(span * 0.04, 0.08)
    for sample in archive.samples[::stride]:
        body_z_axis = np.asarray(sample.body_z_axis, dtype=np.float64)
        origin = np.asarray(sample.state_position_m, dtype=np.float64)
        ax.quiver(
            origin[0],
            origin[1],
            origin[2],
            body_z_axis[0],
            body_z_axis[1],
            body_z_axis[2],
            length=quiver_length,
            normalize=True,
            color="#2ca02c",
            alpha=0.35,
        )

    ax.scatter(state_positions[0, 0], state_positions[0, 1], state_positions[0, 2], color="#2ca02c", s=42, label="Inicio")
    ax.scatter(state_positions[-1, 0], state_positions[-1, 1], state_positions[-1, 2], color="#d62728", s=42, label="Fin")
    ax.set_title("Trayectoria 3D y actitud básica")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    ax.set_xlim(center[0] - span * 0.62, center[0] + span * 0.62)
    ax.set_ylim(center[1] - span * 0.62, center[1] + span * 0.62)
    ax.set_zlim(center[2] - span * 0.62, center[2] + span * 0.62)
    ax.view_init(elev=24, azim=135)
    ax.legend(loc="upper left", frameon=False)
    fig.colorbar(scatter, ax=ax, pad=0.02, shrink=0.7, label="t [s]")
    return fig


def render_analysis_outputs(
    telemetry: str | Path | TelemetryArchive,
    output_dir: str | Path,
    *,
    prefix: str = "analysis",
) -> AnalysisArtifactBundle:
    archive = load_telemetry_archive(telemetry) if not isinstance(telemetry, TelemetryArchive) else telemetry
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    trajectory_2d_path = _save_figure(render_trajectory_2d_figure(archive), output_path / f"{prefix}_trajectory_2d.png")
    tracking_errors_path = _save_figure(render_tracking_error_figure(archive), output_path / f"{prefix}_tracking_errors.png")
    trajectory_3d_path = _save_figure(render_trajectory_3d_figure(archive), output_path / f"{prefix}_trajectory_3d.png")
    telemetry_path = archive.source_path or output_path / f"{prefix}_telemetry"
    return AnalysisArtifactBundle(
        telemetry_path=Path(telemetry_path),
        trajectory_2d_path=trajectory_2d_path,
        tracking_errors_path=tracking_errors_path,
        trajectory_3d_path=trajectory_3d_path,
    )
