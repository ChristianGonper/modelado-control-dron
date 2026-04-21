# Implementation Plan: Flujo Operable De Control Neuronal

## Overview

Este breakdown convierte el plan del flujo operable de control neuronal en tareas pequenas, verificables y ordenadas por dependencia. El objetivo no es rehacer el pipeline neuronal existente, sino exponerlo como una experiencia clara y reproducible desde CLI para dataset, entrenamiento, benchmark, reporte e inspeccion de artefactos para `MLP`, `GRU` y `LSTM`.

## Architecture Decisions

- La implementacion reutiliza los modulos internos ya existentes de dataset, entrenamiento, benchmark y reporting antes de introducir logica nueva.
- La superficie oficial de uso vive bajo el mismo comando raiz del simulador y no en scripts Python ad hoc externos al producto.
- El contrato actual del controlador se mantiene intacto: los modelos siguen entrando al runner como controladores validos y emiten el mismo tipo de mando.
- La convencion metodologica se mantiene fija y visible: el control usa `observed_state` y la evaluacion usa `true_state`.
- Los artefactos deben quedar separados por etapa y por finalidad: dataset, checkpoints, benchmark principal, benchmark OOD y reportes.
- El benchmark principal y el benchmark OOD siguen siendo flujos distintos, con interpretacion distinta y sin mezclar seleccion con robustez exploratoria.

## Task List

### Phase 1: CLI Foundation

- [x] Task 1: Inventariar capacidades internas reutilizables para el flujo CLI
- [x] Task 2: Disenar la superficie CLI neuronal y el contrato de argumentos
- [x] Task 3: Definir la convencion de artefactos y metadatos de ejecucion

## Task 1: Inventariar capacidades internas reutilizables para el flujo CLI

**Description:** Revisar y consolidar que partes del repositorio ya cubren dataset, entrenamiento, benchmarking, reporting e inspeccion de artefactos para evitar duplicacion. Esta tarea fija el mapa de reutilizacion sobre el que se apoyara toda la capa operable.

**Acceptance criteria:**
- [x] Existe un inventario escrito de capacidades internas ya disponibles para dataset, `MLP`, `GRU`, `LSTM`, benchmark y reporting.
- [x] El inventario identifica huecos reales de operabilidad frente a la superficie publica actual del simulador.
- [x] Queda claro que partes deben exponerse por CLI y que partes solo necesitan adaptacion ligera.

**Verification:**
- [x] Revision manual: el inventario cubre `app.py`, `dataset`, `control`, `benchmark`, `reporting` y pruebas relevantes.
- [x] Revision manual: el inventario distingue entre codigo reutilizable, codigo que necesita adaptador y funcionalidades todavia no expuestas.

**Dependencies:** None

**Files likely touched:**
- `plans/control-neuronal-operable-task-breakdown.md`
- `plans/control-neuronal-operable-plan.md`
- notas de apoyo en `docs/` si hacen falta
- `docs/software/control-neuronal-cli-foundation.md`
- `docs/decisions/ADR-018-neural-cli-foundation-and-artifact-convention.md`

**Estimated scope:** Small: 1-2 files

## Task 2: Disenar la superficie CLI neuronal y el contrato de argumentos

**Description:** Definir la estructura de comandos del flujo neuronal dentro del comando raiz del simulador, incluyendo subcomandos, argumentos comunes, argumentos especificos por arquitectura y errores esperados. Esta tarea fija la API humana del producto antes de implementarla.

**Acceptance criteria:**
- [x] Existe un diseno claro de subcomandos para dataset, entrenamiento individual, entrenamiento comparativo, benchmark principal, benchmark OOD, reporte e inspeccion.
- [x] Los argumentos comunes y especificos por arquitectura quedan definidos sin ambiguedad.
- [x] Quedan listados los errores de uso que deben validarse pronto desde CLI.

**Verification:**
- [x] Revision manual: la superficie CLI cubre el flujo completo del PRD sin exigir scripts externos.
- [x] Revision manual: la nomenclatura de argumentos es consistente entre arquitecturas y etapas.

**Dependencies:** Task 1

**Files likely touched:**
- `plans/control-neuronal-operable-task-breakdown.md`
- documentacion de apoyo en `docs/`
- `docs/software/control-neuronal-cli-foundation.md`
- `docs/decisions/ADR-018-neural-cli-foundation-and-artifact-convention.md`

**Estimated scope:** Small: 1-2 files

## Task 3: Definir la convencion de artefactos y metadatos de ejecucion

