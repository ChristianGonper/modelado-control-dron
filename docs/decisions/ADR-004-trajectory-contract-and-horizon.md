# ADR-004: Contrato de trayectoria y agotamiento de horizonte

## Status
Accepted

## Date
2026-04-13

## Context
Phase 3 necesita un contrato común para trayectorias nativas y externas que el runner pueda consumir sin conocer clases concretas. Además, las trayectorias deben definir de forma uniforme qué ocurre cuando el tiempo consultado supera el horizonte configurado.

## Decision
Las trayectorias se modelan como objetos con un método `reference_at(time_s)` que devuelve un `TrajectoryReference` compartido. El contrato común expone el `kind`, la `source`, los `parameters` y el `duration_s`, de forma que las selecciones desde escenario y las adaptaciones externas puedan tratarse igual.

Cuando `time_s` supera el horizonte de una trayectoria, la evaluación se clampa al último instante válido. El `TrajectoryReference` devuelto conserva `valid_until_s` igual al horizonte de la trayectoria y marca en sus metadatos que la referencia está agotada. Esta política evita extrapolaciones implícitas y mantiene estable el último punto de referencia para el controlador y para los tests.

La selección de trayectoria desde escenario usa un registry por `kind`, no branching disperso en el runner.

## Alternatives Considered

### Extrapolar más allá del horizonte
- Pros: mantiene un tiempo de muestra estrictamente creciente.
- Cons: introduce comportamiento no obvio y puede ocultar errores de configuración.
- Rejected for this slice: la Phase 3 pide una semántica uniforme y explícita.

### Hacer que el runner conozca cada familia de trayectoria
- Pros: implementación inmediata.
- Cons: acopla el bucle de simulación a la geometría concreta y complica la extensión.
- Rejected for this slice: rompe el objetivo de desacoplar origen y consumo.

## Consequences
- El runner depende solo del contrato, no de la familia concreta.
- Las referencias temporizadas y parametrizadas quedan soportadas por el mismo mecanismo.
- El agotamiento del horizonte es predecible y verificable con tests.
- Nuevas trayectorias se añaden registrando una fábrica, no modificando el lazo principal.

