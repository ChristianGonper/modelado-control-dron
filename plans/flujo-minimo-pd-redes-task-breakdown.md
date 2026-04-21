# Implementation Plan: Flujo Minimo Repetible Desde PD Hasta Redes

## Overview

Este breakdown convierte el PRD del flujo minimo PD -> redes en tareas pequenas, ordenadas por dependencia y pensadas como vertical slices reales. La idea es cerrar primero la baseline fisica y de control, despues la produccion de telemetria experta y solo entonces reutilizar el pipeline neuronal ya existente para dataset, entrenamiento, benchmark y reporte.

## Architecture Decisions

- El primer entregable real no es una red, sino una baseline de dron generico y PD suficientemente defendible para producir datos.
- La baseline oficial se expresa como configuracion experimental trazable, no como conocimiento tacito repartido entre codigo y documentos.
- El controlador experto sigue siendo el cascaded controller actual; cualquier ajuste debe quedar asociado al baseline del dron.
- La telemetria persistida es la unica fuente oficial para dataset y entrenamiento.
- El control sigue usando `observed_state` y la evaluacion `true_state`.
- `MLP`, `GRU` y `LSTM` son las unicas arquitecturas dentro del alcance.
- Benchmark principal, OOD y reporte final deben quedar separados a nivel metodologico y de artefactos.

## Task List

### Phase 1: Baseline Del Dron Generico

- [ ] Task 1: Fijar el perfil baseline del dron generico
- [ ] Task 2: Documentar parametros, unidades y criterios de modificacion
- [ ] Task 3: Cubrir consistencia fisica minima y trazabilidad del baseline

## Task 1: Fijar el perfil baseline del dron generico

**Description:** Definir un perfil oficial del dron generico de referencia, reutilizando el contrato de escenario y parametros de dinamica existentes. Esta tarea debe dejar un baseline unico y reconocible para todas las fases posteriores.

**Acceptance criteria:**
- [ ] Existe un perfil baseline unico para el dron generico de referencia.
- [ ] El baseline fija masa, inercias, limites, actuadores y geometria de rotores de forma coherente.
- [ ] El baseline puede instanciarse dentro del contrato actual sin introducir una via paralela.

**Verification:**
- [ ] Tests pass: pruebas de consistencia basica del perfil baseline.
- [ ] Manual check: el baseline puede ejecutarse en simulacion nominal sin configuracion ad hoc externa.

**Dependencies:** None

**Estimated scope:** Small: 2-4 files

## Task 2: Documentar parametros, unidades y criterios de modificacion

**Description:** Convertir el baseline en un artefacto entendible para el TFG, explicando que significa cada parametro y como debe variarse sin romper el flujo experimental.

**Acceptance criteria:**
- [ ] Los parametros del baseline quedan documentados con unidades, significado y efecto esperado.
- [ ] La documentacion separa fisica, control y configuracion experimental.
- [ ] La documentacion indica que cambios siguen siendo comparables y cuales abren una nueva campaña experimental.

**Verification:**
- [ ] Revision manual: un lector tecnico puede reconstruir el baseline sin leer codigo fuente.
- [ ] Revision manual: la documentacion no depende de conocimiento implicito del desarrollador.

**Dependencies:** Task 1

**Estimated scope:** Small: 1-2 files

## Task 3: Cubrir consistencia fisica minima y trazabilidad del baseline

**Description:** Proteger el baseline con pruebas y metadatos suficientes para que sea reutilizable como fundamento del resto del flujo.

**Acceptance criteria:**
- [ ] Existen pruebas para masa, inercias, limites de empuje y coherencia entre rotores y limites globales.
- [ ] La configuracion baseline deja metadatos suficientes para identificarla en artefactos posteriores.
- [ ] Una configuracion fisicamente incoherente falla con mensajes claros.

**Verification:**
- [ ] Tests pass: pruebas del baseline y sus errores principales.
- [ ] Manual check: los metadatos baseline quedan visibles en la salida experimental.

**Dependencies:** Task 2

