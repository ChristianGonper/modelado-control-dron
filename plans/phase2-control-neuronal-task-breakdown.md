# Implementation Plan: Fase 2 - Control neuronal para seguimiento de trayectorias

## Overview

Este breakdown convierte el plan de Fase 2 en tareas ejecutables, pequeñas y verificables. El objetivo es construir un pipeline reproducible que parta de telemetría persistida del simulador, entrene controladores neuronales bajo el contrato actual del runner, compare MLP, GRU y LSTM frente al baseline clásico y deje artefactos reutilizables para la memoria del TFG y la siguiente fase.

## Architecture Decisions

- El runner sigue siendo la frontera oficial de ejecución y solo aceptará controladores que cumplan el contrato actual.
- El dataset se genera desde telemetría persistida y no modifica el bucle vivo del simulador.
- La política usa `observed_state` y referencia como entrada; `true_state` queda reservado para evaluación.
- La representación de features y targets ya está cerrada por el PRD y debe mantenerse estable entre entrenamiento e inferencia.
- El split principal es `70/15/15` por episodios completos y la robustez fuera de distribución se evalúa en una batería separada.

## Task List

### Phase 1: Foundation Dataset

- [ ] Task 1: Inventariar y formalizar el contrato de dataset
- [ ] Task 2: Implementar extracción de episodios desde telemetría persistida
- [ ] Task 3: Implementar esquema de features y targets por instante

## Task 1: Inventariar y formalizar el contrato de dataset

**Description:** Definir de forma explícita el esquema de dataset de Fase 2 para que extracción, entrenamiento, inferencia y evaluación compartan la misma semántica. Esta tarea debe fijar nombres de campos, metadatos mínimos, modos de features permitidos, convención de targets y estructura de episodios.

**Acceptance criteria:**
- [ ] Existe una especificación escrita del dataset con entradas, targets, metadatos y política de observabilidad alineada con el PRD.
- [ ] La especificación distingue claramente datos por episodio, por muestra y por split.
- [ ] La especificación deja cerrados los dos modos permitidos de features y la salida supervisada de 4 dimensiones.

**Verification:**
- [ ] Revisión manual: el contrato cubre observación, referencia, target, ventana, split y metadatos reproducibles.
- [ ] Revisión manual: la especificación es consistente con el PRD y el plan de Fase 2.

**Dependencies:** None

**Files likely touched:**
- `plans/phase2-control-neuronal-task-breakdown.md`
- `docs/PRD_phase2_control_neuronal.md`
- `docs/` o documentación auxiliar de Fase 2

**Estimated scope:** Small: 1-2 files

## Task 2: Implementar extracción de episodios desde telemetría persistida

**Description:** Construir el primer módulo funcional que lea telemetría exportada por el simulador y la convierta en episodios reutilizables para aprendizaje supervisado, preservando observación, referencia, acción experta y metadatos de escenario y seed.

**Acceptance criteria:**
- [ ] El extractor puede cargar exports persistidos y generar episodios completos listos para featurización.
- [ ] Cada episodio conserva trazabilidad de escenario, seed, controlador y configuración experimental.
- [ ] El extractor falla con errores claros si faltan columnas o metadatos necesarios.

**Verification:**
- [ ] Tests pass: pruebas del extractor de episodios y validación de esquema.
- [ ] Manual check: se puede inspeccionar un episodio derivado y verificar observación, referencia y acción.

**Dependencies:** Task 1

**Files likely touched:**
- `src/...` módulo de dataset o training
- `tests/...` pruebas de extracción
- `docs/...` notas de uso si hace falta

**Estimated scope:** Medium: 3-5 files

## Task 3: Implementar esquema de features y targets por instante

**Description:** Añadir el pipeline que transforma cada episodio en features y targets por instante usando la representación cerrada en el PRD: observación en cuaternión, referencia activa, codificación trigonométrica de yaw y, opcionalmente, errores explícitos de seguimiento.

**Acceptance criteria:**
- [ ] El pipeline soporta `raw_observation` y `observation_plus_tracking_errors`.
- [ ] Los features calculados respetan la dimensionalidad esperada y la semántica de observación frente a verdad física.
- [ ] El target supervisado siempre representa thrust colectivo y torques en cuerpo.

**Verification:**
- [ ] Tests pass: pruebas de dimensionalidad, orden de features y cálculo de yaw/error.
- [ ] Manual check: un ejemplo generado coincide con la convención del PRD.

**Dependencies:** Task 2

**Files likely touched:**
- `src/...` módulo de features
- `tests/...` pruebas de features

**Estimated scope:** Medium: 3-5 files

