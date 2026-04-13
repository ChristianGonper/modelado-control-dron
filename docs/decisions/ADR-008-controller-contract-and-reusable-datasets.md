# ADR-008: Replaceable controller contract and reusable execution metadata

Status: Accepted

## Context

Phase 7 requires a stable extension boundary for future intelligent control and a dataset-friendly execution format for later calibration or sim-to-real work. Before this change, the runner instantiated the PID controller indirectly through scenario-specific logic, and exported telemetry only embedded vehicle and controller information inside the generic scenario payload.

That was good enough for the tracer bullet, but it made two things harder than necessary:

- replacing the controller without touching the runner
- reusing telemetry as a self-describing dataset artifact

## Decision

Introduce a dedicated controller contract in `src/simulador_multirotor/control/contract.py` with explicit `observation -> reference -> action` typing. The runner now accepts any object implementing that contract, and the existing cascaded PID controller remains one implementation of it.

Execution exports now persist reusable metadata at the top level:

- `scenario`
- `vehicle`
- `controller`
- `telemetry`

This keeps the execution self-describing even if scenario schema details evolve later.

## Alternatives Considered

### Keep the runner coupled to the cascaded PID

- Pros: no code changes now
- Cons: the extension boundary stays implicit and future replacement becomes invasive
- Rejected: this is the exact coupling Phase 7 is meant to remove

### Use an untyped callable only

- Pros: minimal code
- Cons: no stable contract, weaker validation, and no clear guidance for future integrations
- Rejected: the simulator needs a predictable boundary for both tests and future external controllers

### Store vehicle metadata only inside the scenario blob

- Pros: fewer top-level fields
- Cons: dataset consumers must know the scenario schema to recover basic execution context
- Rejected: calibration and reuse benefit from explicit top-level metadata

## Consequences

- The existing PID controller still works unchanged through a compatibility alias.
- Tests can inject a stub controller without restructuring the runner.
- Dataset exports are easier to consume independently of the current scenario schema.
- Future controllers can be added either as direct contract implementations or through `ControllerAdapter`.
