# Implementation Plan: Mejoras de física y funcionamiento del simulador

## Overview

Este plan traduce `mejoras_ejecutar.md` a una secuencia de tareas pequeñas y verificables sobre la base actual del simulador. El objetivo no es añadir las 11 mejoras como parches aislados, sino reordenarlas según dependencias reales: primero contratos y núcleo físico, después control y telemetría, y finalmente escenarios reproducibles y validación experimental.

## Architecture Decisions

- La actitud pasa a ser una magnitud nativa en cuaterniones en todo el camino de control y dinámica; los ángulos de Euler quedan solo para análisis y visualización.
- El controlador seguirá generando una consigna de wrench en cuerpo o una consigna intermedia equivalente; la aplicación física final de fuerzas y torques se resolverá mediante una capa de `mixer + actuadores`.
- La dinámica 6DOF debe exponer una función de derivada pura para habilitar RK4 y facilitar pruebas de regresión entre integradores.
- El `runner` debe separar explícitamente `physics_dt`, `control_dt` y `telemetry_dt` para mantener coherencia temporal entre planta, observación, control y logging.
- El estado verdadero y el estado observado deben coexistir como señales distintas; la telemetría no debe mezclar ambos en una misma muestra.
- Los escenarios deben convertirse en artefactos externos e inmutables para congelar las condiciones de cada experimento y hacerlos auditables.
- Las perturbaciones atmosféricas y ráfagas deben formularse con invariancia respecto a `dt`; no se aceptan modelos cuyo nivel de energía cambie al variar la discretización.
- La validación final debe apoyarse en escenarios de referencia versionados y métricas de regresión física, no solo en inspección visual.

## Task List

### Phase 1: Contratos y núcleo dinámico

## Task 1: Redefinir contratos de vehículo, mando y observación para soportar motorización y doble estado

**Description:** Extender los contratos base para dejar de asumir que el mando físico es únicamente `collective_thrust + body_torque`. Esta tarea introduce la distinción entre consigna de control, salida del mixer, estado verdadero y estado observado, además de los parámetros geométricos mínimos del vehículo y de cada rotor.

**Acceptance criteria:**
- [ ] `VehicleCommand` o un contrato equivalente separa claramente la consigna de alto nivel de las señales por motor.
- [ ] El modelo del vehículo puede describir rotores individuales, brazos de palanca, sentido de giro e inercia/constantes relevantes.
- [ ] `VehicleObservation` y telemetría pueden representar por separado estado verdadero y estado observado sin ambigüedad temporal.

**Verification:**
- [ ] Tests de validación de contratos pasan con `uv run pytest`
- [ ] Los nuevos modelos rechazan configuraciones inconsistentes de rotores y estados
- [ ] El `runner` y el controlador pueden instanciar los contratos sin adaptaciones ad hoc

**Dependencies:** None

