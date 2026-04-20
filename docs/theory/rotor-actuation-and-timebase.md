# Rotor Actuation, Mixer, And Simulation Time Bases

## Metadata

- Title: Rotor Actuation, Mixer, And Simulation Time Bases
- Status: active
- Scope: how controller intent becomes applied thrust and torque in the plant
- Applies to: `dynamics/rigid_body.py`, `runner.py`, `control/`, telemetry
- Primary view: `theory`

## Concept Summary

The controller does not act directly on the rigid body with an ideal wrench.
In the implemented simulator, controller intent is resolved through rotor
allocation, first-order motor response, and separate update rates for physics,
control, and telemetry.

This matters because it defines what "applied command" means in the simulator
and explains why the same controller can behave differently when actuator lag or
sampling cadence changes.

## Essential Formulation

- Controller-facing input:
  - `VehicleIntent = (collective thrust, body torque)`
- Mixer role:
  - distribute the desired wrench over the configured rotor geometry
  - reconstruct the effective wrench from individual rotor thrusts
- Actuator dynamics:
  - each rotor follows a first-order response with time constant `tau_m`
  - the plant applies the lagged rotor output, not the instantaneous target
- Time bases:
  - `physics_dt_s` advances the rigid-body plant
  - `control_dt_s` defines when the controller recomputes intent
  - `telemetry_dt_s` defines when history is sampled and exported

## Assumptions And Simplifications

- Rotor geometry is used for allocation and reaction torque, but the plant still
  aggregates the resulting wrench at vehicle level.
- Motor dynamics are simplified as first-order lag; electrical transients,
  saturating ESC logic, and battery-coupled thrust loss are omitted.
- The mixer assumes a conventional rotor axis aligned with body `+z`.
- Decoupled rates improve experimental realism, but the simulator remains
  synchronous and deterministic for a given scenario seed.

## Impact On The Simulator

- `RigidBody6DOFDynamics` can map high-level intent to rotor commands and keep
  the last applied motor-ready command for telemetry.
- `SimulationRunner` separates physics stepping, control refresh, and telemetry
  sampling without changing the controller contract.
- Telemetry records both timing metadata and the command actually applied to the
  plant, which matters for debugging and later dataset extraction.
- Interpretation limit: this is a realistic actuator abstraction for the TFG,
  not a full firmware or ESC model of the real drone.

## Related Documents

- System blocks:
  - [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
  - [Main Simulator Interfaces](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
- Hardware context:
  - [LiteWing Physical Context](/Users/chris/Documents/Universidad/TFG/docs/hardware/litewing-physical-context.md)
- Validation artifacts:
  - benchmark and telemetry traces routed through the runner

## Related ADRs

- ADRs:
  - [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
  - [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)

## Notes For Thesis Reuse

- Possible chapter or section: actuacion y discretizacion temporal del simulador
- What can be reused almost verbatim later:
  - explanation of mixer and motor lag
  - distinction between commanded and applied control action
  - motivation for separate physics, control, and telemetry cadences