**Estimated scope:** Small: 1-3 files

### Checkpoint: Baseline Ready

- [ ] El dron generico de referencia ya existe como baseline unico y trazable
- [ ] Sus parametros ya estan documentados y protegidos por pruebas
- [ ] El proyecto ya tiene una base experimental clara antes de hablar de trayectorias o redes

### Phase 2: Validacion PD

- [ ] Task 4: Definir el escenario minimo de validacion PD
- [ ] Task 5: Fijar criterios de aceptacion observables para la baseline experta
- [ ] Task 6: Exponer la validacion PD con salida reutilizable y pruebas

## Task 4: Definir el escenario minimo de validacion PD

**Description:** Crear el escenario minimo que pruebe estabilidad y seguimiento razonable del PD sobre el dron baseline. Esta tarea cierra el primer vertical slice demoable del flujo.

**Acceptance criteria:**
- [ ] Existe un escenario minimo de validacion PD asociado al baseline oficial.
- [ ] La trayectoria minima queda definida de forma explicita y reproducible.
- [ ] El escenario puede ejecutarse sin decisiones manuales adicionales.

**Verification:**
- [ ] Tests pass: prueba del escenario minimo y su ejecucion.
- [ ] Manual check: la simulacion produce un comportamiento interpretable y no divergente.

**Dependencies:** Task 3

**Estimated scope:** Small: 2-4 files

## Task 5: Fijar criterios de aceptacion observables para la baseline experta

**Description:** Definir que significa "el PD funciona correctamente" en este proyecto, con umbrales y reglas observables que habiliten o bloqueen la generacion de dataset.

**Acceptance criteria:**
- [ ] Existen criterios de aceptacion explicitamente documentados para la baseline PD.
- [ ] Los criterios cubren error de seguimiento, estabilidad, saturacion y coherencia temporal.
- [ ] La validacion deja claro cuando la baseline es apta para producir telemetria fuente.

**Verification:**
- [ ] Revision manual: los criterios son comprensibles y defendibles para el TFG.
- [ ] Tests pass: al menos una prueba usa esos criterios como gate observable.

**Dependencies:** Task 4

**Estimated scope:** Small: 1-2 files

## Task 6: Exponer la validacion PD con salida reutilizable y pruebas

**Description:** Convertir la validacion PD en una etapa operable que produzca telemetria y metadata reutilizables por fases posteriores.

**Acceptance criteria:**
- [ ] La validacion PD genera una salida persistida y trazable.
- [ ] La telemetria conserva metadata de baseline, controlador y trayectoria.
- [ ] Existen pruebas del recorrido feliz y de configuraciones invalidas principales.

**Verification:**
- [ ] Tests pass: suite dirigida a la validacion PD y su persistencia.
- [ ] Manual check: un usuario puede ejecutar la validacion como primer recorrido minimo del sistema.

**Dependencies:** Task 5

**Estimated scope:** Medium: 3-5 files

### Checkpoint: Expert Gate Ready

- [ ] Ya existe un gate formal que decide si la baseline PD es apta para generar datos
- [ ] La telemetria baseline ya puede persistirse con trazabilidad suficiente
- [ ] El flujo minimo ya tiene una primera demo extremo a extremo antes de dataset

### Phase 3: Telemetria Fuente Y Dataset

- [ ] Task 7: Definir la bateria minima de trayectorias fuente
- [ ] Task 8: Generar telemetria experta reproducible desde la bateria minima
- [ ] Task 9: Preparar dataset trazable desde telemetria persistida

## Task 7: Definir la bateria minima de trayectorias fuente

**Description:** Seleccionar y documentar un conjunto pequeno de trayectorias nativas suficiente para producir datos utiles sin perder simplicidad metodologica.

**Acceptance criteria:**
- [ ] Existe una bateria minima documentada y separada del escenario de validacion PD.
- [ ] La bateria incluye suficiente diversidad para no limitarse a hover trivial.
- [ ] La bateria queda fijada como protocolo experimental repetible.

