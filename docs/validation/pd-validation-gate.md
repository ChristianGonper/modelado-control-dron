# PD Validation Gate

## Purpose

This document defines the minimum observable gate for the official PD baseline. The gate is intentionally small: it validates one explicit scenario, one controller baseline, one reproducible trajectory, and one persisted telemetry artifact set.

## Scenario

- Official scenario name: `generic-drone-pd-validation-v1`
- Vehicle baseline: `generic-drone-baseline-v1`
- Controller baseline: the existing cascaded controller
- Trajectory family: native `line`
- Seed: optional metadata only; the scenario remains deterministic for a fixed seed

The minimum validation trajectory is explicit and reproducible:

- start position: `(0.0, 0.0, 1.0)` m
- velocity: `(0.1, 0.0, 0.0)` m/s
- duration: `1.0` s
- physics dt: `0.02` s
- control dt: `0.04` s
- telemetry dt: `0.04` s

The gate is meant to answer one question: is the official baseline healthy enough to become source telemetry for later dataset generation?

## Acceptance Criteria

The validation passes only if all of the following are true:

| Area | Criterion |
| --- | --- |
| Tracking error | `position_rmse_m <= 0.10`, `final_position_error_m <= 0.12`, `velocity_rmse_m_s <= 0.20`, `final_velocity_error_m_s <= 0.20`, `yaw_rmse_rad <= 0.01` |
| Saturation | `collective_thrust_fraction_max <= 0.80`, each body torque axis `<= 0.80`, no saturated sample beyond the configured threshold |
| Stability | telemetry must not diverge, samples must remain strictly increasing in time, and the run must complete at the expected horizon |
| Temporal coherence | observed duration and sample count must match the configured cadence, and `telemetry_dt_s` must remain numerically stable |
| Reusability | telemetry must preserve scenario, controller, and trajectory metadata at full detail |

## Persisted Output

The validation command persists a small artifact set:

- `scenario.json`
- `telemetry.json`
- `validation-report.json`
- `manifest.json`
- `validation-summary.md`

The telemetry export is the source artifact consumed by later phases. The report and manifest make the gate auditable without re-running the simulation.

## CLI

```bash
uv run multirotor-sim validation pd
```

The command runs the scenario, evaluates the gate, and writes the artifacts in a single path.
