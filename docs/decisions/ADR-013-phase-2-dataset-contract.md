# ADR-013: Phase 2 dataset contract from persisted telemetry

## Status
Accepted

## Date
2026-04-15

## Context

Phase 2 needs a stable supervised-learning contract that can be shared by extraction, feature building, training, inference, and later split logic. The repository already persists structured telemetry with both `true_state` and `observed_state`, but the Phase 2 dataset boundary was not yet formalized.

## Decision

Use persisted telemetry exports as the source of truth for dataset episodes, and define a closed contract with:

- episode-level traceability via `scenario_name`, `scenario_seed`, `trajectory_kind`, `controller_kind`, `controller_source`, `disturbance_regime`, and `source_path`
- two allowed feature modes: `raw_observation` and `observation_plus_tracking_errors`
- a fixed supervised target of four values: collective thrust plus body torques x, y, z
- `observed_state` as the policy input and `true_state` as the evaluation anchor
- acceleration features filled from the reference when available, otherwise zero-filled to keep dimensionality stable

The canonical base feature vector is 24-dimensional and the error-augmented mode appends 8 tracking-error features.

## Alternatives Considered

### Use `true_state` directly as the model input
- Pros: simpler extraction.
- Cons: breaks the observability contract and makes the dataset unusable once observation noise is introduced.
- Rejected: Phase 2 must train on the same information available to the controller online.

### Drop reference acceleration from the base vector
- Pros: smaller input dimension.
- Cons: weakens the contract and diverges from the detailed representation already closed in the PRD.
- Rejected: the dataset keeps the feature vector stable and documents the zero-fill fallback when acceleration is unavailable.

### Split by rows instead of episodes
- Pros: simpler implementation.
- Cons: leakage across train/validation/test.
- Rejected: the split unit must be the full episode.

## Consequences

- The dataset contract is explicit and testable.
- Training and inference can share the same feature semantics.
- Later split and batching code can rely on stable episode traceability.
- Telemetry exports that omit the full reference acceleration still remain usable through zero-fill, without changing the feature dimension.

