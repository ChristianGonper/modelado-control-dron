# ADR-003: Escenario como contrato principal y semilla controlada

## Status
Accepted

## Date
2026-04-13

## Context
La Phase 2 del simulador necesita un contrato formal para escenarios que centralice la configuración de una ejecución completa. El runner ya no debe depender de parámetros sueltos o configuración ad hoc, y la reproducibilidad debe quedar controlada desde el mismo contrato.

## Decision
Modelar el escenario como un conjunto de `dataclasses` en `src/simulador_multirotor/scenarios/schema.py`, con bloques separados para tiempo, trayectoria, controlador, perturbaciones, telemetría, vehículo y metadatos. El runner consumirá ese escenario como única entrada principal y registrará un resumen del escenario dentro de la telemetría de ejecución.

La semilla de ejecución se almacenará en los metadatos del escenario y se usará para construir un generador pseudoaleatorio local al runner. Cualquier componente aleatorio del slice actual pasará por ese generador, de modo que dos ejecuciones con la misma semilla produzcan el mismo comportamiento.

## Alternatives Considered

### Mantener configuración suelta en el runner
- Pros: menos tipos al principio.
- Cons: dificulta la trazabilidad, la reproducibilidad y el crecimiento por fases.
- Rejected for this slice: la Phase 2 exige que el escenario sea el contrato principal.

### Usar un serializador externo desde el inicio
- Pros: validación y carga declarativa más cómoda.
- Cons: añade dependencia y complejidad antes de estabilizar el esquema.
- Rejected for this slice: el contrato todavía está cambiando y `dataclasses` bastan.

## Consequences
- El runner queda alineado con el roadmap y con la PRD.
- Los metadatos del escenario viajan junto con cada ejecución.
- La semilla y el ruido quedan centralizados, lo que facilita las pruebas de reproducibilidad.
- Si en fases posteriores hace falta cargar escenarios desde YAML/JSON, se podrá añadir sin redefinir el contrato base.