**Description:** Diseñar como se organizan carpetas, nombres y metadatos persistidos para que cada etapa del flujo deje salidas trazables y encadenables. Esta tarea debe evitar desde el principio mezcla entre dataset, checkpoints, benchmark y reportes.

**Acceptance criteria:**
- [x] Existe una convencion escrita para rutas y nombres de artefactos por etapa.
- [x] La convencion deja claro que metadatos minimos deben persistirse en cada salida para trazabilidad.
- [x] El diseno distingue benchmark principal y benchmark OOD tambien a nivel de artefactos.

**Verification:**
- [x] Revision manual: la convencion permite localizar un dataset, un checkpoint y un reporte sin ambiguedad.
- [x] Revision manual: la convencion es compatible con el estilo actual del repositorio y con futuras campañas experimentales.

**Dependencies:** Task 2

**Files likely touched:**
- `plans/control-neuronal-operable-task-breakdown.md`
- `docs/` o notas de convencion operativa
- `docs/software/control-neuronal-cli-foundation.md`
- `docs/decisions/ADR-018-neural-cli-foundation-and-artifact-convention.md`

**Estimated scope:** Small: 1-2 files

### Checkpoint: CLI Foundation

- [x] Las tareas 1-3 dejan clara la base de reutilizacion, la superficie CLI y la convencion de artefactos
- [x] El flujo operable ya tiene una API humana definida antes de escribir implementacion
- [x] No hay ambiguedad sobre entradas, salidas ni metadatos de cada etapa

### Phase 2: Dataset Slice

- [ ] Task 4: Implementar el comando CLI de dataset sobre telemetria persistida
- [ ] Task 5: Persistir manifiesto y trazabilidad del dataset generado
- [ ] Task 6: Cubrir el flujo de dataset con pruebas CLI y validaciones de error

## Task 4: Implementar el comando CLI de dataset sobre telemetria persistida

**Description:** Exponer por CLI la preparacion o registro de dataset a partir de telemetria persistida reutilizando el extractor y los contratos ya existentes. Esta tarea debe dejar un primer slice operable completo y reusable por el resto de fases.

**Acceptance criteria:**
- [ ] Existe un comando CLI que toma uno o varios artefactos de telemetria y genera o registra un dataset utilizable.
- [ ] El comando reutiliza el pipeline oficial de extraccion en vez de duplicarlo.
- [ ] La salida deja un artefacto reconocible para dataset dentro de la convencion acordada.

**Verification:**
- [ ] Tests pass: pruebas del comando CLI de dataset con entradas pequenas y deterministas.
- [ ] Manual check: una ejecucion corta genera un dataset trazable y reutilizable por etapas posteriores.

**Dependencies:** Task 3

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/dataset/`
- `tests/` pruebas de CLI o dataset

**Estimated scope:** Medium: 3-5 files

## Task 5: Persistir manifiesto y trazabilidad del dataset generado

**Description:** Añadir una salida legible y estable para describir como se genero cada dataset desde CLI, incluyendo origenes, seeds, politica de split y modo de features. Esta tarea convierte el dataset en un artefacto auditable y no solo en una estructura interna.

**Acceptance criteria:**
- [ ] Cada dataset generado por CLI deja un manifiesto o resumen persistido con configuracion efectiva.
- [ ] El manifiesto identifica telemetria de origen, semillas, politica de split y metadatos necesarios para reproducibilidad.
- [ ] La salida sigue la convencion de artefactos definida en la fase anterior.

**Verification:**
- [ ] Tests pass: pruebas de persistencia y lectura del manifiesto de dataset.
- [ ] Manual check: el manifiesto permite reconstruir de forma clara que comando produjo el dataset.

**Dependencies:** Task 4

**Files likely touched:**
- `src/simulador_multirotor/dataset/`
- `src/simulador_multirotor/app.py`
- `tests/` pruebas de persistencia

**Estimated scope:** Small: 1-2 files

## Task 6: Cubrir el flujo de dataset con pruebas CLI y validaciones de error

**Description:** Endurecer la experiencia de uso del comando de dataset validando errores comunes y dejando pruebas de comportamiento observable de la CLI. Esta tarea protege la primera etapa del flujo antes de añadir entrenamiento y benchmark.

**Acceptance criteria:**
- [ ] La CLI falla con mensajes claros ante rutas inexistentes, entradas vacias o combinaciones invalidas.
- [ ] Existen pruebas de humo del recorrido feliz y de errores principales del comando de dataset.
- [ ] El sistema queda en estado consistente cuando el comando falla antes de generar artefactos.

**Verification:**
- [ ] Tests pass: suite dirigida a CLI de dataset y errores de validacion.
- [ ] Manual check: los mensajes de error permiten corregir el uso sin inspeccionar codigo.

**Dependencies:** Task 5

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `tests/` pruebas CLI

**Estimated scope:** Small: 1-2 files

### Checkpoint: Dataset Ready

- [ ] Las tareas 4-6 dejan un comando de dataset completo, trazable y robusto
- [ ] El dataset ya puede producirse desde CLI sin scripts externos
- [ ] La base del flujo operable queda protegida por pruebas de comportamiento

### Phase 3: Training And Checkpoint Inspection

- [ ] Task 7: Implementar el comando CLI de entrenamiento individual por arquitectura
- [ ] Task 8: Persistir resumen legible y configuracion efectiva de checkpoints
- [ ] Task 9: Implementar el comando CLI de inspeccion de checkpoints

## Task 7: Implementar el comando CLI de entrenamiento individual por arquitectura

**Description:** Exponer por CLI el entrenamiento individual de `MLP`, `GRU` y `LSTM` usando el dataset oficial, con argumentos comunes, defaults reproducibles y overrides especificos por arquitectura. Esta tarea debe cerrar el primer tramo fuerte del flujo operable de modelo individual.

**Acceptance criteria:**
- [ ] Existe un comando CLI que entrena una arquitectura concreta usando un dataset ya preparado.
- [ ] El comando soporta parametros comunes y parametros especificos por arquitectura sin nomenclatura ambigua.
- [ ] La implementacion reutiliza los pipelines de entrenamiento existentes en lugar de reimplementarlos.

**Verification:**
- [ ] Tests pass: pruebas de humo del entrenamiento individual para al menos una arquitectura densa y una recurrente.
- [ ] Manual check: una ejecucion corta produce un checkpoint valido desde CLI.

**Dependencies:** Task 6

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/control/`
- `tests/` pruebas CLI de entrenamiento

