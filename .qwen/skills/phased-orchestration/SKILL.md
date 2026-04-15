---
name: phased-orchestration
description: Coordinates a multi-phase implementation from a task-breakdown document while one orchestrator agent supervises dedicated phase workers. Use when the user explicitly wants orchestration, phased delegation, or one agent to stay in control across multiple phases, not when a single subagent is only implementing one assigned phase.
---

# Phased Orchestration

## Quick Start

Use this skill when the user wants one agent to stay in control while other agents execute phases and tasks from a task-breakdown document.

Core stance:
- The orchestrator stays active for the full run.
- Work advances phase by phase unless the user explicitly asks for parallelism.
- A different subagent is launched for each phase.
- Each phase ends with review, verification, and a git checkpoint before the next handoff.

See [REFERENCE.md](REFERENCE.md) for the full workflow and guardrails.

## Workflow

1. Read the task-breakdown document, current repo state, and any explicit constraints from the user.
2. Extract the ordered phases, tasks, checkpoints, dependencies, acceptance criteria, and verification steps from that document.
3. Launch a distinct subagent only for the current phase, passing the path to the task-breakdown file so the subagent can read the full task context directly.
4. Wait for that phase to complete, then review the result before sending follow-up work or moving on.
5. Record decisions or architectural changes using [$documentation-and-adrs](../documentation-and-adrs/SKILL.md) when the phase changes design, APIs, or engineering assumptions.
6. Create a commit checkpoint for the phase when the work is verified.
7. Continue launching one fresh subagent per remaining phase until the task breakdown is complete, then do the final integration step to `main`.

## Operating Rules

- Default to sequential execution. Do not parallelize dependent phases.
- Assume the source file is a phased task breakdown unless the user explicitly says otherwise.
- The orchestrator does not disappear after spawning a subagent; it remains responsible for supervision and review until all phases are closed.
- Do not reuse the same subagent across multiple phases unless the user explicitly asks for it.
- Every handoff to a subagent must include: the path to the task-breakdown file, scope, files or ownership area, acceptance criteria, verification, and any required constraints.
- Instruct the subagent to read the referenced task-breakdown file before implementing the assigned phase or tasks.
- Instruct the subagent that it may invoke [$documentation-and-adrs](../documentation-and-adrs/SKILL.md) when the phase introduces decisions, API changes, or other durable context that should be recorded.
- If a phase fails review, send a focused follow-up to the same subagent or a replacement agent with the specific gap.
- Use Context7 for programming documentation.
- The model to use for subagents should come from the user's orchestration prompt. If missing, use gpt-5.4-mini with medium effort.
- Keep git actions explicit and phase-based. Keep commit messages simple, less than 10 words.
- Respect task checkpoints from the breakdown. Do not jump past a checkpoint without closing the tasks that feed it, unless the user explicitly reprioritizes.

## Deliverables

The orchestrator should leave behind:
- A visible phase sequence
- Review outcomes for each phase
- Commit checkpoints.
- Documentation updates for important decisions
- A final summary of completed phases, open risks, and next actions
