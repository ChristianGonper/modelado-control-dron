# ADR-012: External scenario artifacts and reference battery

## Status
Accepted

## Date
2026-04-14

## Context

Phase 4 needs the simulator to move from code-built scenarios to immutable external artifacts that can be versioned, audited, and replayed exactly. The phase also needs a small reference battery that proves the physics stack still behaves as expected after the earlier refactors.

The requirements are:

- the runner and CLI must be able to load a scenario from a file
- the format must be stable enough to round-trip without changing simulation behavior
- reference scenarios must cover hover, angular maneuvering, wind perturbation, and `dt` comparison

## Decision

Use canonical JSON scenario artifacts with an explicit `schema_version` field.

- store the artifacts under `scenario_artifacts/v1/`
- load them through `SimulationScenario.from_json()` and the public scenario IO helpers
- expose CLI execution with `multirotor-sim --scenario <path>`
- keep the reference battery in tests, with quantitative assertions on the loaded scenarios

The JSON format is intentionally strict:

- unknown top-level keys are rejected
- the schema version is checked before loading
- nested vehicle, trajectory, control, disturbance, and telemetry blocks are reconstructed explicitly

## Alternatives Considered

### YAML

- Pros: more human-friendly for manual editing
- Cons: adds another parser and more ambiguity around canonical serialization
- Rejected for this phase: the artifacts are meant to be immutable reference inputs, not hand-authored config templates

### TOML

- Pros: readable and compact
- Cons: less convenient for nested structured data such as rotor arrays and telemetry metadata
- Rejected for this phase: JSON maps more directly to the dataclass graph already in the codebase

### Keep scenarios in Python only

- Pros: zero file-format work
- Cons: no immutable artifact, no external versioning, and weaker auditability
- Rejected: this phase explicitly needs frozen experiment inputs

## Consequences

- Experiments can be replayed from versioned files instead of ad hoc code construction
- The CLI can execute external scenarios without special-case wiring
- Round-trip serialization becomes part of the regression surface
- The reference battery documents the physical behaviors that are expected to remain stable across future changes
