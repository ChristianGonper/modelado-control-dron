# ADR-014: Episode-level split and temporal window metadata for Phase 2

## Status
Accepted

## Date
2026-04-15

## Context

Phase 2 needs deterministic dataset preparation for three downstream consumers:

- offline training
- recurrent sequence batching
- reproducible benchmark comparison

The contract already fixes the supervised features and targets, but the dataset still needed an explicit operational rule for how episodes map to splits and how temporal windows inherit that split without leakage.

## Decision

Use complete episodes as the atomic split unit and assign them deterministically with a fixed seed. The main split remains `70/15/15`, bucketed by trajectory family and disturbance regime so comparable experimental families stay distributed across train, validation, and test.

Temporal windowing is handled as a derived view of each episode:

- MLP windows are flattened, default to 30 steps, and use stride 10 by default for train/validation.
- GRU and LSTM windows preserve temporal shape and record their architecture-specific window size in metadata.
- Every derived window carries the source episode split metadata so downstream loaders do not need to recompute split provenance.

## Alternatives Considered

### Row-level splitting
- Pros: simpler to implement.
- Cons: leaks temporal context across train/validation/test.
- Rejected: the split must remain episode-based.

### Architecture-specific input schemas
- Pros: each model could use a custom layout.
- Cons: makes comparison unfair and complicates inference.
- Rejected: all architectures share the same per-step feature contract.

## Consequences

- Split assignment is reproducible and auditable.
- Windows cannot silently cross episode boundaries.
- Training metadata can reconstruct window size, stride, architecture, and source split provenance.
- Later phases can consume the same dataset without redefining the split policy.
