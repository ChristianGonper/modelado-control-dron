# Extension Points

This simulator keeps the tracer bullet intact, but Phase 7 makes the extension boundary explicit so a future controller or dataset pipeline can reuse the same execution core.

## Replacing The Controller

The runner accepts any object that implements the controller contract:

- `kind`
- `source`
- `parameters`
- `compute_action(observation, reference) -> VehicleCommand`

Use it directly:

```python
from simulador_multirotor.control import ControllerAdapter, NullController
from simulador_multirotor.runner import SimulationRunner

history = SimulationRunner().run(scenario, controller=NullController())
```

For an external algorithm, wrap its step function with `ControllerAdapter`:

```python
controller = ControllerAdapter(step_fn, kind="ml-policy", source="external")
history = SimulationRunner().run(scenario, controller=controller)
```

The controller sees two explicit inputs:

- `VehicleObservation`
- `TrajectoryReference`

The action remains the existing `VehicleCommand` contract used by the dynamics.

## Reusing Exports As Datasets

Exported telemetry is self-describing and keeps the minimum execution context needed for reuse:

- `scenario`
- `vehicle`
- `controller`
- `telemetry`
- `initial_state`
- `final_state`

Recommended export for reuse is the full JSON or NPZ format through `simulador_multirotor.telemetry.export`.

The important rule is that datasets should be generated from persisted telemetry, not from the live runner. That keeps analysis, calibration, and future training pipelines decoupled from simulation execution.