**Verification:**
- [ ] Revision manual: la bateria es pequena, explicita y defendible.
- [ ] Tests pass: las trayectorias seleccionadas pueden ejecutarse en el simulador.

**Dependencies:** Task 6

**Estimated scope:** Small: 1-3 files

## Task 8: Generar telemetria experta reproducible desde la bateria minima

**Description:** Convertir la bateria fuente en una etapa operable que produzca episodios persistidos con toda la metadata necesaria para entrenamiento posterior.

**Acceptance criteria:**
- [ ] La bateria minima produce telemetrias persistidas reutilizables.
- [ ] Cada episodio identifica baseline, trayectoria, ganancias y seed.
- [ ] La salida deja clara la relacion entre validacion PD y generacion de datos fuente.

**Verification:**
- [ ] Tests pass: pruebas de generacion y lectura de telemetria fuente.
- [ ] Manual check: los episodios resultantes son trazables y consistentes.

**Dependencies:** Task 7

**Estimated scope:** Medium: 3-5 files

## Task 9: Preparar dataset trazable desde telemetria persistida

**Description:** Reutilizar la capa de dataset existente para cerrar el paso telemetria -> dataset dentro del flujo minimo reproducible.

**Acceptance criteria:**
- [ ] Existe un flujo operable que transforma telemetria fuente en dataset listo para entrenamiento.
- [ ] El dataset persiste seeds, split, feature mode y procedencia de episodios.
- [ ] Los artefactos de dataset quedan separados y encadenados respecto a la telemetria fuente.

**Verification:**
- [ ] Tests pass: smoke test del paso telemetria -> dataset.
- [ ] Manual check: el dataset puede inspeccionarse y reutilizarse sin pasos manuales ocultos.

**Dependencies:** Task 8

**Estimated scope:** Small: 2-4 files

### Checkpoint: Dataset Ready

- [ ] El proyecto ya produce telemetria experta util y reproducible
- [ ] El paso a dataset ya es operativo y auditable
- [ ] La cadena baseline -> PD -> telemetria -> dataset ya esta cerrada

### Phase 4: Entrenamiento E Inspeccion

- [ ] Task 10: Integrar entrenamiento operable para `MLP`, `GRU` y `LSTM`
- [ ] Task 11: Persistir resumentes legibles y configuracion efectiva de checkpoints
- [ ] Task 12: Exponer inspeccion y repeticion controlada de entrenamiento

## Task 10: Integrar entrenamiento operable para `MLP`, `GRU` y `LSTM`

**Description:** Reutilizar el pipeline neuronal existente para dejar entrenamiento reproducible dentro del flujo minimo, preservando el vinculo con dataset y baseline fuente.

**Acceptance criteria:**
- [ ] Existe un flujo operable para entrenar `MLP`, `GRU` y `LSTM`.
- [ ] El entrenamiento consume el dataset oficial sin vias paralelas.
- [ ] La salida produce checkpoints validos y comparables.

**Verification:**
- [ ] Tests pass: smoke tests de entrenamiento denso y recurrente.
- [ ] Manual check: una corrida corta deja checkpoints utilizables por benchmark.

**Dependencies:** Task 9

**Estimated scope:** Medium: 3-5 files

## Task 11: Persistir resumentes legibles y configuracion efectiva de checkpoints

**Description:** Hacer auditables los resultados de entrenamiento, exponiendo arquitectura, ventana, features, seeds y metricas sin depender de cargar el checkpoint desde codigo.

**Acceptance criteria:**
- [ ] Cada entrenamiento deja checkpoint, resumen legible y configuracion efectiva persistida.
- [ ] Los artefactos reflejan el origen experimental del dataset y baseline.
- [ ] La salida mantiene una convencion estable para futuras campañas experimentales.

**Verification:**
- [ ] Tests pass: pruebas de sidecars y manifests de checkpoint.
- [ ] Manual check: el resumen de un checkpoint permite reconstruir los parametros importantes.

**Dependencies:** Task 10

**Estimated scope:** Small: 1-3 files

