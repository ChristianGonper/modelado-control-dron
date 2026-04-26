# Source Telemetry Battery

## Purpose

This battery is the Phase 3 source of expert telemetry used to prepare the official dataset for neural training. It is separate from the PD validation gate:

- `validation pd` proves that the baseline expert is healthy enough to generate data.
- `validation source-battery` produces the longer, more diverse telemetry episodes used for dataset preparation.

## Protocol

- Battery key: `source-telemetry-battery-v1`
- Baseline profile: `generic-drone-baseline-v1`
- Related gate: `pd-expert-gate-v1`
- Controller: cascaded PD baseline
- Duration per episode: `6.0 s`
- Physics dt: `0.02 s`
- Control dt: `0.04 s`
- Telemetry dt: `0.02 s`
- Telemetry detail: `full`

The battery is intentionally small but not trivial. It combines:

- `circle` trajectories with wind and gust regimes
- `lissajous` trajectories with observation noise and aerodynamic losses

This gives enough temporal length and motion diversity to make downstream `MLP`, `GRU`, and `LSTM` training viable.

## Public Flow

Generate the source battery:

```bash
uv run multirotor-sim validation source-battery
```

Prepare the dataset from the emitted telemetry files:

```bash
uv run multirotor-sim neural dataset prepare --telemetry <telemetry-paths...>
```

## Boundary With PD Validation

The PD validation gate is still the first expert gate. Passing that gate does not mean its single short trajectory should be used directly as the training dataset. The source battery is the explicit Phase 3 protocol that turns the validated baseline into reusable expert telemetry.