**Files likely touched:**
- `src/simulador_multirotor/core/contracts.py`
- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/telemetry/memory.py`
- `tests/...`

**Estimated scope:** M

## Task 2: Sustituir la cinemática rotacional simplificada por dinámica de Euler y actualización geométrica en SO(3)

**Description:** Reescribir la parte rotacional del cuerpo rígido para incluir acoplamiento giroscópico y propagación exacta de actitud mediante mapa exponencial. Esta tarea elimina la aceleración angular desacoplada y la integración aditiva del cuaternión.

**Acceptance criteria:**
- [ ] La aceleración angular usa `I^-1 (tau - omega x (I omega))`.
- [ ] La orientación se actualiza con integración geométrica en cuaterniones y preserva norma sin correcciones espurias por paso.
- [ ] Existen utilidades explícitas para calcular el incremento rotacional desde `omega` y `dt`.

**Verification:**
- [ ] Tests unitarios de dinámica rotacional pasan con `uv run pytest`
- [ ] Un caso con `omega != 0` y torque nulo conserva el comportamiento esperado del cuerpo rígido
- [ ] La norma del cuaternión se mantiene estable en simulaciones largas sin deriva apreciable

**Dependencies:** Task 1

**Files likely touched:**
- `src/simulador_multirotor/dynamics/rigid_body.py`
- `src/simulador_multirotor/core/attitude.py`
- `tests/...`

**Estimated scope:** M

## Task 3: Reestructurar el integrador a derivadas puras y migrar de Euler a RK4

**Description:** Separar la evaluación de derivadas del avance temporal para permitir un integrador RK4 real sobre el estado completo. El objetivo es reducir error numérico y dejar el núcleo preparado para pruebas cruzadas entre integradores.

**Acceptance criteria:**
- [ ] La dinámica expone una función de derivada del estado sin efectos laterales sobre el integrador.
- [ ] El avance nominal usa RK4 para traslación y rotación.
- [ ] El integrador preserva correctamente la sincronización del tiempo del estado.

**Verification:**
- [ ] Tests de regresión entre pasos pequeños y grandes muestran menor error que el integrador Euler previo
- [ ] `uv run pytest` pasa incluyendo pruebas de estabilidad numérica básica
- [ ] El runner sigue produciendo simulaciones completas sin romper la interfaz pública principal

**Dependencies:** Task 2

**Files likely touched:**
- `src/simulador_multirotor/dynamics/rigid_body.py`
- `src/simulador_multirotor/runner.py`
- `tests/...`

**Estimated scope:** M

### Checkpoint: Núcleo dinámico

- [ ] La dinámica rotacional ya incluye acoplamiento giroscópico
- [ ] La actitud se integra en cuaterniones sobre SO(3)
- [ ] El integrador nominal usa RK4 y la simulación sigue siendo ejecutable de extremo a extremo

### Phase 2: Actuación y control

## Task 4: Introducir arquitectura de mixer y dinámica de actuadores por motor

**Description:** Añadir una capa explícita entre el controlador y la planta que convierta consignas de fuerza/torque en señales por rotor y modele la respuesta de cada motor como un sistema de primer orden. Esta tarea materializa la transición desde una planta sintética global a una planta basada en motores individuales.

**Acceptance criteria:**
- [ ] Existe una representación explícita de motores/rotores con posición, eje y sentido de giro.
- [ ] Un `mixer` calcula fuerza total y torque total a partir de comandos por rotor.
- [ ] La dinámica del motor sigue una respuesta de primer orden con constante de tiempo configurable.

**Verification:**
- [ ] Tests del mixer pasan para configuraciones simétricas nominales
- [ ] Tests de respuesta transitoria del motor pasan con `uv run pytest`
- [ ] La planta reacciona con retardo finito ante cambios bruscos de mando

**Dependencies:** Task 1, Task 3

**Files likely touched:**
- `src/simulador_multirotor/dynamics/rigid_body.py`
- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/core/contracts.py`
- `tests/...`

**Estimated scope:** M

## Task 5: Migrar el control de actitud a error en cuaterniones y body rates

**Description:** Reemplazar el control actual basado en Euler por una ley PD en el marco del cuerpo usando cuaternión de error y velocidades angulares deseadas. La tarea debe eliminar la resta incoherente entre error angular inercial y body rates.

**Acceptance criteria:**
- [ ] El error de actitud se calcula con cuaterniones y selección de rotación corta.
- [ ] La derivativa del controlador usa `omega_curr - omega_des` en ejes cuerpo.
- [ ] El controlador ya no depende de `euler_from_quaternion` para la estabilización nominal.

**Verification:**
- [ ] Tests del controlador pasan con maniobras grandes y cambios de yaw
- [ ] No aparecen singularidades o discontinuidades al cruzar configuraciones cercanas a gimbal lock
- [ ] El runner puede ejecutar hover y trayectorias básicas con el nuevo controlador

**Dependencies:** Task 2, Task 4

**Files likely touched:**
- `src/simulador_multirotor/control/cascade.py`
- `src/simulador_multirotor/core/attitude.py`
- `tests/...`

**Estimated scope:** M

## Task 6: Desacoplar frecuencias de física, control y telemetría manteniendo coherencia temporal

**Description:** Reorganizar el `runner` para que la planta evolucione a su propio `physics_dt`, el controlador actúe a `control_dt` y la telemetría muestree a `telemetry_dt`, garantizando que estado, observación, referencia y acción correspondan al mismo instante lógico cuando se registran.

**Acceptance criteria:**
- [ ] El esquema temporal de escenario permite configurar frecuencias separadas para física, control y telemetría.
- [ ] El control no se recalcula en cada paso físico salvo que corresponda por su frecuencia.
- [ ] Cada muestra de telemetría identifica unívocamente el instante del estado verdadero, la observación usada y la acción aplicada.

**Verification:**
- [ ] Tests de scheduling temporal pasan con combinaciones distintas de `dt`
- [ ] `uv run pytest` valida que cambiar `physics_dt` no altera artificialmente el ritmo de control configurado
- [ ] Una simulación con `control_dt > physics_dt` conserva trazabilidad correcta en la telemetría

