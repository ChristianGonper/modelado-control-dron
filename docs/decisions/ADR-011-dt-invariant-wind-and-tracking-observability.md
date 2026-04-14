# ADR-011: Use dt-invariant wind gusts and explicit tracking-state observability

Status: Accepted

## Date
2026-04-14

## Context

Phase 3 needs two changes that are tightly coupled:

- wind and gust perturbations must keep comparable energy when the simulator `dt` changes
- telemetry and tracking metrics must distinguish the physical state, the noisy observation, and the state used to compute tracking error

The previous per-step Gaussian wind sampling made the disturbance strength depend on the sampling cadence. That was acceptable for an early tracer bullet, but it makes `dt` sweeps misleading and breaks regression comparisons between scenarios.

## Decision

Use an exact discrete Ornstein-Uhlenbeck process for wind gusts:

- the base wind remains a deterministic offset
- the gust component has a configurable stationary standard deviation and correlation time
- the update is seeded and reproducible for a fixed scenario and time step schedule

Keep the aerodynamic plant model aggregated at the body level:

- parasitic drag and induced hover loss are body-level aerodynamic effects
- rotor-level thrust and reaction torque still come from the explicit rotor geometry and mixer path

Expose observability explicitly in telemetry and metrics:

- `VehicleObservation` preserves `true_state` and `observed_state`
- telemetry exports include `true_state`, `observed_state`, and `tracking_state`
- tracking metrics report the source state used for error computation and remain anchored to the true physical state by default

## Alternatives Considered

### Per-step white-noise gusts

- Pros: trivial implementation
- Cons: the effective energy changes with `dt`, making comparison across discretizations unreliable
- Rejected: the simulator needs stable disturbance statistics when physics rate changes

### Per-rotor aerodynamic disturbances

- Pros: higher fidelity
- Cons: significantly more tuning and a larger validation surface
- Rejected for this phase: the current plant still treats aerodynamic disturbance as a body-level effect

### Hide the tracking-state source inside generic telemetry metadata

- Pros: smaller schema
- Cons: downstream analysis cannot tell whether a metric came from the true state, the observed state, or another derived signal
- Rejected: the observability contract needs to be explicit, not inferred

## Consequences

- `dt` sweeps can be compared with statistical tolerance instead of artifact-level equality
- replay and auditing retain enough disturbance context to reconstruct the wind sample path for a given run
- metrics remain comparable only when they use the same tracking-state source
- the telemetry schema is slightly larger, but the data is unambiguous
