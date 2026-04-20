# Aerodynamic Disturbances And Observability Limits

## Metadata

- Title: Aerodynamic Disturbances And Observability Limits
- Status: active
- Scope: environmental effects and state visibility assumptions used in experiments
- Applies to: `dynamics/aerodynamics.py`, `runner.py`, telemetry, metrics, dataset extraction
- Primary view: `theory`

## Concept Summary

The simulator adds a compact disturbance layer on top of the rigid-body model:
parasitic drag, induced hover efficiency loss, deterministic wind offset, and
seeded stochastic gusts. It also distinguishes between the true plant state,
the observed state, and the state used for tracking metrics.

This matters because it defines what uncertainties are present in the
experiments and prevents reading logged errors as if all states were directly
measured without noise or modeling bias.

## Essential Formulation

- Parasitic drag:
  - body-level force opposite to relative air velocity
  - proportional to air density, effective drag area, and speed magnitude
- Induced hover loss:
  - simplified reduction of effective collective thrust as commanded thrust
    approaches the configured maximum
- Wind:
  - deterministic base velocity plus a seeded gust process
  - gusts follow an Ornstein-Uhlenbeck update so their stationary variance does
    not depend on the chosen `dt`
- Observability split:
  - `true_state`: simulated physical state
  - `observed_state`: state exposed to the controller after observation
    perturbations
  - `tracking_state`: source used to compute tracking error, currently anchored
    to the true state by default

## Assumptions And Simplifications

- Aerodynamic effects are aggregated at body level, not modeled per rotor.
- Drag area and induced-loss parameters are compact tuning coefficients rather
  than identified airframe constants.
- Wind is stochastic but seeded and reproducible through scenario configuration.
- The observability model is explicit but still lightweight: no full sensor
  fusion stack, delay chain, or onboard estimator is simulated.

## Impact On The Simulator

- `AerodynamicEnvironment` centralizes drag, induced effects, and wind sampling.
- The runner preserves disturbance metadata and the true/observed split inside
  telemetry, metrics, and downstream dataset generation.
- Robustness and benchmark experiments can compare controllers under controlled
  disturbance settings without changing the base contracts.
- Interpretation limit: these effects make the simulator less idealized, but
  they do not validate sim-to-real transfer by themselves.

## Related Documents

- System blocks:
  - [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
  - [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
- Hardware context:
  - [LiteWing Physical Context](/Users/chris/Documents/Universidad/TFG/docs/hardware/litewing-physical-context.md)
- Validation artifacts:
  - telemetry, metrics, benchmark, and robustness reports

## Related ADRs

- ADRs:
  - [ADR-006](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-006-aerodynamics-and-disturbances.md)
  - [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)

## Notes For Thesis Reuse

- Possible chapter or section: perturbaciones, incertidumbre y observabilidad
- What can be reused almost verbatim later:
  - compact disturbance model description
  - observability split and its consequence for metrics
  - statement of sim-to-real limits