**Dependencies:** Task 3, Task 5

**Files likely touched:**
- `src/simulador_multirotor/runner.py`
- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/telemetry/memory.py`
- `tests/...`

**Estimated scope:** M

### Checkpoint: Control y actuación

- [ ] La planta ya se alimenta mediante motores individuales con inercia
- [ ] El control de actitud opera íntegramente en cuaterniones y body rates
- [ ] Física, control y telemetría tienen relojes separados y consistentes

### Phase 3: Entorno, escalado físico y observabilidad

## Task 7: Sustituir el modelo de viento por perturbaciones invariantes a `dt`

**Description:** Reemplazar el ruido de ráfagas muestreado directamente por paso por un modelo estocástico formulado para conservar densidad espectral al variar el `dt`. Puede implementarse una aproximación tipo Dryden discreta o un modelo equivalente bien documentado.

**Acceptance criteria:**
- [ ] El nivel energético de las perturbaciones no depende artificialmente del `dt` del simulador.
- [ ] El modelo distingue al menos viento base y componente de ráfaga.
- [ ] La configuración de perturbaciones sigue siendo reproducible a partir de la semilla del escenario.

**Verification:**
- [ ] Tests estadísticos básicos comparan simulaciones con distintos `dt` y tolerancias equivalentes
- [ ] `uv run pytest` pasa incluyendo pruebas de reproducibilidad del modelo estocástico
- [ ] La telemetría registra muestras del viento aplicado para auditoría

**Dependencies:** Task 6

**Files likely touched:**
- `src/simulador_multirotor/dynamics/aerodynamics.py`
- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/runner.py`
- `tests/...`

**Estimated scope:** M

## Task 8: Revisar el modelo aerodinámico y el escalado de parámetros del vehículo

**Description:** Hacer explícitas las hipótesis del modelo aerodinámico respecto a masa, inercias, empuje, drag y agregación de parámetros para evitar incoherencias de escala. La tarea debe fijar qué parámetros representan física agregada y cuáles dependen de la geometría del vehículo.

**Acceptance criteria:**
- [ ] El vehículo define de forma explícita masa, tensor de inercia y parámetros aerodinámicos compatibles con la nueva planta.
- [ ] El modelo documenta si las fuerzas aerodinámicas son agregadas o por rotor.
- [ ] Existen validaciones que evitan configuraciones físicamente absurdas o mal escaladas.

**Verification:**
- [ ] Tests de validación de parámetros pasan con `uv run pytest`
- [ ] Escenarios nominales e intensificados producen respuestas coherentes al escalar masa o empuje
- [ ] La documentación interna refleja los supuestos de proporcionalidad física

**Dependencies:** Task 4, Task 7

**Files likely touched:**
- `src/simulador_multirotor/dynamics/rigid_body.py`
- `src/simulador_multirotor/scenarios/schema.py`
- `docs/...`
- `tests/...`

**Estimated scope:** S

## Task 9: Separar formalmente estado verdadero, observación ruidosa y métricas de seguimiento

**Description:** Rehacer el flujo de telemetría y cálculo de error para que el simulador registre por separado el estado físico verdadero y la señal observada por sensores simulados. Esta tarea corrige la mezcla actual entre variables ruidosas y absolutas en una misma muestra lógica.

**Acceptance criteria:**
- [ ] La telemetría preserva ambos estados por muestra o documenta claramente cuál usa cada métrica.
- [ ] El cálculo de tracking error se hace contra un estado bien definido y consistente en tiempo.
- [ ] El exportado y las métricas siguen funcionando con el nuevo esquema sin pérdida de trazabilidad.

**Verification:**
- [ ] Tests de telemetría y exportación pasan con `uv run pytest`
- [ ] La comparación entre estado verdadero y observado puede reconstruirse desde artefactos persistidos
- [ ] No existen campos ambiguos que mezclen señal ruidosa y señal verdadera

**Dependencies:** Task 1, Task 6, Task 7

**Files likely touched:**
- `src/simulador_multirotor/telemetry/memory.py`
- `src/simulador_multirotor/telemetry/export.py`
- `src/simulador_multirotor/metrics/report.py`
- `tests/...`

**Estimated scope:** M

### Checkpoint: Entorno y telemetría

- [ ] Las perturbaciones son invariantes a `dt` dentro de tolerancias razonables
- [ ] El modelo de vehículo y aerodinámica tiene hipótesis explícitas y validadas
- [ ] La telemetría diferencia estado verdadero y observado de forma consistente