**Estimated scope:** Medium: 3-5 files

## Task 8: Persistir resumen legible y configuracion efectiva de checkpoints

**Description:** Asegurar que cada entrenamiento por CLI deje no solo el checkpoint binario, sino tambien una salida humana legible con arquitectura, ventana, features, normalizacion y parametros efectivos. Esta tarea hace auditable el resultado del entrenamiento.

**Acceptance criteria:**
- [ ] Cada run de entrenamiento persiste checkpoint y resumen legible asociado.
- [ ] El resumen deja visibles arquitectura, ventana, modo de features, seed, normalizacion y metricas basicas.
- [ ] Los artefactos de checkpoint siguen la convencion establecida en la fase 1.

**Verification:**
- [ ] Tests pass: pruebas de persistencia del resumen de checkpoint para `MLP` y recurrentes.
- [ ] Manual check: el resumen puede leerse sin cargar el checkpoint desde Python.

**Dependencies:** Task 7

**Files likely touched:**
- `src/simulador_multirotor/control/`
- `src/simulador_multirotor/app.py`
- `tests/` pruebas de checkpoints

**Estimated scope:** Small: 1-2 files

## Task 9: Implementar el comando CLI de inspeccion de checkpoints

**Description:** Añadir una capacidad de inspeccion rapida por CLI que lea un checkpoint existente y muestre los metadatos relevantes para auditoria experimental. Esta tarea debe permitir entender un modelo entrenado sin escribir codigo auxiliar.

**Acceptance criteria:**
- [ ] Existe un comando CLI que inspecciona checkpoints de `MLP`, `GRU` y `LSTM`.
- [ ] La inspeccion muestra arquitectura, modo de features, ventana, seed, normalizacion y procedencia suficiente.
- [ ] El comando falla con errores claros si el checkpoint es invalido o no compatible.

**Verification:**
- [ ] Tests pass: pruebas del comando de inspeccion sobre checkpoints validos e invalidos.
- [ ] Manual check: la salida de inspeccion es util para auditoria rapida y lectura humana.

