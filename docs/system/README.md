# System

## Purpose

This folder explains the TFG as an engineered system through layers, blocks,
interfaces, and traceability toward decisions and later software documents.

The goal of this view is not to restate the code file by file. It is to make
the project explainable at system level to a tutor or technical reader who
needs to understand what exists, how it fits together, and where the modeled
system stops.

## Current Core Documents

- [Layered System View](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
- [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- [Main Simulator Interfaces](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
- [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
- [Estado Actual Del Simulador](/Users/chris/Documents/Universidad/TFG/docs/estado_actual_simulador.md)
- [System Block Template](/Users/chris/Documents/Universidad/TFG/docs/templates/system-block-template.md)
- related ADRs in [Decisions](/Users/chris/Documents/Universidad/TFG/docs/decisions)

## Reading Order

1. Start with [Layered System View](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
   to understand the global flow.
2. Continue with [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
   to identify the main functional pieces.
3. Use [Main Simulator Interfaces](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
   to follow the contracts between those blocks.
4. Use [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
   to clarify the relation between the simulator and the real drone context.
5. Open [Estado Actual Del Simulador](/Users/chris/Documents/Universidad/TFG/docs/estado_actual_simulador.md)
   when you need the delivered-state inventory.

## What Belongs Here

- layer views of the system
- high-level system flow without code reading
- block-level responsibilities and relations
- main contracts between blocks
- system-level boundaries toward hardware, theory, software, and validation
- selective links to ADRs when they stabilize the view

## What Does Not Belong Here

- exhaustive theory derivations
- file-by-file code inventory
- exhaustive interface contracts between modules
- class-level design depth that belongs to `docs/software/`

## Boundary

System documents explain responsibilities and interactions.
They should remain stable even if the internal implementation evolves.
