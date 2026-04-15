# ADR-015: Phase 3 MLP checkpoint and benchmark slice

## Status
Accepted

## Date
2026-04-15

## Context

Phase 3 needs the first end-to-end neural control slice without changing the simulator runner contract. The slice must train reproducibly from the official dataset pipeline, persist train-only normalization, reconstruct inference from an auditable artifact, and compare the neural controller against the baseline on homogeneous scenarios.

## Decision

Use a PyTorch-based MLP controller with a stateful window buffer behind the existing `ControllerContract`.

- Training consumes episode-level splits and MLP windows derived from the dataset API.
- Normalization statistics are computed from train windows only and stored inside the checkpoint.
- The checkpoint stores architecture, feature mode, window configuration, split seed, split ratios, history, and model weights.
- Inference reconstructs the controller from the checkpoint and exposes the same `compute_action(...)` surface as the existing controllers.
- The benchmark path persists a JSON artifact comparing baseline and MLP metrics on homogeneous scenarios.

## Alternatives Considered

### Add a special runner path for neural models
- Pros: simpler controller wiring.
- Cons: couples the simulator to PyTorch and creates a second execution path.
- Rejected: the runner boundary already provides the correct integration point.

### Use ad hoc serialized weights only
- Pros: smaller artifact.
- Cons: cannot reconstruct feature semantics, normalization, or window configuration safely.
- Rejected: the checkpoint must be auditable and reproducible.

## Consequences

- Phase 3 can train, persist, reload, and run the MLP without contract changes.
- Checkpoints are self-describing enough to support later recurrent phases with the same pattern.
- The benchmark artifact is reproducible and can be compared across runs.
- PyTorch becomes a project dependency for neural control phases.
