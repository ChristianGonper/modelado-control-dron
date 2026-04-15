# Phase 2 Dataset Specification

## Scope

This specification defines the supervised dataset contract for Phase 2 control neuronal work. One persisted telemetry export corresponds to one dataset episode. The dataset is built from persisted simulator telemetry, not from live runner hooks.

## Observability Policy

- The policy input is `observed_state` plus the active trajectory reference.
- `true_state` is preserved for auditing, traceability, and tracking evaluation.
- All downstream training and inference must use the same observed-state feature contract.

## Episode Semantics

- The unit of extraction is the complete telemetry episode.
- Episodes preserve `scenario_name`, `scenario_seed`, `trajectory_kind`, `controller_kind`, `controller_source`, `disturbance_regime`, and `source_path`.
- The episode-level split key is stable and uses the same traceability fields so later phases can split by episode without leakage.

## Sample Semantics

- Each sample is one control instant.
- Each sample stores `true_state`, `observed_state`, `reference`, `command`, and sample metadata.
- The supervised target is always four-dimensional: collective thrust plus body torques in x, y, z.

## Feature Contract

Two feature modes are allowed:

- `raw_observation`
- `observation_plus_tracking_errors`

The canonical base feature vector has 24 values:

- observed position, linear velocity, orientation quaternion, and angular velocity
- reference position, velocity, acceleration
- reference yaw encoded as `sin(yaw)` and `cos(yaw)`

The augmented mode appends 8 tracking-error features:

- position error x, y, z
- velocity error x, y, z
- yaw error encoded as `sin(error)` and `cos(error)`

If a reference does not expose acceleration, the dataset fills the three acceleration features with zeros and keeps the dimension stable.

## Split Semantics

- Splits are episode-level, never row-level.
- The intended main split is 70/15/15 by episodes.
- Split assignment must remain deterministic for a fixed seed and traceability bucket.

## Window Semantics

- MLP windows are flattened, default to 30 steps, and use stride 10 in train and validation.
- GRU and LSTM windows preserve temporal order as `[sequence_length, feature_dim]`.
- Derived windows inherit the split and traceability of the source episode.
- Window metadata records the source episode id, architecture, window size, stride, and split provenance.

## Validation Rules

- Missing scenario metadata is a hard error.
- Missing telemetry metadata required for dataset construction is a hard error.
- Missing sample columns in a persisted export are a hard error.
- Telemetry must be anchored to `true_state` tracking for this phase.
