# Estado Actual Del Simulador

Fecha de corte: 2026-04-13 18:20

## Resumen

Tras esta sesión, el simulador cubre de extremo a extremo las fases 1 a 7 del plan de implementación:

- núcleo 6 DOF con integración mínima y actuadores simplificados
- controlador base en cascada con frontera reemplazable
- contrato formal de escenarios con semilla y reproducibilidad
- trayectorias nativas y contrato común para referencias externas
- telemetría estructurada, exportación `CSV`/`JSON`/`NumPy` y métricas
- perturbaciones configurables y modelo aerodinámico simple
- análisis post-procesado 2D/3D sobre telemetría persistida
- puntos de extensión documentados para control inteligente y reutilización de datasets

## Qué Se Ha Entregado

### Núcleo de simulación

- `core/`: contratos de estado, observación, mando y utilidades de actitud.
- `dynamics/`: dinámica rígida 6 DOF y entorno aerodinámico opcional.
- `control/`: PID en cascada más contrato explícito `ControllerContract`.
- `runner.py`: lazo de simulación desacoplado del controlador concreto.

### Configuración y ejecución

- `scenarios/`: esquema formal de escenario con bloques de vehículo, tiempo, trayectoria, perturbaciones, telemetría y metadatos.
- `app.py`: CLI mínima para ejecutar simulación nominal y generar artefactos de análisis.

### Referencias, telemetría y análisis

- `trajectories/`: recta, círculo, espiral, curva paramétrica y Lissajous, además de adaptador externo.
- `telemetry/`: historia de ejecución, exportadores y metadatos reutilizables.
- `metrics/`: métricas de seguimiento y comparación entre ejecuciones homogéneas.
- `visualization/`: reapertura de telemetría persistida y generación de PNG 2D/3D.

### Documentación ya disponible

- ADRs `ADR-001` a `ADR-008` en `docs/decisions/`.
- [extension-points.md](/C:/Users/chris/Documents/Universidad/TFG/docs/extension-points.md) para enchufar nuevos controladores.

## Cómo Usarlo Hoy

### Flujo mínimo

1. `uv sync`
2. `uv run multirotor-sim`
3. `uv run pytest`

### Generar análisis

1. `uv run multirotor-sim --analysis-dir analysis_outputs`
2. Revisar:
   - `analysis_outputs/telemetry.json`
   - `analysis_outputs/analysis_trajectory_2d.png`
   - `analysis_outputs/analysis_tracking_errors.png`
   - `analysis_outputs/analysis_trajectory_3d.png`

## Riesgos Técnicos Actuales

### Fidelidad física

- El modelo aerodinámico es deliberadamente compacto.
- El término inducido solo aproxima pérdida de eficiencia en hover; no modela rotor ni interacción hélice-estructura.
- La integración es suficiente para el tracer bullet del TFG, pero no está validada frente a datos reales.

### Control

- El controlador actual sirve como baseline, no como referencia de alto rendimiento.
- `NullController` solo valida la frontera de extensión; no representa una política útil.
- No hay todavía una batería formal de tuning o robustez para grandes maniobras.

### Datos y análisis

- El esquema de exportación ya es reutilizable, pero cualquier cambio futuro debe mantener sincronizados exportación y reapertura.
- La salida 3D es estática y orientada a inspección cualitativa, no a exploración interactiva.
- La comparación de métricas exige ejecuciones homogéneas por diseño.

## Simplificaciones Que Conviene Recordar

- El objetivo actual es experimentación reproducible, no réplica completa del LiteWing.
- El runner sigue priorizando claridad arquitectónica sobre complejidad física.
- La visualización es de post-procesado y no forma parte del bucle vivo de simulación.

## Qué Está Preparado Para La Siguiente Etapa

- sustituir el controlador en cascada por un controlador inteligente sin reescribir runner ni dinámica
- reutilizar telemetría exportada como dataset de entrenamiento o calibración
- ampliar el esquema de escenario con más parámetros sin romper el contrato base
- refinar aerodinámica, exportación o análisis manteniendo la estructura ya fijada
