# Phased Orchestration Reference

Primary expected input:
- A phased task-breakdown document like `plans/task_breakdown_.md`
- Optional user constraints about model choice, git policy, documentation, and external research

## Intent

The orchestrator is the control plane for a multi-phase implementation derived from a task-breakdown file:
- It advances the plan one phase at a time.
- It keeps responsibility for supervision, review, and next-step decisions.
- It stays active until every phase is reviewed and closed.
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
   - Path to the task-breakdown file
   - Goal of the phase
   - Specific tasks being executed in this round
   - Relevant files, modules, or ownership boundary
   - Acceptance criteria
   - Required verification
   - Dependencies or checkpoint constraints
   - Documentation or git expectations
   - Using Context7 for libraries documentation.
3. Launch a fresh subagent for that phase with the model named by the user.
   - Do not reuse a previous phase worker unless the user explicitly asks for it.
   - Explicitly tell the subagent to open the task-breakdown file first and use it as detailed execution context.
   - Explicitly tell the subagent that it may invoke [$documentation-and-adrs](../documentation-and-adrs/SKILL.md) when the phase creates durable decisions or architecture changes.
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

## Recommended Handoff Template

Use a brief like this for each phase subagent:

```md
Implement Phase [N]: [title]

Task breakdown path:
- [path/to/task_breakdown.md]

Read that file first. Use it as the detailed source of truth for the assigned tasks.

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
- You may invoke [$documentation-and-adrs](../documentation-and-adrs/SKILL.md) if this phase introduces decisions worth recording

Output:
- Summary of changes
- Risks or unresolved issues
- Exact verification performed
```
