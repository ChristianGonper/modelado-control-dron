"""Scenario IO helpers for versioned external artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .schema import SimulationScenario


def load_simulation_scenario(path: str | Path) -> SimulationScenario:
    return SimulationScenario.from_json(path)


def load_simulation_scenario_dict(payload: Mapping[str, object]) -> SimulationScenario:
    return SimulationScenario.from_dict(payload)


def save_simulation_scenario(scenario: SimulationScenario, path: str | Path) -> Path:
    return scenario.to_json(path)
