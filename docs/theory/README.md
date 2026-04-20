# Theory

## Purpose

This folder will hold the theory notes and concept sheets needed to explain the simulator and the control problem.
It is the home for selective physical and mathematical basis, not for code documentation.

## Prioritized Concepts

The theory scope for this TFG is intentionally selective. A concept only gets a
dedicated sheet when it explains a real simulator block or a physical boundary
that appears elsewhere in `docs/`.

### Priority 1

1. [Rigid-body 6DOF dynamics and reference frames](/Users/chris/Documents/Universidad/TFG/docs/theory/rigid-body-6dof.md)
   because `dynamics/`, `control/`, telemetry, and tracking all depend on the
   meaning of state, quaternion attitude, thrust, and body torque.
2. [Rotor actuation, mixer, and simulation time bases](/Users/chris/Documents/Universidad/TFG/docs/theory/rotor-actuation-and-timebase.md)
   because the implemented plant no longer consumes an instantaneous wrench only:
   the simulator resolves controller intent through a mixer, first-order motor
   lag, and decoupled physics/control/telemetry rates.
3. [Aerodynamic disturbances and observability limits](/Users/chris/Documents/Universidad/TFG/docs/theory/aerodynamic-disturbances-and-observability.md)
   because the current model includes drag, induced hover loss, seeded wind
   gusts, and an explicit split between true, observed, and tracking states.

### Priority 2

4. Physical drone context, especially propulsion, sensing, and onboard control
   constraints, documented in
   [LiteWing Physical Context](/Users/chris/Documents/Universidad/TFG/docs/hardware/litewing-physical-context.md).
   This belongs primarily to `hardware/`, but it is part of the theory route
   because it explains what the simulator is abstracting instead of reproducing.

## Reading Order

1. Start with the prioritized concept list in this document.
2. Read the three theory sheets in priority order.
3. Use [LiteWing Physical Context](/Users/chris/Documents/Universidad/TFG/docs/hardware/litewing-physical-context.md)
   when you need the real-platform boundary.
4. Continue with [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
   or [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
   to place each concept inside the full simulator.

## Current Seeds

- [Theory Sheet Template](/Users/chris/Documents/Universidad/TFG/docs/templates/theory-sheet-template.md)
- [PRD Phase 1](/Users/chris/Documents/Universidad/TFG/docs/PRD_phase1_simulador_multirotor.md)
- relevant ADRs in [Decisions](/Users/chris/Documents/Universidad/TFG/docs/decisions)

## Current Sheets

- [Rigid-Body 6DOF Dynamics And Reference Frames](/Users/chris/Documents/Universidad/TFG/docs/theory/rigid-body-6dof.md)
- [Rotor Actuation, Mixer, And Simulation Time Bases](/Users/chris/Documents/Universidad/TFG/docs/theory/rotor-actuation-and-timebase.md)
- [Aerodynamic Disturbances And Observability Limits](/Users/chris/Documents/Universidad/TFG/docs/theory/aerodynamic-disturbances-and-observability.md)

## Boundary

Theory documents explain concepts, assumptions, and modeling limits.
Implementation details belong in `docs/software/`, and real-platform context belongs in `docs/hardware/`.
