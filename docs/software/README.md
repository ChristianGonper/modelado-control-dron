# Software

## Purpose

This folder will contain the code-facing design view of the project at module, interface, and main-class level.

## Main Documents

- [Software Module Selection](/Users/chris/Documents/Universidad/TFG/docs/software/software-module-selection.md)
- [Execution, Scenarios, and Core Contracts](/Users/chris/Documents/Universidad/TFG/docs/software/execution-scenarios-and-core-contracts.md)
- [Control, Trajectories, and Dynamics](/Users/chris/Documents/Universidad/TFG/docs/software/control-trajectories-and-dynamics.md)
- [Telemetry, Dataset, and Experimental Outputs](/Users/chris/Documents/Universidad/TFG/docs/software/telemetry-dataset-and-experimental-outputs.md)
- [Main Interfaces and Classes](/Users/chris/Documents/Universidad/TFG/docs/software/main-interfaces-and-classes.md)
- [Base Operativa De La CLI Neuronal](./control-neuronal-cli-foundation.md)

## Supporting Seeds

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
-> the relevant module or interface sheet
-> the relevant ADR.

The current software view intentionally prioritizes:

- contracts that stabilize the simulator architecture
- orchestration modules that define the execution flow
- extension points used by trajectories, controllers, telemetry, and learning

It intentionally does not document every helper file, utility function, or training detail with no architectural role.
