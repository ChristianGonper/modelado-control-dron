# Implementation Plan: Simulador modular para control inteligente de dron multirotor

## Overview

Este documento descompone el plan del simulador en tareas pequeñas, verificables y ordenadas por dependencias. El objetivo es empezar por un tracer bullet funcional y extenderlo por capas sin romper el estado ejecutable del sistema.

## Architecture Decisions

- El simulador se implementará en Python y su producto inicial será un entorno de experimentación reproducible, no una réplica completa del dron real.
- El núcleo físico expondrá estado del vehículo y aceptará thrust colectivo y torques en ejes cuerpo como interfaz de mando.
- Los escenarios serán el contrato principal de entrada del sistema y deberán ser reproducibles, validables y ampliables.
- Las trayectorias nativas y externas compartirán un contrato único de referencia.
- La telemetría será un producto de primera clase del sistema y no un subproducto opcional.
- La arquitectura debe dejar preparado el reemplazo futuro del lazo externo PID por un controlador inteligente.

## Task List

### Phase 1: Foundation

## Task 1: Inicializar el esqueleto del proyecto

**Description:** Crear la base mínima del repositorio para el simulador, incluyendo estructura de paquete, configuración de proyecto Python y punto de entrada para ejecutar una simulación simple sin lógica compleja todavía.

**Acceptance criteria:**
- [ ] Existe una estructura base coherente para núcleo, control, trayectorias, escenarios, telemetría y visualización.
- [ ] El proyecto puede instalarse y ejecutarse localmente con `uv`.
- [ ] Hay un punto de entrada único para lanzar una ejecución mínima.

**Verification:**
- [ ] Entorno sincronizado con `uv sync`
- [ ] Ejecución básica funciona con un comando único de arranque
- [ ] El paquete importa sin errores

**Dependencies:** None

**Files likely touched:**
- `pyproject.toml`
- `README.md`
- `src/...`

**Estimated scope:** M

## Task 2: Definir modelos de datos del estado y del mando

**Description:** Introducir las estructuras de datos estables para representar estado del vehículo, observaciones, comandos de control y referencias de trayectoria. Estas estructuras deben servir de base a dinámica, control y telemetría.

**Acceptance criteria:**
- [ ] El estado del vehículo está definido con campos explícitos y consistentes.
- [ ] El mando del sistema representa thrust colectivo y torques de forma desacoplada.
- [ ] La referencia de trayectoria comparte un formato estable reutilizable por runner y controladores.

**Verification:**
- [ ] Tests de creación y validación de modelos pasan
- [ ] Los tipos/estructuras pueden instanciarse desde una ejecución mínima
- [ ] No hay dependencias circulares entre modelos

**Dependencies:** Task 1

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 3: Implementar dinámica rígida 6 DOF mínima

**Description:** Implementar el primer módulo profundo del sistema: evolución temporal del estado del vehículo con gravedad, integración básica y actuadores simplificados suficientes para soportar una simulación nominal.

**Acceptance criteria:**
- [ ] La dinámica acepta estado actual, mando y paso temporal.
- [ ] La evolución del estado es físicamente coherente en casos básicos.
- [ ] El módulo permanece testeable en aislamiento.

**Verification:**
- [ ] Tests de gravedad e integración básica pasan
- [ ] Tests de saturación o límites mínimos pasan
- [ ] Una ejecución corta produce estados numéricamente válidos

**Dependencies:** Task 2

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** M

## Task 4: Implementar controlador en cascada mínimo

**Description:** Construir el primer controlador base con contrato plug-and-play, suficiente para consumir observaciones y producir thrust colectivo y torques sobre una referencia sencilla.

**Acceptance criteria:**
- [ ] El controlador consume observación y referencia sin depender del integrador.
- [ ] El controlador emite mandos compatibles con la dinámica.
- [ ] El lazo interno y el externo quedan desacoplados a nivel de interfaz.

**Verification:**
- [ ] Tests de contrato del controlador pasan
- [ ] Tests cualitativos de corrección básica pasan
- [ ] El controlador puede conectarse al runner mínimo sin cambios ad hoc

