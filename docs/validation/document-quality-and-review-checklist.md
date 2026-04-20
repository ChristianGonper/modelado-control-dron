# Document Quality Criteria And Review Checklist

## Purpose

This document defines when a documentation view or sheet is good enough to keep
as active TFG documentation. The goal is to support closure decisions and
future updates without turning review into heavy process.

## Use Rule

Use these criteria in two moments:

- when creating a new document from a template
- when updating an existing document after code, theory, or scope changes

Apply the general checklist first, then the view-specific criteria for the
document you are reviewing.

## Quality Threshold

A document is ready to keep as live documentation when:

- its purpose, scope, and boundaries are explicit
- the content answers the main question owned by that view
- the reader can follow the next step through links instead of guessing
- the document does not duplicate an authoritative source unnecessarily
- no missing point blocks technical explanation of the simulator

Small omissions are acceptable if they do not break navigation or distort the
system explanation. Open improvements can stay as future work; critical gaps
cannot.

## General Review Checklist

Use this checklist for any document in `overview`, `theory`, `system`,
`software`, `hardware`, `decisions`, `validation`, or `templates`.

- the title matches the question the document answers
- the purpose section explains why this document exists
- the content stays inside the owning view and links out instead of duplicating
- the terminology matches the rest of `docs/`
- the document states relevant assumptions, simplifications, or boundaries
- related documents are reachable from the current text without hidden context
- ADR links appear only where they justify shape, not as decoration
- the document is still aligned with the current repository and system view
- the level of detail is sustainable for the TFG maintenance rhythm
- no section reads as placeholder text or phase note that should already be closed

## View-Specific Criteria

### Overview

- it gives a clear starting point for a new reader
- it explains reading order, scope, or classification rather than subsystem detail
- it points to theory, system, software, hardware, decisions, and validation
- it does not become a parallel architecture document

### Theory

- it explains a concept that is actually needed to understand the simulator
- it states the essential formulation without trying to become a full textbook
- it makes assumptions and modeling limits explicit
- it links to the system or hardware context where the concept matters

### System

- it explains layers, blocks, interfaces, or boundaries at system level
- responsibilities are distinguishable and not redundant
- the main flow can be explained without reading code
- the relation to hardware, theory, software, or validation is visible

### Software

- it documents modules, contracts, or main classes with architectural value
- the described responsibilities match the current code organization
- important collaborators, extension points, or invariants are visible
- it stops before exhaustive function-by-function documentation

### Hardware

- it explains the physical platform or subsystem relevant to the TFG
- it distinguishes real platform facts from simulator abstractions
- it clarifies what informs the model and what remains out of scope
- it does not imply sim-to-real equivalence without justification

### Validation

- it explains how results, evidence, or documentary closure are reviewed
- it points to the system or software elements being validated
- it clarifies what the evidence can and cannot support
- it stays lightweight enough to be reused during future updates

### Templates

- it is reusable across more than one future document
- the sections are short enough to complete without bureaucratic overhead
- it captures traceability and boundaries, not every possible detail
- it stays stable unless the documentation model itself changes

## Reusable Review Checklist For New Sheets Or Updates

Reviewers can use this sequence as a lightweight pass/fail guide.

1. Confirm the document belongs in its current folder.
2. Confirm the document answers one stable question.
3. Confirm the purpose and boundaries are explicit near the top.
4. Confirm the wording matches the established terms used elsewhere.
5. Confirm the document links to the next relevant view or source.
6. Confirm assumptions, simplifications, and non-goals are visible.
7. Confirm no key claim depends on stale or missing repository reality.
8. Confirm the document avoids duplicating ADRs, code, or theory verbatim.
9. Confirm the current level of detail is worth maintaining during the TFG.
10. Confirm there is no critical gap that would block technical explanation or thesis writing.

## Closure Guidance

Use these outcomes after applying the checklist:

- close now: the document is coherent, navigable, and good enough for current TFG use
- close with follow-up note: the core explanation is sound, but a non-critical refinement remains
- keep open: a missing link, stale claim, or structural gap still prevents reliable use

## Related Documents

- [Validation Landing Page](/Users/chris/Documents/Universidad/TFG/docs/validation/README.md)
- [Thesis Mapping And Final Coherence Review](/Users/chris/Documents/Universidad/TFG/docs/validation/thesis-mapping-and-final-coherence-review.md)
- [Document Conventions](/Users/chris/Documents/Universidad/TFG/docs/overview/document_conventions.md)
