# ADR-019: Canonical generic-drone baseline profile

## Status

Accepted

## Date

2026-04-21

## Context

Phase 1 needs a single official vehicle profile for the generic multirotor reference. The simulator already has a stable scenario contract and a validated rigid-body dynamics contract, so the baseline should reuse those existing boundaries instead of adding a parallel scenario type or a second vehicle API.

The baseline must be traceable in later telemetry and benchmark artifacts, and it must be easy to distinguish comparable experimental changes from changes that open a new campaign.

## Decision

Define `generic-drone-baseline-v1` as the canonical profile and implement it as a helper that builds the existing `SimulationScenario` contract.

- `build_baseline_scenario()` is the official entry point.
- `build_minimal_scenario()` remains as a compatibility alias and returns the same baseline.
- The scenario metadata carries the profile identity through its name and tags.
- The trajectory parameters also record the baseline profile id for downstream traceability.
- The vehicle profile fixes mass, inertia, rotor geometry, actuator coefficients, motor lag, and global thrust/torque limits as one coherent package.

## Alternatives Considered

### Introduce a separate baseline scenario contract

- Pros: explicit separation from older nominal helpers.
- Cons: duplicates the scenario API and fragments the execution path.
- Rejected: the phase requires reuse of the current contract, not a parallel one.

### Keep the current helper unnamed and document the values only

- Pros: minimal code churn.
- Cons: the profile would be easy to lose inside later artifacts and harder to reference consistently.
- Rejected: this phase needs a baseline that is both executable and identifiable.

## Consequences

- Downstream phases can reference one baseline profile by name.
- Telemetry and scenario artifacts remain comparable as long as the vehicle profile is unchanged.
- Changes to physical parameters or actuator limits now have an explicit campaign boundary.
- Existing code that imports `build_minimal_scenario()` continues to work without modification.