### Checkpoint: Foundation Dataset

- [ ] Las tareas 1-3 dejan un contrato de dataset estable y verificable
- [ ] Los tests de extracción y features pasan
- [ ] Existe al menos un flujo mínimo desde telemetría persistida hasta muestras supervisadas

### Phase 2: Splits And Windowing

- [ ] Task 4: Implementar partición determinista por episodios
- [ ] Task 5: Implementar windowing temporal para MLP
- [ ] Task 6: Implementar windowing secuencial para GRU/LSTM

## Task 4: Implementar partición determinista por episodios

**Description:** Construir la lógica de split principal `70/15/15` por episodios completos, estratificada por buckets experimentales y con persistencia de la decisión para reproducibilidad. Esta tarea debe impedir leakage temporal entre train, validation y test.

**Acceptance criteria:**
- [ ] La unidad mínima de split es el episodio completo.
- [ ] La partición es determinista a partir de una seed fija y conserva buckets experimentales comparables.
- [ ] Toda muestra o ventana hereda el split del episodio del que proviene.

**Verification:**
- [ ] Tests pass: pruebas de estratificación, determinismo y no contaminación entre splits.
- [ ] Manual check: dos ejecuciones con la misma seed producen la misma partición.

**Dependencies:** Task 2

**Files likely touched:**
- `src/...` módulo de split
- `tests/...` pruebas de split

**Estimated scope:** Medium: 3-5 files

## Task 5: Implementar windowing temporal para MLP

**Description:** Construir la generación de ventanas apiladas para MLP con la configuración base acordada de 30 pasos y stride por defecto de 10 en train/validation. La salida debe quedar lista para batching estándar y compatible con el esquema de features.

**Acceptance criteria:**
- [ ] El pipeline genera ventanas MLP sin cruzar episodios.
- [ ] Cada muestra MLP concatena correctamente la historia temporal en un vector 1D.
- [ ] La configuración de ventana y stride queda registrada en metadatos reutilizables.

**Verification:**
- [ ] Tests pass: pruebas de tamaño de ventana, stride y dimensionalidad final.
- [ ] Manual check: una ventana de ejemplo contiene exactamente 30 pasos concatenados.

**Dependencies:** Task 3, Task 4

**Files likely touched:**
- `src/...` módulo de windowing
- `tests/...` pruebas de windowing MLP

**Estimated scope:** Small: 1-2 files

## Task 6: Implementar windowing secuencial para GRU/LSTM

**Description:** Añadir generación de secuencias temporales para modelos recurrentes con tamaños base de 100 y 150 pasos, sin mezclar episodios ni asumir entrenamiento stateful entre batches.

**Acceptance criteria:**
- [ ] El pipeline genera secuencias válidas para GRU y LSTM con tamaños configurables.
- [ ] Las secuencias mantienen formato temporal consistente y no se aplanan como en MLP.
- [ ] La configuración temporal usada por cada arquitectura queda persistida en metadatos.

**Verification:**
- [ ] Tests pass: pruebas de forma, longitud y límites de episodio para secuencias recurrentes.
- [ ] Manual check: una secuencia ejemplo conserva el orden temporal correcto.

**Dependencies:** Task 3, Task 4

**Files likely touched:**
- `src/...` módulo de windowing recurrente
- `tests/...` pruebas de secuencias

**Estimated scope:** Small: 1-2 files

### Checkpoint: Dataset Ready

- [ ] Las tareas 4-6 dejan listo el dataset completo con splits y ventanas
- [ ] Se puede producir input válido tanto para MLP como para GRU/LSTM
- [ ] No existe leakage entre episodios o entre splits

### Phase 3: MLP End-to-End Slice

- [ ] Task 7: Implementar configuración y entrenamiento reproducible de MLP
- [ ] Task 8: Implementar checkpoint auditable y carga de inferencia para MLP
- [ ] Task 9: Integrar la MLP en el runner y ejecutar benchmark mínimo

## Task 7: Implementar configuración y entrenamiento reproducible de MLP

**Description:** Crear el primer pipeline completo de entrenamiento neuronal usando la MLP baseline, con normalización persistida, validación reproducible y salida de métricas offline mínimas sobre train/validation.

**Acceptance criteria:**
- [ ] La MLP puede entrenarse con el dataset oficial y producir resultados reproducibles.
- [ ] Las estadísticas de normalización se calculan solo sobre train y se guardan junto al modelo.
- [ ] El proceso deja historial suficiente para comparar runs de entrenamiento.

**Verification:**
- [ ] Tests pass: pruebas de entrenamiento mínimo o smoke tests del pipeline.
- [ ] Manual check: un entrenamiento corto produce checkpoint y resumen offline válidos.

