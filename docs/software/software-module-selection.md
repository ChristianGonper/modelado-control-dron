# Seleccion priorizada de modulos software

## Proposito

Este documento delimita el alcance de la vista software de la Fase 6. La
seleccion prioriza paquetes, modulos e interfaces con valor estructural claro
para explicar el simulador en el TFG y deja fuera piezas auxiliares sin peso
arquitectonico propio.

Vista de sistema relacionada:

- [Bloques y responsabilidades principales](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- [Interfaces principales del simulador](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)

## Criterios de seleccion

Se documenta un modulo cuando cumple al menos uno de estos criterios:

- fija un contrato transversal entre subsistemas
- orquesta el flujo principal de ejecucion
- actua como punto de extension real del simulador
- concentra trazabilidad experimental reutilizada por varias capas
- enlaza de forma directa con ADRs relevantes para justificar la arquitectura

No se documentan con ficha propia:

- utilidades privadas de serializacion o validacion
- cada archivo de entrenamiento, visualizacion o calculo si su papel ya queda
  cubierto en una ficha modular mayor
- funciones internas sin responsabilidad arquitectonica estable

## Modulos priorizados

### Prioridad 1: nucleo contractual y de ejecucion

| Modulo o paquete | Por que merece ficha propia | Interfaces o clases a destacar |
| --- | --- | --- |
| `core/contracts.py` | fija el vocabulario compartido del simulador | `VehicleState`, `VehicleObservation`, `TrajectoryReference`, `VehicleCommand` |
| `scenarios/schema.py` | concentra la configuracion reproducible de una ejecucion | `SimulationScenario`, `ScenarioTimeConfig`, `ScenarioDisturbanceConfig` |
| `runner.py` | coordina el flujo runner-control-dinamica-telemetria | `SimulationRunner` |

### Prioridad 2: puntos de extension del sistema modelado

| Modulo o paquete | Por que merece ficha propia | Interfaces o clases a destacar |
| --- | --- | --- |
| `trajectories/contract.py` + `trajectories/` | desacopla la generacion de referencias del resto del sistema | `TrajectoryContract`, `TrajectoryAdapter` |
| `control/contract.py` + `control/` | permite control clasico y neuronal bajo la misma frontera | `ControllerContract`, `ControllerAdapter`, `CascadedController` |
| `dynamics/rigid_body.py` + `dynamics/aerodynamics.py` | implementa la planta y la frontera hacia actuacion y entorno | `RigidBody6DOFDynamics`, `RigidBodyParameters`, `RotorMixer` |

### Prioridad 3: observabilidad, reutilizacion y ciclo experimental

| Modulo o paquete | Por que merece ficha propia | Interfaces o clases a destacar |
| --- | --- | --- |
| `telemetry/memory.py` + `telemetry/export.py` | convierte la ejecucion en un artefacto trazable y persistible | `SimulationStep`, `SimulationHistory`, `TelemetryEvent`, `TrackingError` |
| `dataset/contract.py` + `dataset/extract.py` + `dataset/windowing.py` | conecta telemetria con aprendizaje sin rutas ad hoc | `DatasetContract`, `DatasetEpisode`, `DatasetSample`, `DatasetWindow` |
| `benchmark.py`, `reporting.py`, `robustness.py` | cierran el marco experimental del TFG | funciones de benchmark y seleccion, documentadas dentro de la ficha modular de salidas experimentales |

## Interfaces y clases principales seleccionadas

Las abstracciones con ficha o seccion dedicada en esta fase son:

- `SimulationScenario`
- `SimulationRunner`
- `VehicleState`
- `VehicleObservation`
- `TrajectoryReference`
- `VehicleCommand`
- `TrajectoryContract`
- `ControllerContract`
- `SimulationHistory`
- `DatasetContract`
- `DatasetEpisode`

Tambien se citan como colaboradores estructurales:

- `ScenarioDisturbanceConfig`
- `RigidBody6DOFDynamics`
- `CascadedController`
- `TrackingError`
- `DatasetSample`
- `DatasetWindow`

## Agrupacion documental elegida

Para evitar una vista software atomizada, las fichas se agrupan por fronteras
arquitectonicas y no por cada archivo:

1. ejecucion, escenarios y contratos base
2. control, trayectorias y dinamica
3. telemetria, dataset y salidas experimentales
4. interfaces y clases principales

Esta agrupacion cubre nucleo, extension points y abstracciones clave sin caer
en una lista plana de todos los archivos del repositorio.
