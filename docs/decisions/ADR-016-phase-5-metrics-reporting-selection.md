# ADR-016: Phase 5 metrics, reporting, and model selection

## Status
Accepted

## Date
2026-04-15

## Context

Phase 5 needs a reproducible way to compare the classic controller with the MLP, GRU, and LSTM candidates using persisted benchmark results. The benchmark artifact already stores per-scenario metrics, but the reporting layer also needs access to the time-series traces so it can render figures without re-running the simulator.

The selection step must be explicit and deterministic. It should not depend on manual judgment after the benchmark has been produced.

## Decision

Extend the telemetry-derived metrics with explicit provenance and richer error summaries:

- control decisions are attributed to `observed_state`
- tracking evaluation remains anchored to `true_state`
- metrics include RMSE, MAE, IAE, ISE, and control-smoothness summaries

Persist a compact per-controller trace in the benchmark artifact so reporting can generate trajectory, temporal-error, and control-behavior figures from the JSON output alone.

The reporting layer will:

- aggregate the benchmark into a consolidated classic vs MLP vs GRU vs LSTM table
- render comparative figures per scenario from the persisted traces
- write a human-readable report artifact alongside the table and figures

The model-selection rule will be deterministic and automatic:

- restrict the decision to the neural candidates
- score each candidate on precision, smoothness, robustness, and inference cost
- normalize each axis against the best candidate on that axis
- combine the normalized axes with fixed weights
- break ties by model key

## Alternatives Considered

### Keep only the existing summary metrics
- Pros: smaller benchmark payload.
- Cons: no way to render the requested comparative figures from persisted results.
- Rejected: Phase 5 needs report generation without recomputation.

### Select the best model by a single metric
- Pros: simpler.
- Cons: ignores the tradeoff between precision, smoothness, robustness, and inference cost.
- Rejected: the PRD explicitly asks for a multi-criteria decision rule.

### Select the best model manually after reading the table
- Pros: flexible.
- Cons: not reproducible or automatable.
- Rejected: the decision must be explicit and repeatable.

## Consequences

- The benchmark JSON grows modestly because it now includes traces.
- Reporting can be regenerated from persisted artifacts without rerunning the simulator.
- The winner selection is auditable because the score breakdown is serialized.
- Metrics stay methodologically clear because control observability and tracking evaluation are recorded separately.
