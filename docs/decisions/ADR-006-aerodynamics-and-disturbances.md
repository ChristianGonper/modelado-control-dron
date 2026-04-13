# ADR-006: Modelo aerodinámico simple y perturbaciones configurables

## Status
Accepted

## Date
2026-04-13

## Context
Phase 5 adds aerodynamic effects and disturbances on top of the rigid-body model. The plan requires the model to stay compatible with the existing dynamics contract, preserve the nominal mode, and allow isolated analysis of each perturbation.

We need the first implementation to be physically plausible, reproducible, and small enough to validate with short tests. A high-fidelity rotor model would add complexity without improving the validation surface for this TFG slice.

## Decision
Use a two-layer aerodynamic model:

- Parasitic drag is modeled as a quadratic force opposing the relative air velocity in the world frame, using air density and an effective drag area from vehicle or scenario parameters.
- Induced hover effects are modeled as a simplified thrust-efficiency loss that reduces the effective collective thrust in proportion to commanded thrust and a configurable loss ratio.
- Wind is modeled as a scenario-configured background velocity with optional Gaussian gusts sampled from the scenario seed.
- Observation noise remains scenario-controlled and reproducible through the same seed path.

The rigid-body step contract stays unchanged. Aerodynamic effects are attached through an optional environment object built from scenario configuration, so nominal dynamics remain available by default.

## Alternatives Considered

### Full rotor or blade-element aerodynamics
- Pros: higher fidelity.
- Cons: much harder to validate, calibrate, and keep stable in this phase.
- Rejected for this slice: the PRD asks for a deliberately simple model first.

### Encode disturbances directly in the runner
- Pros: fewer physics classes.
- Cons: mixes simulation logic with scenario orchestration and makes the model harder to reuse.
- Rejected for this slice: the disturbance model belongs in the physics layer.

### Make induced effects a hard-coded thrust reduction
- Pros: very small implementation.
- Cons: harder to separate and reason about in tests.
- Rejected for this slice: the explicit environment object makes isolated analysis easier.

## Consequences
- Nominal runs remain unchanged when aerodynamic flags are disabled.
- Drag, induced effects, and wind can be tested independently or together.
- Scenario metadata now carries the disturbance configuration used in a run.
- Future phases can refine the coefficients or replace the simplified model without changing the runner contract.