**Dependencies:** Task 5

**Files likely touched:**
- `src/...` módulo de entrenamiento MLP
- `tests/...` pruebas smoke de training
- configuración o scripts de ejecución

**Estimated scope:** Medium: 3-5 files

## Task 8: Implementar checkpoint auditable y carga de inferencia para MLP

**Description:** Añadir el formato de checkpoint y el adaptador de carga que reconstruye el modelo, la normalización y la configuración temporal necesarias para inferencia consistente dentro del simulador.

**Acceptance criteria:**
- [ ] El checkpoint conserva arquitectura, ventana, modo de features y normalización.
- [ ] El adaptador puede cargar el checkpoint y reconstruir una política lista para inferencia.
- [ ] La salida del adaptador cumple el contrato de comando del simulador.

**Verification:**
- [ ] Tests pass: pruebas de round-trip guardar/cargar checkpoint.
- [ ] Manual check: la inferencia sobre un ejemplo produce un mando válido.

**Dependencies:** Task 7

**Files likely touched:**
- `src/...` módulo de checkpoint
- `src/...` adaptador de inferencia
- `tests/...` pruebas de carga

**Estimated scope:** Medium: 3-5 files

## Task 9: Integrar la MLP en el runner y ejecutar benchmark mínimo

**Description:** Enchufar la MLP entrenada al runner a través del contrato oficial y ejecutar una batería corta de escenarios homogéneos frente al baseline clásico para demostrar el primer slice extremo a extremo de vuelo neuronal.

**Acceptance criteria:**
- [ ] El runner acepta la política MLP sin caminos especiales ni cambios de contrato.
- [ ] La MLP ejecuta vuelos completos con resultados persistidos.
- [ ] Existe una comparación mínima clásica vs MLP sobre escenarios homogéneos.

**Verification:**
- [ ] Tests pass: prueba de integración del controlador MLP con el runner.
- [ ] Manual check: al menos un benchmark corto genera artefactos comparables.

**Dependencies:** Task 8

**Files likely touched:**
- `src/...` integración con runner
- `tests/...` prueba de integración end-to-end
- scripts o config de benchmark

**Estimated scope:** Medium: 3-5 files

### Checkpoint: First Neural Flight

- [ ] Las tareas 7-9 dejan un camino completo dataset -> entrenamiento -> checkpoint -> runner
- [ ] Existe benchmark mínimo reproducible clásico vs MLP
- [ ] El sistema sigue funcionando con el contrato actual del simulador

### Phase 4: Recurrent Models

- [ ] Task 10: Implementar entrenamiento GRU end-to-end
- [ ] Task 11: Implementar entrenamiento LSTM end-to-end
- [ ] Task 12: Integrar GRU/LSTM en el runner y consolidar benchmarking principal

## Task 10: Implementar entrenamiento GRU end-to-end

**Description:** Añadir el pipeline completo para GRU usando las secuencias definidas, modo stateless por batch y el mismo esquema de features por instante ya validado para MLP.

**Acceptance criteria:**
- [ ] La GRU entrena con secuencias válidas y checkpoints auditables.
- [ ] El pipeline comparte normalización y semántica de input con el resto de arquitecturas.
- [ ] La configuración recurrente queda registrada para reproducibilidad.

**Verification:**
- [ ] Tests pass: smoke tests de entrenamiento y carga de GRU.
- [ ] Manual check: una run corta produce checkpoint funcional.

**Dependencies:** Task 6, Task 8

**Files likely touched:**
- `src/...` módulo de entrenamiento recurrente
- `tests/...` pruebas GRU

**Estimated scope:** Medium: 3-5 files

## Task 11: Implementar entrenamiento LSTM end-to-end

**Description:** Extender el pipeline recurrente a LSTM manteniendo la misma familia de features, la misma semántica de target y la configuración temporal cerrada para esta arquitectura.

**Acceptance criteria:**
- [ ] La LSTM entrena con secuencias válidas y checkpoints auditables.
- [ ] La LSTM puede recargarse en inferencia con la misma política temporal usada en entrenamiento.
- [ ] La implementación no introduce una representación distinta para la misma tarea.

**Verification:**
- [ ] Tests pass: smoke tests de entrenamiento y carga de LSTM.
- [ ] Manual check: una run corta produce checkpoint funcional.

**Dependencies:** Task 6, Task 8

**Files likely touched:**
- `src/...` módulo de entrenamiento recurrente
- `tests/...` pruebas LSTM

**Estimated scope:** Small: 1-2 files