**Dependencies:** Task 2, Task 3

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** M

## Task 5: Construir el runner mínimo extremo a extremo

**Description:** Unir escenario mínimo, dinámica, controlador y un reloj de simulación en una ejecución completa que permita validar el primer tracer bullet.

**Acceptance criteria:**
- [ ] Existe un flujo único para ejecutar una simulación nominal de extremo a extremo.
- [ ] El runner coordina integración, referencia, control y acumulación de resultados.
- [ ] El sistema queda en estado demoable aunque todavía sea básico.

**Verification:**
- [ ] La ejecución mínima corre de principio a fin
- [ ] Hay un test de integración corta para el runner
- [ ] Se puede inspeccionar una salida simple de estados en consola o memoria

**Dependencies:** Task 3, Task 4

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** M

### Checkpoint: Foundation

- [ ] `uv sync` funciona sin errores
- [ ] El tracer bullet básico ejecuta una simulación completa
- [ ] Los tests de modelos, dinámica, control y runner pasan
- [ ] El sistema queda listo para introducir escenarios formales

### Phase 2: Core Scenarios

## Task 6: Definir el esquema mínimo de escenario

**Description:** Formalizar el contrato de configuración de escenarios con bloques estables de vehículo, estado inicial, tiempo, trayectoria, perturbaciones, controlador, telemetría y metadatos.

**Acceptance criteria:**
- [ ] El esquema de escenario refleja la PRD y puede ampliarse sin romper compatibilidad.
- [ ] Existen valores por defecto razonables para escenarios nominales.
- [ ] Los bloques obligatorios y opcionales están claramente diferenciados.

**Verification:**
- [ ] Tests de validación de escenarios pasan
- [ ] Un escenario mínimo puede construirse con pocos campos
- [ ] Configuraciones incompletas generan errores claros

**Dependencies:** Task 2, Task 5

**Files likely touched:**
- `src/...`
- `tests/...`
- `docs/...`

**Estimated scope:** S

## Task 7: Integrar escenarios en el runner

**Description:** Hacer que el runner deje de depender de configuraciones ad hoc y pase a ejecutarse únicamente a través del contrato de escenario.

**Acceptance criteria:**
- [ ] El runner consume escenarios como única entrada principal de configuración.
- [ ] El estado inicial, horizonte y paso temporal se leen desde escenario.
- [ ] El runner guarda metadatos del escenario junto con la ejecución.

**Verification:**
- [ ] Tests de integración de runner con escenario pasan
- [ ] La misma configuración produce ejecuciones equivalentes
- [ ] Se pueden inspeccionar metadatos asociados a la ejecución

**Dependencies:** Task 6

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 8: Añadir semilla y reproducibilidad controlada

**Description:** Incorporar control explícito de semilla y reproducibilidad para que las ejecuciones puedan repetirse y compararse con confianza en fases posteriores.

**Acceptance criteria:**
- [ ] El escenario permite fijar semilla de ejecución.
- [ ] Dos corridas con misma semilla reproducen el mismo comportamiento esperado.
- [ ] Los elementos aleatorios quedan centralizados y controlados.

**Verification:**
- [ ] Tests de reproducibilidad pasan
- [ ] Cambiar la semilla altera solo los componentes aleatorios
- [ ] Los resultados reproducibles se documentan en el flujo de ejecución

**Dependencies:** Task 7

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

### Checkpoint: Core Scenarios

- [ ] Todo experimento se lanza desde un escenario válido
- [ ] La reproducibilidad queda verificada
- [ ] El runner ya no depende de configuración embebida o manual

### Phase 3: Trajectories

## Task 9: Implementar el contrato común de trayectorias

**Description:** Definir el adaptador o interfaz única para referencias nativas y externas, con campos mínimos de posición, velocidad, yaw y validez temporal.

**Acceptance criteria:**
- [ ] Las trayectorias comparten una firma y salida comunes.
- [ ] El contrato soporta referencias temporizadas y parametrizadas.
- [ ] El runner puede consumir la referencia sin conocer su origen.

