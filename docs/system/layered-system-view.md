# Vista de sistema por capas

## Propósito

Este documento presenta el TFG como un sistema por capas, con una lectura
orientada a explicación oral y revisión técnica de alto nivel. La intención es
que el flujo principal pueda entenderse sin leer código y sin asumir una
equivalencia fuerte entre simulador y dron real.

## Idea general

El TFG se apoya en un simulador de multirrotor usado como plataforma académica
de experimentación. Sobre ese núcleo se organizan varias capas que permiten:

- representar un contexto físico de referencia sin copiarlo de forma literal
- ejecutar escenarios reproducibles
- observar y persistir ejecuciones
- analizarlas con métricas y visualización
- reutilizar los datos para aprendizaje y comparación de controladores

## Capas del sistema

### 1. Contexto físico de referencia

Esta capa no ejecuta el sistema software. Su función es informar el problema:
qué tipo de dron se toma como referencia, qué subsistemas físicos existen y qué
límites tiene el entorno real.

En este TFG esa referencia está recogida en
[Dron Físico](/Users/chris/Documents/Universidad/TFG/docs/Dron_fisico.md) y en
la carpeta [hardware](/Users/chris/Documents/Universidad/TFG/docs/hardware/README.md).

Papel dentro del conjunto:

- fija el dominio de aplicación
- orienta magnitudes, componentes y supuestos físicos
- recuerda que el TFG modela una parte del problema, no el sistema completo real

### 2. Capa de modelado y simulación

Es el núcleo ejecutable del proyecto. Convierte un escenario reproducible en una
secuencia temporal de estados, observaciones, referencias y acciones de control.

Incluye principalmente:

- contratos compartidos de estado, observación, referencia y mando en `core/`
- modelo dinámico y aerodinámico en `dynamics/`
- definición del escenario, tiempos, perturbaciones y configuración en `scenarios/`
- generadores y adaptadores de trayectorias en `trajectories/`
- frontera de control reemplazable en `control/`
- lazo de ejecución en `runner.py`

Esta es la capa que más directamente representa el sistema modelado.

### 3. Capa de observabilidad y persistencia

Esta capa toma la ejecución producida por el runner y la convierte en un
artefacto inspeccionable y reutilizable.

Incluye:

- historia estructurada de simulación en `telemetry/`
- eventos relevantes del experimento
- exportación a formatos persistentes
- metadatos de escenario, vehículo, controlador y telemetría

Su función no es controlar el dron ni alterar la dinámica, sino dejar la
ejecución trazable para análisis posterior.

### 4. Capa de análisis y validación experimental

Esta capa responde a la pregunta "qué ha pasado en la ejecución y cómo se
compara con otras". Trabaja sobre telemetría persistida o sobre historias
homogéneas.

Incluye:

- métricas de seguimiento en `metrics/`
- visualización 2D/3D de trayectorias y errores en `visualization/`
- escenarios de referencia y robustez
- benchmark y reporting en `benchmark.py`, `reporting.py` y `robustness.py`

Su papel es producir interpretación experimental, no redefinir el modelo base.

### 5. Capa de aprendizaje y control inteligente

Esta capa reutiliza la telemetría como dataset y entrena controladores
neuronales manteniendo la misma frontera de control que usa el baseline clásico.

Incluye:

- contrato de dataset y trazabilidad en `dataset/`
- extracción de muestras, features, split por episodios y windowing
- controladores `MLP`, `GRU` y `LSTM` bajo `ControllerContract`
- checkpoints auditables y evaluación comparativa

Cuando se activa, esta capa se apoya en las inferiores. No sustituye la
necesidad de escenario, dinámica, telemetría o métricas.

## Flujo principal del sistema

El flujo dominante del TFG puede resumirse así:

1. Se define un escenario reproducible con vehículo, tiempo, trayectoria,
   perturbaciones, telemetría y metadatos.
2. El runner construye dinámica, trayectoria, generador aleatorio y controlador.
3. En cada iteración, la dinámica actualiza el estado y el controlador calcula
   la acción a partir de observación y referencia.
4. La ejecución se registra como historia estructurada con eventos, errores,
   comandos y metadatos.
5. Esa historia puede exportarse, visualizarse o resumirse con métricas.
6. La telemetría persistida puede convertirse en dataset para entrenar
   controladores neuronales.
7. Los controladores resultantes vuelven a ejecutarse sobre escenarios
   homogéneos u OOD para compararlos con el baseline clásico.

## Lectura rápida de la pila completa

| Capa | Pregunta que responde | Artefactos principales |
| --- | --- | --- |
| Contexto físico | ¿Qué sistema real inspira el TFG? | `docs/Dron_fisico.md`, `docs/hardware/` |
| Modelado y simulación | ¿Qué sistema se ejecuta realmente? | `core/`, `dynamics/`, `scenarios/`, `trajectories/`, `control/`, `runner.py` |
| Observabilidad | ¿Qué queda registrado de una ejecución? | `telemetry/` |
| Análisis | ¿Cómo se interpreta o compara una ejecución? | `metrics/`, `visualization/`, `benchmark.py`, `reporting.py` |
| Aprendizaje | ¿Cómo se reutilizan los datos para control neuronal? | `dataset/`, `control/mlp.py`, `control/recurrent.py` |

## Límites de esta vista

- No describe aún interfaces detalladas entre módulos.
- No entra en diseño software profundo ni en clases concretas.
- No afirma que cada elemento del dron real tenga un gemelo exacto en el simulador.

Para la frontera explícita entre sistema real y sistema modelado, ver
[Physical Boundary And Drone Context](/Users/chris/Documents/Universidad/TFG/docs/system/physical-boundary.md).
