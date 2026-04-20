# Documentation Map

## Purpose

This document defines the target documentation map for the TFG without yet forcing the full folder reorganization planned for later phases.
It answers what each view exists for, what should live there, and how readers move between them.

## Reader Model

The documentation is meant to support four recurring reading modes:

- understand the TFG quickly as an academic project
- explain the current system and its limits to tutors
- justify design choices with explicit decisions
- locate detailed technical support without reading the entire repo

## Target Views

### Overview

- Purpose: provide the first reading path, project scope, reading order, and global simplifications.
- Questions answered:
  - what this TFG is about
  - what the simulator represents and what it does not
  - where to go next depending on the reader's question
- Content type:
  - main README
  - documentation inventory and map
  - phase-level PRDs and historical framing documents
- Anti-overlap rule: overview points to deeper views; it does not duplicate technical detail from system, software, or theory.

### Theory

- Purpose: explain the physical and mathematical ideas needed to understand the simulator and the control problem.
- Questions answered:
  - what theoretical concepts matter for the TFG
  - what simplifications were adopted in the model
  - where theory constrains interpretation of results
- Content type:
  - theory notes and future concept sheets
- Anti-overlap rule: theory explains principles and assumptions, not module structure or code organization.

### System

- Purpose: explain the TFG as an engineered system using layers, blocks, interfaces, and data flow.
- Questions answered:
  - what subsystems exist
  - how the physical context, simulation core, observability, analysis, and learning pieces relate
  - what interfaces connect the main blocks
- Content type:
  - layer view
  - block view
  - interface traceability
- Anti-overlap rule: system talks about responsibilities and interactions, not low-level code anatomy.

### Software

- Purpose: explain the code-facing design of the simulator and ML pipeline at package, module, interface, and main-class level.
- Questions answered:
  - where major responsibilities live in the codebase
  - what contracts modules expose
  - what extension points exist
- Content type:
  - module sheets
  - interface/class sheets
  - software-level integration notes
- Anti-overlap rule: software maps design to implementation, but does not restate all ADR rationale or all system-level flows.

### Hardware

- Purpose: document the physical drone context that motivates the simulator without implying a one-to-one digital twin.
- Questions answered:
  - what physical platform informs the work
  - what physical aspects matter to the simulator
  - where the sim-to-real boundary is intentionally loose
- Content type:
  - drone/platform description
  - physical subsystems
  - model boundary notes
- Anti-overlap rule: hardware gives real-world context; it does not describe software internals or reproduce theory derivations.

### Decisions

- Purpose: preserve the official rationale for important architecture and methodology choices.
- Questions answered:
  - why the system is shaped this way
  - what alternatives were rejected
  - which decisions affect a given subsystem
- Content type:
  - ADRs only
- Anti-overlap rule: other views summarize and link to ADRs, but do not rewrite them in full.

### Validation

- Purpose: document how the system is checked, compared, and interpreted.
- Questions answered:
  - what evidence supports the simulator and controller workflow
  - what benchmark and reference artifacts exist
  - what methodological limits constrain conclusions
- Content type:
  - reference scenarios
  - benchmark/reporting method
  - future review checklists
- Anti-overlap rule: validation explains evidence and review criteria, not the whole architecture.

### Templates

- Purpose: keep reusable formats for future theory, hardware, system, software, and validation documents.
- Questions answered:
  - how new documents should be written
  - what minimum sections preserve consistency
- Content type:
  - templates only
- Anti-overlap rule: templates define form, not project content.

## View Relationships

The map is intended to be navigated like this:

1. `overview` explains the TFG, scope, and reading order.
2. From there, readers branch according to intent:
   - `theory` for principles and assumptions
   - `system` for architecture and block interactions
   - `software` for code-facing design
   - `hardware` for physical context
   - `decisions` for rationale
   - `validation` for evidence and limits
3. `templates` support future maintenance but are not part of the main reading path.

## Current Mapping From Existing Documents

| View | Current main seeds |
|---|---|
| `overview` | `docs/README.md`, `docs/documentation_inventory.md`, `docs/documentation_map.md`, `docs/PRD_documentacion_integral_tfg.md` |
| `theory` | no dedicated seed yet; theory currently lives inside PRDs and ADRs |
| `system` | `docs/estado_actual_simulador.md` |
| `software` | `docs/extension-points.md`, `docs/phase2-control-neuronal-dataset-spec.md` |
| `hardware` | `docs/Dron_fisico.md` |
| `decisions` | `docs/decisions/ADR-001...017` |
| `validation` | `docs/reference_scenarios.md`, `docs/phase6_robustness_and_delivery.md`, selected ADRs |
| `templates` | no documents yet; reserved for Phase 2 |

## Global Boundaries And Simplifications

- The documentation system is organized by stable views, not by project phases, even though many existing documents were written phase by phase.
- The TFG centers on a useful experimental simulator, not on a full-fidelity replica of the physical drone firmware or aerodynamics.
- Hardware context informs the simulator, but the documentation must avoid claiming direct equivalence between the LiteWing platform and the simulator.
- Theory should stay selective and tied to the simulator's needs; it is not meant to become a full textbook appendix.
- Software documentation should stop at modules, interfaces, and main classes; exhaustive function-by-function documentation is out of scope.
- ADRs remain the official decision mechanism and should not be duplicated into narrative documents.
