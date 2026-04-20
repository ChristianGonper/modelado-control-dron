# Interfaces principales del simulador

## Proposito

Este documento identifica los contratos que conectan los bloques principales del
simulador. No intenta inventariar todas las clases ni cada API interna; se
centra en las interfaces que sostienen el flujo dominante:

1. definicion del escenario
2. generacion de referencias
3. bucle runner-control-dinamica
4. telemetria estructurada
5. reutilizacion como dataset

## Criterio de seleccion

Solo se documentan interfaces que cumplen al menos uno de estos criterios:

- desacoplan subsistemas distintos del flujo principal
- aparecen como contrato estable en `core/`, `control/`, `trajectories/`,
  `scenarios/`, `telemetry/` o `dataset/`
- tienen ADRs que justifican su forma actual

## Cadena principal de interfaces

| Interfaz | Donde vive | Une que bloques |
| --- | --- | --- |
| `SimulationScenario` | `src/simulador_multirotor/scenarios/schema.py` | configuracion experimental -> runner |
| `TrajectoryContract` + `TrajectoryReference` | `src/simulador_multirotor/trajectories/contract.py`, `src/simulador_multirotor/core/contracts.py` | trayectorias -> control y runner |
| `VehicleState` + `VehicleObservation` | `src/simulador_multirotor/core/contracts.py` | dinamica y perturbaciones -> control, telemetria, metricas |
| `ControllerContract` + `VehicleCommand` | `src/simulador_multirotor/control/contract.py`, `src/simulador_multirotor/core/contracts.py` | control -> runner y dinamica |
| `SimulationStep` + `SimulationHistory` | `src/simulador_multirotor/telemetry/memory.py` | runner -> exportacion, metricas, dataset |
| `DatasetEpisode` + `DatasetSample` | `src/simulador_multirotor/dataset/contract.py` | telemetria persistida -> aprendizaje |

## 1. Contrato de escenario reproducible

Contrato principal:

- `SimulationScenario`
- `ScenarioTimeConfig`
- `ScenarioTrajectoryConfig`
- `ScenarioControllerConfig`
- `ScenarioDisturbanceConfig`
- `ScenarioTelemetryConfig`
- `ScenarioMetadata`

Entrada principal:

- estado inicial `VehicleState`
- configuracion temporal con `physics_dt_s`, `control_dt_s` y `telemetry_dt_s`
- definicion de trayectoria, controlador, perturbaciones, telemetria y
  metadatos

Salida o servicio hacia otros bloques:

- construccion de `RigidBody6DOFDynamics`, `ControllerContract`,
  `TrajectoryContract` y generador aleatorio local
- resumen serializable mediante `to_dict()`, `to_json()` y `describe()`

Papel en el sistema:

- es la frontera de configuracion completa de una ejecucion
- evita que el runner dependa de parametros sueltos
- concentra reproducibilidad, semilla y cadencias temporales

Subsistemas conectados:

- escenarios
- runner
- dinamica y aerodinamica
- control
- telemetria

ADRs relacionadas:

- [ADR-003](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-003-scenario-contract-and-seed.md)
- [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)

## 2. Contratos compartidos de estado, observacion y referencia

Contrato principal:

- `VehicleState`
- `VehicleObservation`
- `TrajectoryReference`

Entrada principal:

- `VehicleState`: posicion, orientacion, velocidades y tiempo fisico
- `VehicleObservation`: `true_state`, `observed_state` y metadatos de muestreo
- `TrajectoryReference`: posicion, velocidad, yaw, ventana de validez y
  aceleracion opcional

Salida o servicio hacia otros bloques:

- vocabulario comun para control, runner, telemetria, metricas y dataset
- separacion explicita entre estado fisico y estado observado

Papel en el sistema:

- estabilizan la semantica de "que sabe el controlador" frente a "que ocurre en
  la planta"
- fijan como se expresa la consigna temporal de trayectoria
- permiten que telemetria y metricas no dependan de detalles del integrador

Subsistemas conectados:

- dinamica
- perturbaciones
- control
- trayectorias
- telemetria
- dataset

ADRs relacionadas:

- [ADR-001](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-001-core-contracts.md)
- [ADR-004](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-004-trajectory-contract-and-horizon.md)
- [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
- [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)

## 3. Frontera de trayectoria consumible por el runner

Contrato principal:

- `TrajectoryContract.reference_at(time_s) -> TrajectoryReference`
- `TrajectoryContract.is_complete_at(time_s) -> bool`

Entrada principal:

- tiempo de simulacion
- configuracion de trayectoria seleccionada desde `ScenarioTrajectoryConfig`

Salida:

- una muestra `TrajectoryReference` valida en ese instante
- indicacion de agotamiento de horizonte

Papel en el sistema:

- desacopla el runner de cada familia de trayectorias
- permite tratar trayectorias nativas y adaptadas con el mismo consumo
- mantiene una politica uniforme cuando se agota el horizonte temporal

Subsistemas conectados:

- escenario
- runner
- control

ADRs relacionadas:

- [ADR-004](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-004-trajectory-contract-and-horizon.md)

## 4. Frontera de control reemplazable

Contrato principal:

- `ControllerContract.compute_action(observation, reference) -> VehicleCommand`
- `VehicleCommand` con `VehicleIntent` y `RotorCommand` opcionales

Entrada principal:

- `VehicleObservation` alineada temporalmente
- `TrajectoryReference` para el mismo instante de control

Salida:

- `VehicleCommand`, con intencion de empuje/par y, cuando aplica, comandos por
  rotor

Papel en el sistema:

- permite sustituir PID clasico, `MLP`, `GRU`, `LSTM` u otros controladores sin
  reescribir el runner
- separa la frontera del controlador de la implementacion de mezcla y actuacion

Subsistemas conectados:

- control clasico y neuronal
- runner
- dinamica/actuadores
- benchmark

ADRs relacionadas:

- [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md)
- [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
- [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)

## 5. Contrato de historia de simulacion

Contrato principal:

- `SimulationStep`
- `SimulationHistory`
- `TelemetryEvent`
- `TrackingError`

Entrada principal:

- muestras sincronizadas de estado, observacion, referencia, error y comando
- metadatos de escenario, vehiculo, controlador y telemetria

Salida:

- historia estructurada en memoria, lista para exportar, medir y reabrir

Papel en el sistema:

- convierte el bucle runner-dinamica-control en un artefacto experimental
  trazable
- conserva la distincion entre `true_state`, `observed_state` y
  `tracking_state_source`

Subsistemas conectados:

- runner
- exportacion de telemetria
- metricas
- visualizacion
- dataset

ADRs relacionadas:

- [ADR-005](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-005-telemetry-export-and-metrics.md)
- [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)
- [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)

## 6. Contrato de dataset reutilizable

Contrato principal:

- `DatasetContract`
- `DatasetEpisode`
- `DatasetSample`
- `DatasetTraceability`
- `DatasetSplitContext`

Entrada principal:

- telemetria persistida reabierta como `TelemetryArchive`
- semantica fija de features, targets y trazabilidad por episodio

Salida:

- episodios reutilizables para entrenamiento, validacion e inferencia
- matrices de features y targets compatibles entre arquitecturas

Papel en el sistema:

- conecta observabilidad con aprendizaje sin rutas ad hoc
- preserva procedencia experimental suficiente para comparar modelos y evitar
  leakage entre splits

Subsistemas conectados:

- exportacion y visualizacion de telemetria
- dataset extraction
- entrenamiento `MLP`, `GRU`, `LSTM`
- benchmark y reporting

ADRs relacionadas:

- [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md)
- [ADR-013](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-013-phase-2-dataset-contract.md)
- [ADR-014](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-014-phase-2-episode-split-and-windowing.md)

## Recorrido minimo trazable

Una lectura minima del flujo contractual puede seguir esta cadena:

1. `SimulationScenario` define la ejecucion y sus cadencias.
2. `TrajectoryContract` produce `TrajectoryReference`.
3. la dinamica entrega `VehicleState` y las perturbaciones construyen
   `VehicleObservation`.
4. `ControllerContract` devuelve `VehicleCommand`.
5. `SimulationRunner` registra todo en `SimulationStep` y `SimulationHistory`.
6. la telemetria exportada se transforma en `DatasetEpisode` y `DatasetSample`.

Para bajar desde esta vista de sistema a la lectura software, ver
[Software Contracts And Traceability](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md).