## Task 12: Integrar GRU/LSTM en el runner y consolidar benchmarking principal

**Description:** Completar la integración de inferencia para GRU y LSTM dentro del runner y ejecutar una batería principal homogénea que produzca resultados comparables para MLP, GRU y LSTM frente al baseline clásico.

**Acceptance criteria:**
- [ ] GRU y LSTM pueden volar en el runner bajo el mismo contrato que la MLP.
- [ ] La batería principal produce resultados persistidos y comparables para las tres arquitecturas.
- [ ] La medición de tiempo de inferencia queda registrada en CPU como caso base.

**Verification:**
- [ ] Tests pass: pruebas de integración de controladores recurrentes con runner.
- [ ] Manual check: la batería principal genera resultados para las tres arquitecturas.

**Dependencies:** Task 10, Task 11

**Files likely touched:**
- `src/...` integración de inferencia recurrente
- `tests/...` pruebas end-to-end
- scripts o config de benchmark principal

**Estimated scope:** Medium: 3-5 files

### Checkpoint: Main Model Battery

- [ ] Las tareas 10-12 dejan operativas MLP, GRU y LSTM en el simulador
- [ ] Existe batería principal comparable entre baseline clásico y modelos neuronales
- [ ] Los checkpoints y metadatos son reutilizables

### Phase 5: Metrics And Reporting

- [ ] Task 13: Ampliar métricas cuantitativas de comparación
- [ ] Task 14: Generar tabla consolidada y figuras comparativas
- [ ] Task 15: Definir selector reproducible del mejor modelo

## Task 13: Ampliar métricas cuantitativas de comparación

**Description:** Extender la capa de métricas para cubrir la batería comprometida en el PRD, manteniendo explícita la diferencia entre el estado usado para controlar y el estado usado para evaluar.

**Acceptance criteria:**
- [ ] La evaluación soporta las métricas principales acordadas para comparación homogénea.
- [ ] Las métricas reflejan explícitamente la fuente del estado de evaluación.
- [ ] La implementación permite comparar resultados persistidos sin cálculo manual externo.

**Verification:**
- [ ] Tests pass: pruebas sintéticas de métricas y comparaciones homogéneas.
- [ ] Manual check: un conjunto pequeño produce valores coherentes y legibles.

**Dependencies:** Task 9, Task 12

**Files likely touched:**
- `src/...` módulo de métricas
- `tests/...` pruebas de métricas

**Estimated scope:** Medium: 3-5 files

## Task 14: Generar tabla consolidada y figuras comparativas

**Description:** Construir la capa de reporting que toma resultados persistidos de la batería principal y genera una tabla consolidada y figuras suficientes para análisis cuantitativo y visual en el TFG.

**Acceptance criteria:**
- [ ] Existe una tabla comparativa clásico vs MLP vs GRU vs LSTM generada desde resultados persistidos.
- [ ] Existen figuras comparativas de trayectoria, error temporal y comportamiento del control.
- [ ] El reporte es legible y reutilizable para documentación académica.

**Verification:**
- [ ] Manual check: el reporte se puede abrir e interpretar sin procesamiento manual extra.
- [ ] Manual check: las figuras corresponden a la batería principal y no a muestras aisladas.

**Dependencies:** Task 13

**Files likely touched:**
- `src/...` módulo de reporting
- configuración o scripts de reporte
- documentación de resultados

**Estimated scope:** Medium: 3-5 files

## Task 15: Definir selector reproducible del mejor modelo

**Description:** Formalizar el criterio de decisión que combina precisión, suavidad, robustez e inferencia, para que la elección del candidato final no dependa de juicio informal posterior.

**Acceptance criteria:**
- [ ] Existe una regla explícita y reproducible para seleccionar el mejor modelo de la batería principal.
- [ ] La regla puede aplicarse automáticamente a resultados persistidos.
- [ ] La salida deja trazabilidad suficiente de por qué un modelo fue elegido.

**Verification:**
- [ ] Manual check: la regla aplicada a resultados ejemplo selecciona un candidato de forma transparente.
- [ ] Revisión manual: el criterio es coherente con el PRD.

**Dependencies:** Task 14

**Files likely touched:**
- `src/...` selector o lógica de ranking
- documentación de decisión

**Estimated scope:** Small: 1-2 files

### Checkpoint: Decision-Ready Results

- [ ] Las tareas 13-15 dejan resultados cuantitativos y visuales listos para decidir
- [ ] El mejor candidato puede seleccionarse de forma reproducible
- [ ] La evidencia es reutilizable para la memoria del TFG

### Phase 6: Robustness And Delivery

