# ADR-010: Add rotor mixer, motor lag, and decoupled simulation rates

Status: Accepted

## Context

Phase 2 needs the simulator to stop treating control effort as an instantaneous wrench applied directly to the rigid body. The planned improvements require three coupled changes:

- controller output should remain a high-level wrench intent
- the plant should resolve that intent through explicit per-rotor commands and finite motor dynamics
- physics, control, and telemetry should run at distinct rates without losing temporal coherence in the logged history

The previous tracer-bullet architecture assumed a single update rate and a direct wrench-to-plant path. That was sufficient for the first phase, but it made actuator dynamics and telemetry downsampling awkward to add later.

## Decision

Adopt the following simulation structure:

- `VehicleCommand` remains the controller-facing contract and carries a high-level `VehicleIntent`.
- `VehicleCommand` can also carry explicit `RotorCommand` entries when a mixer or actuator layer is involved.
- `RigidBody6DOFDynamics` owns a rotor mixer when rotor geometry is available, and advances each rotor through a first-order motor response before integrating rigid-body motion.
- `ScenarioTimeConfig` now supports separate `physics_dt_s`, `control_dt_s`, and `telemetry_dt_s` values, while keeping `dt_s` as a physics-rate alias for compatibility.
- `SimulationRunner` advances physics at the physics rate, refreshes control at the control rate, and records telemetry at the telemetry rate while preserving the applied-command timestamp in metadata.

## Alternatives Considered

### Keep a direct wrench-to-plant path

- Pros: fewer moving parts
- Cons: actuator lag cannot be represented, and the plant would still behave as if motors were instantaneous
- Rejected: this blocks the phase goal and makes later tuning misleading

### Fold control and telemetry back into the physics rate

- Pros: simpler runner loop
- Cons: no independent control cadence or telemetry downsampling, which prevents realistic logging and controller sampling
- Rejected: the roadmap explicitly requires separate rates

### Log only the latest command without applied-command metadata

- Pros: smaller telemetry payloads
- Cons: the history would lose the distinction between command intent and the actually applied rotor response
- Rejected: coherent debugging and analysis need both values

## Consequences

- Rotorized scenarios now exercise an explicit mixer path.
- The plant response is smoother and more physically plausible because motor commands lag intent.
- Telemetry and exports can expose both the sampled state and the command that actually drove the step.
- Hidden assumptions about one global update rate are now removed from the runner contract.
