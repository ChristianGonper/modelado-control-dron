# ADR-009: Separate motor-ready contracts and geometric rigid-body integration

Status: Accepted

## Context

The next physics phases require the simulator to stop assuming that the physical command is only a global collective thrust plus body torque. We also need the runner, telemetry, and control surfaces to distinguish between the true plant state and the noisy observed state, otherwise later phases cannot add actuator dynamics, sensor realism, or audit-friendly telemetry without further contract churn.

At the same time, the rigid-body core was still advancing the full state with a simplified explicit Euler scheme and decoupled angular acceleration. That was sufficient for the tracer bullet, but it was not consistent with the target roadmap:

- future per-rotor actuation needs a stable place for motor-level signals
- telemetry and metrics need a clear truth-vs-observation split
- later numerical validation depends on a pure derivative API and a higher-quality nominal integrator
- rotational dynamics must include gyroscopic coupling and a quaternion update that stays on the manifold

## Decision

Adopt the following contracts and dynamics baseline:

- `VehicleCommand` keeps a high-level `VehicleIntent` and can also carry optional `RotorCommand` entries for future mixer and actuator phases.
- `RigidBodyParameters` can describe validated `RotorGeometry` entries even before the plant consumes them directly.
- `VehicleObservation` stores both `true_state` and `observed_state`, while preserving `.state` as a compatibility alias to the observed state.
- `RigidBody6DOFDynamics` exposes a pure derivative evaluation path and uses RK4 as the nominal state integrator.
- Rotational acceleration uses Euler rigid-body dynamics with gyroscopic coupling.
- Attitude propagation uses a geometric quaternion increment derived from angular velocity so the state remains on `SO(3)` without ad hoc normalization-by-step fixes.

## Alternatives Considered

### Keep the old global command until the mixer exists

- Pros: fewer immediate code changes
- Cons: phase 2 would need another cross-cutting contract migration touching controller, runner, telemetry, and tests again
- Rejected: the dependency chain in the task breakdown explicitly puts contract stabilization first

### Represent only observed state in telemetry

- Pros: simpler payloads
- Cons: breaks traceability, makes sensor noise auditing impossible, and forces metrics to mix physical truth with observation artifacts
- Rejected: later validation phases need both signals available and time-aligned

### Use Euler integration with quaternion renormalization

- Pros: minimal implementation effort
- Cons: larger integration error, weaker regression baseline across `dt`, and no clean derivative surface for future comparison tests
- Rejected: the roadmap explicitly requires pure derivatives and RK4 as the nominal baseline

## Consequences

- Phase 2 can add mixer and actuator dynamics without redefining the top-level command contract.
- Telemetry and metrics can now evolve around explicit true vs observed state semantics.
- Existing control code remains source-compatible through the observation `.state` alias and the high-level wrench view on `VehicleCommand`.
- The rigid-body core has a clearer numerical boundary for future integrator comparisons and regression scenarios.
