# Phased Orchestration Reference

Primary expected input:
- A phased task-breakdown document like `plans/task_breakdown_continuacion_producto_final.md`
- Optional user constraints about model choice, git policy, documentation, and external research

## Intent

The orchestrator is the control plane for a multi-phase implementation derived from a task-breakdown file:
- It advances the plan one phase at a time.
- It keeps responsibility for supervision, review, and next-step decisions.
- It uses subagents as workers, not as replacements for orchestration.

The task-breakdown file is the source of truth for:
- Phase order
- Task boundaries
- Dependencies
- Checkpoints
- Acceptance criteria
- Verification expectations

## Phase Loop

For each phase:

1. Identify the exact phase and task slice to execute now from the task breakdown.
2. Prepare the subagent brief:
   - Goal of the phase
   - Specific tasks being executed in this round
   - Relevant files, modules, or ownership boundary
   - Acceptance criteria
   - Required verification
   - Dependencies or checkpoint constraints
   - Documentation or git expectations
   - Whether external research is allowed in this run
3. Launch the subagent with the model named by the user.
4. Stay active and monitor progress.
5. Review the completed work:
   - Check correctness and regressions
   - Run or inspect verification artifacts
   - Identify gaps, bugs, or missing tests
6. If needed, send a corrective follow-up and re-review.
7. When the phase is complete, perform the requested git checkpoint.
8. Move to the next phase only when the current one is closed.

## Git Discipline

Apply the standard git workflow defined by the orchestration prompt or skill:
- Commit at the end of each verified phase.
- Keep branch strategy explicit.
- Keep commit messages short and simple.
- Merge to `main` only after all phases are complete.

Never assume destructive git operations are acceptable.

If the task breakdown already implies a phase cadence, keep the git cadence aligned to those phase boundaries rather than inventing new ones.

## Documentation Rule

When a phase introduces architectural, scientific, engineering, or implementation decisions that future agents will need, invoke [$documentation-and-adrs](../documentation-and-adrs/SKILL.md).

Typical triggers:
- New architecture or subsystem boundaries
- API contract changes
- Physics or engineering assumptions
- Non-obvious implementation tradeoffs

## External Research Toggle

The original orchestration flow treated external research as optional and user-controlled.

Rule:
- If the user explicitly says to use Context7 and/or Exa, allow subagents to use them for current docs and targeted implementation research.
- Otherwise keep the run local to the repository and existing context.

This prevents unnecessary browsing and keeps the orchestration prompt modular.

## Findings Consolidated

These findings were promoted into the skill:
- Keep the orchestrator awake for the entire run.
- Make the subagent model configurable from the orchestration prompt.
- Improve git hygiene with a commit checkpoint per phase.
- Treat documentation as a first-class part of the flow.
- Reserve final merge to `main` for the end of the full sequence.
- Treat the phased task-breakdown document as the operational source of truth.

## Recommended Handoff Template

Use a brief like this for each subagent:

```md
Implement Phase [N]: [title]

Tasks in scope:
- [task IDs or task titles]

Scope:
- [owned files or subsystem]

Acceptance criteria:
- [criterion]
- [criterion]

Verification:
- [test or command]
- [manual check]

Constraints:
- Stay within the assigned scope
- Do not revert unrelated work
- [Use / do not use Context7 and Exa]
- [Document decisions if needed]

Output:
- Summary of changes
- Risks or unresolved issues
- Exact verification performed
```

## Boundaries

This skill is for orchestration, not for replacing implementation discipline:
- Do not skip review because a subagent reports success.
- Do not start the next phase with unresolved defects in the current one.
- Do not broaden scope mid-phase unless the user asks or the dependency graph forces it.
- Do not ignore dependencies or checkpoints defined by the task-breakdown file.
