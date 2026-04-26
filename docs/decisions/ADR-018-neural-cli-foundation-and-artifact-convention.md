# ADR-018: Phase 1 neural CLI foundation and artifact convention

## Status
Accepted

## Date
2026-04-21

## Context

The repository already contains reusable internal capabilities for dataset extraction, supervised training, benchmark execution, reporting, and checkpoint inspection. What it does not yet have is a public and consistent operational surface for those capabilities.

The current root CLI only supports a minimal demo path, external scenario execution, and analysis output generation. That is sufficient for simulator validation, but not for a reproducible neural-control workflow with clear dataset, training, benchmark, report, and inspection stages.

Phase 1 needs a durable public contract for the CLI and for artifact naming so that later phases can be implemented without re-deciding how runs are organized.

## Decision

Expose the neural-control workflow under the root simulator command as a dedicated namespace, with stage-oriented subcommands:

- dataset preparation
- individual training for `MLP`, `GRU`, and `LSTM`
- comparative training for the three architectures
- main benchmark execution
- OOD benchmark execution
- main report generation
- OOD report generation
- checkpoint inspection

Use a shared argument vocabulary across the entire surface:

- `seed` and `split_seed`
- `feature_mode`
- explicit input and output directories
- architecture-specific hyperparameters only where they are genuinely different

Persist artifacts in stage-separated directories with a manifest for every run. The persisted payload must record the stage, run identifier, command, input paths, output path, and the effective configuration used for the execution.

Keep benchmark main and benchmark OOD separate at the artifact level as well as at the command level:

- the main benchmark and report may participate in model selection
- the OOD benchmark and report must not participate in model selection
- both payloads must store `benchmark_kind` and `scenario_set_key`

Preserve the existing methodological boundary:

- control is computed from `observed_state`
- tracking evaluation is anchored to `true_state`

## Alternatives Considered

### Keep the current minimal CLI and add ad hoc scripts

- Pros: fewer immediate changes.
- Cons: hides the workflow, weakens traceability, and invites incompatible one-off conventions.
- Rejected: the whole point of Phase 1 is to make the workflow operable without scripts outside the product.

### Add a flat set of flags to the existing root command

- Pros: minimal surface area.
- Cons: ambiguous as soon as training, benchmarking, and reporting need different inputs and outputs.
- Rejected: the workflow needs stage separation, not a long list of unrelated flags.

### Mix main and OOD outputs into the same artifact tree

- Pros: simpler directory layout.
- Cons: makes the methodological boundary easy to blur and easy to misuse.
- Rejected: the main benchmark and OOD battery solve different questions.

## Consequences

- Future CLI implementation can map directly to the internal dataset, control, benchmark, and reporting modules.
- Users get a stable mental model for where each artifact lives and what it means.
- The repository gains a written contract for stage naming, metadata, and separation between main and OOD evaluation.
- Any later addition to the CLI must follow the same argument vocabulary and artifact convention or be treated as a breaking change in documentation.
