# Execution, Scenarios, and Core Contracts

## Metadata

- Module name: execution, scenarios, and core contracts
- Status: active
- Code location: `src/simulador_multirotor/scenarios/schema.py`, `src/simulador_multirotor/core/contracts.py`, `src/simulador_multirotor/runner.py`
- Primary view: `software`

## Responsibility

Esta ficha cubre el nucleo que hace ejecutable el simulador como experimento
reproducible. Agrupa:

- el contrato de escenario que describe una corrida completa
- el vocabulario compartido de estado, observacion, referencia y comando
- el runner que coordina el bucle principal sin absorber logica de control o de
  fisica

Queda fuera a proposito:

- la implementacion interna de controladores y trayectorias
- el detalle de la planta fisica y de la aerodinamica
- la persistencia y postprocesado de resultados

## Main Contracts

- Public inputs:
  `SimulationScenario`, `VehicleObservation`, `TrajectoryReference`,
  `VehicleCommand`
- Public outputs:
  `SimulationHistory` como resultado de `SimulationRunner.run(...)`
- Data or protocol assumptions:
  tiempos fisico, de control y de telemetria compatibles; observacion y estado
  referidos al mismo instante; referencias validas para el tiempo solicitado

## Dependencies

- Internal dependencies:
  `control/`, `trajectories/`, `dynamics/`, `telemetry/`
- External libraries or runtime dependencies:
  `dataclasses`, `typing`, `random`, `json`, `pathlib`
- Related system blocks:
  [Configuracion experimental y escenarios](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Contratos compartidos del dominio](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Orquestacion de la simulacion](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)

## Main Classes Or Components

- `SimulationScenario`:
  agrega estado inicial, tiempos, vehiculo, trayectoria, controlador,
  perturbaciones, telemetria y metadatos; tambien construye dependencias del
  runner con `build_*()`
- `ScenarioTimeConfig`:
  impone invariantes temporales como multiplicidad entera entre
  `physics_dt_s`, `control_dt_s` y `telemetry_dt_s`
- `ScenarioDisturbanceConfig`:
  concentra la frontera entre configuracion experimental y entorno perturbado
- `VehicleState`, `VehicleObservation`, `TrajectoryReference`, `VehicleCommand`:
  definen el lenguaje comun del flujo principal
- `SimulationRunner`:
  orquesta el lazo fisica -> observacion -> referencia -> control ->
  telemetria, delegando cada especialidad en su propio modulo

## Extension Points

- Supported customization points:
  nuevos tipos de trayectoria via `SimulationScenario.build_trajectory()`,
  nuevos controladores via `SimulationScenario.build_controller()` o parametro
  explicito en `SimulationRunner.run(...)`, nuevas configuraciones de
  perturbacion y telemetria via subconfiguraciones del escenario
- Constraints for extensions:
  las extensiones deben respetar los contratos de `core/contracts.py` y no
  romper la consistencia temporal entre estado, observacion y referencia

## Traceability

- Related documents:
  [Interfaces principales del simulador](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md),
  [Software Contracts And Traceability](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md),
  [Main Interfaces and Classes](/Users/chris/Documents/Universidad/TFG/docs/software/main-interfaces-and-classes.md)
- Related ADRs:
  [ADR-001](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-001-core-contracts.md),
  [ADR-002](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-002-tracer-bullet-runner.md),
  [ADR-003](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-003-scenario-contract-and-seed.md),
  [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md),
  [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)
- Related interfaces or classes:
  `SimulationScenario`, `SimulationRunner`, `VehicleState`,
  `VehicleObservation`, `TrajectoryReference`, `VehicleCommand`

## Maintenance Notes

- Stability expectations:
  esta ficha deberia cambiar solo cuando cambien las fronteras del flujo
  principal o la semantica de los contratos base
- Known boundaries or debt:
  `SimulationScenario.build_controller()` actualmente conoce el baseline
  clasico; si la seleccion de controladores crece mucho, la fabrica puede
  merecer un modulo propio
