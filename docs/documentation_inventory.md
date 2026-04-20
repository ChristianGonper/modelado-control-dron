# Documentation Inventory And Classification

## Purpose

This inventory classifies the current documentation in `docs/` before Phase 2 restructures folders and templates.
Its role is to answer three questions:

- what document is the current source of truth for each topic
- what material should remain as specialized support or historical context
- where the current system has duplication, overlap, or missing views

## Role Definitions

- `primary`: main source for a topic in the current documentation map
- `specialized`: valid support document for a narrow topic or phase
- `historical`: useful project history or planning context, but not the main reader path
- `structural`: document that defines how the documentation system itself should work

## Inventory

| Document | Current topic | Role | Destination in target map | Decision |
|---|---|---|---|---|
| `docs/README.md` | Main entry point | primary | `overview` | Created in Phase 1 as the navigation root for new readers. |
| `docs/documentation_inventory.md` | Documentation inventory | structural | `overview` | Keep as the explicit baseline for future consolidation work. |
| `docs/documentation_map.md` | Target documentation map | structural | `overview` | Keep as the stable description of views and relationships. |
| `docs/PRD_documentacion_integral_tfg.md` | PRD for the documentation system | structural | `overview` + historical support | Keep as the product definition for the documentation effort, but do not use it as the everyday entry point. |
| `docs/IDEA_inicial.md` | Original project vision and roadmap | historical | `overview` historical context | Preserve as project origin and early scope framing. |
| `docs/PRD_phase1_simulador_multirotor.md` | Product definition for simulator phase | historical | `overview` historical context + future traceability | Keep as the main planning record for Phase 1, not as the architectural overview. |
| `docs/estado_actual_simulador.md` | Current delivered simulator capabilities | primary | `system` overview seed | Keep as the main current-state summary until dedicated system-view documents exist. |
| `docs/reference_scenarios.md` | Reference scenario battery | specialized | `validation` | Keep as a validation/support document. |
| `docs/extension-points.md` | Controller and dataset extension boundary | specialized | `software` or `system` support | Keep as implementation support until a fuller software view exists. |
| `docs/backlog_tecnico.md` | Recommended technical backlog | specialized | `validation` or project-planning appendix | Keep as forward-looking context, not as core system documentation. |
| `docs/Dron_fisico.md` | LiteWing physical platform context | primary | `hardware` | Keep as the seed of the hardware view, but rewrite later to align tone and cite project-specific relevance more explicitly. |
| `docs/PRD_phase2_control_neuronal.md` | Product definition for neural-control phase | historical | `overview` historical context + future traceability | Keep as the main planning record for Phase 2. |
| `docs/Phase-2_Idea.md` | Early Phase 2 plan | historical | historical appendix | Keep only as early exploration context; it should not compete with the formal PRD. |
| `docs/phase2-control-neuronal-dataset-spec.md` | Dataset contract | specialized | `software` + `validation` support | Keep as the current source for dataset semantics. |
| `docs/phase6_robustness_and_delivery.md` | OOD and delivery methodology | specialized | `validation` | Keep as methodology and reporting support. |
| `docs/decisions/ADR-001-core-contracts.md` | Core simulator contracts | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-002-tracer-bullet-runner.md` | Runner baseline | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-003-scenario-contract-and-seed.md` | Scenario contract and reproducibility | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-004-trajectory-contract-and-horizon.md` | Trajectory contract | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-005-telemetry-export-and-metrics.md` | Telemetry and metrics | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-006-aerodynamics-and-disturbances.md` | Aerodynamics and disturbances | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-007-static-analysis-outputs.md` | Analysis outputs | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md` | Replaceable controller boundary | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md` | Dynamics and observability baseline | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-010-mixer-actuator-timebase.md` | Mixer, actuators, and timing model | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md` | Wind model and tracking observability | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-012-external-scenarios-and-reference-battery.md` | External scenarios and validation battery | primary | `decisions` + `validation` traceability | Keep as accepted decision record. |
| `docs/decisions/ADR-013-phase-2-dataset-contract.md` | Dataset contract | primary | `decisions` + `software` traceability | Keep as accepted decision record. |
| `docs/decisions/ADR-014-phase-2-episode-split-and-windowing.md` | Dataset split and windowing | primary | `decisions` + `validation` traceability | Keep as accepted decision record. |
| `docs/decisions/ADR-015-phase-3-mlp-checkpoint-and-benchmark.md` | MLP checkpoint and benchmark slice | primary | `decisions` | Keep as accepted decision record. |
| `docs/decisions/ADR-016-phase-5-metrics-reporting-selection.md` | Reporting and model selection | primary | `decisions` + `validation` traceability | Keep as accepted decision record. |
| `docs/decisions/ADR-017-phase-6-ood-robustness-and-delivery.md` | OOD robustness and delivery packaging | primary | `decisions` + `validation` traceability | Keep as accepted decision record. |

## Classification By View

### Overview

- Current primary source: `docs/README.md`
- Current supporting sources:
  - `docs/PRD_documentacion_integral_tfg.md`
  - `docs/IDEA_inicial.md`
  - `docs/PRD_phase1_simulador_multirotor.md`
  - `docs/PRD_phase2_control_neuronal.md`

### Theory

- Current primary source: none
- Current supporting sources: theory is embedded indirectly inside PRDs and ADRs
- Gap: there is no dedicated theory view yet

### System

- Current primary source: `docs/estado_actual_simulador.md`
- Current supporting sources:
  - `docs/extension-points.md`
  - multiple ADRs in `docs/decisions/`

### Software

- Current primary source: none
- Current supporting sources:
  - `docs/extension-points.md`
  - `docs/phase2-control-neuronal-dataset-spec.md`
  - ADR series in `docs/decisions/`
- Gap: there is no software design overview that bridges repo structure, modules, and contracts

### Hardware

- Current primary source: `docs/Dron_fisico.md`
- Gap: the physical platform exists as imported context, but not yet as a TFG-specific hardware view

### Decisions

- Current primary source: `docs/decisions/ADR-001...017`
- Status: this is already the cleanest and most stable documentation area

### Validation

- Current primary source: none
- Current supporting sources:
  - `docs/reference_scenarios.md`
  - `docs/phase2-control-neuronal-dataset-spec.md`
  - `docs/phase6_robustness_and_delivery.md`
  - selected ADRs
- Gap: validation is documented by artifact or phase, not yet as a clear view

## Duplications And Overlaps

- `docs/IDEA_inicial.md`, `docs/PRD_phase1_simulador_multirotor.md`, and `docs/estado_actual_simulador.md` overlap on simulator scope, but each answers a different time horizon:
  - `IDEA_inicial.md`: early project vision
  - `PRD_phase1_simulador_multirotor.md`: planned scope for Phase 1
  - `estado_actual_simulador.md`: current delivered state
- `docs/Phase-2_Idea.md` and `docs/PRD_phase2_control_neuronal.md` overlap strongly on Phase 2 planning:
  - the PRD should be treated as the authoritative phase-planning document
  - `Phase-2_Idea.md` should remain historical only
- `docs/extension-points.md`, `docs/phase2-control-neuronal-dataset-spec.md`, and ADR-008/013/014 partially overlap around controller replacement and dataset semantics:
  - ADRs hold the "why"
  - specialized docs hold the operational contract
  - a future software view should absorb the high-level explanation and link out instead of repeating it
- validation knowledge is split between `reference_scenarios.md`, `phase6_robustness_and_delivery.md`, and several ADRs, with no single validation landing page

## Evident Gaps

- No dedicated theory documentation view
- No dedicated software architecture overview
- No dedicated system map by layers, blocks, and interfaces
- No documentation landing page for new readers
- No explicit document explaining what belongs to overview, theory, system, software, hardware, decisions, validation, and templates
- No template area yet, although it is part of the target map

## Main Consolidation Decisions For Phase 1

- Keep ADRs as the official source of architecture decisions without rewriting them elsewhere.
- Treat PRDs and early idea documents as planning and historical context, not as the first reading path.
- Use `estado_actual_simulador.md` as the best current seed for the future system view.
- Use `Dron_fisico.md` as the seed for the future hardware view, while noting that it still needs TFG-specific framing.
- Create a stable overview layer now, and defer folder reorganization and templates to Phase 2.
