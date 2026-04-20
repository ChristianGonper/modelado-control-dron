# Rigid-Body 6DOF Dynamics And Reference Frames

## Metadata

- Title: Rigid-Body 6DOF Dynamics And Reference Frames
- Status: active
- Scope: nominal multirotor state evolution used by the simulator core
- Applies to: `dynamics/rigid_body.py`, `core/contracts.py`, `control/`, telemetry, and metrics
- Primary view: `theory`

## Concept Summary

The simulator models the vehicle as a rigid body with six coupled degrees of
freedom: three translational and three rotational.

This matters because the core contracts, the baseline controller, telemetry,
and tracking metrics all assume the same physical meaning for position,
velocity, orientation, angular velocity, thrust, and torque.

## Essential Formulation

- State variables:
  - world-frame position `p`
  - world-frame linear velocity `v`
  - quaternion attitude `q = (w, x, y, z)`
  - body-frame angular velocity `omega`
- Translational dynamics:
  - `m * dv/dt = F_thrust + F_gravity + F_aero`
- Rotational dynamics:
  - `I * domega/dt = tau - omega x (I * omega)`
- Attitude propagation:
  - orientation is stored as a unit quaternion and advanced from angular
    velocity using a geometric increment instead of Euler angles
- Reference frames used by the simulator:
  - position and linear velocity live in the inertial/world frame
  - angular velocity and commanded torque live in body axes
  - thrust is generated along body `+z` and rotated into the world frame

## Assumptions And Simplifications

- The airframe is treated as a single rigid body with lumped mass and diagonal
  inertia tensor.
- The nominal plant uses aggregated thrust and torque at body level even when a
  rotor-level path exists internally.
- Structural flexibility, rotor flapping, battery voltage sag, and contact
  effects are outside the model scope.
- Quaternion representation avoids singularities from Euler angles, but the
  simulator is still a discrete-time numerical approximation, not a symbolic
  continuous proof.

## Impact On The Simulator

- `VehicleState` and `VehicleObservation` depend on this state definition.
- `RigidBody6DOFDynamics` uses this model as the plant baseline and integrates
  it with RK4.
- The cascade controller reasons over this same split between translational and
  rotational motion.
- Tracking metrics and telemetry interpretation depend on understanding which
  magnitudes are in the world frame and which ones are in body axes.
- Interpretation limit: the model is physically coherent for TFG experiments,
  but it is not a high-fidelity digital twin of the LiteWing platform.

## Related Documents

- System blocks:
  - [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
  - [Main Simulator Interfaces](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
- Hardware context:
  - [LiteWing Physical Context](/Users/chris/Documents/Universidad/TFG/docs/hardware/litewing-physical-context.md)
  - [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
- Validation artifacts:
  - telemetry and metrics flows described from the system view

## Related ADRs

- ADRs:
  - [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
  - [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)

## Notes For Thesis Reuse

- Possible chapter or section: modelado dinamico del multirrotor
- What can be reused almost verbatim later:
  - state definition
  - frame conventions
  - main assumptions of the nominal 6DOF plant