**Dependencies:** Task 8

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/control/`
- `tests/` pruebas CLI de inspeccion

**Estimated scope:** Small: 1-2 files

### Checkpoint: Training Operable

- [ ] Las tareas 7-9 dejan entrenamiento individual e inspeccion de checkpoints completamente expuestos por CLI
- [ ] `MLP`, `GRU` y `LSTM` ya pueden operarse de forma individual sin scripts externos
- [ ] Cada checkpoint entrenado queda auditado y entendible por artefactos legibles

### Phase 4: Main Benchmark Slice

- [ ] Task 10: Implementar el flujo CLI de comparativa principal entre las tres arquitecturas
- [ ] Task 11: Persistir benchmark principal con trazas, tiempos y configuracion efectiva
- [ ] Task 12: Cubrir el benchmark principal con pruebas end-to-end de CLI

## Task 10: Implementar el flujo CLI de comparativa principal entre las tres arquitecturas

**Description:** Exponer por CLI un recorrido completo que tome checkpoints ya existentes o los resuelva por convencion, cargue `MLP`, `GRU` y `LSTM` en el simulador y ejecute el benchmark principal frente al baseline clasico. Esta tarea debe demostrar el valor experimental del flujo operable.

**Acceptance criteria:**
- [ ] Existe un comando CLI para lanzar el benchmark principal entre baseline, `MLP`, `GRU` y `LSTM`.
- [ ] El comando reutiliza el benchmark oficial ya existente y no crea una via paralela de comparacion.
- [ ] La ejecucion deja un artefacto principal de benchmark reconocible y reutilizable.

**Verification:**
- [ ] Tests pass: prueba de humo del benchmark principal desde CLI.
- [ ] Manual check: una ejecucion corta produce resultados comparables para las tres arquitecturas.

**Dependencies:** Task 9

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/benchmark.py`
- `tests/` pruebas CLI de benchmark

**Estimated scope:** Medium: 3-5 files

## Task 11: Persistir benchmark principal con trazas, tiempos y configuracion efectiva

**Description:** Asegurar que el benchmark principal expuesto por CLI deja todos los artefactos relevantes para analisis posterior: resultados por escenario, trazas, tiempos de inferencia y metadatos suficientes de configuracion. Esta tarea prepara el terreno del reporte final.

**Acceptance criteria:**
- [ ] El benchmark principal persiste trazas comparativas, tiempos de inferencia y resultados por escenario.
- [ ] El artefacto final deja claro que checkpoints y configuracion experimental se usaron.
- [ ] La salida queda separada de los artefactos de entrenamiento y de OOD.

**Verification:**
- [ ] Tests pass: pruebas de presencia y forma basica de los artefactos del benchmark principal.
- [ ] Manual check: a partir del artefacto puede reconstruirse que comando y que modelos participaron.

**Dependencies:** Task 10

**Files likely touched:**
- `src/simulador_multirotor/benchmark.py`
- `src/simulador_multirotor/app.py`
- `tests/` pruebas de persistencia

**Estimated scope:** Small: 1-2 files

## Task 12: Cubrir el benchmark principal con pruebas end-to-end de CLI

**Description:** Cerrar la slice principal con pruebas de comportamiento observable que cubran el recorrido dataset o checkpoint -> benchmark -> artefactos persistidos. Esta tarea protege el primer flujo comparativo completo del sistema.

**Acceptance criteria:**
- [ ] Existen pruebas end-to-end de CLI para la comparativa principal con checkpoints validos.
- [ ] Existen pruebas de error para rutas faltantes o combinaciones invalidas de checkpoints.
- [ ] La fase deja al menos un camino verificable de extremo a extremo para comparativa principal.

**Verification:**
- [ ] Tests pass: suite dirigida al benchmark principal desde CLI.
- [ ] Manual check: el flujo comparativo puede demostrarse sin pasos manuales intermedios.

**Dependencies:** Task 11

**Files likely touched:**
- `tests/` pruebas end-to-end CLI
- `src/simulador_multirotor/app.py`

**Estimated scope:** Small: 1-2 files

### Checkpoint: Main Benchmark Ready

- [ ] Las tareas 10-12 dejan operable la comparativa principal de `MLP`, `GRU` y `LSTM` frente al baseline clasico
- [ ] El benchmark principal ya es reproducible desde CLI y persistente
- [ ] La salida contiene metadatos, tiempos y trazas suficientes para analisis posterior

### Phase 5: OOD And Reporting

- [ ] Task 13: Implementar el flujo CLI separado para benchmark OOD
- [ ] Task 14: Implementar el flujo CLI de reporte final sobre benchmark principal
- [ ] Task 15: Cubrir separacion metodologica y generacion de reportes con pruebas y mensajes visibles

## Task 13: Implementar el flujo CLI separado para benchmark OOD

**Description:** Exponer por CLI la bateria OOD como una ruta independiente del benchmark principal, reutilizando los mismos contratos pero separando claramente sus artefactos y su interpretacion. Esta tarea cierra la parte operable de robustez sin mezclarla con seleccion principal.

**Acceptance criteria:**
- [ ] Existe un comando CLI especifico para benchmark OOD.
- [ ] El comando persiste artefactos separados de los del benchmark principal.
- [ ] La ayuda y la salida del comando dejan claro que OOD no debe usarse para tuning ni seleccion.

