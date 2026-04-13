# ADR-002: Separar dinámica, cascada de control y runner mínimo

## Status
Accepted

## Date
2026-04-13

## Context
La segunda slice de la Fase 1 necesita un tracer bullet ejecutable extremo a extremo sin adelantar el esquema formal de escenarios. El simulador debe poder integrar un estado, consumir una referencia mínima y producir una historia en memoria, pero cada capa tiene que seguir testeable en aislamiento.

## Decision
Mantener tres responsabilidades separadas:
- `dynamics`: integra `VehicleState` a partir de `VehicleCommand` y `dt`.
- `control`: convierte `VehicleObservation` y `TrajectoryReference` en un mando desacoplado mediante un lazo externo y uno interno.
- `runner`: orquesta referencia, control, integración y acumulación de telemetría en memoria para el flujo mínimo.

## Alternatives Considered

### Runner monolítico
- Pros: menos archivos.
- Cons: acopla control, dinámica y acumulación de resultados.
- Rejected for this slice: dificulta probar cada módulo por separado.

### Controlador único sin separación de lazos
- Pros: implementación más corta.
- Cons: no deja clara la frontera entre error de posición y mando de actitud.
- Rejected for this slice: la interfaz del controlador debía quedar preparada para sustituir el lazo externo más adelante.

## Consequences
- La dinámica puede probarse sin runner ni control.
- El controlador puede probarse sin integrador.
- El runner queda como composición fina, fácil de reemplazar o ampliar en la siguiente fase.

