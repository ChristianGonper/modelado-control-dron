# Plan: Flujo Operable De Control Neuronal

> Source PRD: [docs/PRD_control_neuronal_operable.md](../docs/PRD_control_neuronal_operable.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Product boundary**: el alcance cubre una capa operable sobre el pipeline neuronal ya existente, no una reescritura del sistema de aprendizaje ni del runner.
- **Command surface**: la superficie oficial de uso debe vivir bajo el mismo comando raíz del simulador y agrupar dataset, entrenamiento, benchmark, reporte e inspección.
- **Controller boundary**: cualquier modelo entrenado debe seguir integrándose a través del contrato actual de controlador y devolver el mismo tipo de mando que ya consume la dinámica.
- **Training source of truth**: el flujo operable seguirá construyéndose desde telemetría persistida exportada por el simulador, no desde hooks ad hoc incrustados en ejecución.
- **Observability policy**: el control se calcula desde `observed_state` y la evaluación del seguimiento se realiza sobre `true_state`; esta convención debe mantenerse visible en CLI, artefactos y documentación.
- **Architecture scope**: la experiencia operable oficial cubre exactamente `MLP`, `GRU` y `LSTM`; no se amplía a otras familias de modelos en este plan.
- **Parameter policy**: seeds, modo de features, split, rutas de entrada/salida y metadatos de experimento deben expresarse con una terminología común; los hiperparámetros específicos de arquitectura se exponen de forma separada.
- **Artifact policy**: cada etapa debe dejar artefactos trazables y encadenables, distinguiendo claramente dataset, checkpoints, benchmark principal, benchmark OOD y reportes.
- **Reuse-before-rewrite policy**: la implementación debe reutilizar los módulos internos ya existentes de dataset, entrenamiento, benchmark y reporting antes de introducir nuevas capas.
- **Methodology boundary**: el benchmark principal y la batería OOD permanecen separados tanto en ejecución como en interpretación de resultados.

---

## Phase 1: CLI Base Y Convencion De Artefactos

**User stories**: 1, 2, 7, 17, 18, 19, 20, 24, 27, 30

### What to build

Construir el primer slice vertical del flujo operable: una superficie CLI pública y coherente para el control neuronal, junto con una convención estable de carpetas, nombres de artefactos y mensajes de ejecución. Esta fase debe permitir descubrir el flujo, entender qué entra y qué sale en cada paso y ejecutar un recorrido mínimo sin scripts externos, aunque todavía no cubra todas las variantes del pipeline completo.

### Acceptance criteria

- [ ] Existe un espacio de comandos de control neuronal bajo el comando raíz del simulador.
- [ ] La ayuda CLI describe claramente etapas, entradas, salidas, defaults y precondiciones del flujo.
- [ ] La ejecución crea una convención reconocible para artefactos intermedios y finales sin mezclar dataset, checkpoints, benchmark y reportes.
- [ ] Las validaciones de argumentos fallan pronto y con mensajes claros ante combinaciones inválidas o entradas incompletas.
- [ ] Un usuario nuevo puede identificar desde la CLI cuál es el recorrido mínimo recomendado para empezar.

---

## Phase 2: Dataset Operable Desde CLI

**User stories**: 8, 17, 21, 24, 25, 27, 28

### What to build

Añadir el slice completo de preparación o registro de dataset desde CLI, reutilizando la telemetría persistida como fuente oficial. Esta fase debe permitir tomar uno o varios artefactos de telemetría, convertirlos en episodios reutilizables para entrenamiento y dejar trazabilidad suficiente de cómo se construyó ese dataset dentro de una ejecución operable y repetible.

### Acceptance criteria

- [ ] Existe un comando CLI que toma telemetría persistida y genera o registra un dataset listo para entrenamiento.
- [ ] El dataset resultante conserva seeds, política de split, modo de features y procedencia de la telemetría.
- [ ] La salida distingue claramente artefactos de dataset respecto a checkpoints y reportes posteriores.
- [ ] El flujo deja suficiente trazabilidad para reconstruir qué comando produjo el dataset y con qué parámetros efectivos.
- [ ] Un recorrido mínimo reproducible puede detenerse en dataset y dejar un artefacto reutilizable por fases posteriores.

---

## Phase 3: Entrenamiento Individual E Inspeccion De Checkpoints

**User stories**: 3, 4, 5, 6, 9, 11, 21, 25, 28, 29

### What to build

Construir el slice de entrenamiento por arquitectura individual, incluyendo presets razonables, overrides explícitos y una capacidad de inspección rápida de checkpoints. Esta fase debe permitir entrenar `MLP`, `GRU` o `LSTM` desde CLI, persistir configuración efectiva y resultados básicos de entrenamiento, y leer después el checkpoint generado sin depender de código Python auxiliar.

### Acceptance criteria

- [ ] Existe un comando CLI para entrenar una arquitectura concreta usando el dataset oficial.
- [ ] La CLI expone parámetros comunes y específicos por arquitectura con defaults reproducibles.
- [ ] Cada entrenamiento persiste checkpoint, resumen legible, configuración efectiva y métricas básicas de train y validation.
- [ ] Existe un comando o modo de inspección que resume features, ventana, seed, normalización y metadatos del checkpoint.
- [ ] Las pruebas cubren al menos una ejecución individual completa y la inspección posterior del checkpoint generado.

---

## Phase 4: Comparativa Completa De Las Tres Arquitecturas

**User stories**: 10, 12, 13, 15, 17, 21, 25, 28, 29

### What to build

Construir el primer slice comparativo completo del flujo neuronal: entrenar o registrar los tres candidatos, cargarlos en el simulador, ejecutar benchmark homogéneo frente al controlador clásico y persistir resultados comparables. Esta fase debe cerrar un camino extremo a extremo que demuestre valor experimental real del flujo operable.

### Acceptance criteria

- [ ] Existe un flujo CLI para ejecutar una comparativa principal entre baseline clásico, `MLP`, `GRU` y `LSTM`.
- [ ] El benchmark principal reutiliza checkpoints válidos y produce resultados homogéneos sobre una misma batería de escenarios.
- [ ] La salida persiste métricas por escenario, trazas comparativas y tiempos de inferencia en CPU.
- [ ] Los artefactos del benchmark dejan claro qué checkpoints y qué configuración experimental se usaron.
- [ ] La fase es demoable de extremo a extremo sin scripts externos al comando principal del simulador.

---

## Phase 5: Benchmark OOD Y Separacion Metodologica

**User stories**: 14, 15, 21, 22, 25, 28, 29

### What to build

Añadir el slice de robustez fuera de distribución como una ruta operable independiente del benchmark principal. Esta fase debe permitir lanzar la batería OOD desde CLI, persistir sus artefactos por separado y dejar explícita en la experiencia de uso la diferencia entre selección principal y robustez exploratoria.

### Acceptance criteria

- [ ] Existe un comando CLI específico para benchmark OOD separado del benchmark principal.
- [ ] Los artefactos OOD quedan claramente aislados de los artefactos usados para selección principal.
- [ ] La salida mantiene la misma trazabilidad experimental que el benchmark principal, incluyendo configuración y checkpoints usados.
- [ ] La documentación y la CLI dejan explícito que el benchmark OOD no debe reutilizarse para tuning o selección.
- [ ] Las pruebas cubren la separación observable entre benchmark principal y benchmark OOD.

---

## Phase 6: Reporte Final Y Guia Operativa

**User stories**: 16, 22, 23, 26, 30

### What to build

Cerrar el flujo con un slice de reporte y documentación operativa que convierta los artefactos experimentales en una salida legible para el TFG. Esta fase debe generar reportes finales, tabla consolidada, figuras y selección de modelo, y además dejar una guía de uso que explique el recorrido mínimo y el recorrido comparativo completo de las tres arquitecturas.

### Acceptance criteria

- [ ] Existe un flujo CLI que genera el reporte final a partir de resultados persistidos del benchmark principal.
- [ ] El reporte final incluye tabla consolidada, selección del mejor modelo y figuras comparativas reutilizables para análisis académico.
- [ ] La salida deja visible la convención metodológica de observación para control y estado verdadero para evaluación.
- [ ] La documentación operativa explica de forma única cómo usar y entender `MLP`, `GRU` y `LSTM` dentro del simulador.
- [ ] Un tutor o revisor puede seguir la guía y entender el flujo experimental sin deducirlo desde el código fuente.