**Verification:**
- [ ] Tests de contrato de trayectorias pasan
- [ ] Una trayectoria externa simulada puede adaptarse al contrato
- [ ] El runner usa solo el contrato y no tipos concretos

**Dependencies:** Task 2, Task 7

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 10: Implementar recta y círculo como primeras trayectorias nativas

**Description:** Entregar las dos primeras familias nativas para validar el camino completo desde selección en escenario hasta seguimiento por el controlador.

**Acceptance criteria:**
- [ ] El sistema soporta al menos una recta y un círculo parametrizables.
- [ ] Las referencias son geométricamente correctas en puntos clave.
- [ ] Pueden seleccionarse desde escenario sin lógica especial.

**Verification:**
- [ ] Tests geométricos de trayectorias pasan
- [ ] El runner ejecuta escenarios con recta y círculo
- [ ] La telemetría refleja el cambio de referencia correctamente

**Dependencies:** Task 9

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 11: Implementar espiral, curva paramétrica simple y Lissajous

**Description:** Completar el conjunto mínimo de trayectorias de la PRD para cubrir la batería base del TFG y habilitar comparativas más ricas.

**Acceptance criteria:**
- [ ] El simulador soporta espiral, curva paramétrica simple y Lissajous.
- [ ] Todas las familias reutilizan el mismo contrato de referencia.
- [ ] El comportamiento al agotar horizonte temporal está definido y probado.

**Verification:**
- [ ] Tests de continuidad temporal y validez geométrica pasan
- [ ] Hay escenarios de ejemplo para cada nueva familia
- [ ] La finalización o agotamiento de referencia se maneja de forma uniforme

**Dependencies:** Task 10

**Files likely touched:**
- `src/...`
- `tests/...`
- `docs/...`

**Estimated scope:** M

### Checkpoint: Trajectories

- [ ] El conjunto mínimo de trayectorias de la PRD está implementado
- [ ] El runner puede consumir trayectorias nativas y externas
- [ ] La referencia queda completamente desacoplada del núcleo

### Phase 4: Telemetry and Metrics

## Task 12: Diseñar el esquema de telemetría de ejecución

**Description:** Definir las series y metadatos mínimos que toda simulación debe registrar para soportar análisis, exportación y trazabilidad.

**Acceptance criteria:**
- [ ] La telemetría incluye tiempo, estado, referencia, error, control y eventos relevantes.
- [ ] El esquema es coherente con el contrato de escenario y trayectorias.
- [ ] La estructura de datos es apta para exportación y análisis posterior.

**Verification:**
- [ ] Tests de esquema de telemetría pasan
- [ ] Una ejecución mínima genera registros completos
- [ ] Los metadatos del escenario quedan enlazados a la telemetría

**Dependencies:** Task 7, Task 9

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 13: Implementar exportación a CSV, JSON y NumPy

**Description:** Añadir exportadores que transformen la telemetría interna a los tres formatos definidos en la PRD sin pérdida relevante de información.

**Acceptance criteria:**
- [ ] La telemetría puede exportarse a `CSV`, `JSON` y `NumPy`.
- [ ] Los formatos preservan datos y metadatos esenciales.
- [ ] El nivel de detalle exportado puede controlarse desde escenario.

**Verification:**
- [ ] Tests de exportación por formato pasan
- [ ] Los artefactos exportados pueden abrirse y leerse correctamente
- [ ] Una misma ejecución produce salidas consistentes entre formatos

**Dependencies:** Task 12

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** M

## Task 14: Implementar métricas básicas de seguimiento

**Description:** Calcular métricas comparables de error y esfuerzo de control para permitir evaluación objetiva entre ejecuciones y controladores.

**Acceptance criteria:**
- [ ] Existen métricas básicas de seguimiento definidas sobre telemetría.
- [ ] Las métricas pueden compararse entre ejecuciones homogéneas.
- [ ] Los resultados se integran con la salida de análisis del simulador.

