# ADR-001: Contratos compartidos en `core` con `dataclasses`

## Status
Accepted

## Date
2026-04-13

## Context
La primera fase del simulador necesita definir contratos estables para el estado del vehículo, el mando y la referencia de trayectoria. Estos tipos van a ser consumidos por dinámica, control, runner y telemetría, así que la prioridad es mantenerlos simples, explícitos y libres de dependencias circulares.

## Decision
Usar `dataclasses` del estándar en `src/simulador_multirotor/core/contracts.py` para los contratos compartidos iniciales. El módulo `core` será la fuente única de verdad para esos tipos, y el resto de paquetes importará desde ahí cuando necesite los contratos.

## Alternatives Considered

### Pydantic
- Pros: validación declarativa y serialización cómoda.
- Cons: añade una dependencia externa antes de que el esquema esté estabilizado.
- Rejected for this slice: la fase 1 no necesita todavía la complejidad adicional.

### Tipos separados por módulo
- Pros: cada área tendría sus propios modelos.
- Cons: aumenta el riesgo de duplicación y ciclos entre `control`, `trajectories` y `core`.
- Rejected for this slice: el contrato debe ser compartido desde el principio.

## Consequences
- Los modelos son fáciles de instanciar en tests y en una ejecución mínima.
- El contrato compartido queda centralizado para futuras fases.
- Si más adelante hace falta validación declarativa o serialización avanzada, se podrá migrar con un ADR nuevo y sin tocar el resto del diseño de fase 1.

