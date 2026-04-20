# LiteWing Physical Context

## Metadata

- Title: LiteWing Physical Context
- Status: active
- Physical subsystem: reference drone platform and the subsystems that matter to the simulator boundary
- Real platform relevance: anchors the TFG in a plausible multirotor context without claiming digital-twin fidelity
- Primary view: `hardware`

## Subsystem Role In The Real Drone

The LiteWing drone provides the physical reference that motivates the simulator:
small multirotor propulsion, onboard sensing, embedded control, and lightweight
power constraints.

It is relevant to the TFG because the simulator is not an abstract control toy.
Vehicle mass, thrust generation, noisy sensing, and disturbance sensitivity make
sense only in relation to a real class of platform.

## Real-World Characteristics

- Main components:
  - quadrotor airframe in a lightweight PCB-based format
  - four coreless DC motors with PWM motor control
  - IMU-based attitude sensing and optional altitude/position aids
  - onboard ESP32-S3 compute, wireless communication, and battery-powered flight
- Key signals, magnitudes, or operating limits:
  - limited thrust margin and energy budget compared with larger drones
  - sensing depends primarily on IMU data unless extra sensors are integrated
  - onboard firmware and communications introduce implementation constraints not
    reproduced by the simulator
- Environmental or operational constraints:
  - sensitivity to wind and setup variation because of small size and low mass
  - real flights depend on calibration, firmware timing, and hardware health

## Representation In The Model

- How this subsystem is represented in the simulator:
  - the vehicle is condensed into lumped rigid-body parameters, optional rotor
    geometry, disturbance settings, and observation perturbations
  - controller output is interpreted as thrust and torque intent, optionally
    resolved through a rotor mixer and motor lag
- What is abstracted, simplified, or omitted:
  - no embedded firmware stack, radio protocol, estimator internals, battery
    discharge model, or detailed sensor driver behavior
  - aerodynamic effects are compact body-level approximations
  - actuator dynamics are first-order rather than hardware-specific
- What should not be interpreted as sim-to-real equivalence:
  - a matched parameter value in the simulator does not imply LiteWing-grade
    fidelity
  - neural or classical controllers validated here still need a dedicated
    transfer and safety process before real deployment

## Interfaces With The Rest Of The System

- Upstream or downstream physical relationships:
  - propulsion generates thrust and torque
  - sensing constrains what the controller can observe
  - power and compute constraints shape real deployment, even when not modeled
- Related simulated blocks:
  - [Dynamics And Environment](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
  - [Flight Control](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
  - [Telemetry And Traceability](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- Observable effects in telemetry or experiments:
  - tracking error under wind or observation noise
  - actuator-lag effects on aggressive maneuvers
  - sensitivity of benchmark results to disturbance settings

## Traceability

- Related theory documents:
  - [Rigid-Body 6DOF Dynamics And Reference Frames](/Users/chris/Documents/Universidad/TFG/docs/theory/rigid-body-6dof.md)
  - [Rotor Actuation, Mixer, And Simulation Time Bases](/Users/chris/Documents/Universidad/TFG/docs/theory/rotor-actuation-and-timebase.md)
  - [Aerodynamic Disturbances And Observability Limits](/Users/chris/Documents/Universidad/TFG/docs/theory/aerodynamic-disturbances-and-observability.md)
- Related system blocks:
  - [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
  - [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- Related software modules, if any:
  - `src/simulador_multirotor/dynamics/`
  - `src/simulador_multirotor/control/`
  - `src/simulador_multirotor/runner.py`
- Related ADRs:
  - [ADR-006](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-006-aerodynamics-and-disturbances.md)
  - [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
  - [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)
  - [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)

## Open Questions Or Boundaries

- Pending uncertainty:
  - the simulator uses a LiteWing-informed context, but not an identified
    parameter set extracted from flight tests
- Evidence source or reference material:
  - [Dron Fisico](/Users/chris/Documents/Universidad/TFG/docs/Dron_fisico.md)
  - vendor and wiki material referenced there
