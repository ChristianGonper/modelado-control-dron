"""Reference scenario catalog and artifact paths."""

from __future__ import annotations

from pathlib import Path


REFERENCE_SCENARIO_VERSION = "v1"
REFERENCE_SCENARIO_NAMES = (
    "hover",
    "angular_maneuver",
    "perturbation",
    "dt_comparison_coarse",
    "dt_comparison_fine",
)

_REFERENCE_SCENARIO_FILENAMES = {
    name: f"{name}.json" for name in REFERENCE_SCENARIO_NAMES
}


def reference_scenario_root(version: str = REFERENCE_SCENARIO_VERSION) -> Path:
    return Path(__file__).resolve().parents[3] / "scenario_artifacts" / version


def reference_scenario_path(name: str, *, version: str = REFERENCE_SCENARIO_VERSION) -> Path:
    normalized_name = str(name).strip().lower()
    if normalized_name not in _REFERENCE_SCENARIO_FILENAMES:
        expected = ", ".join(sorted(REFERENCE_SCENARIO_NAMES))
        raise ValueError(f"unsupported reference scenario: {normalized_name}. expected one of: {expected}")
    return reference_scenario_root(version) / _REFERENCE_SCENARIO_FILENAMES[normalized_name]
