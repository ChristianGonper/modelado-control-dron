# ADR-007: Static analysis outputs from persisted telemetry

Status: Accepted

## Context

Phase 6 requires analysis outputs that do not depend on the live simulation loop. The telemetry layer already exports structured artifacts, so the remaining choice is how downstream analysis should consume them and which artifact format should be used for fast inspection and documentation.

## Decision

Visualization reads telemetry from persisted export artifacts and renders static figures with Matplotlib using the non-interactive `Agg` backend.

The baseline analysis flow produces:

- 2D trajectory figures for quick qualitative inspection
- 2D error figures for position, velocity, and yaw tracking
- 3D trajectory figures with basic attitude cues

PNG is the default artifact format because it is portable, stable for tests, and easy to embed in the TFG memory.

## Alternatives Considered

### Interactive plots or notebooks

- Pros: richer exploration and zooming
- Cons: heavier runtime story and weaker artifact stability
- Rejected: the phase asks for lightweight reusable outputs

### Vector formats as the default

- Pros: good for publication-quality figures
- Cons: not as convenient for fast inspection and simple checks
- Rejected: PNG is the simpler baseline; vector export can be added later

### Coupling plotting to the runner

- Pros: fewer commands for the user
- Cons: mixes simulation and analysis concerns
- Rejected: the runner should remain pure and analysis should work on persisted telemetry

## Consequences

- Telemetry export becomes the source of truth for post-processing.
- The same persisted telemetry can drive both 2D and 3D inspection.
- Tests can validate artifact generation without pixel comparisons.
- The simulator keeps a clear separation between simulation and analysis.