**Verification:**
- [ ] Tests con series sintéticas pasan
- [ ] Las métricas se calculan sobre ejecuciones reales
- [ ] La salida de métricas queda asociada a la ejecución

**Dependencies:** Task 12

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

### Checkpoint: Telemetry and Metrics

- [ ] Toda ejecución produce telemetría estructurada
- [ ] La exportación multiformato funciona
- [ ] Ya es posible comparar escenarios con métricas básicas

### Phase 5: Aerodynamics and Disturbances

## Task 15: Implementar arrastre parásito básico

**Description:** Introducir el primer término aerodinámico simple y parametrizable en el núcleo físico sin romper el comportamiento nominal existente.

**Acceptance criteria:**
- [ ] El arrastre parásito puede activarse o desactivarse.
- [ ] El término usa parámetros del vehículo o del escenario.
- [ ] La dinámica nominal sigue disponible sin perturbaciones.

**Verification:**
- [ ] Tests de plausibilidad física pasan
- [ ] Hay comparación entre ejecución nominal y con arrastre
- [ ] La telemetría registra la activación relevante del modelo

**Dependencies:** Task 3, Task 7, Task 12

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 16: Implementar término inducido simplificado para hover

**Description:** Añadir un segundo nivel de fidelidad aerodinámica, centrado en el efecto inducido simplificado que más impacta en hover según la PRD.

**Acceptance criteria:**
- [ ] El término inducido se integra sin romper el contrato de dinámica.
- [ ] Su configuración se controla desde escenario.
- [ ] El efecto puede analizarse de forma aislada frente al caso nominal.

**Verification:**
- [ ] Tests de comportamiento en hover pasan
- [ ] El escenario puede activar solo el término inducido
- [ ] La salida de telemetría permite diferenciar el efecto

**Dependencies:** Task 15

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 17: Añadir viento y ruido configurables

**Description:** Completar la capa de perturbaciones configurables con viento y ruido controlados por escenario y compatibles con reproducibilidad.

**Acceptance criteria:**
- [ ] Viento y ruido pueden activarse y parametrizarse desde escenario.
- [ ] La semilla controla su reproducibilidad.
- [ ] El sistema sigue respetando restricciones físicas básicas bajo perturbaciones razonables.

**Verification:**
- [ ] Tests de reproducibilidad con perturbaciones pasan
- [ ] El runner ejecuta escenarios perturbados y nominales
- [ ] La telemetría y los metadatos reflejan perturbaciones activas

**Dependencies:** Task 8, Task 12, Task 16

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** M

### Checkpoint: Aerodynamics and Disturbances

- [ ] El modelo simple de aerodinámica de la PRD está cubierto
- [ ] Las perturbaciones son configurables y reproducibles
- [ ] El sistema sigue siendo usable en modo nominal

### Phase 6: Analysis Outputs

## Task 18: Implementar visualización 2D de trayectorias y errores

**Description:** Crear el primer flujo de análisis post-procesado para representar trayectoria, referencia y errores sin acoplarse al bucle de simulación.

**Acceptance criteria:**
- [ ] La visualización consume telemetría persistida.
- [ ] Se generan salidas 2D útiles para inspección rápida.
- [ ] El flujo no afecta a la ejecución del runner.

**Verification:**
- [ ] Una telemetría exportada puede visualizarse en 2D
- [ ] Hay pruebas ligeras de generación de artefactos
- [ ] El resultado es reutilizable en documentación

**Dependencies:** Task 13, Task 14

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

## Task 19: Implementar visualización 3D básica

**Description:** Añadir representación 3D de trayectoria y actitud para validar cualitativamente maniobras y dar soporte a la memoria del TFG.

**Acceptance criteria:**
- [ ] Existen salidas 3D básicas para trayectorias del dron.
- [ ] La visualización usa la misma telemetría que el análisis 2D.
- [ ] El resultado permite inspección cualitativa de maniobras.

