# Telemetry, Dataset, and Experimental Outputs

## Metadata

- Module name: telemetry, dataset, and experimental outputs
- Status: active
- Code location: `src/simulador_multirotor/telemetry/`, `src/simulador_multirotor/dataset/`, `src/simulador_multirotor/metrics/`, `src/simulador_multirotor/visualization/`, `src/simulador_multirotor/benchmark.py`, `src/simulador_multirotor/reporting.py`, `src/simulador_multirotor/robustness.py`
- Primary view: `software`

## Responsibility

Esta ficha cubre la parte del sistema que transforma una ejecucion en evidencia
experimental reutilizable:

- memoria estructurada de la simulacion
- exportacion y reapertura de telemetria
- reconstruccion de episodios y ventanas para aprendizaje
- benchmark, reporting y robustez como cierre del ciclo experimental

Queda fuera a proposito:

- el calculo interno del control o de la dinamica
- los detalles de presentacion de cada grafica o artefacto visual

## Main Contracts

- Public inputs:
  `SimulationHistory`, `SimulationStep`, `TelemetryArchive`,
  `DatasetEpisode`, `DatasetSample`
- Public outputs:
  `JSON`, `CSV`, `NPZ`, episodios y ventanas de dataset, metricas y reportes
- Data or protocol assumptions:
  cada muestra conserva trazabilidad suficiente de escenario, controlador,
  trayectoria y cadencias; dataset y reporting reutilizan artefactos persistidos
  en lugar de hooks ad hoc

## Dependencies

- Internal dependencies:
  `runner.py`, `core/contracts.py`, `control/`, `trajectories/`
- External libraries or runtime dependencies:
  `json`, `csv`, `numpy`, y `matplotlib` en la capa de visualizacion
- Related system blocks:
  [Telemetria y trazabilidad de ejecuciones](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Metricas y visualizacion](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Dataset para aprendizaje](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md),
  [Benchmark, reporting y robustez](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)

## Main Classes Or Components

- `SimulationStep`:
  muestra canonica sincronizada de estado, observacion, referencia, comando y
  error
- `SimulationHistory`:
  contenedor estable de una ejecucion completa, con metadatos de escenario,
  vehiculo, controlador y telemetria
- `TelemetryEvent` y `TrackingError`:
  semantica minima de eventos y error de seguimiento
- `DatasetContract`:
  define nombres y dimensiones oficiales de features y targets
- `DatasetSample` y `DatasetEpisode`:
  reconstruyen la telemetria en unidades reutilizables para aprendizaje
- `DatasetWindow`:
  encapsula el paso de episodios a ventanas MLP o recurrentes
- `benchmark.py`, `reporting.py`, `robustness.py`:
  convierten episodios, metricas y checkpoints en comparaciones reproducibles

## Extension Points

- Supported customization points:
  nuevos formatos de exportacion, nuevas metricas, nuevos esquemas de
  windowing, nuevas baterias de benchmark o robustez sobre la misma base de
  telemetria
- Constraints for extensions:
  deben preservar trazabilidad por episodio, consistencia de `DatasetContract` y
  compatibilidad con artefactos persistidos

## Traceability

- Related documents:
  [Software Contracts And Traceability](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md),
  [Main Interfaces and Classes](/Users/chris/Documents/Universidad/TFG/docs/software/main-interfaces-and-classes.md),
  [Technical Rationale Map](/Users/chris/Documents/Universidad/TFG/docs/validation/technical-rationale-map.md),
  [Phase 2 Dataset Specification](/Users/chris/Documents/Universidad/TFG/docs/phase2-control-neuronal-dataset-spec.md)
- Related ADRs:
  [ADR-005](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-005-telemetry-export-and-metrics.md),
  [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md),
  [ADR-013](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-013-phase-2-dataset-contract.md),
  [ADR-014](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-014-phase-2-episode-split-and-windowing.md),
  [ADR-016](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-016-phase-5-metrics-reporting-selection.md),
  [ADR-017](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-017-phase-6-ood-robustness-and-delivery.md)
- Related interfaces or classes:
  `SimulationHistory`, `SimulationStep`, `DatasetContract`, `DatasetEpisode`,
  `DatasetSample`, `DatasetWindow`

## Maintenance Notes

- Stability expectations:
  la historia de simulacion y el contrato de dataset son piezas de alta
  estabilidad porque sostienen metricas, benchmark y entrenamiento
- Known boundaries or debt:
  benchmark, reporting y robustness son modulos orientados a flujo experimental
  mas que a un contrato OO; por eso se documentan aqui como subsistema conjunto
  y no con ficha separada por archivo
