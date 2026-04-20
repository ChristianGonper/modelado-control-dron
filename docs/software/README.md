# Software

## Purpose

This folder will contain the code-facing design view of the project at module, interface, and main-class level.

## Current Seeds

- [Extension Points](/Users/chris/Documents/Universidad/TFG/docs/extension-points.md)
- [Phase 2 Dataset Specification](/Users/chris/Documents/Universidad/TFG/docs/phase2-control-neuronal-dataset-spec.md)
- [Software Contracts And Traceability](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
- [Software Module Template](/Users/chris/Documents/Universidad/TFG/docs/templates/software-module-template.md)
- [Interface Or Class Template](/Users/chris/Documents/Universidad/TFG/docs/templates/interface-or-class-template.md)

## Expected Content

- module sheets
- software contracts that bridge the code and the system view
- main classes and interfaces with architectural value
- extension points and important dependencies
- selective ADR links when the contract shape needs justification

## Boundary

Software documents should remain above exhaustive API documentation.
If a point is only meaningful at system level, keep the primary explanation in `docs/system/`.
If a reader starts from `overview`, the expected route is `system` ->
[Software Contracts And Traceability](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
-> the relevant ADR.
