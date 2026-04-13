from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import build_minimal_scenario
from simulador_multirotor.telemetry import export_history_to_json
from simulador_multirotor.visualization import load_telemetry_archive, render_analysis_outputs


def test_persisted_telemetry_can_be_visualized_in_2d_and_3d(tmp_path) -> None:
    history = SimulationRunner().run(build_minimal_scenario())
    telemetry_path = export_history_to_json(history, tmp_path / "telemetry.json")

    archive = load_telemetry_archive(telemetry_path)
    bundle = render_analysis_outputs(archive, tmp_path)

    assert archive.sample_count == len(history.steps)
    assert archive.vehicle_metadata["mass_kg"] == history.vehicle_metadata["mass_kg"]
    assert archive.controller_metadata["kind"] == history.controller_metadata["kind"]
    assert bundle.trajectory_2d_path.exists()
    assert bundle.tracking_errors_path.exists()
    assert bundle.trajectory_3d_path.exists()
    assert bundle.trajectory_2d_path.stat().st_size > 0
    assert bundle.tracking_errors_path.stat().st_size > 0
    assert bundle.trajectory_3d_path.stat().st_size > 0

    image = plt.imread(bundle.trajectory_2d_path)
    assert image.ndim == 3
    assert np.isfinite(image).all()