### Phase 4: Escenarios, validación y cierre experimental

## Task 10: Convertir el escenario en artefacto externo e inmutable

**Description:** Dejar de depender de escenarios construidos exclusivamente en código y soportar carga desde un archivo externo versionable. El escenario debe ser la fuente de verdad congelada de cada experimento, incluyendo vehículo, tiempo, control, perturbaciones y referencias.

**Acceptance criteria:**
- [ ] Existe un formato externo soportado para escenarios versionables.
- [ ] El `runner` puede ejecutar un escenario cargado desde archivo sin reconstrucción manual en código.
- [ ] El escenario serializado captura toda la configuración necesaria para repetir el experimento.

**Verification:**
- [ ] Tests de carga y validación de escenarios externos pasan con `uv run pytest`
- [ ] Un escenario guardado y vuelto a cargar produce la misma simulación dentro de tolerancia
- [ ] La CLI puede ejecutar al menos un escenario externo de referencia

**Dependencies:** Task 6, Task 8, Task 9

**Files likely touched:**
- `src/simulador_multirotor/scenarios/schema.py`
- `src/simulador_multirotor/scenarios/...`
- `src/simulador_multirotor/app.py`
- `tests/...`

**Estimated scope:** M

## Task 11: Crear batería de escenarios de referencia y regresiones físicas

**Description:** Cerrar la iteración con un conjunto pequeño de escenarios auditables que permitan verificar las nuevas capacidades: hover, respuesta angular libre, escalón de actitud, perturbación con viento y comparación entre discretizaciones. Esta tarea convierte las mejoras en una base de validación reutilizable.

**Acceptance criteria:**
- [ ] Existen escenarios de referencia versionados para hover, maniobra angular, perturbación y comparación de `dt`.
- [ ] Cada escenario tiene criterios de aceptación cuantitativos mínimos o checks de regresión definidos.
- [ ] La batería puede ejecutarse de forma automatizada para detectar regresiones futuras.

**Verification:**
- [ ] `uv run pytest` o el comando de validación equivalente ejecuta la batería básica
- [ ] Los escenarios generan telemetría suficiente para inspección y comparación
- [ ] La documentación indica qué propiedad física valida cada escenario

**Dependencies:** Task 10

**Files likely touched:**
- `tests/...`
- `docs/...`
- `analysis_outputs/...`
- `src/simulador_multirotor/scenarios/...`

**Estimated scope:** M

### Checkpoint: Complete

- [ ] Las 11 mejoras de `mejoras_ejecutar.md` quedan cubiertas por tareas implementables y ordenadas por dependencia
- [ ] Existe una ruta clara desde refactor de contratos hasta validación experimental
- [ ] El simulador queda preparado para evolucionar sin mezclar fidelidad física con deuda de arquitectura

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Intentar migrar control, mixer e integrador a la vez | High | Forzar primero contratos y derivadas puras antes de tocar lazo de control y actuadores |
| Romper compatibilidad de telemetría durante la separación de estado verdadero/observado | High | Versionar el esquema exportado y añadir tests de round-trip antes de modificar métricas |
| Introducir un modelo de viento demasiado complejo sin validación mínima | Medium | Empezar con una formulación discreta bien acotada y añadir tests estadísticos simples antes de ampliar |
| Dejar el escenario externo para el final y perder reproducibilidad durante la migración | Medium | Definir desde temprano el contrato serializable aunque la CLI se conecte después |
| Crear tareas demasiado grandes alrededor de “refactor de física” | High | Mantener tareas S/M y usar checkpoints obligatorios tras núcleo, control y telemetría |

## Open Questions

- Qué formato externo se quiere priorizar para escenarios: `JSON`, `YAML` o ambos.
- Si el controlador seguirá emitiendo wrench deseado o si se quiere permitir control directo por motor en fases futuras.
- Qué tolerancias cuantitativas se aceptarán para las pruebas de invariancia respecto a `dt` y para las regresiones físicas básicas.
- Si conviene introducir una versión explícita del esquema de telemetría antes de separar estado verdadero y observado.

## Verification

- [ ] Every task has acceptance criteria
- [ ] Every task has a verification step
- [ ] Task dependencies are identified and ordered correctly
- [ ] No task touches more than ~5 files
- [ ] Checkpoints exist between major phases
- [ ] The human has reviewed and approved the plan
