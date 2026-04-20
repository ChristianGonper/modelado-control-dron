# TFG Documentation

## What This Documentation Is For

This `docs/` area explains the TFG as a coherent system, not just as a sequence of phase deliverables.
The project centers on a multirotor simulator used as an academic experimental platform for trajectory control, later extended toward neural controllers and eventual hardware-informed validation.

This documentation is written for three practical uses:

- explain the project clearly to a new reader or tutor
- justify technical decisions and simplifications
- support future writing of the TFG report without rebuilding the context from scratch

## Academic Scope And Global Simplifications

The scope is academic and experimental.
The simulator is intended to be useful, traceable, and maintainable inside a TFG, not to be a full digital twin of the LiteWing platform or a full flight-stack replacement.

Global simplifications that apply across the documentation:

- the simulator is a controlled research platform, not a production autopilot
- physical fidelity is intentionally selective and bounded by TFG scope
- sim-to-real implications are treated cautiously and must not be overstated
- theory is included only where it helps explain the modeled system and the interpretation of results
- software documentation focuses on modules, interfaces, and major classes rather than exhaustive function-level detail
- architecture decisions stay in ADRs, which remain the official source for "why"

## How To Read This Documentation

Start here, then choose the next path based on your question:

- Project and documentation structure:
  - [Overview Landing Page](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md)
  - [Document Conventions](/Users/chris/Documents/Universidad/TFG/docs/overview/document_conventions.md)
  - [Documentation Inventory](/Users/chris/Documents/Universidad/TFG/docs/documentation_inventory.md)
  - [Documentation Map](/Users/chris/Documents/Universidad/TFG/docs/documentation_map.md)
  - [PRD: Documentacion Integral Del TFG](/Users/chris/Documents/Universidad/TFG/docs/PRD_documentacion_integral_tfg.md)
- Architecture and current system state:
  - [System Landing Page](/Users/chris/Documents/Universidad/TFG/docs/system/README.md)
  - [Layered System View](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
  - [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
  - [Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md)
  - [Estado Actual Del Simulador](/Users/chris/Documents/Universidad/TFG/docs/estado_actual_simulador.md)
  - [Extension Points](/Users/chris/Documents/Universidad/TFG/docs/extension-points.md)
  - [ADRs](/Users/chris/Documents/Universidad/TFG/docs/decisions)
- Theory and modeling basis:
  - [Theory Landing Page](/Users/chris/Documents/Universidad/TFG/docs/theory/README.md)
  - current theory is still embedded in [PRD Phase 1](/Users/chris/Documents/Universidad/TFG/docs/PRD_phase1_simulador_multirotor.md), [PRD Phase 2](/Users/chris/Documents/Universidad/TFG/docs/PRD_phase2_control_neuronal.md), and the relevant ADRs
- Hardware context:
  - [Hardware Landing Page](/Users/chris/Documents/Universidad/TFG/docs/hardware/README.md)
  - [Dron Fisico](/Users/chris/Documents/Universidad/TFG/docs/Dron_fisico.md)
- Software design:
  - [Software Landing Page](/Users/chris/Documents/Universidad/TFG/docs/software/README.md)
- Validation and experimental support:
  - [Validation Landing Page](/Users/chris/Documents/Universidad/TFG/docs/validation/README.md)
  - [Document Quality And Review Checklist](/Users/chris/Documents/Universidad/TFG/docs/validation/document-quality-and-review-checklist.md)
  - [Thesis Mapping And Final Coherence Review](/Users/chris/Documents/Universidad/TFG/docs/validation/thesis-mapping-and-final-coherence-review.md)
  - [Reference Scenarios](/Users/chris/Documents/Universidad/TFG/docs/reference_scenarios.md)
  - [Phase 2 Dataset Specification](/Users/chris/Documents/Universidad/TFG/docs/phase2-control-neuronal-dataset-spec.md)
  - [Phase 6 Robustness And Delivery](/Users/chris/Documents/Universidad/TFG/docs/phase6_robustness_and_delivery.md)
- Reusable formats:
  - [Templates Landing Page](/Users/chris/Documents/Universidad/TFG/docs/templates/README.md)

## Recommended Reading Order

For a new technical reader:

1. Read this file.
2. Read the [Documentation Inventory](/Users/chris/Documents/Universidad/TFG/docs/documentation_inventory.md) to understand what is current, historical, or specialized.
3. Read the [Documentation Map](/Users/chris/Documents/Universidad/TFG/docs/documentation_map.md) to understand the target view structure.
4. Read [Estado Actual Del Simulador](/Users/chris/Documents/Universidad/TFG/docs/estado_actual_simulador.md) for the present system baseline.
5. Branch to theory, hardware, validation, or ADRs depending on the question you need to answer.

## What Each Main Area Means

- `overview`: entry point, scope, reading order, and documentation structure
- `theory`: physical and mathematical basis that explains the model and its limits
- `system`: layers, blocks, interfaces, and overall system behavior
- `software`: module-level and contract-level code design
- `hardware`: the physical drone context that motivates the simulator
- `decisions`: ADRs and decision traceability
- `validation`: reference scenarios, benchmark method, and methodological limits
- `templates`: future reusable document formats

## Folder Structure

The Phase 2 structure now exists explicitly under `docs/`:

- `overview/`
- `theory/`
- `system/`
- `software/`
- `hardware/`
- `decisions/`
- `validation/`
- `templates/`

Existing root-level documents remain accessible while the new views grow around them.
The conventions for naming, placement, and cross-links live in [Document Conventions](/Users/chris/Documents/Universidad/TFG/docs/overview/document_conventions.md).

## Current State Of The Documentation System

Phase 2 establishes the base folders and templates, but it does not yet populate the deeper technical content planned for later phases.
That means some views already have strong source documents, while others are still represented by seed documents:

- `overview` now has an explicit entry point, map, and conventions
- `decisions` is already mature through ADRs
- `system` currently starts from `docs/system/README.md` and `estado_actual_simulador.md`
- `hardware` currently starts from `docs/hardware/README.md` and `Dron_fisico.md`
- `validation` now also includes review criteria, a reusable checklist, and a provisional thesis mapping for final closure
- `templates` keeps the reusable formats that support future maintenance

## Reading Caution

Several existing documents were written for specific project phases.
They remain useful, but they should be interpreted according to their role:

- PRDs and idea documents explain planned intent at the time they were written
- status documents explain delivered state
- ADRs explain accepted decisions
- support specifications explain narrow operational contracts

When two documents appear to overlap, prefer the classification in the [Documentation Inventory](/Users/chris/Documents/Universidad/TFG/docs/documentation_inventory.md).