- [ ] Task 16: Implementar batería OOD de robustez
- [ ] Task 17: Ejecutar análisis metodológico final y límites
- [ ] Task 18: Empaquetar reproducibilidad y entrega documental

## Task 16: Implementar batería OOD de robustez

**Description:** Añadir una batería separada de robustez fuera de distribución que reutilice el pipeline principal pero evalúe condiciones más duras o no vistas, sin contaminar la selección principal del modelo.

**Acceptance criteria:**
- [ ] La batería OOD está separada del split principal y no se usa para tuning.
- [ ] La batería reutiliza el mismo contrato de ejecución y reporting que la evaluación principal.
- [ ] Los resultados permiten detectar degradación bajo condiciones no vistas o más severas.

**Verification:**
- [ ] Manual check: la batería OOD usa escenarios distintos a los del split principal.
- [ ] Manual check: genera artefactos separados y trazables.

**Dependencies:** Task 15

**Files likely touched:**
- configuración o scripts de robustness
- `src/...` benchmark o reporting OOD
- documentación de evaluación

**Estimated scope:** Medium: 3-5 files

## Task 17: Ejecutar análisis metodológico final y límites

**Description:** Redactar y consolidar el análisis de riesgos, simplificaciones y límites metodológicos de la Fase 2 a partir de los resultados obtenidos, separando claramente conclusiones dentro de distribución y conclusiones exploratorias de robustez.

**Acceptance criteria:**
- [ ] El análisis distingue explícitamente qué resultados pertenecen a la batería principal y cuáles a OOD.
- [ ] Quedan documentados límites de imitation learning, observabilidad y alcance de robustez.
- [ ] El documento final deja una recomendación clara para la siguiente fase del TFG.

**Verification:**
- [ ] Revisión manual: el análisis es consistente con el PRD y los resultados obtenidos.
- [ ] Revisión manual: no se hacen afirmaciones sim-to-real no justificadas.

**Dependencies:** Task 16

**Files likely touched:**
- `docs/...`
- resultados o memoria de fase

**Estimated scope:** Small: 1-2 files

## Task 18: Empaquetar reproducibilidad y entrega documental

**Description:** Cerrar la Fase 2 organizando artefactos, rutas de reproducción, referencias a escenarios, checkpoints y tablas finales, de modo que otra sesión o persona pueda repetir el benchmark principal y entender la arquitectura seleccionada.

**Acceptance criteria:**
- [ ] Los artefactos clave quedan organizados y referenciados para repetición del benchmark principal.
- [ ] Cada resultado relevante referencia escenario, seed, checkpoint, ventana y modo de features.
- [ ] La documentación final deja claro qué arquitectura fue seleccionada y por qué.

**Verification:**
- [ ] Manual check: otra persona puede seguir la documentación para repetir el flujo principal.
- [ ] Revisión manual: la entrega final es utilizable para memoria del TFG y continuidad técnica.

**Dependencies:** Task 17

**Files likely touched:**
- `docs/...`
- `plans/...`
- scripts o notas de reproducción

**Estimated scope:** Small: 1-2 files

### Checkpoint: Complete

- [ ] Todas las tareas completadas dejan la Fase 2 ejecutable y documentada
- [ ] El benchmark principal y la batería OOD son reproducibles
- [ ] Existe candidato final seleccionado con evidencia cuantitativa, visual y metodológica

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Leakage entre episodios o splits | High | Fijar split por episodio desde temprano y probarlo con tests dedicados |
| Divergencia entre features de entrenamiento e inferencia | High | Formalizar el contrato de dataset antes de entrenar ningún modelo |
| Sobrecargar una sola tarea con dataset, entrenamiento e integración | Medium | Mantener tasks S/M y checkpoints frecuentes |
| Comparaciones injustas entre arquitecturas por cambiar representación | High | Mantener fijo el mismo esquema de features y targets en toda la batería principal |
| Métricas insuficientes para decidir el mejor modelo | Medium | Ampliar métricas antes del cierre de resultados |
| Conclusiones exageradas sobre robustez o sim-to-real | High | Separar evaluación principal y batería OOD, y documentar límites explícitamente |

## Open Questions

- Si durante la implementación aparece una familia de trayectorias adicional especialmente relevante para el TFG, habrá que decidir si entra en la batería principal o solo en robustez.
- Si el coste de entrenamiento recurrente resulta alto, habrá que decidir si reducir tamaño de ventana o simplificar la exploración de hiperparámetros.
- Si más adelante se implementa una perturbación explícita de degradación equivalente a batería, habrá que decidir si entra en OOD o en una futura extensión metodológica.