**Verification:**
- [ ] Tests pass: prueba de humo del benchmark OOD y de separacion de artefactos.
- [ ] Manual check: un usuario puede distinguir benchmark principal y OOD solo leyendo la CLI y las rutas generadas.

**Dependencies:** Task 12

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/benchmark.py`
- `tests/` pruebas OOD

**Estimated scope:** Small: 1-2 files

## Task 14: Implementar el flujo CLI de reporte final sobre benchmark principal

**Description:** Exponer por CLI la generacion de reporte final reutilizando la capa de reporting ya existente. Esta tarea debe transformar los resultados del benchmark principal en tabla consolidada, seleccion de modelo y figuras listas para analisis academico.

**Acceptance criteria:**
- [ ] Existe un comando CLI que genera el reporte final a partir de un benchmark principal persistido.
- [ ] El reporte incluye tabla consolidada, seleccion del mejor modelo y figuras comparativas.
- [ ] La salida deja visible la politica metodologica de observacion para control y estado verdadero para evaluacion.

**Verification:**
- [ ] Tests pass: prueba de humo del reporte final desde CLI.
- [ ] Manual check: el reporte resultante puede leerse como resumen academico de la comparativa principal.

**Dependencies:** Task 11

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/reporting.py`
- `tests/` pruebas de reporting CLI

**Estimated scope:** Small: 1-2 files

## Task 15: Cubrir separacion metodologica y generacion de reportes con pruebas y mensajes visibles

**Description:** Endurecer la ultima capa operable asegurando que CLI, artefactos y mensajes de usuario reflejan correctamente la separacion entre benchmark principal, OOD y reporte final. Esta tarea protege el significado metodologico del flujo, no solo su ejecucion tecnica.

**Acceptance criteria:**
- [ ] Existen pruebas que validan la separacion observable entre benchmark principal, OOD y reporte final.
- [ ] Los mensajes CLI y ayudas visibles explicitan la frontera metodologica principal vs OOD.
- [ ] El recorrido completo deja un conjunto final de artefactos legibles y no ambiguos.

**Verification:**
- [ ] Tests pass: suite dirigida a separacion metodologica y artefactos finales.
- [ ] Manual check: un tutor o usuario nuevo puede interpretar correctamente el flujo solo leyendo la salida y la ayuda CLI.

**Dependencies:** Task 13, Task 14

**Files likely touched:**
- `src/simulador_multirotor/app.py`
- `tests/` pruebas finales de CLI
- `docs/` guia operativa si hace falta

**Estimated scope:** Small: 1-2 files

### Checkpoint: Complete

- [ ] Todas las tareas dejan operativo el flujo neuronal desde CLI para dataset, entrenamiento, benchmark principal, benchmark OOD, inspeccion y reporte
- [ ] Los artefactos quedan trazables, separados por etapa y consistentes con la metodologia del proyecto
- [ ] El flujo completo puede demostrarse y entenderse sin scripts Python externos ni conocimiento tacito del codigo

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Duplicar logica ya existente al exponer la CLI | High | Inventariar primero y reutilizar modulos internos antes de escribir adaptadores nuevos |
| Disenar una CLI incoherente entre arquitecturas y etapas | High | Fijar primero el contrato de argumentos y revisarlo como API humana estable |
| Mezclar artefactos de dataset, entrenamiento, benchmark y reportes | High | Definir una convencion unica de rutas y manifiestos antes de implementar persistencia |
| Dejar visible solo la ejecucion tecnica y no la frontera metodologica principal vs OOD | High | Incluir mensajes, ayudas y pruebas especificas para esa separacion |
| Introducir pruebas demasiado lentas por depender de entrenamiento completo | Medium | Usar datasets pequenos, escenarios cortos y smoke tests orientados a comportamiento |
| Hacer el flujo demasiado flexible y dificil de usar | Medium | Priorizar recorrido minimo y presets razonables antes de ampliar configurabilidad |

## Open Questions

- Si el flujo comparativo debe poder entrenar automaticamente los tres modelos en una sola orden o limitarse inicialmente a consumir checkpoints ya generados por comandos individuales.
- Si el dataset operable debe persistir episodios serializados completos o solo un manifiesto que apunte a telemetria y configuracion efectiva.
- Si conviene anadir un comando agregado de recorrido completo despues de estabilizar primero dataset, entrenamiento, benchmark y reporte como etapas separadas.

## Verification

- [ ] Every task has acceptance criteria
- [ ] Every task has a verification step
- [ ] Task dependencies are identified and ordered correctly
- [ ] No task touches more than ~5 files
- [ ] Checkpoints exist between major phases
- [ ] The human has reviewed and approved the plan
