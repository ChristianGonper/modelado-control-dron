# ADR-005: Structured telemetry export and tracking metrics

Status: Accepted

## Context

Phase 4 requires telemetry that can be analyzed, exported, and compared across runs without coupling file generation to the runner.

The simulator already produces a full in-memory history. The missing piece is a stable telemetry schema that captures the control loop context and a set of export formats that preserve the same execution semantics.

## Decision

The telemetry model is now centered on per-step records with:

- simulation time
- post-step state
- reference sample
- tracking error derived from the observed state
- control command
- relevant events

The history also stores scenario and telemetry metadata separately so downstream tools can inspect execution context without re-running the simulation.

Export is handled outside the runner and supports three targets:

- `CSV` with a comment header containing execution metadata and a flattened tabular sample stream
- `JSON` with a hierarchical payload containing metadata plus the sample list
- `NumPy` via compressed `.npz` archives with numeric arrays and JSON-encoded metadata fields

Telemetry detail level is validated in the scenario schema and currently supports `compact`, `standard`, and `full`. The same scenario field also controls optional sampling density for export.

Basic tracking metrics are computed from telemetry histories and expose comparable summaries for error and control effort.

## Consequences

- The runner remains pure and returns structured data only.
- Exporters can evolve independently from simulation code.
- Metrics can be compared across homogeneous runs using the same telemetry contract.
- The CSV and NumPy representations are intentionally flattened for analysis tools, while JSON keeps the most readable structure.
