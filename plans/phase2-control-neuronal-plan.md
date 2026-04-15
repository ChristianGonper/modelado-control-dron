# Plan: Fase 2 - Control neuronal para seguimiento de trayectorias

> Source PRD: [docs/PRD_phase2_control_neuronal.md](../docs/PRD_phase2_control_neuronal.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Controller boundary**: cualquier política candidata debe integrarse a través del mismo contrato de controlador que ya consume el runner y debe devolver el mismo comando de alto nivel usado por la dinámica.
- **Training source of truth**: el dataset se construirá desde telemetría persistida exportada por el simulador, no desde hooks ad hoc acoplados al runner.
- **Observability policy**: entrenamiento e inferencia usan observación (`observed_state` + referencia); las métricas de seguimiento usan estado físico verdadero (`true_state`).
- **Feature schema**: la representación base de entrada queda fijada por observación continua, cuaternión unitario, referencia activa y codificación trigonométrica del yaw; la vista recomendada añade errores explícitos de seguimiento.
- **Target schema**: la salida objetivo del modelo es un mando de alto nivel con thrust colectivo y torques en cuerpo.
- **Temporal policy**: MLP usa ventana apilada; GRU y LSTM usan secuencias temporales; las ventanas nunca cruzan episodios.
- **Split policy**: la partición oficial es `70/15/15` por episodios completos, estratificada por familia de trayectoria y régimen de perturbación; la robustez fuera de distribución vive en una batería separada.
- **Evaluation policy**: la comparación oficial entre baseline y candidatos se decide con vuelos completos dentro del simulador, no con loss offline aislada.
- **Reproducibility artifacts**: cada ejecución relevante debe dejar trazabilidad suficiente de escenarios, seeds, configuración de features, normalización, arquitectura y checkpoint.

---

## Phase 1: Dataset Slice End-to-End

**User stories**: 1, 2, 3, 4, 8, 10, 24, 29

### What to build

Construir el primer slice vertical que toma ejecuciones del controlador clásico ya exportadas por el simulador, las convierte en episodios reutilizables, aplica la política de observabilidad fijada en el PRD, genera features y targets consistentes y produce particiones `train/validation/test` reproducibles sin leakage temporal. El resultado de esta fase debe ser un dataset versionado, auditable y listo para alimentar un primer entrenamiento real.

### Acceptance criteria

- [ ] El pipeline puede leer telemetría persistida del simulador y transformarla en ejemplos supervisados con observación, referencia y acción experta.
- [ ] Las features respetan la convención cerrada en el PRD, incluyendo cuaternión, codificación del yaw y modo recomendado con errores explícitos de seguimiento.
- [ ] Las ventanas temporales se generan sin cruzar episodios y cada ventana hereda correctamente el split del episodio de origen.
- [ ] La partición `70/15/15` es determinista, estratificada por buckets experimentales y comprobable desde metadatos del dataset.
- [ ] El dataset resultante deja artefactos suficientes para reconstruir cómo se generó: escenarios, seeds, modo de features, normalización y política de split.

---

## Phase 2: Baseline Neural Controller Slice

**User stories**: 5, 8, 9, 11, 21, 22, 23, 24

### What to build

Implementar el primer camino completo de entrenamiento a vuelo con una MLP baseline. Esta fase debe tomar el dataset de la fase anterior, entrenar un modelo con la configuración temporal acordada para MLP, guardar un checkpoint con metadatos completos, recargarlo como controlador válido del simulador y ejecutar vuelos completos de benchmark contra el baseline clásico en un subconjunto representativo de escenarios.

### Acceptance criteria

- [ ] Existe una configuración de entrenamiento reproducible para MLP que consume el dataset oficial y produce checkpoints auditables.
- [ ] El checkpoint conserva suficiente información para reconstruir arquitectura, normalización, ventana y esquema de entrada/salida.
- [ ] Un adaptador de inferencia puede cargar el checkpoint y producir un comando válido bajo el contrato actual del simulador.
- [ ] El runner puede ejecutar vuelos completos con la MLP integrada sin scripts especiales ni bypasses del contrato de controlador.
- [ ] La fase genera una primera comparación extremo a extremo entre baseline clásico y MLP en escenarios homogéneos con resultados persistidos.

---

## Phase 3: Recurrent Controller Slice

**User stories**: 6, 7, 8, 9, 11, 18, 21, 23, 24, 29

### What to build

Extender el camino ya validado a políticas recurrentes GRU y LSTM, manteniendo fijo el resto del experimento. Esta fase debe añadir soporte completo para secuencias, batching temporal y checkpoints recurrentes, y demostrar que ambos modelos pueden entrenarse, cargarse y volar en el simulador bajo el mismo contrato y los mismos escenarios principales que la MLP.

### Acceptance criteria

- [ ] El pipeline soporta entrenamiento secuencial stateless por batch para GRU y LSTM con las longitudes de ventana acordadas.
- [ ] GRU y LSTM pueden usar exactamente la misma familia de features por instante que la MLP, sin introducir representaciones ad hoc por arquitectura.
- [ ] Los checkpoints recurrentes pueden recargarse en inferencia con la misma normalización y política temporal usadas en entrenamiento.
- [ ] El runner puede ejecutar vuelos completos con controladores GRU y LSTM integrados a través del contrato oficial.
- [ ] La fase deja resultados comparables de tiempo de inferencia y comportamiento de vuelo para MLP, GRU y LSTM sobre una misma batería principal.

---

## Phase 4: Metrics And Comparison Slice

**User stories**: 12, 14, 15, 16, 17, 18, 20, 25, 26, 30

### What to build

Ampliar la capa de evaluación para que la comparación entre controlador clásico, MLP, GRU y LSTM deje de depender de métricas mínimas y pase a producir una tabla consolidada útil para decidir. Esta fase debe ejecutar la batería principal de escenarios, calcular métricas homogéneas y generar salidas comparativas legibles para análisis cuantitativo y visual.

### Acceptance criteria

- [ ] La evaluación calcula la batería principal de métricas comprometidas en el PRD para comparaciones homogéneas entre ejecuciones.
- [ ] Las métricas distinguen explícitamente la fuente de control y la fuente del estado usado para evaluar el seguimiento.
- [ ] La fase produce una tabla consolidada clásico vs MLP vs GRU vs LSTM a partir de resultados persistidos y no de cálculos manuales.
- [ ] La fase genera gráficas comparativas suficientes para inspeccionar trayectoria, error temporal y comportamiento del control.
- [ ] El mejor candidato de la batería principal puede seleccionarse con un criterio reproducible basado en precisión, suavidad, robustez y coste de inferencia.

---

## Phase 5: Robustness And OOD Slice

**User stories**: 13, 19, 20, 27, 28, 29, 30

### What to build

Construir una batería separada de robustez fuera de distribución que reutilice el mejor pipeline ya validado y someta a baseline y candidatos a condiciones más duras o no vistas en entrenamiento. Esta fase debe dejar clara la frontera metodológica entre generalización dentro de distribución y robustez bajo estrés, y debe producir resultados que puedan citarse con rigor en la memoria del TFG.

### Acceptance criteria

- [ ] Existe una batería de robustez separada del split principal y explícitamente fuera del circuito de selección de hiperparámetros.
- [ ] La batería de robustez reutiliza los mismos controladores y contratos que la evaluación principal, sin crear caminos especiales de ejecución.
- [ ] Los resultados permiten identificar qué degradaciones aparecen bajo condiciones más severas o no vistas.
- [ ] La fase documenta claramente qué conclusiones son válidas dentro de distribución y cuáles solo describen robustez exploratoria.
- [ ] El análisis final deja por escrito riesgos, límites del enfoque de imitation learning y criterio de continuidad hacia la siguiente fase del TFG.

---

## Phase 6: Reproducibility And Thesis Delivery Slice

**User stories**: 22, 25, 26, 27, 28, 30

### What to build

Cerrar el circuito de entrega con un slice de reproducibilidad y packaging experimental. Esta fase debe asegurar que cualquier resultado relevante de la Fase 2 puede regenerarse desde artefactos versionados y que el proyecto queda listo para alimentar tanto la memoria del TFG como la siguiente fase técnica sin depender de conocimiento tácito.

### Acceptance criteria

- [ ] Los artefactos clave de la fase quedan organizados y descritos de forma que otra persona pueda repetir el benchmark principal.
- [ ] Cada resultado relevante referencia escenarios, seeds, checkpoint, modo de features, ventana y configuración de evaluación.
- [ ] El proyecto deja una narrativa clara de qué arquitectura fue seleccionada y por qué.
- [ ] La documentación deja explícitas las simplificaciones, límites y riesgos metodológicos de la Fase 2.
- [ ] La salida final de la fase es utilizable tanto para la memoria del TFG como para iniciar la fase siguiente sin redescubrir decisiones ya cerradas.
