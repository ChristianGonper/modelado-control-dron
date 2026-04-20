# Thesis Mapping And Final Coherence Review

## Purpose

This document maps the live documentation system to probable TFG thesis chapters
and records the final coherence review of the current documentation structure.
It is a working bridge for writing, not a fixed thesis index.

## Working Rule

Chapter names, boundaries, and order may change later according to tutor
feedback or university format. The mapping below is provisional on purpose:

- it helps reuse existing documents when drafting the thesis
- it avoids rewriting the same explanation from zero
- it does not freeze the final structure of the memory

## Provisional Mapping To Thesis Chapters

| Live documentation view | Main documents | Probable thesis use |
|---|---|---|
| `overview` | [docs/README.md](/Users/chris/Documents/Universidad/TFG/docs/README.md), [overview/README.md](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md), [documentation_map.md](/Users/chris/Documents/Universidad/TFG/docs/documentation_map.md) | introduction to the project, scope, objectives, reading frame, documentation method |
| `theory` | [theory/README.md](/Users/chris/Documents/Universidad/TFG/docs/theory/README.md), [rigid-body-6dof.md](/Users/chris/Documents/Universidad/TFG/docs/theory/rigid-body-6dof.md), [rotor-actuation-and-timebase.md](/Users/chris/Documents/Universidad/TFG/docs/theory/rotor-actuation-and-timebase.md), [aerodynamic-disturbances-and-observability.md](/Users/chris/Documents/Universidad/TFG/docs/theory/aerodynamic-disturbances-and-observability.md) | theoretical foundations, model assumptions, physical and mathematical basis |
| `system` | [system/README.md](/Users/chris/Documents/Universidad/TFG/docs/system/README.md), [layered-system-view.md](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md), [system-blocks.md](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md), [system-interfaces.md](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md), [physical-boundary.md](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md) | system design, architecture, subsystem decomposition, system boundaries |
| `software` | [software/README.md](/Users/chris/Documents/Universidad/TFG/docs/software/README.md), [software-module-selection.md](/Users/chris/Documents/Universidad/TFG/docs/software/software-module-selection.md), [execution-scenarios-and-core-contracts.md](/Users/chris/Documents/Universidad/TFG/docs/software/execution-scenarios-and-core-contracts.md), [control-trajectories-and-dynamics.md](/Users/chris/Documents/Universidad/TFG/docs/software/control-trajectories-and-dynamics.md), [telemetry-dataset-and-experimental-outputs.md](/Users/chris/Documents/Universidad/TFG/docs/software/telemetry-dataset-and-experimental-outputs.md), [main-interfaces-and-classes.md](/Users/chris/Documents/Universidad/TFG/docs/software/main-interfaces-and-classes.md) | implementation design, software architecture, core contracts, main abstractions |
| `hardware` | [hardware/README.md](/Users/chris/Documents/Universidad/TFG/docs/hardware/README.md), [litewing-physical-context.md](/Users/chris/Documents/Universidad/TFG/docs/hardware/litewing-physical-context.md), [Dron_fisico.md](/Users/chris/Documents/Universidad/TFG/docs/Dron_fisico.md) | platform context, real drone description, model boundary against the physical system |
| `decisions` | [docs/decisions](/Users/chris/Documents/Universidad/TFG/docs/decisions) and linked ADRs | design rationale, engineering decisions, justification of key architectural choices |
| `validation` | [validation/README.md](/Users/chris/Documents/Universidad/TFG/docs/validation/README.md), [technical-rationale-map.md](/Users/chris/Documents/Universidad/TFG/docs/validation/technical-rationale-map.md), [document-quality-and-review-checklist.md](/Users/chris/Documents/Universidad/TFG/docs/validation/document-quality-and-review-checklist.md), [reference_scenarios.md](/Users/chris/Documents/Universidad/TFG/docs/reference_scenarios.md), [phase6_robustness_and_delivery.md](/Users/chris/Documents/Universidad/TFG/docs/phase6_robustness_and_delivery.md) | validation method, evidence interpretation, documentary review, writing support |
| `templates` | [templates/README.md](/Users/chris/Documents/Universidad/TFG/docs/templates/README.md) and templates folder | appendix material or internal writing aid; not usually thesis body unless methodology discussion needs it |

## Practical Reuse Guidance

Use this mapping as a drafting shortcut:

- start thesis sections from the live document that already answers the same question
- rewrite for academic tone and chapter flow, but keep the technical structure
- link decisions and assumptions back to ADRs or validation notes instead of inventing parallel explanations
- when one live document serves multiple thesis sections, split the narrative in the thesis, not the source document by default

## Final Coherence Review

Review date: 2026-04-20

### Coverage Check

The current structure covers the required views:

- overview
- theory
- system
- software
- hardware
- decisions
- validation
- templates

### Navigation Check

The main route is complete and readable:

1. [docs/README.md](/Users/chris/Documents/Universidad/TFG/docs/README.md)
2. [overview/README.md](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md)
3. [system/README.md](/Users/chris/Documents/Universidad/TFG/docs/system/README.md)
4. [layered-system-view.md](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
5. [system-blocks.md](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
6. [system-interfaces.md](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
7. [software/software-contracts-and-traceability.md](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
8. [validation/technical-rationale-map.md](/Users/chris/Documents/Universidad/TFG/docs/validation/technical-rationale-map.md)
9. relevant ADRs in [docs/decisions](/Users/chris/Documents/Universidad/TFG/docs/decisions)

Theory and hardware are also reachable from the same route through
[docs/README.md](/Users/chris/Documents/Universidad/TFG/docs/README.md),
[theory/README.md](/Users/chris/Documents/Universidad/TFG/docs/theory/README.md),
and [hardware/README.md](/Users/chris/Documents/Universidad/TFG/docs/hardware/README.md).

### Coherence Findings

- the documentation now has an explicit validation view for both technical rationale and documentary closure
- the bridge from overview to system, software, and decisions is present and navigable
- theory, hardware, and system boundaries remain differentiated instead of merged into one narrative
- templates stay separated as maintenance tools rather than being confused with final explanation
- the thesis mapping is explicit about being provisional, which avoids freezing the final memory structure too early

### Critical Gap Review

No critical structural gap was found in the explanation route from entry point to
theory, system, software, decisions, and validation.

No broken structural link was found during the manual review of the documents
listed in this report. Legacy root-level documents remain reachable where they
still act as source material.

### Remaining Non-Critical Risk

Some root-level historical documents still coexist with the newer view-based
structure. This is acceptable for now because the current conventions already
state that legacy sources remain reachable until a later intentional migration.

## Related Documents

- [Validation Landing Page](/Users/chris/Documents/Universidad/TFG/docs/validation/README.md)
- [Document Quality Criteria And Review Checklist](/Users/chris/Documents/Universidad/TFG/docs/validation/document-quality-and-review-checklist.md)
- [Technical Rationale Map](/Users/chris/Documents/Universidad/TFG/docs/validation/technical-rationale-map.md)
