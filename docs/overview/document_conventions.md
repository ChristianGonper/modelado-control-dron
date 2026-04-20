# Document Conventions

## Purpose

These conventions define how the `docs/` structure grows from Phase 2 onward without repeated reorganization.

## Folder Responsibilities

| Folder | Responsibility |
|---|---|
| `docs/overview/` | Entry points, reading guides, scope, and documentation-system structure |
| `docs/theory/` | Physical and mathematical concepts, assumptions, and simplifications |
| `docs/system/` | Layers, blocks, interfaces, and system-level responsibilities |
| `docs/software/` | Modules, software contracts, main classes, and extension points |
| `docs/hardware/` | Physical drone context and physical subsystems relevant to the model |
| `docs/decisions/` | ADRs only |
| `docs/validation/` | Scenarios, evaluation method, evidence, and review criteria |
| `docs/templates/` | Reusable document templates |

## Naming Rules

- Use lowercase kebab-case for new document filenames.
- Reserve `README.md` for the landing page of each folder.
- Use stable nouns in filenames, not phase-specific temporary wording, unless the document is intentionally historical.
- Prefer names that describe the question answered, such as `system-layers.md`, `control-loop.md`, or `motor-mixer.md`.

## Placement Rules

- Put a document in the folder that owns its main question, then link out instead of duplicating content.
- Keep existing root-level documents reachable until later phases migrate or supersede them intentionally.
- Keep ADRs in `docs/decisions/`; other views may summarize and link to them, but should not rewrite them.
- Store templates only in `docs/templates/`, even when they are primarily used by another view.

## Cross-Linking Rules

- Start each substantial document with a short purpose statement.
- Include "Related Documents" and "Related ADRs" sections when the document participates in system traceability.
- Prefer relative conceptual links across views over repeated narrative text.
- Link to source documents that remain authoritative today, even if they still live at `docs/` root.

## Suggested Document Granularity

- One document should answer one stable question.
- Split a document when it starts covering multiple blocks, multiple concepts, or multiple audiences.
- Do not document every function or every file.
- Software detail should normally stop at module, interface, and main-class level.

## Traceability Minimum

New theory, hardware, system, and software documents should be able to answer:

- what this document is about
- where it fits in the TFG
- what other documents it depends on
- which ADRs constrain it, if any
- what assumptions or boundaries apply

## Migration Rule

When a root-level legacy document gains a clearer home later, do not move it casually.
First create the new view document, link both directions, and only reorganize paths when that move is clearly justified.