**Verification:**
- [ ] El flujo 3D se ejecuta sobre telemetrías reales
- [ ] Hay pruebas ligeras o checks automáticos de artefactos
- [ ] Los artefactos pueden reutilizarse en informes

**Dependencies:** Task 18

**Files likely touched:**
- `src/...`
- `tests/...`

**Estimated scope:** S

### Checkpoint: Analysis Outputs

- [ ] El simulador produce artefactos 2D y 3D desacoplados
- [ ] El análisis puede usarse sobre cualquier ejecución exportada
- [ ] La salida es aprovechable para memoria y revisión técnica

### Phase 7: Extension Readiness

## Task 20: Consolidar interfaz de controlador reemplazable

**Description:** Refinar la frontera entre runner y control para garantizar que el lazo externo pueda sustituirse más adelante sin reestructurar el simulador.

**Acceptance criteria:**
- [ ] El contrato de controlador separa claramente observación, referencia y acción.
- [ ] El runner no depende de detalles internos del PID.
- [ ] Queda preparado el punto de extensión para control inteligente.

**Verification:**
- [ ] Tests de contrato de controlador pasan
- [ ] Un controlador alternativo mínimo puede conectarse como stub
- [ ] La documentación interna describe el punto de extensión

**Dependencies:** Task 4, Task 11, Task 14

**Files likely touched:**
- `src/...`
- `tests/...`
- `docs/...`

**Estimated scope:** S

## Task 21: Preparar salida para datasets y calibración futura

**Description:** Asegurar que parámetros del vehículo, telemetría y metadatos de ejecución quedan listos para reutilización posterior en calibración sim-to-real y entrenamiento de control inteligente.

**Acceptance criteria:**
- [ ] Los datos exportados contienen la información mínima para reutilización posterior.
- [ ] Los parámetros del vehículo quedan asociados a la ejecución.
- [ ] La batería base de escenarios puede reutilizarse para comparativas futuras.

**Verification:**
- [ ] Se genera una ejecución completa con datos reutilizables
- [ ] Los metadatos de vehículo y escenario se preservan en exportación
- [ ] La documentación describe cómo reutilizar la salida en fases posteriores

**Dependencies:** Task 13, Task 14, Task 17, Task 20

**Files likely touched:**
- `src/...`
- `docs/...`

**Estimated scope:** S

### Checkpoint: Complete

- [ ] Todas las fases del plan tienen al menos un camino verificable implementable
- [ ] El simulador queda preparado para PID hoy y control inteligente más adelante
- [ ] Los contratos principales del sistema están estabilizados
- [ ] La salida del simulador sirve para análisis, comparación y generación de datasets

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sobrediseñar el simulador antes de tener el tracer bullet ejecutable | High | Forzar las primeras 5 tareas a cerrar un flujo mínimo extremo a extremo antes de añadir fidelidad |
| Mezclar contratos de runner, trayectoria y controlador demasiado pronto | High | Definir primero modelos de datos y contratos comunes antes de expandir familias de trayectorias o exportadores |
| Introducir aerodinámica compleja sin capacidad de validación | Medium | Limitar el primer modelo a arrastre parásito e inducido simplificado con tests de plausibilidad |
| Telemetría insuficiente para fases futuras | High | Diseñar el esquema de telemetría antes de exportación y validarlo contra necesidades de métricas y datasets |
| Tareas demasiado grandes para ejecutarse en una sesión | Medium | Mantener tareas S/M y usar checkpoints explícitos al final de cada bloque |

## Open Questions

- Qué librerías concretas se van a usar para integración numérica, visualización y validación de configuraciones.
- Si se quiere priorizar compatibilidad con notebooks desde el inicio o mantener el primer flujo solo por CLI/script.
- Qué métricas de seguimiento serán obligatorias en la primera implementación más allá del error base y esfuerzo de control.

## Verification

- [ ] Every task has acceptance criteria
- [ ] Every task has a verification step
- [ ] Task dependencies are identified and ordered correctly
- [ ] No task touches more than ~5 files
- [ ] Checkpoints exist between major phases
- [ ] The human has reviewed and approved the plan
