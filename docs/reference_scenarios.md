# Reference Scenarios v1

The repository includes immutable scenario artifacts under `scenario_artifacts/v1/`.

## Scenarios

- `hover.json` validates nominal hover stability and thrust balance.
- `angular_maneuver.json` exercises attitude tracking through a circular reference.
- `perturbation.json` validates the disturbance model and noisy observation path.
- `dt_comparison_coarse.json` and `dt_comparison_fine.json` validate the `dt`-invariant wind model and the effect of physics discretization.

## Validation Rules

- Round-trip load and save must preserve the scenario contract and the simulated behavior within numerical tolerance.
- Hover should stay near the reference position with bounded final error.
- The angular maneuver should produce non-trivial yaw tracking error and body torque activity.
- The perturbation scenario should produce larger tracking error than hover and expose the disturbance context in telemetry.
- The fine `dt` reference should not regress relative to the coarse reference on the position tracking metric.

## CLI Usage

Run a reference artifact directly:

```bash
uv run multirotor-sim --scenario scenario_artifacts/v1/hover.json
```

