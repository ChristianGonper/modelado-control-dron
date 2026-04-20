# Estado Actual Del Simulador

Fecha de corte: 2026-04-15 23:59

## Resumen

Tras la sesión del 15/04/2026, el simulador queda preparado para cubrir de extremo a extremo la Fase 2 de control neuronal sobre la base física ya existente:

- núcleo 6 DOF con integración mínima y actuadores simplificados
- controlador base en cascada con frontera reemplazable
- contrato formal de escenarios con semilla y reproducibilidad
- trayectorias nativas y contrato común para referencias externas
- telemetría estructurada, exportación `CSV`/`JSON`/`NumPy` y métricas
- perturbaciones configurables y modelo aerodinámico simple
- análisis post-procesado 2D/3D sobre telemetría persistida
- puntos de extensión documentados para control inteligente y reutilización de datasets
- contrato explícito de dataset para aprendizaje supervisado desde telemetría persistida
- split reproducible por episodios completos y windowing temporal para `MLP`, `GRU` y `LSTM`
- entrenamiento reproducible, checkpoints auditables e integración en runner para `MLP`, `GRU` y `LSTM`
- benchmark principal clásico vs modelos neuronales, reporting cuantitativo y selector reproducible del mejor modelo
- batería OOD separada del benchmark principal con documentación de límites metodológicos y reproducibilidad

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

### Control neuronal y evaluación

- `dataset/`: contrato, extracción, features, split por episodios y windowing para arquitecturas densas y recurrentes.
- `control/mlp.py`: entrenamiento, checkpoint e inferencia para la baseline `MLP`.
- `control/recurrent.py`: entrenamiento, checkpoint e inferencia para `GRU` y `LSTM`.
- `benchmark.py`: benchmark principal y batería OOD con persistencia de métricas, trazas y tiempos de inferencia en CPU.
- `reporting.py`: tabla consolidada, figuras comparativas, selector reproducible y reporte OOD separado.
- `robustness.py`: escenarios OOD explícitos para robustez fuera de distribución.

### Documentación ya disponible

- ADRs `ADR-001` a `ADR-017` en [docs/decisions](docs/decisions/).
- [extension-points.md](extension-points.md) para enchufar nuevos controladores.
- [phase2-control-neuronal-dataset-spec.md](phase2-control-neuronal-dataset-spec.md) para el contrato del dataset de Fase 2.
- [phase6_robustness_and_delivery.md](phase6_robustness_and_delivery.md) para cierre metodológico y paquete de reproducibilidad.

## Cómo Usarlo Hoy

### Flujo mínimo

1. `uv sync`
2. `uv run multirotor-sim`
3. `uv run pytest`

### Repetir el flujo neuronal principal

1. Generar o reutilizar telemetría persistida del baseline clásico.
2. Construir episodios y ventanas desde `simulador_multirotor.dataset`.
3. Entrenar checkpoints `MLP`, `GRU` y `LSTM` con los módulos de `simulador_multirotor.control`.
4. Ejecutar `run_homogeneous_neural_benchmark(...)` para el benchmark principal.
5. Generar `report.md`, `comparison_table.md` y `selection.json` con `generate_phase5_report(...)`.
6. Ejecutar `run_ood_robustness_benchmark(...)` y `generate_ood_report(...)` para la batería OOD separada.

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
- El selector del mejor modelo neuronal es deliberadamente heurístico y ponderado; si cambia el criterio académico habrá que actualizar pesos y documentación.

### Datos y análisis

- El esquema de exportación ya es reutilizable, pero cualquier cambio futuro debe mantener sincronizados exportación y reapertura.
- La salida 3D es estática y orientada a inspección cualitativa, no a exploración interactiva.
- La comparación de métricas exige ejecuciones homogéneas por diseño.
- El benchmark principal y la batería OOD deben seguir separados; no conviene reutilizar resultados OOD para tuning ni selección.

### Entrenamiento neuronal

- La fase actual sigue siendo imitation learning sobre el controlador experto disponible.
- `MLP`, `GRU` y `LSTM` ya están integrados en el runner, pero la exploración de hiperparámetros sigue siendo mínima.
- La inferencia recurrente usa buffers temporales y padding inicial para arrancar antes de completar la ventana completa.

## Simplificaciones Que Conviene Recordar

- El objetivo actual es experimentación reproducible, no réplica completa del LiteWing.
- El runner sigue priorizando claridad arquitectónica sobre complejidad física.
- La visualización es de post-procesado y no forma parte del bucle vivo de simulación.

## Qué Está Preparado Para La Siguiente Etapa

- sustituir el controlador en cascada por un controlador inteligente sin reescribir runner ni dinámica
- reutilizar telemetría exportada como dataset de entrenamiento o calibración
- ampliar el esquema de escenario con más parámetros sin romper el contrato base
- refinar aerodinámica, exportación o análisis manteniendo la estructura ya fijada
- extender el benchmark neuronal con nuevas familias de trayectorias o perturbaciones manteniendo la separación entre benchmark principal y OOD
- iterar sobre criterios de selección, robustez o entrenamiento sin rediseñar el contrato principal de dataset o controlador