## Task 12: Exponer inspeccion y repeticion controlada de entrenamiento

**Description:** Cerrar esta fase con una capacidad operable de inspeccion y con documentacion suficiente para repetir el entrenamiento variando parametros declarados.

**Acceptance criteria:**
- [ ] Existe un modo de inspeccionar checkpoints y resultados de entrenamiento.
- [ ] La documentacion explica como repetir el entrenamiento modificando hiperparametros o seeds.
- [ ] El flujo deja claro que parametros siguen siendo comparables y cuales cambian la campaña experimental.

**Verification:**
- [ ] Tests pass: pruebas del recorrido de inspeccion.
- [ ] Manual check: un usuario nuevo puede repetir el entrenamiento desde la guia.

**Dependencies:** Task 11

**Estimated scope:** Small: 1-2 files

### Checkpoint: Training Ready

- [ ] `MLP`, `GRU` y `LSTM` ya pueden entrenarse sobre el dataset oficial
- [ ] Cada checkpoint ya es legible, auditable y repetible
- [ ] La cadena baseline -> dataset -> training ya esta cerrada

### Phase 5: Benchmark, OOD Y Reporte

- [ ] Task 13: Ejecutar benchmark principal frente al baseline PD
- [ ] Task 14: Separar benchmark OOD y persistir artefactos finales
- [ ] Task 15: Generar reporte final y guia operativa completa

## Task 13: Ejecutar benchmark principal frente al baseline PD

**Description:** Cerrar la comparacion principal de las tres arquitecturas frente al experto PD ya validado, reutilizando la capa de benchmark existente.

**Acceptance criteria:**
- [ ] Existe un benchmark principal reproducible frente al baseline PD.
- [ ] El benchmark produce resultados comparables para `MLP`, `GRU` y `LSTM`.
- [ ] Los artefactos dejan trazabilidad suficiente hacia checkpoints, dataset y baseline.

**Verification:**
- [ ] Tests pass: smoke test del benchmark principal.
- [ ] Manual check: la comparativa principal puede leerse y seguirse de extremo a extremo.

**Dependencies:** Task 12

**Estimated scope:** Medium: 3-5 files

## Task 14: Separar benchmark OOD y persistir artefactos finales

**Description:** Exponer la evaluacion OOD sin mezclarla con seleccion, manteniendo una frontera metodologica visible y persistida.

**Acceptance criteria:**
- [ ] Existe una ruta separada para benchmark OOD.
- [ ] Los artefactos OOD quedan aislados de los usados para seleccion principal.
- [ ] La salida deja visible que OOD no participa en tuning ni seleccion.

**Verification:**
- [ ] Tests pass: pruebas de separacion entre benchmark principal y OOD.
- [ ] Manual check: la distincion metodologica es visible en salidas y artefactos.

**Dependencies:** Task 13

**Estimated scope:** Small: 1-3 files

## Task 15: Generar reporte final y guia operativa completa

**Description:** Convertir el flujo tecnico en un entregable academico reutilizable con reporte final, seleccion de modelo, figuras y guia paso a paso para repetir el experimento.

**Acceptance criteria:**
- [ ] Existe un reporte final con tabla, seleccion, figuras y resumen metodologico.
- [ ] Existe una guia operativa unica para repetir el flujo cambiando parametros declarados.
- [ ] La guia permite reconstruir la cadena baseline -> telemetria -> dataset -> training -> benchmark -> reporte.

**Verification:**
- [ ] Tests pass: prueba de humo del reporte final.
- [ ] Manual check: un tutor o revisor puede seguir la guia y entender el flujo sin deducirlo desde el codigo.

**Dependencies:** Task 14

**Estimated scope:** Small: 2-4 files

### Checkpoint: Complete

- [ ] El flujo minimo PD -> redes ya queda cerrado de extremo a extremo
- [ ] La separacion metodologica entre benchmark principal y OOD ya es visible y estable
- [ ] El proyecto ya dispone de documentacion suficiente para repetir el experimento modificando parametros declarados
