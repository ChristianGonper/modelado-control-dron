from __future__ import annotations

import json
from dataclasses import replace

import pytest

from simulador_multirotor.app import main
from simulador_multirotor.runner import SimulationRunner
from simulador_multirotor.scenarios import BASELINE_PROFILE_ID, ScenarioTelemetryConfig, ScenarioTrajectoryConfig
from simulador_multirotor.validation import (
    PD_VALIDATION_GATE_ID,
    PD_VALIDATION_PROFILE_ID,
    PD_VALIDATION_SCENARIO_NAME,
    PDValidationCriteria,
    build_pd_validation_scenario,
    evaluate_pd_validation,
    run_pd_validation,
    validate_pd_validation_scenario,
)


def test_pd_validation_gate_accepts_the_official_baseline() -> None:
    scenario = build_pd_validation_scenario(seed=11)
    history = SimulationRunner().run(scenario)

    structural_failures = validate_pd_validation_scenario(scenario)
    result = evaluate_pd_validation(history, scenario=scenario, criteria=PDValidationCriteria())

    assert structural_failures == ()
    assert result.gate_id == PD_VALIDATION_GATE_ID
    assert result.passed is True
    assert result.failures == ()
    assert result.scenario_name == PD_VALIDATION_SCENARIO_NAME
    assert result.baseline_profile_id == BASELINE_PROFILE_ID
    assert result.temporal.observed_sample_count == 25
    assert result.temporal.monotonic_time is True
    assert result.saturation.saturated_sample_fraction == 0.0
    assert result.metrics.position_rmse_m < PDValidationCriteria().max_position_rmse_m


def test_pd_validation_persists_traced_artifacts(tmp_path) -> None:
    output_dir = tmp_path / "pd-validation"
    bundle = run_pd_validation(seed=7, output_dir=output_dir, overwrite=True)

    assert bundle.result.passed is True
    assert bundle.scenario_path.exists()
    assert bundle.telemetry_path.exists()
    assert bundle.report_path.exists()
    assert bundle.manifest_path.exists()
    assert bundle.summary_path.exists()

    scenario_payload = json.loads(bundle.scenario_path.read_text(encoding="utf-8"))
    telemetry_payload = json.loads(bundle.telemetry_path.read_text(encoding="utf-8"))
    report_payload = json.loads(bundle.report_path.read_text(encoding="utf-8"))
    manifest_payload = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))

    assert scenario_payload["metadata"]["name"] == PD_VALIDATION_SCENARIO_NAME
    assert scenario_payload["trajectory"]["parameters"]["baseline_profile_id"] == BASELINE_PROFILE_ID
    assert telemetry_payload["scenario"]["metadata"]["name"] == PD_VALIDATION_SCENARIO_NAME
    assert telemetry_payload["controller"]["kind"] == "cascade"
    assert telemetry_payload["telemetry"]["detail_level"] == "full"
    assert telemetry_payload["telemetry"]["tracking_state_source"] == "true_state"
    assert report_payload["passed"] is True
    assert manifest_payload["passed"] is True
    assert manifest_payload["scenario"]["baseline_profile_id"] == BASELINE_PROFILE_ID
    assert manifest_payload["telemetry"]["record_scenario_metadata"] is True


def test_pd_validation_cli_entrypoint_persists_artifacts(tmp_path) -> None:
    output_dir = tmp_path / "cli-validation"

    exit_code = main(["validation", "pd", "--output-dir", str(output_dir), "--overwrite", "--seed", "21"])

    assert exit_code == 0
    assert (output_dir / "telemetry.json").exists()
    assert (output_dir / "validation-report.json").exists()
    assert (output_dir / "manifest.json").exists()


@pytest.mark.parametrize(
    "scenario",
    [
        replace(
            build_pd_validation_scenario(),
            trajectory=ScenarioTrajectoryConfig(
                kind="hover",
                target_position_m=(0.0, 0.0, 1.0),
                valid_until_s=1.0,
                source="native",
                parameters={
                    "scenario": PD_VALIDATION_SCENARIO_NAME,
                    "validation_profile_id": PD_VALIDATION_PROFILE_ID,
                    "baseline_profile_id": PD_VALIDATION_PROFILE_ID,
                    "validation_gate_id": PD_VALIDATION_GATE_ID,
                    "start_position_m": (0.0, 0.0, 1.0),
                    "velocity_m_s": (0.1, 0.0, 0.0),
                },
            ),
        ),
        replace(
            build_pd_validation_scenario(),
            telemetry=ScenarioTelemetryConfig(record_scenario_metadata=True, detail_level="compact", sample_dt_s=0.04),
        ),
    ],
)
def test_pd_validation_rejects_principal_invalid_configurations(scenario) -> None:
    failures = validate_pd_validation_scenario(scenario)

    assert failures
