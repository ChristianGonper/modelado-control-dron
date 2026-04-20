# Contratos software y trazabilidad

## Proposito

Este documento aterriza las interfaces principales del simulador al nivel de
modulos y contratos reales del codigo. Sirve como puente entre la vista de
sistema y las ADRs, sin convertir `docs/software/` en un inventario exhaustivo.

Documento de sistema relacionado:

- [Interfaces principales del simulador](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)

## Mapa rapido por modulos

| Contrato | Modulos principales | Implementaciones o consumidores clave |
| --- | --- | --- |
| `SimulationScenario` | `scenarios/schema.py`, `scenarios/io.py` | `runner.py`, `benchmark.py`, `robustness.py` |
| `TrajectoryContract` | `trajectories/contract.py`, `trajectories/catalog.py` | `runner.py`, `scenarios/schema.py` |
| `ControllerContract` | `control/contract.py` | `control/cascade.py`, `control/mlp.py`, `control/recurrent.py`, `benchmark.py` |
| `VehicleState`, `VehicleObservation`, `TrajectoryReference`, `VehicleCommand` | `core/contracts.py` | `dynamics/`, `control/`, `telemetry/`, `dataset/`, `visualization/` |
| `SimulationHistory` | `telemetry/memory.py`, `telemetry/export.py` | `metrics/report.py`, `dataset/extract.py`, `visualization/archive.py` |
| `DatasetEpisode` | `dataset/contract.py`, `dataset/extract.py`, `dataset/split.py`, `dataset/windowing.py` | `control/mlp.py`, `control/recurrent.py` |

## Contratos principales y responsabilidad software

### `SimulationScenario`

Archivos principales:

- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/scenarios/io.py`

Responsabilidad software:

- consolidar la configuracion total de una ejecucion
- construir dependencias del runner a partir de un contrato unico
- serializar y deserializar artefactos de escenario versionados

Entradas:

- subconfiguraciones de tiempo, trayectoria, controlador, perturbaciones,
  telemetria y vehiculo

Salidas:

- `build_dynamics()`
- `build_controller()`
- `build_trajectory()`
- `build_rng()`
- `describe()` para telemetria y trazabilidad

ADRs aplicables:

- [ADR-003](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-003-scenario-contract-and-seed.md)
- [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)
- [ADR-012](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-012-external-scenarios-and-reference-battery.md)

### `TrajectoryContract` y `TrajectoryReference`

Archivos principales:

- `src/simulador_multirotor/trajectories/contract.py`
- `src/simulador_multirotor/trajectories/catalog.py`
- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/core/contracts.py`

Responsabilidad software:

- exponer una API minima de muestreo temporal para referencias
- registrar `kind`, `source`, `duration_s` y `parameters`
- uniformar trayectorias nativas y adaptadas

Entradas:

- `time_s`
- configuracion de trayectoria y, si hace falta, `initial_state`

Salidas:

- `TrajectoryReference`
- marca de horizonte agotado a traves de `is_complete_at` y metadatos de la
  referencia

ADRs aplicables:

- [ADR-004](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-004-trajectory-contract-and-horizon.md)
- [ADR-012](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-012-external-scenarios-and-reference-battery.md)

### `ControllerContract` y `VehicleCommand`

Archivos principales:

- `src/simulador_multirotor/control/contract.py`
- `src/simulador_multirotor/control/cascade.py`
- `src/simulador_multirotor/control/mlp.py`
- `src/simulador_multirotor/control/recurrent.py`
- `src/simulador_multirotor/core/contracts.py`

Responsabilidad software:

- fijar la frontera `observation + reference -> action`
- permitir varias implementaciones de controlador bajo la misma superficie
- separar intencion de control de senales por rotor

Entradas:

- `VehicleObservation`
- `TrajectoryReference`

Salidas:

- `VehicleCommand`
- metadatos de `kind`, `source` y `parameters`

ADRs aplicables:

- [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md)
- [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
- [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)
- [ADR-015](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-015-phase-3-mlp-checkpoint-and-benchmark.md)

### `VehicleState` y `VehicleObservation`

Archivos principales:

- `src/simulador_multirotor/core/contracts.py`
- `src/simulador_multirotor/runner.py`
- `src/simulador_multirotor/telemetry/memory.py`

Responsabilidad software:

- representar el estado fisico del vehiculo y su version observada
- garantizar alineacion temporal entre planta, observacion y telemetria
- conservar compatibilidad mediante `.state` como alias de `observed_state`

Entradas:

- salida del integrador y perturbaciones de observacion

Salidas:

- objeto consumible por controladores, metricas, dataset y visualizacion

ADRs aplicables:

- [ADR-001](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-001-core-contracts.md)
- [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
- [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)

### `SimulationHistory`

Archivos principales:

- `src/simulador_multirotor/runner.py`
- `src/simulador_multirotor/telemetry/memory.py`
- `src/simulador_multirotor/telemetry/export.py`
- `src/simulador_multirotor/visualization/archive.py`

Responsabilidad software:

- encapsular la historia completa de una ejecucion con semantica estable
- separar acumulacion en memoria de exportacion a `CSV`, `JSON` y `NPZ`
- proporcionar una base comun para metricas y reapertura de artefactos

Entradas:

- `SimulationStep` con estado, observacion, referencia, comando, error y
  eventos

Salidas:

- artefactos persistidos y reabribles
- metricas comparables
- soporte para dataset extraction

ADRs aplicables:

- [ADR-005](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-005-telemetry-export-and-metrics.md)
- [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)
- [ADR-016](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-016-phase-5-metrics-reporting-selection.md)

### `DatasetEpisode` y `DatasetSample`

Archivos principales:

- `src/simulador_multirotor/dataset/contract.py`
- `src/simulador_multirotor/dataset/extract.py`
- `src/simulador_multirotor/dataset/features.py`
- `src/simulador_multirotor/dataset/split.py`
- `src/simulador_multirotor/dataset/windowing.py`

Responsabilidad software:

- reconstruir episodios desde telemetria persistida
- fijar semantica de features, targets y trazabilidad
- propagar asignacion de split y contexto temporal hacia entrenamiento

Entradas:

- `TelemetryArchive`
- metadatos de escenario, controlador y telemetria

Salidas:

- episodios y ventanas consumibles por `MLP`, `GRU` y `LSTM`
- matrices compatibles para entrenamiento e inferencia

ADRs aplicables:

- [ADR-013](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-013-phase-2-dataset-contract.md)
- [ADR-014](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-014-phase-2-episode-split-and-windowing.md)
- [ADR-015](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-015-phase-3-mlp-checkpoint-and-benchmark.md)

## Trazabilidad minima de justificacion

Una cadena util para preguntas de justificacion tecnica queda asi:

1. [Layered System View](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
2. [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
3. [Interfaces principales del simulador](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
4. este documento para ubicar el contrato en el codigo
5. ADR enlazada para responder por que se adopto ese contrato

Ejemplos directos:

- "Por que el controlador es reemplazable?" ->
  `ControllerContract` -> [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md)
- "Por que la observacion separa `true_state` y `observed_state`?" ->
  `VehicleObservation` -> [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md) y [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)
- "Por que el dataset sale de telemetria persistida y no de hooks ad hoc?" ->
  `DatasetEpisode` -> [ADR-013](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-013-phase-2-dataset-contract.md)
