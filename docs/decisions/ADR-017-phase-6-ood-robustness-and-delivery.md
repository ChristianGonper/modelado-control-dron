# ADR-017: Phase 6 OOD robustness battery and delivery packaging

## Status
Accepted

## Date
2026-04-15

## Context

Phase 6 needs a robustness battery that can stress the neural controllers under harder or unseen conditions without contaminating the main `70/15/15` split or the deterministic model-selection path.

The delivery stage also needs a reproducible handoff that separates in-distribution conclusions from OOD conclusions and keeps the key artifacts easy to rerun.

## Decision

Add a dedicated OOD scenario battery with explicit metadata and separate persisted artifacts:

- the OOD battery uses its own scenario set key
- the OOD benchmark reuses the same controller execution and metric collection contract as the main benchmark
- the OOD report is generated separately from the main Phase 5 report
- no OOD result participates in model selection

The final delivery documentation will:

- reference the main benchmark, report, selection artifact, and checkpoints
- reference the separate OOD benchmark and report
- state the selected architecture through the persisted selection artifact
- record the methodological limits around imitation learning, observability, and robustness

## Alternatives Considered

### Mix OOD runs into the main benchmark
- Pros: one artifact, less code.
- Cons: blurs the boundary between in-distribution comparison and exploratory robustness.
- Rejected: the phase needs a clean methodological separation.

### Use OOD results for selection or tuning
- Pros: could reward more conservative models.
- Cons: makes the selection rule depend on a different question than the main benchmark.
- Rejected: OOD should diagnose robustness, not decide the main architecture.

## Consequences

- Main selection remains reproducible and isolated.
- OOD results are traceable through a separate persisted artifact and report.
- The documentation can describe in-distribution and OOD findings without conflating them.
- Future phases can extend the OOD battery without changing the main evaluation contract.

