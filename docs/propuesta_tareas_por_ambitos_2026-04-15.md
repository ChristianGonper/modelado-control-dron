# Propuesta directa de tareas por ámbitos (2026-04-15)

Este documento aterriza, en formato de ejecución, las tareas recomendadas en **dos ámbitos**:

1. **Ámbito A — Física/Ingeniería y simulación**
2. **Ámbito B — Redes neuronales y pipeline de ML**

Las tareas están agrupadas por **categorías de similitud temática** para facilitar planificación y asignación.

---

## Ámbito A — Física/Ingeniería y simulación

### Categoría A1: Validación física y calibración

- [ ] Definir batería mínima de validación con 3 maniobras canónicas: hover, escalón vertical y traslación lateral.
- [ ] Establecer métricas objetivo por maniobra (error de posición, velocidad, yaw, tiempo de asentamiento).
- [ ] Calibrar parámetros efectivos del modelo (`mass_kg`, `inertia_kg_m2`, `parasitic_drag_area_m2`, `induced_hover_loss_ratio`) contra referencias externas.
- [ ] Generar script reproducible de comparación simulación vs referencia y guardar artefactos en carpeta versionada.
- [ ] Añadir criterio de aceptación cuantitativo para declarar el modelo “válido para conclusiones ID”.

### Categoría A2: Actuación, saturación y asignación de esfuerzos

- [ ] Sustituir o complementar el allocator actual por una versión con restricciones (bounded least-squares / QP).
- [ ] Definir política de prioridad en saturación (empuje total > actitud > yaw, o equivalente documentado).
- [ ] Implementar realocación iterativa cuando uno o más rotores saturan.
- [ ] Añadir tests de no regresión para casos con saturación múltiple y maniobras combinadas.
- [ ] Exportar métricas de “mismatch intent vs wrench aplicado” para diagnóstico.

### Categoría A3: Robustez del control clásico

- [ ] Introducir término integral opcional en cascada con anti-windup.
- [ ] Diseñar presets de ganancias por régimen (hover / traslación / maniobra agresiva).
- [ ] Crear suite de tuning reproducible (escenarios + semillas + reporte automático).
- [ ] Medir sensibilidad a `physics_dt_s`, `control_dt_s` y perturbaciones combinadas.
- [ ] Añadir pruebas de estabilidad en horizontes largos.

### Categoría A4: Perturbaciones, sensores y observabilidad

- [ ] Extender modelos de observación con bias lento, drift y ruido anisotrópico por eje.
- [ ] Definir perfiles de fallos de sensor en escenarios (fault injection controlada).
- [ ] Añadir telemetría específica para separar error de dinámica, error de observación y error de control.
- [ ] Incluir escenarios de viento más severo con perfiles temporales diferenciados.
- [ ] Documentar claramente dominios de validez de cada modelo de perturbación.

### Categoría A5: Contratos, trazabilidad y documentación técnica

- [ ] Publicar matriz “supuesto → impacto → límite de validez”.
- [ ] Formalizar versión semántica para contratos de telemetría y dataset.
- [ ] Definir guía de migración de artefactos cuando cambie el esquema.
- [ ] Consolidar convención oficial de marcos de referencia y signos (world/body/yaw).
- [ ] Crear checklist de reproducibilidad para ejecuciones comparativas.

---

## Ámbito B — Redes neuronales y pipeline de ML

### Categoría B1: Cobertura de dataset y calidad de demostraciones

- [ ] Ampliar dataset con mayor diversidad de trayectorias, perturbaciones y semillas.
- [ ] Medir cobertura del espacio de estados/errores y detectar zonas subrepresentadas.
- [ ] Separar explícitamente conjuntos ID y OOD desde la generación de episodios.
- [ ] Incluir escenarios frontera (cercanos a saturación) para mejorar robustez aprendida.
- [ ] Definir umbral mínimo de cobertura antes de lanzar entrenamiento “oficial”.

### Categoría B2: Entrenamiento, generalización y control de varianza

- [ ] Ejecutar barrido acotado de hiperparámetros por arquitectura (MLP/GRU/LSTM).
- [ ] Evaluar sensibilidad a ventana temporal (`window_size`) y `stride`.
- [ ] Repetir entrenamiento con múltiples seeds y reportar media ± desviación.
- [ ] Añadir stopping criterion consistente y política de selección reproducible.
- [ ] Establecer protocolo de validación temporal (splits por bloque temporal, no solo aleatorios).

### Categoría B3: Evaluación comparativa y métricas orientadas a control

- [ ] Publicar tablero único por modelo: precisión, suavidad, robustez, coste de inferencia.
- [ ] Añadir análisis de “failure cases” (top-N peores episodios por modelo).
- [ ] Reportar degradación explícita ID → OOD por métrica clave.
- [ ] Incorporar intervalos de confianza en comparación contra baseline clásico.
- [ ] Añadir métricas de seguridad operacional (picos de mando, saturaciones, oscilaciones sostenidas).

### Categoría B4: Inferencia, despliegue y estabilidad operativa

- [ ] Definir presupuesto máximo de latencia de inferencia por arquitectura.
- [ ] Validar estabilidad de inferencia ante ruido y distribuciones desplazadas.
- [ ] Añadir pruebas de regresión de checkpoints (compatibilidad de carga, metadatos completos).
- [ ] Revisar estrategia de reset de estado interno en recurrentes para evitar contaminación entre episodios.
- [ ] Añadir benchmarking CPU estandarizado con entorno fijo.

### Categoría B5: Gobernanza experimental y reproducibilidad ML

- [ ] Estandarizar estructura de artefactos de entrenamiento/benchmark/reporting.
- [ ] Versionar configuración completa usada en cada resultado publicado.
- [ ] Añadir plantillas de reporte de experimento (objetivo, config, resultados, conclusiones).
- [ ] Definir política de promoción de modelo (de candidato a seleccionado).
- [ ] Consolidar criterios de “afirmación permitida” para evitar sobreconclusiones sim-to-real.

---

## Priorización sugerida (ejecución inmediata)

### Prioridad 1 (arrancar ya)
- A1 Validación física y calibración.
- A2 Actuación/asignación bajo saturación.
- B1 Cobertura de dataset.
- B2 Control de varianza por seeds.

### Prioridad 2 (tras estabilizar base)
- A3 Robustez del control clásico.
- A4 Perturbaciones/sensores.
- B3 Evaluación comparativa con failure cases.
- B4 Latencia e inferencia operativa.

### Prioridad 3 (consolidación)
- A5 Contratos/documentación técnica.
- B5 Gobernanza experimental y reproducibilidad ML.

---

## Entregables esperados por ámbito

### Entregables Ámbito A
- Informe de validación física con criterios de aceptación y error por maniobra.
- Suite de tests de saturación y robustez del allocator.
- Documento de supuestos/límites de validez actualizado.

### Entregables Ámbito B
- Informe comparativo MLP/GRU/LSTM con varianza por seed e ID vs OOD.
- Dataset ampliado con trazabilidad de cobertura.
- Política de selección/promoción de modelos y checklist de reproducibilidad ML.
