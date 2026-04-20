# Control, Trajectories, and Dynamics

## Metadata

- Module name: control, trajectories, and dynamics
- Status: active
- Code location: `src/simulador_multirotor/control/`, `src/simulador_multirotor/trajectories/`, `src/simulador_multirotor/dynamics/`
- Primary view: `software`

## Responsibility

Esta ficha cubre los modulos que implementan el sistema modelado y sus puntos
de extension principales:

- trayectorias que producen referencias temporales
- controladores que transforman observacion y referencia en accion
- dinamica y actuacion que convierten esa accion en evolucion del estado

Queda fuera a proposito:

- la orquestacion del bucle, que pertenece a `runner.py`
- la persistencia de resultados y el pipeline de dataset

## Main Contracts

- Public inputs:
  `TrajectoryContract.reference_at(time_s)`,
  `ControllerContract.compute_action(observation, reference)`,
  `RigidBody6DOFDynamics.step(state, command, dt_s)`
- Public outputs:
  `TrajectoryReference`, `VehicleCommand`, `VehicleState`
- Data or protocol assumptions:
  referencias y observaciones comparten semantica temporal; el controlador
  produce intencion desacoplada de la mezcla por rotor; la dinamica respeta
  limites del vehiculo y perturbaciones configuradas

## Dependencies

- Internal dependencies:
  `core/contracts.py`, `core/attitude.py`, `scenarios/schema.py`
- External libraries or runtime dependencies:
  `math`, `dataclasses`, `typing`, `numpy`, `torch` en control neuronal
- Related system blocks:
  [Generacion de referencias y trayectorias](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Control de vuelo reemplazable](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Dinamica y entorno modelado](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)

## Main Classes Or Components

- `TrajectoryContract` y `TrajectoryAdapter`:
  fijan la frontera comun para trayectorias nativas y externas
- `ControllerContract`, `ControllerAdapter`, `NullController`:
  definen la superficie intercambiable del control
- `CascadedController`:
  baseline clasico construido desde `PositionLoopController` y
  `AttitudeLoopController`
- `MLPController` y `RecurrentController`:
  implementaciones de control neuronal compatibles con la misma frontera
- `RigidBodyParameters`:
  concentra los parametros fisicos y de actuacion del vehiculo
- `RotorMixer`:
  puente entre intencion de control y comandos por rotor
- `RigidBody6DOFDynamics`:
  planta principal que aplica actuacion, aerodinamica e integracion temporal

## Extension Points

- Supported customization points:
  nuevas trayectorias registradas desde el catalogo, nuevas implementaciones de
  `ControllerContract`, adaptadores externos para control o trayectoria, nuevos
  modelos de entorno dentro de la capa de dinamica/aerodinamica
- Constraints for extensions:
  deben preservar la frontera `observation + reference -> command`,
  reutilizar `TrajectoryReference` y `VehicleCommand`, y mantener compatibilidad
  con los limites y cadencias definidos por `SimulationScenario`

## Traceability

- Related documents:
  [Interfaces principales del simulador](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md),
  [Software Contracts And Traceability](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md),
  [Main Interfaces and Classes](/Users/chris/Documents/Universidad/TFG/docs/software/main-interfaces-and-classes.md),
  [Rotor Actuation And Timebase](/Users/chris/Documents/Universidad/TFG/docs/theory/rotor-actuation-and-timebase.md),
  [Rigid Body 6DOF](/Users/chris/Documents/Universidad/TFG/docs/theory/rigid-body-6dof.md),
  [Aerodynamic Disturbances And Observability](/Users/chris/Documents/Universidad/TFG/docs/theory/aerodynamic-disturbances-and-observability.md)
- Related ADRs:
  [ADR-004](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-004-trajectory-contract-and-horizon.md),
  [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md),
  [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md),
  [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md),
  [ADR-015](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-015-phase-3-mlp-checkpoint-and-benchmark.md)
- Related interfaces or classes:
  `TrajectoryContract`, `ControllerContract`, `CascadedController`,
  `RigidBody6DOFDynamics`, `TrajectoryReference`, `VehicleCommand`

## Maintenance Notes

- Stability expectations:
  la frontera de contratos deberia ser estable; las implementaciones concretas
  pueden crecer mientras respeten esa superficie
- Known boundaries or debt:
  la carpeta `control/` mezcla baseline clasico y entrenamiento neuronal; si la
  parte de aprendizaje sigue creciendo, puede merecer una subvista documental
  propia sin cambiar la frontera arquitectonica
