# Bloques y responsabilidades principales

## Propósito

Este documento aterriza la vista por capas en bloques funcionales concretos del
sistema. Sirve como puente entre la explicación general del TFG y la futura
documentación software más detallada.

## Criterio de descomposición

Los bloques se han definido para que sean compatibles con la estructura real del
repositorio y con las fronteras estabilizadas por las ADRs actuales. No son una
lista exhaustiva de archivos, sino unidades funcionales reconocibles.

## Bloques principales

### 1. Configuración experimental y escenarios

Ubicación principal:

- `src/simulador_multirotor/scenarios/`
- `scenario_artifacts/`

Responsabilidad:

- describir una ejecución reproducible del simulador
- agrupar estado inicial, tiempos, vehículo, trayectoria, perturbaciones,
  telemetría y metadatos
- servir como punto de entrada estable para el runner

Papel en el conjunto:

- define el experimento antes de ejecutar nada
- conecta el sistema modelado con las condiciones de prueba

### 2. Contratos compartidos del dominio

Ubicación principal:

- `src/simulador_multirotor/core/contracts.py`
- `src/simulador_multirotor/core/attitude.py`

Responsabilidad:

- fijar los tipos comunes de estado, observación, referencia, intención y mando
- reducir acoplamientos entre dinámica, control, telemetría y dataset

Papel en el conjunto:

- proporciona el vocabulario técnico mínimo del simulador
- estabiliza la comunicación entre bloques

ADR relacionada:

- [ADR-001](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-001-core-contracts.md)

### 3. Dinámica y entorno modelado

Ubicación principal:

- `src/simulador_multirotor/dynamics/`

Responsabilidad:

- evolucionar el estado físico modelado del multirrotor
- aplicar límites y simplificaciones del modelo dinámico
- incorporar efectos aerodinámicos y perturbaciones configuradas

Papel en el conjunto:

- materializa la parte física del sistema modelado
- es la base sobre la que actúan los controladores

### 4. Generación de referencias y trayectorias

Ubicación principal:

- `src/simulador_multirotor/trajectories/`

Responsabilidad:

- producir referencias temporales para hover, círculo, espiral, Lissajous u
  otras trayectorias
- ofrecer una frontera común tanto para trayectorias nativas como externas

Papel en el conjunto:

- expresa qué debe seguir el sistema
- desacopla el movimiento deseado del controlador concreto

### 5. Control de vuelo reemplazable

Ubicación principal:

- `src/simulador_multirotor/control/`

Responsabilidad:

- transformar observación y referencia en acciones de control
- mantener una frontera común para baseline clásico y controladores neuronales
- permitir sustitución de controlador sin reescribir el runner

Papel en el conjunto:

- concentra la lógica de decisión del experimento
- permite comparar estrategias de control sobre el mismo núcleo

ADR relacionada:

- [ADR-008](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-008-controller-contract-and-reusable-datasets.md)

### 6. Orquestación de la simulación

Ubicación principal:

- `src/simulador_multirotor/runner.py`
- `src/simulador_multirotor/app.py`

Responsabilidad:

- construir y coordinar dinámica, controlador, trayectoria y reloj de simulación
- ejecutar el bucle principal de actualización física, control y muestreo
- devolver una historia estructurada de la ejecución

Papel en el conjunto:

- actúa como columna vertebral del flujo principal
- mantiene desacoplados los bloques especializados

### 7. Telemetría y trazabilidad de ejecuciones

Ubicación principal:

- `src/simulador_multirotor/telemetry/`

Responsabilidad:

- registrar pasos, errores, eventos y metadatos de la ejecución
- persistir resultados en formatos reutilizables
- conservar contexto suficiente para análisis y dataset

Papel en el conjunto:

- convierte la simulación en evidencia experimental reutilizable
- une la ejecución con el análisis posterior

ADR relacionada:

- [ADR-005](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-005-telemetry-export-and-metrics.md)

### 8. Métricas y visualización

Ubicación principal:

- `src/simulador_multirotor/metrics/`
- `src/simulador_multirotor/visualization/`

Responsabilidad:

- resumir el rendimiento de seguimiento
- reabrir telemetría persistida para inspección
- producir salidas visuales 2D/3D y series temporales

Papel en el conjunto:

- hace interpretable el comportamiento del sistema
- apoya validación manual, comparación y explicación oral

### 9. Dataset para aprendizaje

Ubicación principal:

- `src/simulador_multirotor/dataset/`
- `docs/phase2-control-neuronal-dataset-spec.md`

Responsabilidad:

- transformar telemetría en episodios y muestras con trazabilidad
- definir features, targets, split y ventanas temporales
- mantener un contrato reutilizable para entrenamiento

Papel en el conjunto:

- conecta la capa de observabilidad con la de aprendizaje
- evita que el control neuronal dependa de rutas ad hoc

### 10. Entrenamiento e inferencia neuronal

Ubicación principal:

- `src/simulador_multirotor/control/mlp.py`
- `src/simulador_multirotor/control/recurrent.py`

Responsabilidad:

- entrenar modelos `MLP`, `GRU` y `LSTM` desde el contrato oficial de dataset
- persistir checkpoints auditables
- reconstruir controladores neuronales compatibles con la misma frontera de control

Papel en el conjunto:

- añade la capacidad de experimentación con control inteligente
- mantiene el mismo punto de integración que el baseline clásico

ADR relacionada:

- [ADR-015](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-015-phase-3-mlp-checkpoint-and-benchmark.md)

### 11. Benchmark, reporting y robustez

Ubicación principal:

- `src/simulador_multirotor/benchmark.py`
- `src/simulador_multirotor/reporting.py`
- `src/simulador_multirotor/robustness.py`

Responsabilidad:

- comparar baseline y modelos neuronales sobre escenarios homogéneos
- generar artefactos de reporte y selección reproducible
- mantener separada la batería OOD respecto al benchmark principal

Papel en el conjunto:

- cierra el ciclo experimental del TFG
- traduce ejecuciones en resultados comparables y defendibles

ADR relacionada:

- [ADR-017](/Users/chris/Documents/Universidad/TFG/docs/decisions/ADR-017-phase-6-ood-robustness-and-delivery.md)

## Relación entre bloques

El recorrido típico entre bloques es:

1. `scenarios/` define el experimento.
2. `core/`, `trajectories/`, `dynamics/` y `control/` proporcionan las piezas
   del sistema modelado.
3. `runner.py` orquesta la ejecución.
4. `telemetry/` registra la historia.
5. `metrics/` y `visualization/` interpretan la ejecución.
6. `dataset/` reutiliza esa historia para aprendizaje.
7. `control/mlp.py`, `control/recurrent.py`, `benchmark.py` y `reporting.py`
   comparan variantes de control dentro del mismo marco experimental.

## Qué no se está descomponiendo todavía

Esta vista todavía no baja a:

- interfaces detalladas entre módulos
- clases principales por paquete
- decisiones de implementación internas

Eso queda para la fase posterior de documentación software.
