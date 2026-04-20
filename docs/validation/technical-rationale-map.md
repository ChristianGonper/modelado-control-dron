# Mapa de justificacion tecnica

## Proposito

Este documento consolida una ruta navegable desde la vista general del TFG hasta
los contratos e interfaces cuya forma actual queda justificada por ADRs
concretas. Es una trazabilidad ligera: suficiente para revision con tutores, sin
convertirse en una matriz exhaustiva.

## Ruta recomendada

1. [Overview](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md)
2. [Layered System View](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
3. [System Blocks And Responsibilities](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
4. [Interfaces principales del simulador](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
5. [Contratos software y trazabilidad](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
6. ADRs relevantes en [Decisions](/Users/chris/Documents/Universidad/TFG/docs/decisions)

## Trazas de justificacion seleccionadas

### Traza A: ejecucion reproducible del simulador

- overview: [Overview](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md)
- bloque: [Configuracion experimental y escenarios](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- interfaz: [SimulationScenario](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
- aterrizaje software: [Contratos software y trazabilidad](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
- decision:
  - [ADR-003](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-003-scenario-contract-and-seed.md)
  - [ADR-010](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-010-mixer-actuator-timebase.md)

Pregunta que responde:

- por que el runner consume un escenario unico y no configuracion dispersa
- por que existen cadencias separadas de fisica, control y telemetria

### Traza B: observabilidad y semantica del lazo de control

- overview: [Overview](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md)
- bloque: [Dinamica y entorno modelado](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- interfaz: [VehicleState, VehicleObservation y VehicleCommand](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
- aterrizaje software: [Contratos software y trazabilidad](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
- decision:
  - [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md)
  - [ADR-009](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-009-phase-1-dynamics-and-observation-contracts.md)
  - [ADR-011](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-011-dt-invariant-wind-and-tracking-observability.md)

Pregunta que responde:

- por que el controlador ve `observed_state` pero la evaluacion sigue anclada a
  `true_state`
- por que el comando conserva una intencion de alto nivel y senales por rotor
  opcionales

### Traza C: telemetria como base de analisis y aprendizaje

- overview: [Overview](/Users/chris/Documents/Universidad/TFG/docs/overview/README.md)
- bloque: [Telemetria y trazabilidad de ejecuciones](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- interfaz: [SimulationHistory y DatasetEpisode](/Users/chris/Documents/Universidad/TFG/docs/system/system-interfaces.md)
- aterrizaje software: [Contratos software y trazabilidad](/Users/chris/Documents/Universidad/TFG/docs/software/software-contracts-and-traceability.md)
- decision:
  - [ADR-005](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-005-telemetry-export-and-metrics.md)
  - [ADR-013](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-013-phase-2-dataset-contract.md)
  - [ADR-014](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-014-phase-2-episode-split-and-windowing.md)
  - [ADR-016](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-016-phase-5-metrics-reporting-selection.md)

Pregunta que responde:

- por que la telemetria se exporta fuera del runner
- por que el dataset parte de artefactos persistidos y episodios completos
- por que reporting y seleccion se apoyan en contratos de telemetria estables

## Como usar esta vista con tutores

Si la pregunta empieza por "que hace esta parte del simulador", conviene entrar
por `system/`.

Si la pregunta empieza por "que contrato real del codigo sostiene eso", pasar a
`software/`.

Si la pregunta empieza por "por que esta organizado asi", seguir el enlace de
ADR mas proximo desde el bloque o interfaz correspondiente.

## Limite de esta trazabilidad

- no cubre todas las ADRs del repositorio, solo las que justifican el flujo
  principal del simulador
- no sustituye la lectura de una ADR cuando hace falta el detalle de contexto y
  alternativas
- puede crecer por bloques, sin rehacer la estructura, cuando se documenten mas
  modulos en fases posteriores
